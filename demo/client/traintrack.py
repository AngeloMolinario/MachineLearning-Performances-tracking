"""
traintrack.py – TrainTrack client, versione 2.

Design goals
────────────
• Una riga per loss, una per metrica.
• Il batch upload è trasparente: le loss/metriche vengono accumulate in
  memoria e inviate al server in un'unica chiamata quando si chiama
  flush() o complete_run() / fail_run(), oppure all'uscita del context
  manager.
• Il supporto multitask è trasparente: omettere task_name (o passare
  None) indica un esperimento single-task; passare una stringa indica
  un task specifico in un esperimento multitask.
• Il context manager gestisce automaticamente l'apertura e la chiusura
  del run:

      with TrainTrackClient("http://localhost:8000") as tt:
          tt.init("ResNet50", "Segmentation")
          tt.run(lr=0.001, epochs=50)
          for epoch in range(50):
              ...
              tt.loss(epoch, train=train_loss, val=val_loss)
              tt.metric(epoch, "accuracy", train=train_acc, val=val_acc)
              tt.flush()   # facoltativo: invia subito anziché ad ogni epoch

Interfaccia rapida (nomi brevi)
───────────────────────────────
  tt.loss(step, train=..., val=..., task_name=None)
  tt.metric(step, metric_name, train=..., val=..., task_name=None)
  tt.flush()
  tt.complete_run() / tt.fail_run()

Interfaccia completa (nomi espliciti, per compatibilità)
────────────────────────────────────────────────────────
  tt.log_loss(step, split, value, task_name=None)
  tt.log_losses(losses)           # lista di dict
  tt.log_metric(step, split, metric_name, value)
  tt.log_metrics(metrics)         # lista di dict
"""

from __future__ import annotations

import requests
from requests import HTTPError
from typing import Optional
from client.enums import SplitEnum, StatusEnum, MetricEnum

# Sentinel usato internamente dal server per le loss single-task.
# L'utente non deve mai conoscerlo: basta passare task_name=None.
_SINGLE_TASK = "__single_task__"


