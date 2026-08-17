"""
Auditoria Automatizada de Dados
================================
Ferramenta em Python que analisa uma base de dados (CSV) e identifica
automaticamente inconsistências comuns em auditoria de dados:

- Registros duplicados
- Valores nulos/ausentes em campos críticos
- Outliers estatísticos (valores fora do padrão)
- Valores negativos em campos que deveriam ser positivos
- Datas inválidas ou fora do intervalo esperado
- Inconsistências de formatação em campos de texto
- Erros de cálculo (quantidade x valor_unitario != valor_total)

Gera um relatório de auditoria em Markdown e persiste os achados
em um banco SQLite para consulta posterior.

Autor: Matheus Scherer
"""
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
from pathlib import Path


class AuditorDados:
    """Classe responsável por rodar as verificações de qualidade de dados
    sobre um DataFrame e consolidar os achados de auditoria."""

    def __init__(self, df: pd.DataFrame, nome_base: str = "base_auditada"):
        self.df_original = df.copy()
        self.df = df.copy()
        self.nome_base = nome_base
        self.achados = []  # lista de dicts: {tipo, descricao, qtd_registros, indices}
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _registrar_achado(self, tipo, descricao, indices, severidade="média"):
        self.achados.append({
            "tipo": tipo,
            "descricao": descricao,
            "qtd_registros": len(indices),
            "indices": list(indices),
            "severidade": severidade,
        })

    def verificar_duplicatas(self, subset=None):
        """Identifica registros totalmente ou parcialmente duplicados."""
        dup_mask = self.df.duplicated(subset=subset, keep="first")
        indices = self.df[dup_mask].index
        if len(indices) > 0:
            self._registrar_achado(
                tipo="Duplicatas",
                descricao=f"Registros duplicados encontrados"
                          f"{' (considerando: ' + ', '.join(subset) + ')' if subset else ''}",
                indices=indices,
                severidade="alta",
            )
        return indices

    def verificar_nulos(self, colunas_criticas=None):
        """Identifica valores nulos em colunas consideradas críticas."""
        colunas = colunas_criticas or self.df.columns.tolist()
        for col in colunas:
            if col not in self.df.columns:
                continue
            idx_nulos = self.df[self.df[col].isna()].index
            if len(idx_nulos) > 0:
                self._registrar_achado(
                    tipo="Valores Nulos",
                    descricao=f"Coluna '{col}' possui valores ausentes",
                    indices=idx_nulos,
                    severidade="alta" if col in (colunas_criticas or []) else "média",
                )

    def verificar_outliers(self, coluna, metodo="iqr", fator=1.5):
        """Detecta outliers estatísticos usando o método do Intervalo
        Interquartil (IQR), padrão em auditoria de dados numéricos."""
        if coluna not in self.df.columns:
            return
        serie = pd.to_numeric(self.df[coluna], errors="coerce")
        q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
        iqr = q3 - q1
        limite_inferior = q1 - fator * iqr
        limite_superior = q3 + fator * iqr

        idx_outliers = self.df[
            (serie < limite_inferior) | (serie > limite_superior)
        ].index

        if len(idx_outliers) > 0:
            self._registrar_achado(
                tipo="Outliers",
                descricao=(f"Coluna '{coluna}' possui valores fora do padrão "
                           f"estatístico (limites esperados: {limite_inferior:.2f} "
                           f"a {limite_superior:.2f})"),
                indices=idx_outliers,
                severidade="alta",
            )

    def verificar_valores_negativos(self, coluna):
        """Identifica valores negativos em campos que deveriam ser sempre positivos
        (ex: quantidade, valor unitário)."""
        if coluna not in self.df.columns:
            return
        serie = pd.to_numeric(self.df[coluna], errors="coerce")
        idx_negativos = self.df[serie < 0].index
        if len(idx_negativos) > 0:
            self._registrar_achado(
                tipo="Valores Negativos",
                descricao=f"Coluna '{coluna}' possui valores negativos inválidos",
                indices=idx_negativos,
                severidade="alta",
            )

    def verificar_datas(self, coluna, formato="%Y-%m-%d", data_min=None, data_max=None):
        """Verifica se datas estão em formato válido e dentro de um
        intervalo plausível."""
        if coluna not in self.df.columns:
            return

        def data_invalida(valor):
            try:
                d = pd.to_datetime(valor, format=formato, errors="raise")
                if data_min and d < pd.Timestamp(data_min):
                    return True
                if data_max and d > pd.Timestamp(data_max):
                    return True
                return False
            except Exception:
                return True

        idx_invalidas = self.df[self.df[coluna].apply(data_invalida)].index
        if len(idx_invalidas) > 0:
            self._registrar_achado(
                tipo="Datas Inválidas",
                descricao=f"Coluna '{coluna}' possui datas inválidas ou fora do período esperado",
                indices=idx_invalidas,
                severidade="média",
            )

    def verificar_formatacao_texto(self, coluna):
        """Detecta inconsistências de formatação (espaços extras,
        maiúsculas/minúsculas misturadas) que dificultam agrupamentos."""
        if coluna not in self.df.columns:
            return

        serie = self.df[coluna].dropna().astype(str)
        idx_com_espacos = serie[serie != serie.str.strip()].index
        idx_maiuscula_mista = serie[serie != serie.str.upper()].index
        idx_maiuscula_mista = idx_maiuscula_mista.intersection(
            serie[serie.str.isupper()].index
        )

        idx_problema = idx_com_espacos.union(idx_maiuscula_mista)
        if len(idx_problema) > 0:
            self._registrar_achado(
                tipo="Formatação Inconsistente",
                descricao=f"Coluna '{coluna}' possui espaços extras ou "
                          f"capitalização inconsistente, prejudicando agrupamentos",
                indices=idx_problema,
                severidade="baixa",
            )

    def verificar_consistencia_calculo(self, col_qtd, col_valor_unit, col_valor_total, tolerancia=0.01):
        """Verifica se valor_total = quantidade x valor_unitario, comum em
        auditoria de dados financeiros/comerciais."""
        for col in (col_qtd, col_valor_unit, col_valor_total):
            if col not in self.df.columns:
                return

        qtd = pd.to_numeric(self.df[col_qtd], errors="coerce")
        v_unit = pd.to_numeric(self.df[col_valor_unit], errors="coerce")
        v_total = pd.to_numeric(self.df[col_valor_total], errors="coerce")
        v_esperado = qtd * v_unit

        diff = (v_total - v_esperado).abs()
        idx_inconsistente = self.df[diff > tolerancia].index
        # remove os que já têm nulo (evita falso positivo)
        idx_inconsistente = idx_inconsistente.intersection(
            self.df[qtd.notna() & v_unit.notna() & v_total.notna()].index
        )

        if len(idx_inconsistente) > 0:
            self._registrar_achado(
                tipo="Erro de Cálculo",
                descricao=(f"'{col_valor_total}' não corresponde a "
                           f"'{col_qtd}' × '{col_valor_unit}' em {len(idx_inconsistente)} registros"),
                indices=idx_inconsistente,
                severidade="alta",
            )

    def rodar_auditoria_completa(self, config):
        """Executa todas as verificações configuradas de uma vez.

        config: dict com as chaves esperadas por cada verificação, ex:
        {
            "duplicatas_subset": None,
            "colunas_criticas_nulos": ["vendedor", "valor_unitario"],
            "coluna_outlier": "valor_total",
            "coluna_negativa": "quantidade",
            "coluna_data": "data_venda",
            "coluna_texto": "filial",
            "calculo": ("quantidade", "valor_unitario", "valor_total"),
        }
        """
        self.verificar_duplicatas(config.get("duplicatas_subset"))
        self.verificar_nulos(config.get("colunas_criticas_nulos"))
        if config.get("coluna_outlier"):
            self.verificar_outliers(config["coluna_outlier"])
        if config.get("coluna_negativa"):
            self.verificar_valores_negativos(config["coluna_negativa"])
        if config.get("coluna_data"):
            self.verificar_datas(config["coluna_data"], data_min="2020-01-01", data_max="2026-12-31")
        if config.get("coluna_texto"):
            self.verificar_formatacao_texto(config["coluna_texto"])
        if config.get("calculo"):
            self.verificar_consistencia_calculo(*config["calculo"])

        return self.achados

    # ------------------------------------------------------------------
    # Relatórios e persistência
    # ------------------------------------------------------------------

    def gerar_relatorio_markdown(self, caminho_saida="relatorio_auditoria.md"):
        total_registros = len(self.df_original)
        total_problemas = sum(a["qtd_registros"] for a in self.achados)
        registros_unicos_com_problema = set()
        for a in self.achados:
            registros_unicos_com_problema.update(a["indices"])

        pct_afetado = (len(registros_unicos_com_problema) / total_registros * 100) if total_registros else 0

        linhas = [
            f"# Relatório de Auditoria de Dados",
            f"",
            f"**Base analisada:** `{self.nome_base}`  ",
            f"**Data da auditoria:** {self.timestamp}  ",
            f"**Total de registros analisados:** {total_registros}  ",
            f"**Registros com pelo menos um problema:** {len(registros_unicos_com_problema)} ({pct_afetado:.1f}%)  ",
            f"**Total de ocorrências identificadas:** {total_problemas}  ",
            f"",
            f"---",
            f"",
            f"## Resumo dos Achados",
            f"",
            f"| Tipo de Problema | Severidade | Registros Afetados |",
            f"|---|---|---|",
        ]

        severidade_ordem = {"alta": 0, "média": 1, "baixa": 2}
        achados_ordenados = sorted(self.achados, key=lambda a: severidade_ordem.get(a["severidade"], 3))

        for a in achados_ordenados:
            linhas.append(f"| {a['tipo']} | {a['severidade'].capitalize()} | {a['qtd_registros']} |")

        linhas.append("")
        linhas.append("---")
        linhas.append("")
        linhas.append("## Detalhamento dos Achados")
        linhas.append("")

        for a in achados_ordenados:
            linhas.append(f"### {a['tipo']} — Severidade: {a['severidade'].capitalize()}")
            linhas.append(f"")
            linhas.append(f"{a['descricao']}")
            linhas.append(f"")
            linhas.append(f"- **Registros afetados:** {a['qtd_registros']}")
            amostra = a["indices"][:5]
            linhas.append(f"- **Amostra de índices (linhas do DataFrame):** {amostra}")
            linhas.append(f"")

        linhas.append("---")
        linhas.append("")
        linhas.append("## Recomendações")
        linhas.append("")
        if any(a["tipo"] == "Duplicatas" for a in self.achados):
            linhas.append("- Implementar validação de unicidade na origem dos dados (ex: constraint de chave única).")
        if any(a["tipo"] == "Valores Nulos" for a in self.achados):
            linhas.append("- Tornar campos críticos obrigatórios no formulário/sistema de entrada de dados.")
        if any(a["tipo"] == "Outliers" for a in self.achados):
            linhas.append("- Investigar manualmente os outliers identificados; podem indicar fraude ou erro de digitação.")
        if any(a["tipo"] == "Erro de Cálculo" for a in self.achados):
            linhas.append("- Revisar a lógica de cálculo no sistema de origem; valores podem estar sendo alterados manualmente após o cálculo automático.")
        linhas.append("- Reexecutar esta auditoria periodicamente (ex: rotina semanal) para monitoramento contínuo da qualidade dos dados.")

        conteudo = "\n".join(linhas)
        Path(caminho_saida).write_text(conteudo, encoding="utf-8")
        return caminho_saida

    def salvar_no_sqlite(self, caminho_db="auditoria.db"):
        """Persiste os achados de auditoria e a base analisada em SQLite,
        simulando um cenário de auditoria contínua com histórico."""
        conn = sqlite3.connect(caminho_db)

        # Salva a base original com uma coluna indicando se teve problema
        registros_com_problema = set()
        for a in self.achados:
            registros_com_problema.update(a["indices"])

        df_export = self.df_original.copy()
        df_export["auditoria_flag_problema"] = df_export.index.isin(registros_com_problema)
        df_export["auditoria_timestamp"] = self.timestamp
        df_export.to_sql("dados_auditados", conn, if_exists="replace", index_label="idx_original")

        # Salva os achados em formato tabular (uma linha por achado agregado)
        achados_df = pd.DataFrame([
            {
                "tipo": a["tipo"],
                "descricao": a["descricao"],
                "severidade": a["severidade"],
                "qtd_registros": a["qtd_registros"],
                "timestamp_auditoria": self.timestamp,
                "nome_base": self.nome_base,
            }
            for a in self.achados
        ])
        achados_df.to_sql("historico_achados", conn, if_exists="append", index=False)

        conn.commit()
        conn.close()
        return caminho_db


if __name__ == "__main__":
    print("=" * 60)
    print("AUDITORIA AUTOMATIZADA DE DADOS")
    print("=" * 60)

    df = pd.read_csv("dados_vendas_bruto.csv")
    print(f"\nBase carregada: {len(df)} registros, {len(df.columns)} colunas")

    auditor = AuditorDados(df, nome_base="vendas_farmacia_2026")

    colunas_conteudo = [c for c in df.columns if c != "id_venda"]
    config = {
        "duplicatas_subset": colunas_conteudo,  # duplicata por conteúdo, ignorando o ID
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
