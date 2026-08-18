# Validador / Auditoria Automatizada de Dados

Ferramenta em Python que analisa bases de dados e identifica automaticamente inconsistências comuns em processos de auditoria e controle de qualidade:

- Duplicatas
- Valores nulos em campos críticos
- Outliers estatísticos (IQR)
- Valores negativos inválidos
- Datas inválidas
- Formatação inconsistente de texto
- Erros de cálculo (`quantidade × valor_unitario ≠ valor_total`)

Gera **relatório em Markdown** classificado por severidade e persiste os achados em **SQLite**.

---

## Instalação

```bash
git clone https://github.com/matheusscherer/validador_dados.git
cd validador_dados

python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

---

## Como usar

```bash
python -m validador_dados.main
# ou
validador-dados
```

Se não existir `dados_vendas_bruto.csv`, o script gera automaticamente uma base sintética com inconsistências propositais.

Saídas:
- `relatorio_auditoria.md`
- `auditoria.db`

---

## Uso programático

```python
import pandas as pd
from validador_dados import AuditorDados

df = pd.read_csv("sua_base.csv")
auditor = AuditorDados(df, nome_base="minha_base")

config = {
    "duplicatas_subset": None,
    "colunas_criticas_nulos": ["vendedor", "valor_unitario"],
    "coluna_outlier": "valor_total",
    "coluna_negativa": "quantidade",
    "coluna_data": "data_venda",
    "coluna_texto": "filial",
    "calculo": ("quantidade", "valor_unitario", "valor_total"),
}

achados = auditor.rodar_auditoria_completa(config)
auditor.gerar_relatorio_markdown()
auditor.salvar_no_sqlite()
```

---

## Stack

- Python 3.10+
- Pandas + NumPy
- SQLite
- pytest + GitHub Actions

---

**Matheus Scherer** · [github.com/matheusscherer](https://github.com/matheusscherer)

MIT License
