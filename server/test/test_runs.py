"""
test_runs.py – Test CRUD per il router /runs.

Endpoint coperti:
    POST   /runs/                            → crea un run
    GET    /runs/runbymodels/{model_id}      → lista run per modello
    GET    /runs/runbyproject/{project_name} → lista run per progetto
    DELETE /runs/{run_id}                    → elimina uno o più run
    PATCH  /runs/update_status               → aggiorna lo stato di un run
"""

import uuid
import requests
from conftest import BASE_URL


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _create_model(project: str = "run_test_project") -> dict:
    payload = {"name": f"m_{uuid.uuid4().hex[:8]}", "project_name": project}
    r = requests.post(f"{BASE_URL}/models/", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def _create_run(model_id: str, hyperparams: dict | None = None, note: str = None) -> dict:
    payload: dict = {"model_id": model_id}
    if hyperparams is not None:
        payload["hyperparameters"] = hyperparams
    if note is not None:
        payload["note"] = note
    r = requests.post(f"{BASE_URL}/runs/", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def _delete_model(model_id: str) -> None:
    requests.delete(f"{BASE_URL}/models/{model_id}")


# ─────────────────────────────────────────────────────────────────────────────
# POST /runs/
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateRun:
    def test_create_run_success(self):
        """Crea un run valido e verifica i campi della risposta."""
        m = _create_model()
        r = requests.post(
            f"{BASE_URL}/runs/",
            json={"model_id": m["id"], "hyperparameters": {"lr": 0.01, "batch": 32}, "note" : "Questa è una nota"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["model_id"] == m["id"]
        assert data["status"] == "running"
        assert "started_at" in data
        assert data["finished_at"] is None
        assert data["hyperparameters"] == {"lr": 0.01, "batch": 32}
        assert data["note"] == "Questa è una nota"
        _delete_model(m["id"])

    def test_create_run_without_hyperparameters(self):
        """Crea un run senza iperparametri (campo opzionale)."""
        m = _create_model()
        r = requests.post(f"{BASE_URL}/runs/", json={"model_id": m["id"]})
        assert r.status_code == 200        
        assert r.json()["hyperparameters"] is None
        _delete_model(m["id"])

    def test_create_run_without_note(self):
        """Crea un run senza note (campo opzionale)"""
        m = _create_model()
        r = requests.post(f"{BASE_URL}/runs/", json={"model_id": m['id']})
        assert r.status_code == 200
        assert r.json()['note'] is None
        _delete_model(m["id"])

    def test_create_run_returns_uuid(self):
        """L'ID restituito deve essere un UUID valido."""
        m = _create_model()
        r = requests.post(f"{BASE_URL}/runs/", json={"model_id": m["id"]})
        assert r.status_code == 200
        uuid.UUID(r.json()["id"])
        _delete_model(m["id"])

    def test_create_run_invalid_model_id(self):
        """model_id inesistente deve restituire un errore (422 o 500)."""
        r = requests.post(
            f"{BASE_URL}/runs/",
            json={"model_id": str(uuid.uuid4())},
        )
        assert r.status_code in (422, 500)

    def test_create_run_missing_model_id(self):
        """Body senza model_id deve restituire 422."""
        r = requests.post(f"{BASE_URL}/runs/", json={})
        assert r.status_code == 422

    def test_create_run_initial_status_is_running(self):
        """Lo stato iniziale deve sempre essere 'running'."""
        m = _create_model()
        run = _create_run(m["id"])
        assert run["status"] == "running"
        _delete_model(m["id"])

# ─────────────────────────────────────────────────────────────────────────────
# GET /runs/{run_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateRun:
    def test_get_run_success(self):
        """Crea un run valido e verifica i campi della risposta."""
        m = _create_model()
        run = _create_run(m["id"], hyperparams ={"lr": 0.01, "batch": 32}, note="Questa è una nota" )

        r = requests.get(f"{BASE_URL}/runs/{run["id"]}")
        
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["model_id"] == m["id"]
        assert data["status"] == "running"
        assert "started_at" in data
        assert data["finished_at"] is None
        assert data["hyperparameters"] == {"lr": 0.01, "batch": 32}
        assert data["note"] == "Questa è una nota"
        _delete_model(m["id"])
    
    def test_get_run_not_present(self):
        r = requests.get(f"{BASE_URL}/runs/runid")
        assert r.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# GET /runs/runbymodels/{model_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestReadRunsByModel:
    def test_read_runs_by_model(self):
        """Recupera i run di un modello esistente."""
        m = _create_model()
        _create_run(m["id"])
        _create_run(m["id"])
        r = requests.get(f"{BASE_URL}/runs/runbymodels/{m['id']}")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        for run in data:
            assert run["model_id"] == m["id"]
        _delete_model(m["id"])

    def test_read_runs_by_model_not_found(self):
        """model_id senza run associati deve restituire 404."""
        r = requests.get(f"{BASE_URL}/runs/runbymodels/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_read_runs_schema(self, created_run):
        """Ogni run deve avere i campi obbligatori."""
        m_id = created_run["model_id"]
        r = requests.get(f"{BASE_URL}/runs/runbymodels/{m_id}")
        assert r.status_code == 200
        for run in r.json():
            for field in ("id", "model_id", "status", "started_at"):
                assert field in run


# ─────────────────────────────────────────────────────────────────────────────
# GET /runs/runbyproject/{project_name}
# ─────────────────────────────────────────────────────────────────────────────

class TestReadRunsByProject:
    def test_read_runs_by_project(self):
        """Recupera i run di un progetto con modelli e run esistenti."""
        proj = f"proj_{uuid.uuid4().hex[:6]}"
        m = _create_model(project=proj)
        _create_run(m["id"])
        r = requests.get(f"{BASE_URL}/runs/runbyproject/{proj}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1
        _delete_model(m["id"])

    def test_read_runs_by_project_not_found(self):
        """Progetto inesistente deve restituire 404."""
        r = requests.get(f"{BASE_URL}/runs/runbyproject/progetto_xyz_inesistente")
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /runs/update_status
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateRunStatus:
    def test_update_status_to_completed(self):
        """Aggiorna lo stato a 'completed' → finished_at viene impostato."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.patch(
            f"{BASE_URL}/runs/update_status",
            json={"run_id": run["id"], "new_status": "completed"},
        )
        assert r.status_code == 200
        assert r.json().get("rows_updated", 0) >= 1
        _delete_model(m["id"])

    def test_update_status_to_failed(self):
        """Aggiorna lo stato a 'failed'."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.patch(
            f"{BASE_URL}/runs/update_status",
            json={"run_id": run["id"], "new_status": "failed"},
        )
        assert r.status_code == 200
        _delete_model(m["id"])

    def test_update_status_invalid_value(self):
        """Stato non valido deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.patch(
            f"{BASE_URL}/runs/update_status",
            json={"run_id": run["id"], "new_status": "invalid_status"},
        )
        assert r.status_code == 422
        _delete_model(m["id"])

    def test_update_status_missing_run_id(self):
        """Senza run_id deve restituire 422."""
        r = requests.patch(
            f"{BASE_URL}/runs/update_status",
            json={"new_status": "completed"},
        )
        assert r.status_code == 422

    def test_update_status_missing_new_status(self):
        """Senza new_status deve restituire 422."""
        r = requests.patch(
            f"{BASE_URL}/runs/update_status",
            json={"run_id": str(uuid.uuid4())},
        )
        assert r.status_code == 422

# ─────────────────────────────────────────────────────────────────────────────
# PATCH /runs/update_note
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateRunNote:
    def test_update_note(self):
        """Aggiorna lo stato a 'completed' → finished_at viene impostato."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.patch(
            f"{BASE_URL}/runs/update_note",
            json={"run_id": run["id"], "new_note": "nuova nota"},
        )
        assert r.status_code == 200
        assert r.json().get("rows_updated", 0) >= 1
        _delete_model(m["id"])

    def test_update_status_missing_run_id(self):
        """Senza run_id deve restituire 422."""
        r = requests.patch(
            f"{BASE_URL}/runs/update_note",
            json={"new_note": "nuova nota"},
        )
        assert r.status_code == 422

    def test_update_note_to_none(self):
        """Update della nota a None deve andare a buon fine"""
        m = _create_model()
        run = _create_run(m["id"], note="Nota")

        r = requests.get(
            f"{BASE_URL}/runs/{run['id']}"
        )
        assert r.status_code == 200
        assert r.json().get("note", None) == 'Nota'

        r = requests.patch(
            f"{BASE_URL}/runs/update_note",
            json={"run_id": run["id"]},
        )
        assert r.status_code == 200
        assert r.json().get("rows_updated",0) >= 1        

        r = requests.get(
            f"{BASE_URL}/runs/{run['id']}"
        )
        assert r.status_code == 200
        assert r.json().get("note", "--") is None

        _delete_model(m["id"])



# ─────────────────────────────────────────────────────────────────────────────
# DELETE /runs/{run_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestDeleteRun:
    def test_delete_single_run(self):
        """Elimina un singolo run con un UUID."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.delete(f"{BASE_URL}/runs/{run['id']}")
        assert r.status_code == 200
        assert "deleted" in r.json().get("detail", "").lower()
        _delete_model(m["id"])

    def test_delete_multiple_runs_comma_separated(self):
        """Elimina più run passando gli UUID separati da virgola."""
        m = _create_model()
        r1 = _create_run(m["id"])
        r2 = _create_run(m["id"])
        ids = f"{r1['id']},{r2['id']}"
        r = requests.delete(f"{BASE_URL}/runs/{ids}")
        assert r.status_code == 200
        _delete_model(m["id"])
