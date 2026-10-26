import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def sin_openai(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def chat(mensaje):
    return client.post("/chat", json={"mensaje": mensaje})


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_cuota():
    r = chat("cuota de un crédito de $10 millones al 12% a 36 meses")
    assert r.status_code == 200
    assert r.json()["fuente"] == "calculo"
    assert "$332.143" in r.json()["respuesta"]


def test_meta_de_ahorro():
    r = chat("quiero ahorrar $1.200.000 en 12 meses")
    assert r.json()["fuente"] == "calculo"
    assert "$100.000" in r.json()["respuesta"]


def test_glosario():
    r = chat("qué es el CAE")
    assert r.json()["fuente"] == "glosario"
    assert "Carga Anual Equivalente" in r.json()["respuesta"]


def test_pregunta_abierta_sin_clave_no_usa_openai():
    r = chat("¿conviene arrendar o comprar?")
    assert r.json()["fuente"] == "reglas"


@pytest.mark.parametrize("cuerpo", [{"mensaje": ""}, {"mensaje": "   "}, {}])
def test_entrada_vacia_o_invalida(cuerpo):
    assert client.post("/chat", json=cuerpo).status_code == 422
