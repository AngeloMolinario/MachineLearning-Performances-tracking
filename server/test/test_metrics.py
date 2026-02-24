"""
test_metrics.py – Test per il router /metric.

Endpoint coperti:
    POST  /metric/        → crea un singolo record di metrica
    POST  /metric/batch   → crea più record di metrica in un'unica richiesta
    GET   /metric/        → recupera le metriche (filtri: run_id, split, metric_name, limit)

Valori validi per MetricEnum:
    accuracy, f1-score, recall, precision, balanced accuracy, mse, mae

Valori validi per SplitEnum:
    train, validation
"""

import uuid
import requests
from conftest import BASE_URL

# Tutte le metriche supportate dall'enum
ALL_METRICS = [
    "accuracy",
    "f1-score",
    "recall",
    "precision",
    "balanced accuracy",
    "mse",
    "mae",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _create_model() -> dict:
    payload = {"name": f"metric_m_{uuid.uuid4().hex[:8]}", "project_name": "metric_project"}
    r = requests.post(f"{BASE_URL}/models/", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def _create_run(model_id: str) -> dict:
    r = requests.post(f"{BASE_URL}/runs/", json={"model_id": model_id})
    assert r.status_code == 200, r.text
    return r.json()


def _delete_model(model_id: str) -> None:
    requests.delete(f"{BASE_URL}/models/{model_id}")


def _post_metric(run_id: str, step: int, split: str, metric_name: str, value: float) -> requests.Response:
    return requests.post(
        f"{BASE_URL}/metric/",
        json={
            "run_id": run_id,
            "step": step,
            "split": split,
            "metric_name": metric_name,
            "value": value,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /metric/
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateMetric:
    def test_create_metric_accuracy_success(self):
        """Crea una metrica 'accuracy' su split 'train' e verifica la risposta."""
        m = _create_model()
        run = _create_run(m["id"])
        r = _post_metric(run["id"], step=1, split="train", metric_name="accuracy", value=0.91)
        assert r.status_code == 200
        data = r.json()
        assert data["run_id"] == run["id"]
        assert data["step"] == 1
        assert data["split"] == "train"
        assert data["metric_name"] == "accuracy"
        assert abs(data["value"] - 0.91) < 1e-6
        assert "timestamp" in data
        _delete_model(m["id"])

    def test_create_metric_all_valid_metric_names(self):
        """Verifica che ogni valore dell'enum MetricEnum sia accettato."""
        m = _create_model()
        run = _create_run(m["id"])
        for i, metric_name in enumerate(ALL_METRICS, start=1):
            r = _post_metric(run["id"], step=i, split="train", metric_name=metric_name, value=0.5)
            assert r.status_code == 200, f"Metrica '{metric_name}' non accettata: {r.text}"
        _delete_model(m["id"])

    def test_create_metric_validation_split(self):
        """Crea una metrica su split 'validation'."""
        m = _create_model()
        run = _create_run(m["id"])
        r = _post_metric(run["id"], step=1, split="validation", metric_name="f1-score", value=0.88)
        assert r.status_code == 200
        assert r.json()["split"] == "validation"
        _delete_model(m["id"])

    def test_create_metric_invalid_metric_name(self):
        """Nome metrica non valido deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        r = _post_metric(run["id"], step=1, split="train", metric_name="top_k_accuracy", value=0.9)
        assert r.status_code == 422
        _delete_model(m["id"])

    def test_create_metric_invalid_split(self):
        """Split non valido deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        r = _post_metric(run["id"], step=1, split="test", metric_name="accuracy", value=0.9)
        assert r.status_code == 422
        _delete_model(m["id"])

    def test_create_metric_missing_value(self):
        """Senza 'value' deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.post(
            f"{BASE_URL}/metric/",
            json={"run_id": run["id"], "step": 1, "split": "train", "metric_name": "accuracy"},
        )
        assert r.status_code == 422
        _delete_model(m["id"])

    def test_create_metric_missing_metric_name(self):
        """Senza 'metric_name' deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        r = requests.post(
            f"{BASE_URL}/metric/",
            json={"run_id": run["id"], "step": 1, "split": "train", "value": 0.9},
        )
        assert r.status_code == 422
        _delete_model(m["id"])

    def test_create_metric_invalid_run_id(self):
        """run_id inesistente deve restituire un errore (422 o 500)."""
        r = _post_metric(str(uuid.uuid4()), step=1, split="train", metric_name="accuracy", value=0.9)
        assert r.status_code in (422, 500)


# ─────────────────────────────────────────────────────────────────────────────
# POST /metric/batch
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateMetricBatch:
    def test_create_metric_batch_success(self):
        """Invia un batch di metriche e verifica che vengano tutte create."""
        m = _create_model()
        run = _create_run(m["id"])
        metrics = [
            {"run_id": run["id"], "step": i, "split": "train", "metric_name": "accuracy", "value": 0.5 + i * 0.05}
            for i in range(1, 6)
        ]
        payload = {"run_id": run["id"], "metrics": metrics}
        r = requests.post(f"{BASE_URL}/metric/batch", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 5
        _delete_model(m["id"])

    def test_create_metric_batch_multiple_metric_types(self):
        """Batch con tipi di metrica diversi."""
        m = _create_model()
        run = _create_run(m["id"])
        metrics = [
            {"run_id": run["id"], "step": 1, "split": "train", "metric_name": "accuracy", "value": 0.9},
            {"run_id": run["id"], "step": 1, "split": "train", "metric_name": "f1-score", "value": 0.88},
            {"run_id": run["id"], "step": 1, "split": "validation", "metric_name": "recall", "value": 0.85},
        ]
        payload = {"run_id": run["id"], "metrics": metrics}
        r = requests.post(f"{BASE_URL}/metric/batch", json=payload)
        assert r.status_code == 200
        returned_metric_names = {item["metric_name"] for item in r.json()}
        assert "accuracy" in returned_metric_names
        assert "f1-score" in returned_metric_names
        assert "recall" in returned_metric_names
        _delete_model(m["id"])

    def test_create_metric_batch_invalid_item(self):
        """Se un elemento del batch ha metric_name non valido deve restituire 422."""
        m = _create_model()
        run = _create_run(m["id"])
        metrics = [
            {"run_id": run["id"], "step": 1, "split": "train", "metric_name": "INVALID_METRIC", "value": 0.9},
        ]
        payload = {"run_id": run["id"], "metrics": metrics}
        r = requests.post(f"{BASE_URL}/metric/batch", json=payload)
        assert r.status_code == 422
        _delete_model(m["id"])

    def test_create_metric_batch_empty_list(self):
        """Batch vuoto: comportamento atteso (200 o 422)."""
        m = _create_model()
        run = _create_run(m["id"])
        payload = {"run_id": run["id"], "metrics": []}
        r = requests.post(f"{BASE_URL}/metric/batch", json=payload)
        assert r.status_code in (200, 422)
        _delete_model(m["id"])


# ─────────────────────────────────────────────────────────────────────────────
# GET /metric/
# ─────────────────────────────────────────────────────────────────────────────

class TestGetMetrics:
    def test_get_metrics_by_run_id(self, created_run):
        """Recupera le metriche di un run esistente."""
        run_id = created_run["id"]
        # Inserisce alcune metriche
        for i in range(1, 4):
            _post_metric(run_id, step=i, split="train", metric_name="accuracy", value=0.7 + i * 0.05)
        r = requests.get(f"{BASE_URL}/metric/", params={"run_id": run_id})
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 3

    def test_get_metrics_filter_by_split(self, created_run):
        """Filtra per split: solo metriche 'validation' devono essere restituite."""
        run_id = created_run["id"]
        _post_metric(run_id, step=500, split="validation", metric_name="precision", value=0.76)
        r = requests.get(
            f"{BASE_URL}/metric/",
            params={"run_id": run_id, "split": "validation"},
        )
        assert r.status_code == 200
        for item in r.json():
            assert item["split"] == "validation"

    def test_get_metrics_filter_by_metric_name(self, created_run):
        """Filtra per metric_name: solo 'recall' deve essere restituito."""
        run_id = created_run["id"]
        _post_metric(run_id, step=600, split="train", metric_name="recall", value=0.82)
        r = requests.get(
            f"{BASE_URL}/metric/",
            params={"run_id": run_id, "metric_name": "recall"},
        )
        assert r.status_code == 200
        for item in r.json():
            assert item["metric_name"] == "recall"

    def test_get_metrics_limit(self, created_run):
        """Il parametro 'limit' deve restringere il numero di risultati."""
        run_id = created_run["id"]
        for i in range(700, 707):
            _post_metric(run_id, step=i, split="train", metric_name="mse", value=0.3)
        r = requests.get(
            f"{BASE_URL}/metric/",
            params={"run_id": run_id, "metric_name": "mse", "limit": 3},
        )
        assert r.status_code == 200
        assert len(r.json()) <= 3

    def test_get_metrics_without_run_id(self):
        """Senza run_id deve restituire 422."""
        r = requests.get(f"{BASE_URL}/metric/")
        assert r.status_code == 422

    def test_get_metrics_schema(self, created_run):
        """Ogni elemento deve avere tutti i campi obbligatori."""
        run_id = created_run["id"]
        _post_metric(run_id, step=9999, split="train", metric_name="mae", value=0.05)
        r = requests.get(f"{BASE_URL}/metric/", params={"run_id": run_id})
        assert r.status_code == 200
        for item in r.json():
            for field in ("run_id", "step", "split", "metric_name", "value", "timestamp"):
                assert field in item

    def test_get_metrics_ordered_descending_by_step(self, created_run):
        """Le metriche devono essere ordinate per step in modo decrescente."""
        run_id = created_run["id"]
        for step in [50, 60, 70]:
            _post_metric(run_id, step=step, split="train", metric_name="accuracy", value=0.8)
        r = requests.get(
            f"{BASE_URL}/metric/",
            params={"run_id": run_id, "metric_name": "accuracy", "split": "train"},
        )
        steps = [item["step"] for item in r.json()]
        assert steps == sorted(steps, reverse=True)

    def test_get_metrics_combined_filters(self, created_run):
        """Combinazione di filtri: split + metric_name + limit."""
        run_id = created_run["id"]
        for i in range(800, 806):
            _post_metric(run_id, step=i, split="validation", metric_name="f1-score", value=0.75)
        r = requests.get(
            f"{BASE_URL}/metric/",
            params={"run_id": run_id, "split": "validation", "metric_name": "f1-score", "limit": 4},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) <= 4
        for item in data:
            assert item["split"] == "validation"
            assert item["metric_name"] == "f1-score"
