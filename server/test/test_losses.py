"""
test_losses.py – Test per il router /loss.

Endpoint coperti:
    POST  /loss/        → crea un singolo record di loss
    POST  /loss/batch   → crea più record di loss in un'unica richiesta
    GET   /loss/        → recupera le loss (filtri: run_id, split, limit)
"""

import uuid
import requests
from conftest import BASE_URL


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


# ─────────────────────────────────────────────────────────────────────────────
# POST /loss/
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateLoss:
    def test_create_loss_train_success(self):
        """Crea una loss di training e verifica i campi restituiti."""
        m = _create_model()
        run = _create_run(m["id"])
        payload = {
            "run_id": run["id"],
            "step": 1,
            "split": "train",
            "value": 0.534,
        }
        r = requests.post(f"{BASE_URL}/loss/", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["run_id"] == run["id"]
        assert data["step"] == 1
        assert data["split"] == "train"
        assert abs(data["value"] - 0.534) < 1e-6
        assert "timestamp" in data
        _delete_model(m["id"])

    def test_create_loss_validation_split(self):
        """Crea una loss di validation."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.post(
            f"{BASE_URL}/loss/",
            json={"run_id": run["id"], "step": 1, "split": "validation", "value": 0.8},
        )
        assert r.status_code == 200
        assert r.json()["split"] == "validation"
        _delete_model(m["id"])

    def test_create_loss_invalid_split(self):
        """Split non valido deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.post(
            f"{BASE_URL}/loss/",
            json={"run_id": run["id"], "step": 1, "split": "test", "value": 0.5},
        )
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
        r = requests.post(
            f"{BASE_URL}/loss/",
            json={"run_id": str(uuid.uuid4()), "step": 1, "split": "train", "value": 0.5},
        )
        assert r.status_code in (422, 500)


# ─────────────────────────────────────────────────────────────────────────────
# POST /loss/batch
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateLossBatch:
    def test_create_loss_batch_success(self):
        """Invia un batch di loss e verifica che vengano tutte create."""
        m = _create_model()
        run = _create_run(m["id"])
        losses = [
            {"run_id": run["id"], "step": i, "split": "train", "value": 1.0 / (i + 1)}
            for i in range(1, 6)
        ]
        payload = {"run_id": run["id"], "losses": losses}
        r = requests.post(f"{BASE_URL}/loss/batch", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 5
        _delete_model(m["id"])

    def test_create_loss_batch_mixed_splits(self):
        """Batch con split misti (train e validation)."""
        m = _create_model()
        run = _create_run(m["id"])
        losses = [
            {"run_id": run["id"], "step": 1, "split": "train", "value": 0.9},
            {"run_id": run["id"], "step": 1, "split": "validation", "value": 0.85},
        ]
        payload = {"run_id": run["id"], "losses": losses}
        r = requests.post(f"{BASE_URL}/loss/batch", json=payload)
        assert r.status_code == 200
        splits = {item["split"] for item in r.json()}
        assert "train" in splits
        assert "validation" in splits
        _delete_model(m["id"])

    def test_create_loss_batch_empty_list(self):
        """Batch vuoto: comportamento atteso (200 con lista vuota o 422)."""
        m = _create_model()
        run = _create_run(m["id"])
        payload = {"run_id": run["id"], "losses": []}
        r = requests.post(f"{BASE_URL}/loss/batch", json=payload)
        assert r.status_code in (200, 422)
        _delete_model(m["id"])

    def test_create_loss_batch_invalid_item(self):
        """Se un elemento del batch ha split non valido deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        losses = [
            {"run_id": run["id"], "step": 1, "split": "INVALID", "value": 0.5},
        ]
        payload = {"run_id": run["id"], "losses": losses}
        r = requests.post(f"{BASE_URL}/loss/batch", json=payload)
        assert r.status_code == 422
        _delete_model(m["id"])


# ─────────────────────────────────────────────────────────────────────────────
# GET /loss/
# ─────────────────────────────────────────────────────────────────────────────

class TestGetLosses:
    def test_get_losses_by_run_id(self, created_run):
        """Recupera le loss di un run esistente."""
        run_id = created_run["id"]
        # Prima inserisce alcune loss
        for i in range(1, 4):
            requests.post(
                f"{BASE_URL}/loss/",
                json={"run_id": run_id, "step": i, "split": "train", "value": 0.9 - i * 0.1},
            )
        r = requests.get(f"{BASE_URL}/loss/", params={"run_id": run_id})
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 3

    def test_get_losses_filter_by_split(self, created_run):
        """Filtra per split: solo loss 'validation' devono essere restituite."""
        run_id = created_run["id"]
        requests.post(
            f"{BASE_URL}/loss/",
            json={"run_id": run_id, "step": 100, "split": "validation", "value": 0.77},
        )
        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run_id, "split": "validation"},
        )
        assert r.status_code == 200
        for item in r.json():
            assert item["split"] == "validation"

    def test_get_losses_limit(self, created_run):
        """Il parametro 'limit' deve restringere il numero di risultati."""
        run_id = created_run["id"]
        # Inserisce 5 step di train
        for i in range(200, 206):
            requests.post(
                f"{BASE_URL}/loss/",
                json={"run_id": run_id, "step": i, "split": "train", "value": 0.5},
            )
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
        """Ogni elemento deve avere i campi obbligatori."""
        run_id = created_run["id"]
        requests.post(
            f"{BASE_URL}/loss/",
            json={"run_id": run_id, "step": 999, "split": "train", "value": 0.1},
        )
        r = requests.get(f"{BASE_URL}/loss/", params={"run_id": run_id})
        assert r.status_code == 200
        for item in r.json():
            for field in ("run_id", "step", "split", "value", "timestamp"):
                assert field in item

    def test_get_losses_ordered_descending_by_step(self, created_run):
        """Le loss devono essere ordinate per step in modo decrescente."""
        run_id = created_run["id"]
        for i in [10, 20, 30]:
            requests.post(
                f"{BASE_URL}/loss/",
                json={"run_id": run_id, "step": i, "split": "train", "value": 0.5},
            )
        r = requests.get(
            f"{BASE_URL}/loss/",
            params={"run_id": run_id, "split": "train", "limit": 10},
        )
        steps = [item["step"] for item in r.json()]
        assert steps == sorted(steps, reverse=True)
