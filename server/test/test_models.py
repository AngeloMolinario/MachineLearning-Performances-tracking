"""
test_models.py – Test CRUD per il router /models.

Endpoint coperti:
    POST   /models/                       → crea un modello
    GET    /models/                       → lista tutti i modelli
    DELETE /models/{model_id}             → elimina per ID
    DELETE /models/project/{project_name} → elimina per nome progetto

Regola di unicità (vincolo DB: UNIQUE(name, project_name)):
    • Stesso nome  + stesso progetto   → ❌ errore (409/422/500)
    • Stesso nome  + progetto diverso  → ✅ permesso
    • Nome diverso + stesso progetto   → ✅ permesso
"""

import uuid
import pytest
import requests
from conftest import BASE_URL


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _create_model(name: str | None = None, project: str = "test_project") -> dict:
    """Crea un modello e restituisce il JSON della risposta."""
    payload = {
        "name": name or f"model_{uuid.uuid4().hex[:8]}",
        "project_name": project,
    }
    r = requests.post(f"{BASE_URL}/models/", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def _delete_model(model_id: str) -> None:
    requests.delete(f"{BASE_URL}/models/{model_id}")


# ─────────────────────────────────────────────────────────────────────────────
# POST /models/
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateModel:
    def test_create_model_success(self):
        """Crea un modello valido e verifica la risposta."""
        payload = {"name": f"m_{uuid.uuid4().hex[:6]}", "project_name": "proj_A"}
        r = requests.post(f"{BASE_URL}/models/", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["name"] == payload["name"]
        assert data["project_name"] == payload["project_name"]
        _delete_model(data["id"])

    def test_create_model_returns_uuid(self):
        """L'id restituito deve essere un UUID valido."""
        payload = {"name": f"m_{uuid.uuid4().hex[:6]}", "project_name": "proj_B"}
        r = requests.post(f"{BASE_URL}/models/", json=payload)
        assert r.status_code == 200
        data = r.json()
        uuid.UUID(data["id"])  # solleva ValueError se non è un UUID
        _delete_model(data["id"])

    def test_create_model_missing_name(self):
        """Senza 'name' deve restituire 422 Unprocessable Entity."""
        r = requests.post(f"{BASE_URL}/models/", json={"project_name": "proj_C"})
        assert r.status_code == 422

    def test_create_model_missing_project_name(self):
        """Senza 'project_name' deve restituire 422 Unprocessable Entity."""
        r = requests.post(f"{BASE_URL}/models/", json={"name": "only_name"})
        assert r.status_code == 422

    def test_create_model_empty_body_is_422(self):
        """Body vuoto deve restituire 422 (ridondante con test sotto, ma esplicito)."""
        r = requests.post(f"{BASE_URL}/models/", json={})
        assert r.status_code == 422

    def test_create_models_conflict(self):
        payload = {"name": f"m_{uuid.uuid4().hex[:6]}", "project_name": "proj_B"}
        r = requests.post(f"{BASE_URL}/models/", json=payload)
        assert r.status_code == 200
        data = r.json()
        r = requests.post(f"{BASE_URL}/models/", json=payload)
        assert r.status_code == 409
        uuid.UUID(data["id"])  # solleva ValueError se non è un UUID
        _delete_model(data["id"])




# ─────────────────────────────────────────────────────────────────────────────
# GET /models/
# ─────────────────────────────────────────────────────────────────────────────

class TestReadModels:
    def test_list_models_returns_list(self):
        """GET /models/ deve restituire una lista."""
        r = requests.get(f"{BASE_URL}/models/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_models_contains_created_model(self, created_model):
        """Il modello creato dalla fixture deve comparire nella lista."""
        r = requests.get(f"{BASE_URL}/models/")
        ids = [m["id"] for m in r.json()]
        assert created_model["id"] in ids

    def test_list_models_schema(self):
        """Ogni elemento della lista deve avere i campi 'id', 'name', 'project_name'."""
        m = _create_model()
        r = requests.get(f"{BASE_URL}/models/")
        assert r.status_code == 200
        for item in r.json():
            assert "id" in item
            assert "name" in item
            assert "project_name" in item
        _delete_model(m["id"])

# ─────────────────────────────────────────────────────────────────────────────
# GET /models/find
# ─────────────────────────────────────────────────────────────────────────────

class TestReadModelNameProject:
    def test_model_not_found(self):
        """GET /models/ deve restituire una lista."""
        r = requests.get(f"{BASE_URL}/models/find", {"model_name" : "test", "project_name" : "test"})
        assert r.status_code == 404
        
    def test_model_found(self):
        m = _create_model("test", "test")        
        r = requests.get(f"{BASE_URL}/models/find", {"model_name" : "test", "project_name" : "test"})
        assert r.status_code == 200
        _delete_model(m['id'])


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /models/{model_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestDeleteModel:
    def test_delete_existing_model(self):
        """Elimina un modello esistente → 200 e dettaglio."""
        m = _create_model()
        r = requests.delete(f"{BASE_URL}/models/{m['id']}")
        assert r.status_code == 200
        assert "deleted" in r.json().get("detail", "").lower()

    def test_delete_nonexistent_model(self):
        """DELETE con un UUID inesistente deve restituire 404."""
        fake_id = str(uuid.uuid4())
        r = requests.delete(f"{BASE_URL}/models/{fake_id}")
        assert r.status_code == 404

    def test_deleted_model_not_in_list(self):
        """Dopo la cancellazione il modello non deve comparire in GET /models/."""
        m = _create_model()
        requests.delete(f"{BASE_URL}/models/{m['id']}")
        r = requests.get(f"{BASE_URL}/models/")
        ids = [x["id"] for x in r.json()]
        assert m["id"] not in ids


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /models/project/{project_name}
# ─────────────────────────────────────────────────────────────────────────────

class TestDeleteModelsByProject:
    def test_delete_by_project_success(self):
        """Cancella tutti i modelli di un progetto → 200."""
        proj = f"proj_{uuid.uuid4().hex[:6]}"
        m1 = _create_model(project=proj)
        m2 = _create_model(project=proj)
        r = requests.delete(f"{BASE_URL}/models/project/{proj}")
        assert r.status_code == 200
        detail = r.json().get("detail", "")
        assert "2" in detail or "deleted" in detail.lower()

    def test_delete_by_project_not_found(self):
        """Progetto inesistente deve restituire 404."""
        r = requests.delete(f"{BASE_URL}/models/project/progetto_che_non_esiste_xyz")
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Unicità del nome: UNIQUE(name, project_name)
# ─────────────────────────────────────────────────────────────────────────────

class TestModelNameUniqueness:
    """
    La coppia (name, project_name) deve essere unica nel DB.

    Regole:
        1. Stesso nome + stesso progetto   → ERRORE (vincolo violato)
        2. Stesso nome + progetto diverso  → OK (coppia differente)
        3. Nome diverso + stesso progetto  → OK (coppia differente)
        4. Il modello originale non viene alterato dai tentativi falliti
    """

    def test_duplicate_name_same_project_is_rejected(self):
        """
        NON deve essere possibile creare due modelli con lo stesso nome
        **nello stesso progetto** → il server deve restituire un errore.
        """
        name = f"dup_{uuid.uuid4().hex[:8]}"
        proj = f"proj_{uuid.uuid4().hex[:6]}"

        m1 = _create_model(name=name, project=proj)
        try:
            r2 = requests.post(
                f"{BASE_URL}/models/",
                json={"name": name, "project_name": proj},
            )
            # Qualsiasi codice di errore 4xx/5xx è accettato
            assert r2.status_code in (409, 422, 500), (
                f"Atteso errore per duplicato (nome='{name}', progetto='{proj}'), "
                f"ricevuto {r2.status_code}: {r2.text}"
            )
        finally:
            _delete_model(m1["id"])

    def test_same_name_different_project_is_allowed(self):
        """
        DEVE essere possibile creare due modelli con lo stesso nome
        in **progetti diversi** (coppia (name, project_name) distinta).
        """
        name = f"shared_{uuid.uuid4().hex[:8]}"
        proj_a = f"proj_{uuid.uuid4().hex[:6]}_A"
        proj_b = f"proj_{uuid.uuid4().hex[:6]}_B"

        m1 = _create_model(name=name, project=proj_a)
        r2 = requests.post(
            f"{BASE_URL}/models/",
            json={"name": name, "project_name": proj_b},
        )
        try:
            assert r2.status_code == 200, (
                f"Stesso nome '{name}' su progetti diversi deve essere permesso, "
                f"ricevuto {r2.status_code}: {r2.text}"
            )
            m2 = r2.json()
            # I due modelli devono avere ID diversi
            assert m1["id"] != m2["id"]
            # Entrambi hanno lo stesso nome ma project_name diverso
            assert m1["name"] == m2["name"]
            assert m1["project_name"] != m2["project_name"]
        finally:
            _delete_model(m1["id"])
            if r2.status_code == 200:
                _delete_model(r2.json()["id"])

    def test_different_names_same_project_is_allowed(self):
        """
        Due modelli con nomi diversi nello stesso progetto devono coesistere.
        """
        proj = f"proj_{uuid.uuid4().hex[:6]}"
        m1 = _create_model(name=f"alpha_{uuid.uuid4().hex[:4]}", project=proj)
        m2 = _create_model(name=f"beta_{uuid.uuid4().hex[:4]}",  project=proj)
        try:
            # Entrambi devono essere visibili nella lista
            r = requests.get(f"{BASE_URL}/models/")
            assert r.status_code == 200
            ids = {item["id"] for item in r.json()}
            assert m1["id"] in ids
            assert m2["id"] in ids
        finally:
            _delete_model(m1["id"])
            _delete_model(m2["id"])

    def test_original_model_survives_rejected_duplicate(self):
        """
        Dopo un tentativo fallito di duplicato, il modello originale
        deve ancora esistere e rimanere invariato.
        """
        name = f"orig_{uuid.uuid4().hex[:8]}"
        proj = f"proj_{uuid.uuid4().hex[:6]}"

        m1 = _create_model(name=name, project=proj)
        # Tentativo di duplicato (verrà rifiutato)
        requests.post(
            f"{BASE_URL}/models/",
            json={"name": name, "project_name": proj},
        )
        try:
            # Il modello originale deve ancora existere e avere gli stessi dati
            r = requests.get(f"{BASE_URL}/models/")
            assert r.status_code == 200
            found = [item for item in r.json() if item["id"] == m1["id"]]
            assert len(found) == 1, "Il modello originale non è più presente dopo un duplicato rifiutato"
            assert found[0]["name"] == name
            assert found[0]["project_name"] == proj
        finally:
            _delete_model(m1["id"])


# ─────────────────────────────────────────────────────────────────────────────
# Cancellazione a cascata: Model → TrainingRun → Loss / Metric
# ─────────────────────────────────────────────────────────────────────────────

class TestCascadeDeleteOnModel:
    """
    Verifica che l'eliminazione di un modello rimuova in cascata tutte
    le entità dipendenti secondo la catena ORM:

        Model  ──(cascade)──▶  TrainingRun  ──(cascade)──▶  Loss
                                                         └──▶  Metric

    Ogni test costruisce in modo autonomo la gerarchia completa, elimina
    il modello e interroga le API per confermare l'assenza dei dati figli.
    """

    # ── helper interno ────────────────────────────────────────────────────────

    @staticmethod
    def _setup_full_hierarchy(
        n_steps: int = 3,
        splits: tuple = ("train", "validation"),
        metric_names: tuple = ("accuracy", "f1-score"),
    ) -> dict:
        """
        Crea:
            • 1 modello
            • 1 run con iperparametri
            • n_steps × len(splits)       record di Loss
            • n_steps × len(metric_names) record di Metric (split "train")

        Restituisce: { model_id, run_id, loss_count, metric_count }
        """
        # 1. Modello
        mr = requests.post(
            f"{BASE_URL}/models/",
            json={
                "name": f"cascade_{uuid.uuid4().hex[:8]}",
                "project_name": f"proj_{uuid.uuid4().hex[:6]}",
            },
        )
        assert mr.status_code == 200, f"Creazione modello fallita: {mr.text}"
        model = mr.json()

        # 2. Run
        rr = requests.post(
            f"{BASE_URL}/runs/",
            json={
                "model_id": model["id"],
                "hyperparameters": {"lr": 0.001, "batch_size": 32, "epochs": n_steps},
            },
        )
        assert rr.status_code == 200, f"Creazione run fallita: {rr.text}"
        run = rr.json()

        # 3. Losses (batch)
        losses = [
            {
                "run_id": run["id"],
                "step": step,
                "split": split,
                "value": round(1.0 / (step + 1), 4),
            }
            for step in range(1, n_steps + 1)
            for split in splits
        ]
        lr = requests.post(
            f"{BASE_URL}/loss/batch",
            json={"run_id": run["id"], "losses": losses},
        )
        assert lr.status_code == 200, f"Inserimento losses fallito: {lr.text}"

        # 4. Metrics (batch) — su split "train"
        mtr_list = [
            {
                "run_id": run["id"],
                "step": step,
                "split": "train",
                "metric_name": metric_name,
                "value": round(0.5 + step * 0.05, 4),
            }
            for step in range(1, n_steps + 1)
            for metric_name in metric_names
        ]
        mtr = requests.post(
            f"{BASE_URL}/metric/batch",
            json={"run_id": run["id"], "metrics": mtr_list},
        )
        assert mtr.status_code == 200, f"Inserimento metriche fallito: {mtr.text}"

        return {
            "model_id": model["id"],
            "run_id":   run["id"],
            "loss_count":   len(losses),
            "metric_count": len(mtr_list),
        }

    # ── test ─────────────────────────────────────────────────────────────────

    def test_delete_model_returns_200(self):
        """La DELETE del modello deve restituire 200 con messaggio di conferma."""
        ctx = self._setup_full_hierarchy()
        r = requests.delete(f"{BASE_URL}/models/{ctx['model_id']}")
        assert r.status_code == 200
        assert "deleted" in r.json().get("detail", "").lower()

    def test_cascade_runs_are_deleted(self):
        """
        Dopo l'eliminazione del modello,
        GET /runs/runbymodels/{model_id} deve restituire 404.
        """
        ctx = self._setup_full_hierarchy()
        model_id = ctx["model_id"]
        run_id   = ctx["run_id"]

        # Pre-condizione: il run esiste
        pre = requests.get(f"{BASE_URL}/runs/runbymodels/{model_id}")
        assert pre.status_code == 200
        assert any(item["id"] == run_id for item in pre.json()), \
            "Il run non e' presente prima della cancellazione"

        # Elimina il modello
        requests.delete(f"{BASE_URL}/models/{model_id}")

        # Post-condizione: nessun run rimasto → 404
        post = requests.get(f"{BASE_URL}/runs/runbymodels/{model_id}")
        assert post.status_code == 404, (
            f"Atteso 404 per i run dopo DELETE del modello, "
            f"ricevuto {post.status_code}: {post.text}"
        )

    def test_cascade_losses_are_deleted(self):
        """
        Dopo l'eliminazione del modello,
        GET /loss/?run_id=... deve restituire lista vuota.
        """
        ctx = self._setup_full_hierarchy()
        model_id = ctx["model_id"]
        run_id   = ctx["run_id"]

        # Pre-condizione: le loss esistono
        pre = requests.get(f"{BASE_URL}/loss/", params={"run_id": run_id})
        assert pre.status_code == 200
        assert len(pre.json()) == ctx["loss_count"], (
            f"Losses prima della DELETE: attese {ctx['loss_count']}, "
            f"trovate {len(pre.json())}"
        )

        # Elimina il modello
        requests.delete(f"{BASE_URL}/models/{model_id}")

        # Post-condizione: lista vuota
        post = requests.get(f"{BASE_URL}/loss/", params={"run_id": run_id})
        assert post.status_code == 200
        assert post.json() == [], (
            f"Attesa lista vuota per le losses dopo DELETE del modello, "
            f"trovati {len(post.json())} record"
        )

    def test_cascade_metrics_are_deleted(self):
        """
        Dopo l'eliminazione del modello,
        GET /metric/?run_id=... deve restituire lista vuota.
        """
        ctx = self._setup_full_hierarchy()
        model_id = ctx["model_id"]
        run_id   = ctx["run_id"]

        # Pre-condizione: le metriche esistono
        pre = requests.get(f"{BASE_URL}/metric/", params={"run_id": run_id})
        assert pre.status_code == 200
        assert len(pre.json()) == ctx["metric_count"], (
            f"Metriche prima della DELETE: attese {ctx['metric_count']}, "
            f"trovate {len(pre.json())}"
        )

        # Elimina il modello
        requests.delete(f"{BASE_URL}/models/{model_id}")

        # Post-condizione: lista vuota
        post = requests.get(f"{BASE_URL}/metric/", params={"run_id": run_id})
        assert post.status_code == 200
        assert post.json() == [], (
            f"Attesa lista vuota per le metriche dopo DELETE del modello, "
            f"trovati {len(post.json())} record"
        )

    def test_cascade_full_hierarchy_deleted_at_once(self):
        """
        Test end-to-end: costruisce l'intera gerarchia (modello → run →
        losses + metrics), la valida, elimina il modello con una sola
        DELETE e verifica che TUTTE le entità figlie siano sparite.
        """
        ctx = self._setup_full_hierarchy(n_steps=5)
        model_id = ctx["model_id"]
        run_id   = ctx["run_id"]

        # ── PRIMA della cancellazione ─────────────────────────────────────────
        runs_before    = requests.get(f"{BASE_URL}/runs/runbymodels/{model_id}").json()
        losses_before  = requests.get(f"{BASE_URL}/loss/",   params={"run_id": run_id}).json()
        metrics_before = requests.get(f"{BASE_URL}/metric/", params={"run_id": run_id}).json()

        assert len(runs_before) >= 1, "Nessun run trovato prima della cancellazione"
        assert len(losses_before)  == ctx["loss_count"], (
            f"Losses prima: attese {ctx['loss_count']}, trovate {len(losses_before)}"
        )
        assert len(metrics_before) == ctx["metric_count"], (
            f"Metriche prima: attese {ctx['metric_count']}, trovate {len(metrics_before)}"
        )

        # ── Cancellazione del modello ─────────────────────────────────────────
        del_r = requests.delete(f"{BASE_URL}/models/{model_id}")
        assert del_r.status_code == 200, f"DELETE modello fallita: {del_r.text}"

        # ── DOPO la cancellazione ─────────────────────────────────────────────
        runs_after    = requests.get(f"{BASE_URL}/runs/runbymodels/{model_id}")
        losses_after  = requests.get(f"{BASE_URL}/loss/",   params={"run_id": run_id})
        metrics_after = requests.get(f"{BASE_URL}/metric/", params={"run_id": run_id})

        # Il modello non ha piu' run → 404
        assert runs_after.status_code == 404, (
            f"Atteso 404 per i run dopo DELETE del modello, "
            f"ricevuto {runs_after.status_code}"
        )

        # Losses e metriche: lista vuota
        assert losses_after.status_code == 200
        assert losses_after.json() == [], \
            f"Losses residue dopo DELETE: {losses_after.json()}"

        assert metrics_after.status_code == 200
        assert metrics_after.json() == [], \
            f"Metriche residue dopo DELETE: {metrics_after.json()}"
