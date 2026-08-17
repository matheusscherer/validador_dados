# 🔍 Auditoria Automatizada de Dados

Ferramenta em Python que analisa bases de dados e identifica automaticamente
inconsistências comuns em processos de auditoria e controle de qualidade de dados:
duplicatas, valores nulos, outliers estatísticos, erros de cálculo, datas
inválidas e inconsistências de formatação.

Gera um **relatório de auditoria em Markdown** com achados classificados por
severidade e recomendações, além de persistir os resultados em um banco
**SQLite** para consulta e histórico.

## Por que esse projeto existe

Áreas de auditoria interna e controle de qualidade em empresas de médio/grande
porte gastam boa parte do tempo validando manualmente planilhas e bases de
dados. Este projeto automatiza as verificações mais comuns desse processo,
permitindo que a auditoria seja executada de forma contínua (ex: rotina
semanal) em vez de manual e pontual.

## O que o script detecta

| Verificação | Descrição |
|---|---|
| **Duplicatas** | Registros com conteúdo idêntico, considerando todas as colunas relevantes |
| **Valores Nulos** | Campos críticos ausentes (ex: vendedor, valor) |
| **Outliers** | Valores estatisticamente fora do padrão (método IQR) |
| **Valores Negativos** | Campos que deveriam ser sempre positivos (ex: quantidade) |
| **Datas Inválidas** | Datas mal formatadas ou fora do período esperado |
| **Formatação Inconsistente** | Espaços extras, capitalização mista em campos de texto |
| **Erros de Cálculo** | Quando `quantidade × valor_unitário ≠ valor_total` |

## Como rodar

```bash
# 1. Instale as dependências
pip install -r requirements.txt

# 2. Gere uma base de dados de exemplo (com inconsistências propositais)
python3 gerar_dados_exemplo.py

# 3. Rode a auditoria
python3 auditoria.py
```

Isso vai gerar:
- `relatorio_auditoria.md` — relatório completo com achados e recomendações
- `auditoria.db` — banco SQLite com os dados auditados e histórico de achados

## Usando com sua própria base de dados

```python
import pandas as pd
from auditoria import AuditorDados

df = pd.read_csv("sua_base.csv")
auditor = AuditorDados(df, nome_base="minha_base")

config = {
    "duplicatas_subset": None,  # ou lista de colunas específicas
    "colunas_criticas_nulos": ["coluna_importante_1", "coluna_importante_2"],
    "coluna_outlier": "valor",
    "coluna_negativa": "quantidade",
    "coluna_data": "data",
    "coluna_texto": "categoria",
    "calculo": ("quantidade", "valor_unitario", "valor_total"),  # ou None
}

achados = auditor.rodar_auditoria_completa(config)
auditor.gerar_relatorio_markdown("meu_relatorio.md")
auditor.salvar_no_sqlite("meu_banco.db")
```

Cada verificação também pode ser chamada individualmente
(`auditor.verificar_duplicatas()`, `auditor.verificar_outliers("coluna")`, etc.)
para uso mais granular.

## Estrutura do projeto

```
auditoria-dados-automatizada/
├── auditoria.py              # motor principal (classe AuditorDados)
├── gerar_dados_exemplo.py    # gera base sintética para demonstração
├── requirements.txt
└── README.md
```

## Stack técnica

- **Python 3** — linguagem principal
- **Pandas** — manipulação e análise de dados
- **NumPy** — cálculos estatísticos (detecção de outliers via IQR)
- **SQLite** — persistência dos achados e histórico de auditorias

## Possíveis evoluções

- Agendamento automático (ex: `cron` ou Airflow) para rodar a auditoria periodicamente
- Envio de alertas por e-mail quando novos problemas críticos forem detectados
- Interface web para visualização dos achados (ver projeto [dashboard-analise-dados](../dashboard-analise-dados))

---

Desenvolvido por **Matheus Scherer** — [github.com/matheusscherer](https://github.com/matheusscherer)
