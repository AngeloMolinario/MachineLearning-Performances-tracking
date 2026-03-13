"""
test_losses.py – Test per il router /loss.

Endpoint coperti:
    POST  /loss/        → crea un singolo record di loss
    POST  /loss/batch   → crea più record di loss in un'unica richiesta
    GET   /loss/        → recupera le loss (filtri: run_id, split, task_name, limit)

Convenzioni sui task_name:
    - Single-task: task_name omesso nel payload → il server applica il default "__single_task__"
    - Multitask:   task_name esplicito nel payload (es. "segmentation", "detection")

Note sui test che usano created_run (scope=session):
    I test che condividono il run di sessione non possono assumere conteggi
    esatti perché altri test potrebbero aver già inserito loss sullo stesso run.
    Usano quindi asserzioni ">= N" oppure creano run isolati.
"""

import uuid
import requests
from conftest import BASE_URL

SINGLE_TASK = "__single_task__"


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _create_model() -> dict:
    payload = {"name": f"loss_m_{uuid.uuid4().hex[:8]}", "project_name": "loss_project"}
    r = requests.post(f"{BASE_URL}/models/", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def _create_run(model_id: str) -> dict:
    r = requests.post(f"{BASE_URL}/runs/", json={"model_id": model_id})
    assert r.status_code == 200, r.text
    return r.json()


def _delete_model(model_id: str) -> None:
    requests.delete(f"{BASE_URL}/models/{model_id}")


def _post_loss(
    run_id: str,
    step: int,
    split: str,
    value: float,
    task_name: str | None = None,
) -> requests.Response:
    """
    Helper per POST /loss/.
    Se task_name è None il campo viene omesso dal payload: il server
    applica il default "__single_task__".
    """
    payload = {"run_id": run_id, "step": step, "split": split, "value": value}
    if task_name is not None:
        payload["task_name"] = task_name
    return requests.post(f"{BASE_URL}/loss/", json=payload)


def _post_loss_batch(run_id: str, losses: list[dict]) -> requests.Response:
    """Helper per POST /loss/batch."""
    return requests.post(
        f"{BASE_URL}/loss/batch",
        json={"run_id": run_id, "losses": losses},
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /loss/ — single-task
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateLoss:
    def test_create_loss_train_success(self):
        """Crea una loss di training senza task_name e verifica i campi restituiti."""
        m = _create_model()
        run = _create_run(m["id"])
        r = _post_loss(run["id"], step=1, split="train", value=0.534)
        assert r.status_code == 200
        data = r.json()
        assert data["run_id"] == run["id"]
        assert data["step"] == 1
        assert data["split"] == "train"
        assert abs(data["value"] - 0.534) < 1e-6
        assert "timestamp" in data
        assert data["task_name"] == SINGLE_TASK
        _delete_model(m["id"])

    def test_create_loss_validation_split(self):
        """Crea una loss di validation."""
        m = _create_model()
        run = _create_run(m["id"])
        r = _post_loss(run["id"], step=1, split="validation", value=0.8)
        assert r.status_code == 200
        assert r.json()["split"] == "validation"
        assert r.json()["task_name"] == SINGLE_TASK
        _delete_model(m["id"])

    def test_create_loss_invalid_split(self):
        """Split non valido deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        r = _post_loss(run["id"], step=1, split="test", value=0.5)
        assert r.status_code == 422
        _delete_model(m["id"])

    def test_create_loss_missing_value(self):
        """Senza 'value' deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.post(
            f"{BASE_URL}/loss/",
            json={"run_id": run["id"], "step": 1, "split": "train"},
        )
        assert r.status_code == 422
        _delete_model(m["id"])

    def test_create_loss_missing_step(self):
        """Senza 'step' deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.post(
            f"{BASE_URL}/loss/",
            json={"run_id": run["id"], "split": "train", "value": 0.5},
        )
        assert r.status_code == 422
        _delete_model(m["id"])

    def test_create_loss_invalid_run_id(self):
        """run_id inesistente deve restituire un errore (422 o 500)."""
        r = _post_loss(str(uuid.uuid4()), step=1, split="train", value=0.5)
        assert r.status_code in (422, 500)

    def test_create_loss_schema_contains_task_name_field(self):
        """La risposta deve sempre includere il campo task_name."""
        m = _create_model()
        run = _create_run(m["id"])
        r = _post_loss(run["id"], step=1, split="train", value=0.3)
        assert r.status_code == 200
        assert "task_name" in r.json()
        _delete_model(m["id"])

    def test_duplicate_singletask_same_step_split_is_rejected(self):
        """
        Due loss single-task con identico (run_id, step, split) devono
        violare il vincolo di PK → errore atteso (409/422/500).
        """
        m = _create_model()
        run = _create_run(m["id"])
        _post_loss(run["id"], step=1, split="train", value=0.5)
        r2 = _post_loss(run["id"], step=1, split="train", value=0.6)
        assert r2.status_code in (409, 422, 500), (
            f"Atteso errore per PK duplicata single-task, ricevuto {r2.status_code}"
        )
        _delete_model(m["id"])


# ─────────────────────────────────────────────────────────────────────────────
# POST /loss/ — multitask
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateLossMultitask:
    def test_create_loss_with_task_name(self):
        """Crea una loss con task_name e verifica che venga restituito correttamente."""
        m = _create_model()
        run = _create_run(m["id"])
        r = _post_loss(run["id"], step=1, split="train", value=0.42, task_name="detection")
        assert r.status_code == 200
        data = r.json()
        assert data["task_name"] == "detection"
        assert data["step"] == 1
        assert data["split"] == "train"
        _delete_model(m["id"])

    def test_multitask_same_step_same_split_different_tasks_no_pk_conflict(self):
        """
        Due loss con stesso (run_id, step, split) ma task_name diversi
        devono coesistere senza conflitto di PK.
        """
        m = _create_model()
        run = _create_run(m["id"])
        r1 = _post_loss(run["id"], step=1, split="train", value=0.5, task_name="segmentation")
        r2 = _post_loss(run["id"], step=1, split="train", value=0.3, task_name="detection")
        assert r1.status_code == 200, f"Prima loss multitask fallita: {r1.text}"
        assert r2.status_code == 200, f"Seconda loss multitask fallita: {r2.text}"
        assert r1.json()["task_name"] == "segmentation"
        assert r2.json()["task_name"] == "detection"
        _delete_model(m["id"])

    def test_multitask_all_tasks_across_multiple_steps(self):
        """
        Inserisce N task × M step e verifica che tutti i record vengano
        creati correttamente (nessuna collisione di PK).
        Usa un run isolato per poter verificare il conteggio esatto.
        """
        m = _create_model()
        run = _create_run(m["id"])
        tasks = ["segmentation", "detection", "classification"]
        steps = list(range(1, 6))

        for step in steps:
            for task in tasks:
                r = _post_loss(run["id"], step=step, split="train", value=0.5, task_name=task)
                assert r.status_code == 200, (
                    f"Fallita creazione loss step={step} task={task}: {r.text}"
                )

        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run["id"], "split": "train"},
        )
        assert r.status_code == 200
        # 5 step × 3 task = 15 record
        assert len(r.json()) == len(tasks) * len(steps)
        _delete_model(m["id"])

    def test_multitask_and_singletask_coexist_in_same_run(self):
        """
        Stesso (run_id, step, split): una loss single-task (__single_task__)
        e una multitask (task_name esplicito) devono coesistere senza conflitti.
        """
        m = _create_model()
        run = _create_run(m["id"])
        r_single = _post_loss(run["id"], step=1, split="train", value=0.9)
        r_multi  = _post_loss(run["id"], step=1, split="train", value=0.4, task_name="depth")
        assert r_single.status_code == 200
        assert r_multi.status_code == 200
        assert r_single.json()["task_name"] == SINGLE_TASK
        assert r_multi.json()["task_name"] == "depth"
        _delete_model(m["id"])

    def test_duplicate_task_name_same_step_split_is_rejected(self):
        """
        Due loss con identico (run_id, step, split, task_name) devono
        violare il vincolo di PK → errore atteso (409/422/500).
        """
        m = _create_model()
        run = _create_run(m["id"])
        _post_loss(run["id"], step=1, split="train", value=0.5, task_name="segmentation")
        r2 = _post_loss(run["id"], step=1, split="train", value=0.6, task_name="segmentation")
        assert r2.status_code in (409, 422, 500), (
            f"Atteso errore per PK duplicata, ricevuto {r2.status_code}: {r2.text}"
        )
        _delete_model(m["id"])


# ─────────────────────────────────────────────────────────────────────────────
# POST /loss/batch — single-task
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateLossBatch:
    def test_create_loss_batch_success(self):
        """Invia un batch di loss senza task_name e verifica che vengano tutte create."""
        m = _create_model()
        run = _create_run(m["id"])
        losses = [
            {"run_id": run["id"], "step": i, "split": "train", "value": 1.0 / (i + 1)}
            for i in range(1, 6)
        ]
        r = _post_loss_batch(run["id"], losses)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 5
        for item in data:
            assert item["task_name"] == SINGLE_TASK
        _delete_model(m["id"])

    def test_create_loss_batch_mixed_splits(self):
        """Batch con split misti (train e validation), senza task_name."""
        m = _create_model()
        run = _create_run(m["id"])
        losses = [
            {"run_id": run["id"], "step": 1, "split": "train",      "value": 0.9},
            {"run_id": run["id"], "step": 1, "split": "validation",  "value": 0.85},
        ]
        r = _post_loss_batch(run["id"], losses)
        assert r.status_code == 200
        splits = {item["split"] for item in r.json()}
        assert "train" in splits
        assert "validation" in splits
        _delete_model(m["id"])

    def test_create_loss_batch_empty_list(self):
        """Batch vuoto: comportamento atteso (200 con lista vuota o 422)."""
        m = _create_model()
        run = _create_run(m["id"])
        r = _post_loss_batch(run["id"], [])
        assert r.status_code in (200, 422)
        _delete_model(m["id"])

    def test_create_loss_batch_invalid_item(self):
        """Se un elemento del batch ha split non valido deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        losses = [{"run_id": run["id"], "step": 1, "split": "INVALID", "value": 0.5}]
        r = _post_loss_batch(run["id"], losses)
        assert r.status_code == 422
        _delete_model(m["id"])


# ─────────────────────────────────────────────────────────────────────────────
# POST /loss/batch — multitask
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateLossBatchMultitask:
    def test_batch_multitask_success(self):
        """
        Batch con più task per stesso step: tutti i record devono essere
        inseriti correttamente senza conflitti di PK.
        """
        m = _create_model()
        run = _create_run(m["id"])
        tasks = ["seg", "det", "cls"]
        losses = [
            {"run_id": run["id"], "step": 1, "split": "train", "value": 0.5, "task_name": t}
            for t in tasks
        ]
        r = _post_loss_batch(run["id"], losses)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == len(tasks)
        assert {item["task_name"] for item in data} == set(tasks)
        _delete_model(m["id"])

    def test_batch_multitask_multiple_steps(self):
        """
        Batch con N task × M step: il numero di record restituiti
        deve corrispondere esattamente a N × M.
        """
        m = _create_model()
        run = _create_run(m["id"])
        tasks = ["seg", "det"]
        steps = [1, 2, 3]
        losses = [
            {"run_id": run["id"], "step": s, "split": "train", "value": 0.4, "task_name": t}
            for s in steps
            for t in tasks
        ]
        r = _post_loss_batch(run["id"], losses)
        assert r.status_code == 200
        assert len(r.json()) == len(tasks) * len(steps)
        _delete_model(m["id"])

    def test_batch_mixed_singletask_and_multitask(self):
        """
        Batch che contiene sia loss senza task_name sia loss con task_name:
        entrambi i tipi devono essere creati correttamente.
        """
        m = _create_model()
        run = _create_run(m["id"])
        losses = [
            {"run_id": run["id"], "step": 1, "split": "train", "value": 0.9},
            {"run_id": run["id"], "step": 1, "split": "train", "value": 0.5, "task_name": "seg"},
            {"run_id": run["id"], "step": 1, "split": "train", "value": 0.3, "task_name": "det"},
        ]
        r = _post_loss_batch(run["id"], losses)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        task_names = {item["task_name"] for item in data}
        assert SINGLE_TASK in task_names
        assert "seg" in task_names
        assert "det" in task_names
        _delete_model(m["id"])

    def test_batch_multitask_mixed_splits(self):
        """Batch multitask con split train e validation per gli stessi task."""
        m = _create_model()
        run = _create_run(m["id"])
        losses = [
            {"run_id": run["id"], "step": 1, "split": "train",      "value": 0.5,  "task_name": "seg"},
            {"run_id": run["id"], "step": 1, "split": "validation",  "value": 0.6,  "task_name": "seg"},
            {"run_id": run["id"], "step": 1, "split": "train",      "value": 0.4,  "task_name": "det"},
            {"run_id": run["id"], "step": 1, "split": "validation",  "value": 0.45, "task_name": "det"},
        ]
        r = _post_loss_batch(run["id"], losses)
        assert r.status_code == 200
        assert len(r.json()) == 4
        _delete_model(m["id"])


# ─────────────────────────────────────────────────────────────────────────────
# GET /loss/ — single-task
# ─────────────────────────────────────────────────────────────────────────────

class TestGetLosses:
    def test_get_losses_by_run_id(self, created_run):
        """Recupera le loss di un run esistente: il conteggio deve essere >= 3."""
        run_id = created_run["id"]
        for i in range(1, 4):
            _post_loss(run_id, step=i, split="train", value=0.9 - i * 0.1)
        r = requests.get(f"{BASE_URL}/loss/", params={"run_id": run_id})
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 3

    def test_get_losses_filter_by_split(self, created_run):
        """Filtra per split: solo loss 'validation' devono essere restituite."""
        run_id = created_run["id"]
        _post_loss(run_id, step=100, split="validation", value=0.77)
        r = requests.get(f"{BASE_URL}/loss/", params={"run_id": run_id, "split": "validation"})
        assert r.status_code == 200
        for item in r.json():
            assert item["split"] == "validation"

    def test_get_losses_limit(self, created_run):
        """Il parametro 'limit' deve restringere il numero di risultati."""
        run_id = created_run["id"]
        for i in range(200, 206):
            _post_loss(run_id, step=i, split="train", value=0.5)
        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run_id, "split": "train", "limit": 3},
        )
        assert r.status_code == 200
        assert len(r.json()) <= 3

    def test_get_losses_without_run_id(self):
        """Senza run_id (campo obbligatorio) deve restituire 422."""
        r = requests.get(f"{BASE_URL}/loss/")
        assert r.status_code == 422

    def test_get_losses_schema(self, created_run):
        """Ogni elemento deve avere tutti i campi obbligatori incluso task_name."""
        run_id = created_run["id"]
        _post_loss(run_id, step=999, split="train", value=0.1)
        r = requests.get(f"{BASE_URL}/loss/", params={"run_id": run_id})
        assert r.status_code == 200
        for item in r.json():
            for field in ("run_id", "step", "split", "value", "timestamp", "task_name"):
                assert field in item

    def test_get_losses_ordered_descending_by_step(self, created_run):
        """Le loss devono essere ordinate per step in modo decrescente."""
        run_id = created_run["id"]
        for i in [10, 20, 30]:
            _post_loss(run_id, step=i, split="train", value=0.5)
        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run_id, "split": "train", "limit": 10},
        )
        steps = [item["step"] for item in r.json()]
        assert steps == sorted(steps, reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# GET /loss/ — filtro per task_name
# Tutti i test in questa classe usano run ISOLATI per poter verificare
# conteggi esatti senza interferenze da altri test.
# ─────────────────────────────────────────────────────────────────────────────

class TestGetLossesMultitask:
    def test_filter_by_task_name_returns_only_that_task(self):
        """
        ?task_name=segmentation deve restituire esattamente le loss di quel task,
        escludendo detection e le loss single-task.
        """
        m = _create_model()
        run = _create_run(m["id"])
        for step in range(1, 4):
            _post_loss(run["id"], step=step, split="train", value=0.5, task_name="segmentation")
            _post_loss(run["id"], step=step, split="train", value=0.4, task_name="detection")
            _post_loss(run["id"], step=step, split="train", value=0.9)  # single-task

        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run["id"], "task_name": "segmentation"},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        for item in data:
            assert item["task_name"] == "segmentation"
        _delete_model(m["id"])

    def test_filter_by_singletask_sentinel_returns_only_singletask(self):
        """
        ?task_name=__single_task__ deve restituire solo le loss single-task,
        escludendo quelle multitask.
        """
        m = _create_model()
        run = _create_run(m["id"])
        for step in range(1, 4):
            _post_loss(run["id"], step=step, split="train", value=0.9)
            _post_loss(run["id"], step=step, split="train", value=0.5, task_name="seg")

        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run["id"], "task_name": SINGLE_TASK},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        for item in data:
            assert item["task_name"] == SINGLE_TASK
        _delete_model(m["id"])

    def test_filter_by_task_name_nonexistent_returns_empty(self):
        """
        Filtrare per un task_name inesistente deve restituire lista vuota.
        """
        m = _create_model()
        run = _create_run(m["id"])
        _post_loss(run["id"], step=1, split="train", value=0.5, task_name="seg")

        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run["id"], "task_name": "task_inesistente"},
        )
        assert r.status_code == 200
        assert r.json() == []
        _delete_model(m["id"])

    def test_no_task_filter_returns_all_tasks(self):
        """
        Senza ?task_name, GET /loss/ deve restituire le loss di tutti i task
        incluse le single-task.
        """
        m = _create_model()
        run = _create_run(m["id"])
        _post_loss(run["id"], step=1, split="train", value=0.9)
        _post_loss(run["id"], step=1, split="train", value=0.5, task_name="seg")
        _post_loss(run["id"], step=1, split="train", value=0.4, task_name="det")

        r = requests.get(f"{BASE_URL}/loss/", params={"run_id": run["id"]})
        assert r.status_code == 200
        assert len(r.json()) == 3
        returned_tasks = {item["task_name"] for item in r.json()}
        assert SINGLE_TASK in returned_tasks
        assert "seg" in returned_tasks
        assert "det" in returned_tasks
        _delete_model(m["id"])

    def test_filter_by_task_name_and_split_combined(self):
        """
        task_name + split: solo le loss che soddisfano entrambe le condizioni.
        """
        m = _create_model()
        run = _create_run(m["id"])
        for step in range(1, 4):
            _post_loss(run["id"], step=step, split="train",      value=0.5, task_name="seg")
            _post_loss(run["id"], step=step, split="validation",  value=0.6, task_name="seg")
            _post_loss(run["id"], step=step, split="train",      value=0.4, task_name="det")

        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run["id"], "task_name": "seg", "split": "validation"},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        for item in data:
            assert item["task_name"] == "seg"
            assert item["split"] == "validation"
        _delete_model(m["id"])

    def test_filter_by_task_name_with_limit(self):
        """
        task_name + limit: al più 'limit' record, ordinati per step decrescente.
        """
        m = _create_model()
        run = _create_run(m["id"])
        for step in range(1, 8):
            _post_loss(run["id"], step=step, split="train", value=0.5, task_name="cls")

        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run["id"], "task_name": "cls", "limit": 3},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        steps = [item["step"] for item in data]
        assert steps == sorted(steps, reverse=True)
        _delete_model(m["id"])

    def test_multitask_losses_ordered_descending_by_step(self):
        """Le loss multitask devono rispettare l'ordinamento per step decrescente."""
        m = _create_model()
        run = _create_run(m["id"])
        for step in [5, 2, 8, 1, 4]:
            _post_loss(run["id"], step=step, split="train", value=0.5, task_name="seg")

        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run["id"], "task_name": "seg"},
        )
        assert r.status_code == 200
        steps = [item["step"] for item in r.json()]
        assert steps == sorted(steps, reverse=True)
        _delete_model(m["id"])