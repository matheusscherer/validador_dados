"""Testes básicos do motor de auditoria."""

import pandas as pd
import pytest

from validador_dados.auditor import AuditorDados


@pytest.fixture
def df_simples():
    return pd.DataFrame([
        {"id": 1, "qtd": 2, "vu": 10.0, "vt": 20.0, "nome": "A"},
        {"id": 2, "qtd": -1, "vu": 5.0, "vt": -5.0, "nome": "B"},
        {"id": 1, "qtd": 2, "vu": 10.0, "vt": 20.0, "nome": "A"},  # duplicata
    ])


def test_detecta_duplicatas(df_simples):
    auditor = AuditorDados(df_simples)
    auditor.verificar_duplicatas()
    assert any(a["tipo"] == "Duplicatas" for a in auditor.achados)


def test_detecta_negativos(df_simples):
    auditor = AuditorDados(df_simples)
    auditor.verificar_valores_negativos("qtd")
    assert any(a["tipo"] == "Valores Negativos" for a in auditor.achados)


def test_consistencia_calculo(df_simples):
    auditor = AuditorDados(df_simples)
    auditor.verificar_consistencia_calculo("qtd", "vu", "vt")
    # o segundo registro tem qtd negativa, mas o cálculo bate; não deve falhar por isso
    # (a inconsistência real seria se vt != qtd*vu)
