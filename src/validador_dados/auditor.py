"""Motor de auditoria de qualidade de dados."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import sqlite3


class AuditorDados:
    """Classe responsável por rodar verificações de qualidade de dados
    sobre um DataFrame e consolidar os achados de auditoria."""

    def __init__(self, df: pd.DataFrame, nome_base: str = "base_auditada"):
        self.df_original = df.copy()
        self.df = df.copy()
        self.nome_base = nome_base
        self.achados: List[Dict[str, Any]] = []
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _registrar_achado(
        self,
        tipo: str,
        descricao: str,
        indices,
        severidade: str = "média",
    ) -> None:
        self.achados.append({
            "tipo": tipo,
            "descricao": descricao,
            "qtd_registros": len(indices),
            "indices": list(indices),
            "severidade": severidade,
        })

    def verificar_duplicatas(self, subset=None):
        dup_mask = self.df.duplicated(subset=subset, keep="first")
        indices = self.df[dup_mask].index
        if len(indices) > 0:
            self._registrar_achado(
                tipo="Duplicatas",
                descricao=(
                    f"Registros duplicados encontrados"
                    f"{' (considerando: ' + ', '.join(subset) + ')' if subset else ''}"
                ),
                indices=indices,
                severidade="alta",
            )
        return indices

    def verificar_nulos(self, colunas_criticas=None):
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

    def verificar_outliers(self, coluna: str, fator: float = 1.5):
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
                descricao=(
                    f"Coluna '{coluna}' possui valores fora do padrão estatístico "
                    f"(limites: {limite_inferior:.2f} a {limite_superior:.2f})"
                ),
                indices=idx_outliers,
                severidade="alta",
            )

    def verificar_valores_negativos(self, coluna: str):
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

    def verificar_datas(
        self,
        coluna: str,
        formato: str = "%Y-%m-%d",
        data_min: Optional[str] = None,
        data_max: Optional[str] = None,
    ):
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

    def verificar_formatacao_texto(self, coluna: str):
        if coluna not in self.df.columns:
            return

        serie = self.df[coluna].dropna().astype(str)
        idx_com_espacos = serie[serie != serie.str.strip()].index

        if len(idx_com_espacos) > 0:
            self._registrar_achado(
                tipo="Formatação Inconsistente",
                descricao=(
                    f"Coluna '{coluna}' possui espaços extras, "
                    f"prejudicando agrupamentos"
                ),
                indices=idx_com_espacos,
                severidade="baixa",
            )

    def verificar_consistencia_calculo(
        self,
        col_qtd: str,
        col_valor_unit: str,
        col_valor_total: str,
        tolerancia: float = 0.01,
    ):
        for col in (col_qtd, col_valor_unit, col_valor_total):
            if col not in self.df.columns:
                return

        qtd = pd.to_numeric(self.df[col_qtd], errors="coerce")
        v_unit = pd.to_numeric(self.df[col_valor_unit], errors="coerce")
        v_total = pd.to_numeric(self.df[col_valor_total], errors="coerce")
        v_esperado = qtd * v_unit

        diff = (v_total - v_esperado).abs()
        idx_inconsistente = self.df[diff > tolerancia].index
        idx_inconsistente = idx_inconsistente.intersection(
            self.df[qtd.notna() & v_unit.notna() & v_total.notna()].index
        )

        if len(idx_inconsistente) > 0:
            self._registrar_achado(
                tipo="Erro de Cálculo",
                descricao=(
                    f"'{col_valor_total}' não corresponde a "
                    f"'{col_qtd}' × '{col_valor_unit}' em {len(idx_inconsistente)} registros"
                ),
                indices=idx_inconsistente,
                severidade="alta",
            )

    def rodar_auditoria_completa(self, config: Dict[str, Any]):
        self.verificar_duplicatas(config.get("duplicatas_subset"))
        self.verificar_nulos(config.get("colunas_criticas_nulos"))
        if config.get("coluna_outlier"):
            self.verificar_outliers(config["coluna_outlier"])
        if config.get("coluna_negativa"):
            self.verificar_valores_negativos(config["coluna_negativa"])
        if config.get("coluna_data"):
            self.verificar_datas(
                config["coluna_data"],
                data_min="2020-01-01",
                data_max="2026-12-31",
            )
        if config.get("coluna_texto"):
            self.verificar_formatacao_texto(config["coluna_texto"])
        if config.get("calculo"):
            self.verificar_consistencia_calculo(*config["calculo"])
        return self.achados

    def gerar_relatorio_markdown(self, caminho_saida: str = "relatorio_auditoria.md") -> str:
        total_registros = len(self.df_original)
        registros_unicos_com_problema = set()
        for a in self.achados:
            registros_unicos_com_problema.update(a["indices"])

        pct_afetado = (
            len(registros_unicos_com_problema) / total_registros * 100
            if total_registros else 0
        )

        linhas = [
            "# Relatório de Auditoria de Dados",
            "",
            f"**Base analisada:** `{self.nome_base}`  ",
            f"**Data da auditoria:** {self.timestamp}  ",
            f"**Total de registros analisados:** {total_registros}  ",
            f"**Registros com pelo menos um problema:** {len(registros_unicos_com_problema)} ({pct_afetado:.1f}%)  ",
            f"**Total de ocorrências identificadas:** {sum(a['qtd_registros'] for a in self.achados)}  ",
            "",
            "---",
            "",
            "## Resumo dos Achados",
            "",
            "| Tipo de Problema | Severidade | Registros Afetados |",
            "|---|---|---|",
        ]

        severidade_ordem = {"alta": 0, "média": 1, "baixa": 2}
        achados_ordenados = sorted(
            self.achados, key=lambda a: severidade_ordem.get(a["severidade"], 3)
        )

        for a in achados_ordenados:
            linhas.append(
                f"| {a['tipo']} | {a['severidade'].capitalize()} | {a['qtd_registros']} |"
            )

        linhas.extend(["", "---", "", "## Detalhamento dos Achados", ""])

        for a in achados_ordenados:
            linhas.append(f"### {a['tipo']} — Severidade: {a['severidade'].capitalize()}")
            linhas.append("")
            linhas.append(a["descricao"])
            linhas.append("")
            linhas.append(f"- **Registros afetados:** {a['qtd_registros']}")
            amostra = a["indices"][:5]
            linhas.append(f"- **Amostra de índices:** {amostra}")
            linhas.append("")

        linhas.extend(["---", "", "## Recomendações", ""])
        if any(a["tipo"] == "Duplicatas" for a in self.achados):
            linhas.append("- Implementar validação de unicidade na origem dos dados.")
        if any(a["tipo"] == "Valores Nulos" for a in self.achados):
            linhas.append("- Tornar campos críticos obrigatórios no sistema de entrada.")
        if any(a["tipo"] == "Outliers" for a in self.achados):
            linhas.append("- Investigar outliers; podem indicar fraude ou erro de digitação.")
        if any(a["tipo"] == "Erro de Cálculo" for a in self.achados):
            linhas.append("- Revisar a lógica de cálculo no sistema de origem.")
        linhas.append("- Reexecutar esta auditoria periodicamente para monitoramento contínuo.")

        conteudo = "\n".join(linhas)
        Path(caminho_saida).write_text(conteudo, encoding="utf-8")
        return caminho_saida

    def salvar_no_sqlite(self, caminho_db: str = "auditoria.db") -> str:
        conn = sqlite3.connect(caminho_db)

        registros_com_problema = set()
        for a in self.achados:
            registros_com_problema.update(a["indices"])

        df_export = self.df_original.copy()
        df_export["auditoria_flag_problema"] = df_export.index.isin(registros_com_problema)
        df_export["auditoria_timestamp"] = self.timestamp
        df_export.to_sql("dados_auditados", conn, if_exists="replace", index_label="idx_original")

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
        if not achados_df.empty:
            achados_df.to_sql("historico_achados", conn, if_exists="append", index=False)

        conn.commit()
        conn.close()
        return caminho_db
