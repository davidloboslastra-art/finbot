"""Cálculos financieros puros (sin I/O)."""


def cuota_mensual(monto: float, tasa_anual: float, meses: int) -> float:
    """Cuota fija del sistema francés. tasa_anual en porcentaje (ej. 12 = 12%)."""
    if monto <= 0 or meses <= 0:
        raise ValueError("monto y meses deben ser positivos")
    i = tasa_anual / 100 / 12
    if i == 0:
        return monto / meses
    return monto * i / (1 - (1 + i) ** -meses)


def total_pagado(monto: float, tasa_anual: float, meses: int) -> float:
    return cuota_mensual(monto, tasa_anual, meses) * meses


def intereses(monto: float, tasa_anual: float, meses: int) -> float:
    return total_pagado(monto, tasa_anual, meses) - monto


def ahorro_mensual(meta: float, meses: int, tasa_anual: float = 0.0) -> float:
    """Aporte mensual (a fin de mes) para juntar `meta` en `meses`."""
    if meta <= 0 or meses <= 0:
        raise ValueError("meta y meses deben ser positivos")
    i = tasa_anual / 100 / 12
    if i == 0:
        return meta / meses
    return meta * i / ((1 + i) ** meses - 1)


def interes_compuesto(capital: float, tasa_anual: float, anios: float, n: int = 12) -> float:
    """Monto final con capitalización n veces al año."""
    if capital < 0 or anios < 0 or n <= 0:
        raise ValueError("parámetros inválidos")
    return capital * (1 + tasa_anual / 100 / n) ** (n * anios)
