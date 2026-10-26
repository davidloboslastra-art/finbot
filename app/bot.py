"""Lógica del asistente: reglas + glosario, con OpenAI solo para preguntas abiertas."""
import json
import os
import re
import ssl
import urllib.request

import certifi

from . import finanzas

GLOSARIO = {
    "uf": "La UF (Unidad de Fomento) es una unidad de cuenta reajustada diariamente según la inflación. "
          "Se usa en créditos hipotecarios, arriendos y seguros para que el valor no pierda poder adquisitivo.",
    "cae": "El CAE (Carga Anual Equivalente) es el costo total anual de un crédito expresado en porcentaje: "
           "incluye interés, comisiones y seguros. Sirve para comparar ofertas.",
    "apv": "El APV (Ahorro Previsional Voluntario) es un ahorro para la jubilación con beneficios tributarios. "
           "Régimen A: el Estado bonifica 15% de lo ahorrado (tope anual). "
           "Régimen B: rebajas la base del impuesto a la renta.",
    "inflación": "La inflación es el alza sostenida de los precios; reduce lo que puedes comprar con la misma plata. "
                 "En Chile se mide con el IPC y el Banco Central apunta a una meta de 3%.",
    "fondo mutuo": "Un fondo mutuo junta el dinero de muchos aportantes para invertirlo en un conjunto de instrumentos "
                   "(renta fija, acciones, etc.). Puedes rescatar tus cuotas, pero su valor sube y baja según el mercado.",
}
ALIAS = {"inflacion": "inflación", "fondos mutuos": "fondo mutuo", "unidad de fomento": "uf"}

AYUDA = {
    "credito": "Para calcular una cuota dime monto, tasa anual y plazo. Ej: «cuota de un crédito de $10 millones al 12% a 36 meses».",
    "ahorro": "Para calcular el ahorro dime meta y plazo (y tasa si quieres). Ej: «quiero ahorrar $5.000.000 en 2 años al 4%».",
    "compuesto": "Para interés compuesto dime capital, tasa anual y años. Ej: «interés compuesto de $1.000.000 al 6% por 10 años».",
}

_NUM = r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?"
_MULT = {"millon": 1_000_000, "millones": 1_000_000, "mil": 1_000, "lucas": 1_000}


def _num(ent: str, dec: str | None) -> float:
    return float(ent.replace(".", "") + ("." + dec if dec else ""))


def _extraer(texto: str) -> dict:
    """Saca tasa (%), plazo y montos del mensaje, en formato chileno (1.000.000 / 5,5%)."""
    t = texto.lower().replace("millón", "millon")
    out = {"tasa": None, "meses": None, "anios": None, "montos": []}

    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", t)
    if m:
        out["tasa"] = float(m.group(1).replace(",", "."))
        t = t[:m.start()] + " " + t[m.end():]
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(meses|mes|años|año|anios|anio)\b", t)
    if m:
        v = float(m.group(1).replace(",", "."))
        if m.group(2).startswith("mes"):
            out["meses"] = int(round(v))
        else:
            out["anios"] = v
        t = t[:m.start()] + " " + t[m.end():]
    for m in re.finditer(_NUM + r"\s*(millones|millon|mil|lucas)?\b", t):
        v = _num(m.group(1), m.group(2)) * _MULT.get(m.group(3), 1)
        out["montos"].append(v)
    return out


def _clp(x: float) -> str:
    return "$" + f"{x:,.0f}".replace(",", ".")


def _credito(d: dict) -> str | None:
    if not d["montos"] or d["tasa"] is None or not (d["meses"] or d["anios"]):
        return None
    monto = d["montos"][0]
    meses = d["meses"] or int(round(d["anios"] * 12))
    c = finanzas.cuota_mensual(monto, d["tasa"], meses)
    return (f"Crédito de {_clp(monto)} al {d['tasa']:g}% anual en {meses} meses (sistema francés):\n"
            f"• Cuota mensual: {_clp(c)}\n"
            f"• Total pagado: {_clp(c * meses)}\n"
            f"• Intereses: {_clp(c * meses - monto)}\n"
            "(Tasa nominal anual dividida en 12; no incluye comisiones ni seguros, revisa el CAE.)")


def _ahorro(d: dict) -> str | None:
    if not d["montos"] or not (d["meses"] or d["anios"]):
        return None
    meta = d["montos"][0]
    meses = d["meses"] or int(round(d["anios"] * 12))
    tasa = d["tasa"] or 0.0
    a = finanzas.ahorro_mensual(meta, meses, tasa)
    return (f"Para juntar {_clp(meta)} en {meses} meses con tasa {tasa:g}% anual, "
            f"debes ahorrar {_clp(a)} al mes.")


def _compuesto(d: dict) -> str | None:
    if not d["montos"] or d["tasa"] is None or not (d["meses"] or d["anios"]):
        return None
    cap = d["montos"][0]
    anios = d["anios"] if d["anios"] else d["meses"] / 12
    f = finanzas.interes_compuesto(cap, d["tasa"], anios)
    return (f"{_clp(cap)} al {d['tasa']:g}% anual por {anios:g} años (capitalización mensual) "
            f"llegan a {_clp(f)}, es decir {_clp(f - cap)} de ganancia.")


def _intencion(t: str) -> str | None:
    if re.search(r"inter[eé]s compuesto|invertir|inversi[oó]n|rentabilidad", t):
        return "compuesto"
    if re.search(r"ahorr|meta\b", t):
        return "ahorro"
    if re.search(r"cuota|cr[eé]dito|pr[eé]stamo|dividendo", t):
        return "credito"
    return None


def _glosario(t: str) -> str | None:
    for alias, term in ALIAS.items():
        t = t.replace(alias, term)
    for term, texto in GLOSARIO.items():
        if re.search(rf"\b{re.escape(term)}\b", t):
            return texto
    return None


def _openai(mensaje: str) -> str | None:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    body = json.dumps({
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": "Eres Finbot, un asistente de educación financiera para Chile. "
             "Responde en español, breve y claro, con contexto chileno. No des asesoría de inversión personalizada."},
            {"role": "user", "content": mensaje},
        ],
        "max_tokens": 400,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context(cafile=certifi.where())) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def responder(mensaje: str) -> dict:
    t = mensaje.lower().strip()
    pregunta_def = re.search(r"qu[eé] (es|son|significa)|defin|explica", t)
    if pregunta_def and (g := _glosario(t)):
        return {"respuesta": g, "fuente": "glosario"}

    intencion = _intencion(t)
    if intencion:
        calc = {"credito": _credito, "ahorro": _ahorro, "compuesto": _compuesto}[intencion]
        try:
            r = calc(_extraer(mensaje))
        except ValueError:
            r = None
        return {"respuesta": r or AYUDA[intencion], "fuente": "calculo" if r else "reglas"}

    if g := _glosario(t):
        return {"respuesta": g, "fuente": "glosario"}

    if (r := _openai(mensaje)):
        return {"respuesta": r, "fuente": "openai"}
    return {"respuesta": "No tengo una regla para eso. Puedo calcular cuotas de crédito, ahorro para una meta, "
                         "interés compuesto, o explicarte UF, CAE, APV, inflación y fondo mutuo. "
                         "(Para preguntas abiertas configura OPENAI_API_KEY.)",
            "fuente": "reglas"}
