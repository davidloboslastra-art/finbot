import pytest

from app import finanzas


def test_cuota_diez_millones_36_meses_12_pct():
    assert round(finanzas.cuota_mensual(10_000_000, 12, 36)) == 332_143


def test_total_e_intereses_son_consistentes():
    total = finanzas.total_pagado(10_000_000, 12, 36)
    assert total == pytest.approx(finanzas.cuota_mensual(10_000_000, 12, 36) * 36)
    assert finanzas.intereses(10_000_000, 12, 36) == pytest.approx(total - 10_000_000)


def test_cuota_tasa_cero():
    assert finanzas.cuota_mensual(1_200_000, 0, 12) == 100_000


def test_cuota_rechaza_parametros_invalidos():
    with pytest.raises(ValueError):
        finanzas.cuota_mensual(0, 12, 36)
    with pytest.raises(ValueError):
        finanzas.cuota_mensual(1_000_000, 12, 0)


def test_ahorro_mensual_sin_tasa():
    assert finanzas.ahorro_mensual(1_200_000, 12) == 100_000


def test_ahorro_mensual_con_tasa_es_menor():
    assert finanzas.ahorro_mensual(5_000_000, 24, 4) < 5_000_000 / 24


def test_interes_compuesto():
    assert finanzas.interes_compuesto(1_000_000, 6, 10, n=1) == pytest.approx(1_790_847.70, abs=0.01)
    assert finanzas.interes_compuesto(1_000_000, 0, 5) == 1_000_000
