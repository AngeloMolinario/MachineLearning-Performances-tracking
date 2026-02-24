"""
TrainTrack Client — Lightweight Python client for the TrainTrack API.

Usage:
    from traintrack import TrainTrackClient

    tt = TrainTrackClient("http://localhost:8000")

    # Create a model (model_id saved internally)
    tt.create_model("ResNet50", "Image Classification")

    # Start a run (run_id saved internally)
    tt.create_run(hyperparameters={"lr": 0.001, "epochs": 50})

    # Inside your training loop — no need to pass run_id
    for epoch in range(50):
        train_loss = train(...)
        val_loss = validate(...)
        acc = evaluate(...)

        tt.log_loss(step=epoch, split="train", value=train_loss)
        tt.log_loss(step=epoch, split="validation", value=val_loss)
        tt.log_metric(step=epoch, split="validation", metric_name="accuracy", value=acc)

    # Mark run as completed
    tt.complete_run()
"""

import requests
from requests import HTTPError
from typing import Optional
from client.enums import SplitEnum, StatusEnum, MetricEnum

class TrainTrackClient:
    """Simple client for the TrainTrack experiment tracking API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.model_id = None
        self.run_id = None

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

    # ── Models ──────────────────────────────────────

    def create_model(self, name: str, project_name: str):
        """Register a new model. Stores model_id internally."""
        payload = {
            "name": name,
            "project_name": project_name
        }
        try:
            response = self._post("/models/", payload)        
            self.model_id = response.get("id", None)
            return self.model_id
        except HTTPError:
            return None
        

    def get_models(self):
        """List all registered models."""
        return self._get("/models/")
    
    def get_model(self, name, project):
        ''' return the id of the model given its name and project'''
        response = self._get("/models/find", {"model_name" : name, "project_name" : project})
        self.model_id = response.get("id", None)
        return self.model_id
    
    def delete_model(self, model_id: str = None):
        """Delete a model by ID. Uses stored model_id if not provided."""
        mid = model_id or self.model_id
        return self._delete(f"/models/{mid}")

    def delete_project(self, project_name: str):
        """Delete all models in a project."""
        return self._delete(f"/models/project/{project_name}")

    # ── Runs ────────────────────────────────────────

    def create_run(self, hyperparameters: Optional[dict] = None, note: Optional[str] = None, model_id: str = None):
        """Start a new training run. Stores run_id internally."""
        mid = model_id or self.model_id
        if not mid:
            raise ValueError("No model_id available. Call create_model() first or pass model_id.")
        payload = {"model_id": str(mid)}
        if hyperparameters:
            payload["hyperparameters"] = hyperparameters
        if note:
            payload["note"] = note

        response = self._post("/runs/", payload)
        self.run_id = response.get("id", None)
        return self.run_id

    def get_runs(self, model_id: str = None):
        """Get all runs for the current model."""
        mid = model_id or self.model_id
        return self._get(f"/runs/runbymodels/{mid}")

    def complete_run(self, run_id: str = None):
        """Mark the current run as completed."""
        rid = run_id or self.run_id
        return self._patch("/runs/update_status", {
            "run_id": str(rid), "new_status": "completed"
        })

    def fail_run(self, run_id: str = None):
        """Mark the current run as failed."""
        rid = run_id or self.run_id
        return self._patch("/runs/update_status", {
            "run_id": str(rid), "new_status": "failed"
        })

    def delete_run(self, run_id: str = None):
        """Delete a run."""
        rid = run_id or self.run_id
        return self._delete(f"/runs/{rid}")

    # ── Loss ────────────────────────────────────────

    def log_loss(self, step: int, split: SplitEnum, value: float, run_id: str = None):
        """Log a single loss value. split: 'train' or 'validation'."""
        rid = run_id or self.run_id
        return self._post("/loss/", {
            "run_id": str(rid), "step": step, "split": split, "value": value
        })

    def log_losses(self, losses: list[dict], run_id: str = None):
        """
        Log multiple loss values at once.
        losses: list of {"step": int, "split": str, "value": float}
        """
        rid = run_id or self.run_id
        batch = [{"run_id": str(rid), **l} for l in losses]
        return self._post("/loss/batch", {"run_id": str(rid), "losses": batch})

    def get_losses(self, split: Optional[SplitEnum] = None, run_id: str = None):
        """Get loss values for the current run."""
        rid = run_id or self.run_id
        params = {"run_id": str(rid)}
        if split:
            params["split"] = split
        return self._get("/loss/", params)

    # ── Metrics ─────────────────────────────────────

    def log_metric(self, step: int, split: SplitEnum, metric_name: MetricEnum,
                   value: float, run_id: str = None):
        """
        Log a single metric value.
        metric_name: 'accuracy', 'f1-score', 'recall', 'precision',
                     'balanced accuracy', 'mse', 'mae'
        """
        rid = run_id or self.run_id
        return self._post("/metric/", {
            "run_id": str(rid), "step": step, "split": split,
            "metric_name": metric_name, "value": value
        })

    def log_metrics(self, metrics: list[dict], run_id: str = None):
        """
        Log multiple metric values at once.
        metrics: list of {"step": int, "split": str, "metric_name": str, "value": float}
        """
        rid = run_id or self.run_id
        batch = [{"run_id": str(rid), **m} for m in metrics]
        return self._post("/metric/batch", {"run_id": str(rid), "metrics": batch})

    def get_metrics(self, split: Optional[SplitEnum] = None,
                    metric_name: Optional[MetricEnum] = None, run_id: str = None):
        """Get metric values for the current run."""
        rid = run_id or self.run_id
        params = {"run_id": str(rid)}
        if split:
            params["split"] = split
        if metric_name:
            params["metric_name"] = metric_name
        return self._get("/metric/", params)
