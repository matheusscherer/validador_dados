"""Testes do motor de auditoria — cada teste afirma um comportamento."""

import pandas as pd
import pytest

from validador_dados.auditor import AuditorDados


def _auditor(rows):
    return AuditorDados(pd.DataFrame(rows))


def test_detecta_duplicatas():
    auditor = _auditor(
        [
            {"id": 1, "qtd": 2, "vu": 10.0, "vt": 20.0, "nome": "A"},
            {"id": 2, "qtd": 1, "vu": 5.0, "vt": 5.0, "nome": "B"},
            {"id": 1, "qtd": 2, "vu": 10.0, "vt": 20.0, "nome": "A"},
        ]
    )
    auditor.verificar_duplicatas()
    tipos = [a["tipo"] for a in auditor.achados]
    assert "Duplicatas" in tipos
    dup = next(a for a in auditor.achados if a["tipo"] == "Duplicatas")
    assert dup["qtd_registros"] == 1
    assert dup["severidade"] == "alta"


def test_nao_flagra_sem_duplicata():
    auditor = _auditor(
        [
            {"id": 1, "qtd": 2, "vu": 10.0, "vt": 20.0, "nome": "A"},
            {"id": 2, "qtd": 1, "vu": 5.0, "vt": 5.0, "nome": "B"},
        ]
    )
    auditor.verificar_duplicatas()
    assert auditor.achados == []


def test_detecta_negativos():
    auditor = _auditor(
        [
            {"id": 1, "qtd": 2, "vu": 10.0, "vt": 20.0, "nome": "A"},
            {"id": 2, "qtd": -1, "vu": 5.0, "vt": -5.0, "nome": "B"},
        ]
    )
    auditor.verificar_valores_negativos("qtd")
    tipos = [a["tipo"] for a in auditor.achados]
    assert "Valores Negativos" in tipos
    achado = next(a for a in auditor.achados if a["tipo"] == "Valores Negativos")
    assert achado["qtd_registros"] == 1


def test_consistencia_nao_flagra_quando_fecha():
    auditor = _auditor([{"id": 1, "qtd": 2, "vu": 10.0, "vt": 20.0, "nome": "A"}])
    auditor.verificar_consistencia_calculo("qtd", "vu", "vt")
    assert auditor.achados == []


def test_consistencia_flagra_quando_nao_fecha():
    auditor = _auditor([{"id": 1, "qtd": 3, "vu": 10.0, "vt": 25.0, "nome": "A"}])
    auditor.verificar_consistencia_calculo("qtd", "vu", "vt")
    assert len(auditor.achados) == 1
    assert auditor.achados[0]["tipo"] == "Erro de Cálculo"
    assert auditor.achados[0]["qtd_registros"] == 1
    assert auditor.achados[0]["severidade"] == "alta"


@pytest.mark.parametrize(
    "qtd, vu, vt, deve_flagar",
    [
        (2, 10.0, 20.0, False),
        (3, 10.0, 25.0, True),
        (0, 10.0, 0.0, False),
        (5, 2.5, 12.0, True),
        (1, 10.0, 10.009, False),  # dentro da tolerância 0.01
        (1, 10.0, 10.02, True),
    ],
)
def test_consistencia_parametrizada(qtd, vu, vt, deve_flagar):
    auditor = _auditor([{"id": 1, "qtd": qtd, "vu": vu, "vt": vt, "nome": "X"}])
    auditor.verificar_consistencia_calculo("qtd", "vu", "vt")
    tipos = [a["tipo"] for a in auditor.achados]
    if deve_flagar:
        assert "Erro de Cálculo" in tipos
    else:
        assert "Erro de Cálculo" not in tipos


def test_nulos_em_coluna_critica():
    auditor = _auditor(
        [
            {"id": 1, "vendedor": "Ana", "vu": 10.0},
            {"id": 2, "vendedor": None, "vu": 5.0},
        ]
    )
    auditor.verificar_nulos(["vendedor"])
    tipos = [a["tipo"] for a in auditor.achados]
    assert "Valores Nulos" in tipos
    achado = next(a for a in auditor.achados if a["tipo"] == "Valores Nulos")
    assert achado["severidade"] == "alta"
    assert achado["qtd_registros"] == 1


def test_relatorio_markdown_contem_achado(tmp_path):
    auditor = _auditor([{"id": 1, "qtd": 3, "vu": 10.0, "vt": 25.0, "nome": "A"}])
    auditor.verificar_consistencia_calculo("qtd", "vu", "vt")
    saida = tmp_path / "relatorio.md"
    auditor.gerar_relatorio_markdown(str(saida))
    texto = saida.read_text(encoding="utf-8")
    assert "Erro de Cálculo" in texto
    assert "Relatório de Auditoria de Dados" in texto