class TrainTrackClient:
    """
    Client ad alto livello per TrainTrack.

    Uso minimo
    ----------
    with TrainTrackClient("http://localhost:8000") as tt:
        tt.init("ResNet50", "Image Classification")
        tt.run(lr=0.001, batch_size=32, epochs=50)

        for epoch in range(50):
            train_loss, val_loss = train_and_validate(...)
            train_acc,  val_acc  = evaluate(...)

            tt.loss(epoch, train=train_loss, val=val_loss)
            tt.metric(epoch, "accuracy", train=train_acc, val=val_acc)

        # complete_run() e flush() vengono chiamati automaticamente
        # all'uscita del context manager.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.model_id: Optional[str] = None
        self.run_id:   Optional[str] = None

        # Buffer per il batch upload
        self._loss_buffer:   list[dict] = []
        self._metric_buffer: list[dict] = []

    # ── Context manager ──────────────────────────────────────────────────────

    def __enter__(self) -> "TrainTrackClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.run_id:
            if exc_type is None:
                self.complete_run()
            else:
                self.fail_run()
        return False  # non sopprime le eccezioni

    # ── HTTP helpers ─────────────────────────────────────────────────────────

    def _post(self, path: str, data: dict):
        r = requests.post(f"{self.base_url}{path}", json=data)
        r.raise_for_status()
        return r.json()

    def _get(self, path: str, params: dict = None):
        r = requests.get(f"{self.base_url}{path}", params=params)
        r.raise_for_status()
        return r.json()

    def _patch(self, path: str, data: dict):
        r = requests.patch(f"{self.base_url}{path}", json=data)
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str):
        r = requests.delete(f"{self.base_url}{path}")
        r.raise_for_status()
        return r.json()

    # ── Setup ────────────────────────────────────────────────────────────────

    def init(self, model_name: str, project_name: str) -> str:
        """
        Registra il modello (o recupera quello esistente) e salva model_id.

        Restituisce il model_id.
        """
        try:
            response = self._post("/models/", {
                "name": model_name,
                "project_name": project_name,
            })
            self.model_id = response["id"]
        except HTTPError as e:
            if e.response is not None and e.response.status_code == 409:
                # Il modello esiste già: recupera l'id
                response = self._get("/models/find", {
                    "model_name": model_name,
                    "project_name": project_name,
                })
                self.model_id = response["id"]
            else:
                raise
        return self.model_id

    def run(
        self,
        note: Optional[str] = None,
        model_id: Optional[str] = None,
        **hyperparameters,
    ) -> str:
        """
        Avvia un nuovo training run e salva run_id.

        Gli iperparametri si passano come keyword arguments:

            tt.run(lr=0.001, batch_size=32, epochs=50)

        Restituisce il run_id.
        """
        mid = model_id or self.model_id
        if not mid:
            raise ValueError("Chiama init() prima di run(), oppure passa model_id.")
        payload: dict = {"model_id": str(mid)}
        if hyperparameters:
            payload["hyperparameters"] = hyperparameters
        if note:
            payload["note"] = note
        response = self._post("/runs/", payload)
        self.run_id = response["id"]
        return self.run_id

    # ── Interfaccia rapida: loss ──────────────────────────────────────────────

    def loss(
        self,
        step: int,
        train: Optional[float] = None,
        val:   Optional[float] = None,
        task_name: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> None:
        """
        Aggiunge loss al buffer (non invia subito al server).

        Uso tipico — single-task, un epoch, train + val in una riga:
            tt.loss(epoch, train=train_loss, val=val_loss)

        Uso multitask — una riga per task:
            tt.loss(epoch, train=seg_loss, val=seg_val, task_name="segmentation")
            tt.loss(epoch, train=det_loss, val=det_val, task_name="detection")

        I dati vengono inviati al server con tt.flush(), tt.complete_run()
        o automaticamente all'uscita del context manager.
        """
        rid       = run_id or self.run_id
        task      = task_name if task_name is not None else _SINGLE_TASK
        if train is not None:
            self._loss_buffer.append({
                "run_id": str(rid), "step": step,
                "split": SplitEnum.train, "value": train, "task_name": task,
            })
        if val is not None:
            self._loss_buffer.append({
                "run_id": str(rid), "step": step,
                "split": SplitEnum.validation, "value": val, "task_name": task,
            })

    def metric(
        self,
        step: int,
        metric_name: str,
        train: Optional[float] = None,
        val:   Optional[float] = None,
        run_id: Optional[str] = None,
    ) -> None:
        """
        Aggiunge metriche al buffer (non invia subito al server).

        Uso tipico:
            tt.metric(epoch, "accuracy", train=train_acc, val=val_acc)
            tt.metric(epoch, "f1-score", val=f1)

        I dati vengono inviati con tt.flush() o tt.complete_run().
        """
        rid = run_id or self.run_id
        if train is not None:
            self._metric_buffer.append({
                "run_id": str(rid), "step": step,
                "split": SplitEnum.train, "metric_name": metric_name, "value": train,
            })
        if val is not None:
            self._metric_buffer.append({
                "run_id": str(rid), "step": step,
                "split": SplitEnum.validation, "metric_name": metric_name, "value": val,
            })

    # ── Flush ────────────────────────────────────────────────────────────────

    def flush(self, run_id: Optional[str] = None) -> dict:
        """
        Invia al server tutti i dati accumulati nel buffer (loss + metriche)
        in due chiamate batch e svuota il buffer.

        Chiamare una volta per epoch se si vuole monitorare in tempo reale,
        oppure lasciare che venga chiamato automaticamente da complete_run().

        Restituisce {"losses": [...], "metrics": [...]} con i record creati.
        """
        rid = run_id or self.run_id
        result: dict = {"losses": [], "metrics": []}

        if self._loss_buffer:
            result["losses"] = self._post("/loss/batch", {
                "run_id": str(rid),
                "losses": self._loss_buffer,
            })
            self._loss_buffer = []

        if self._metric_buffer:
            result["metrics"] = self._post("/metric/batch", {
                "run_id": str(rid),
                "metrics": self._metric_buffer,
            })
            self._metric_buffer = []

        return result

    # ── Stato del run ────────────────────────────────────────────────────────

    def complete_run(self, run_id: Optional[str] = None):
        """Invia il buffer e marca il run come 'completed'."""
        rid = run_id or self.run_id
        self.flush(rid)
        return self._patch("/runs/update_status", {
            "run_id": str(rid), "new_status": "completed",
        })

    def fail_run(self, run_id: Optional[str] = None):
        """Invia il buffer (se presente) e marca il run come 'failed'."""
        rid = run_id or self.run_id
        self.flush(rid)
        return self._patch("/runs/update_status", {
            "run_id": str(rid), "new_status": "failed",
        })

    # ── Interfaccia completa: log_* (compatibilità v1) ───────────────────────

    def log_loss(
        self,
        step: int,
        split: SplitEnum,
        value: float,
        task_name: Optional[str] = None,
        run_id: Optional[str] = None,
    ):
        """Log singolo — invia subito (non usa il buffer)."""
        rid  = run_id or self.run_id
        task = task_name if task_name is not None else _SINGLE_TASK
        return self._post("/loss/", {
            "run_id": str(rid), "step": step,
            "split": split, "value": value, "task_name": task,
        })

    def log_losses(self, losses: list[dict], run_id: Optional[str] = None):
        """
        Batch upload immediato di una lista di loss.
        Ogni elemento: {"step": int, "split": str, "value": float, "task_name": str (opzionale)}
        """
        rid   = run_id or self.run_id
        batch = []
        for l in losses:
            item = {"run_id": str(rid), **l}
            if "task_name" not in item or item["task_name"] is None:
                item["task_name"] = _SINGLE_TASK
            batch.append(item)
        return self._post("/loss/batch", {"run_id": str(rid), "losses": batch})

    def log_metric(
        self,
        step: int,
        split: SplitEnum,
        metric_name: MetricEnum,
        value: float,
        run_id: Optional[str] = None,
    ):
        """Log singolo — invia subito (non usa il buffer)."""
        rid = run_id or self.run_id
        return self._post("/metric/", {
            "run_id": str(rid), "step": step,
            "split": split, "metric_name": metric_name, "value": value,
        })

    def log_metrics(self, metrics: list[dict], run_id: Optional[str] = None):
        """
        Batch upload immediato di una lista di metriche.
        Ogni elemento: {"step": int, "split": str, "metric_name": str, "value": float}
        """
        rid   = run_id or self.run_id
        batch = [{"run_id": str(rid), **m} for m in metrics]
        return self._post("/metric/batch", {"run_id": str(rid), "metrics": batch})

    # ── Query ────────────────────────────────────────────────────────────────

    def get_losses(
        self,
        split: Optional[SplitEnum] = None,
        task_name: Optional[str] = None,
        limit: Optional[int] = None,
        run_id: Optional[str] = None,
    ):
        """Recupera le loss del run corrente con filtri opzionali."""
        rid    = run_id or self.run_id
        params = {"run_id": str(rid)}
        if split:
            params["split"] = split
        if task_name is not None:
            params["task_name"] = task_name if task_name != "" else _SINGLE_TASK
        if limit:
            params["limit"] = limit
        return self._get("/loss/", params)

    def get_metrics(
        self,
        split: Optional[SplitEnum] = None,
        metric_name: Optional[MetricEnum] = None,
        limit: Optional[int] = None,
        run_id: Optional[str] = None,
    ):
        """Recupera le metriche del run corrente con filtri opzionali."""
        rid    = run_id or self.run_id
        params = {"run_id": str(rid)}
        if split:
            params["split"] = split
        if metric_name:
            params["metric_name"] = metric_name
        if limit:
            params["limit"] = limit
        return self._get("/metric/", params)

    def get_models(self):
        return self._get("/models/")

    def get_runs(self, model_id: Optional[str] = None):
        mid = model_id or self.model_id
        return self._get(f"/runs/runbymodels/{mid}")

    # ── Cancellazione ────────────────────────────────────────────────────────

    def delete_model(self, model_id: Optional[str] = None):
        mid = model_id or self.model_id
        return self._delete(f"/models/{mid}")

    def delete_project(self, project_name: str):
        return self._delete(f"/models/project/{project_name}")

    def delete_run(self, run_id: Optional[str] = None):
        rid = run_id or self.run_id
        return self._delete(f"/runs/{rid}")