"""
conftest.py – Configurazione condivisa per tutti i test.

Ogni test file può importare BASE_URL e gli helper comuni da qui.
La suite usa il modulo `requests` (HTTP sincrono) e assume che il server
FastAPI sia raggiungibile all'indirizzo BASE_URL (default: http://localhost:8000).

Per cambiare l'indirizzo basta impostare la variabile d'ambiente:
    $env:API_BASE_URL = "http://localhost:8000"   # PowerShell
    export API_BASE_URL=http://localhost:8000       # bash
"""

import os
import pytest
import requests

# ──────────────────────────────────────────────
# Configurazione globale
# ──────────────────────────────────────────────
BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")


# ──────────────────────────────────────────────
# Fixture: crea un modello e lo cancella al termine
# ──────────────────────────────────────────────
@pytest.fixture(scope="session")
def created_model():
    """
    Crea un modello temporaneo per i test e lo elimina alla fine della sessione.
    Restituisce il dizionario JSON della risposta di creazione.
    """
    payload = {"name": "test_model_fixture", "project_name": "test_project"}
    response = requests.post(f"{BASE_URL}/models/", json=payload)
    assert response.status_code == 200, f"Setup fallito: {response.text}"
    model = response.json()
    yield model
    # teardown: elimina il modello (e i run correlati per cascading)
    requests.delete(f"{BASE_URL}/models/{model['id']}")


# ──────────────────────────────────────────────
# Fixture: crea un run legato al modello di sessione
# ──────────────────────────────────────────────
@pytest.fixture(scope="session")
def created_run(created_model):
    """
    Crea un TrainingRun temporaneo associato al modello di sessione.
    Restituisce il dizionario JSON della risposta di creazione.
    """
    payload = {
        "model_id": created_model["id"],
        "hyperparameters": {"lr": 0.001, "epochs": 10},
    }
    response = requests.post(f"{BASE_URL}/runs/", json=payload)
    assert response.status_code == 200, f"Setup run fallito: {response.text}"
    return response.json()
