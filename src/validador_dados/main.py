"""Ponto de entrada da auditoria de dados."""

from pathlib import Path

import pandas as pd

from validador_dados.auditor import AuditorDados
from validador_dados.gerar_dados import gerar_base_vendas


def main() -> None:
    print("=" * 60)
    print("AUDITORIA AUTOMATIZADA DE DADOS")
    print("=" * 60)

    caminho_csv = Path("dados_vendas_bruto.csv")
    if not caminho_csv.exists():
        print("\nGerando base de exemplo com inconsistências propositais...")
        df = gerar_base_vendas(500)
        df.to_csv(caminho_csv, index=False, encoding="utf-8")
        print(f"Base gerada: {caminho_csv}")
    else:
        df = pd.read_csv(caminho_csv)

    print(f"\nBase carregada: {len(df)} registros, {len(df.columns)} colunas")

    auditor = AuditorDados(df, nome_base="vendas_farmacia_2026")

    colunas_conteudo = [c for c in df.columns if c != "id_venda"]
    config = {
        "duplicatas_subset": colunas_conteudo,
        "colunas_criticas_nulos": ["vendedor", "valor_unitario"],
        "coluna_outlier": "valor_total",
        "coluna_negativa": "quantidade",
        "coluna_data": "data_venda",
        "coluna_texto": "filial",
        "calculo": ("quantidade", "valor_unitario", "valor_total"),
    }

    achados = auditor.rodar_auditoria_completa(config)

    print(f"\n{len(achados)} tipos de problemas encontrados:\n")
    for a in achados:
        print(f"  [{a['severidade'].upper():6}] {a['tipo']:28} -> {a['qtd_registros']} registros")

    caminho_relatorio = auditor.gerar_relatorio_markdown("relatorio_auditoria.md")
    caminho_db = auditor.salvar_no_sqlite("auditoria.db")

    print(f"\nRelatório salvo em: {caminho_relatorio}")
    print(f"Dados persistidos em: {caminho_db}")
    print("\nAuditoria concluída com sucesso.")


if __name__ == "__main__":
    main()
