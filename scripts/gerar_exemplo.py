"""Gera docs/relatorio_exemplo.md com o mesmo motor da auditoria.

Não inventa métrica: o relatório sai de gerar_base_vendas() + AuditorDados.
"""

from pathlib import Path

from validador_dados.auditor import AuditorDados
from validador_dados.gerar_dados import gerar_base_vendas

ROOT = Path(__file__).resolve().parents[1]
SAIDA = ROOT / "docs" / "relatorio_exemplo.md"

CONFIG = {
    "duplicatas_subset": None,  # preenchido depois, sem id_venda
    "colunas_criticas_nulos": ["vendedor", "valor_unitario"],
    "coluna_outlier": "valor_total",
    "coluna_negativa": "quantidade",
    "coluna_data": "data_venda",
    "coluna_texto": "filial",
    "calculo": ("quantidade", "valor_unitario", "valor_total"),
}


def main() -> None:
    df = gerar_base_vendas(500)
    config = dict(CONFIG)
    config["duplicatas_subset"] = [c for c in df.columns if c != "id_venda"]

    auditor = AuditorDados(df, nome_base="vendas_sinteticas_exemplo")
    auditor.rodar_auditoria_completa(config)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    auditor.gerar_relatorio_markdown(str(SAIDA))

    disclaimer = (
        "> **Exemplo gerado pelo código.** Base sintético "
        "(`gerar_base_vendas(500)` com seed 42). Não é cliente. "
        "Os números abaixo saíram desta execução.\n\n"
    )
    SAIDA.write_text(disclaimer + SAIDA.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"Relatório gerado: {SAIDA}")
    print(f"Registros: {len(df)}")
    print(f"Tipos de achado: {len(auditor.achados)}")
    for a in auditor.achados:
        print(f"  [{a['severidade']}] {a['tipo']}: {a['qtd_registros']}")


if __name__ == "__main__":
    main()
