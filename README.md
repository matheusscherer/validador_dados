# Auditoria de base — CSV entra, relatório sai

Script em Python que lê um CSV, roda checagens de qualidade e grava:

- `relatorio_auditoria.md` — achados por severidade
- `auditoria.db` — SQLite com a base flagada e o histórico

O exemplo usa vendas. O motor serve qualquer planilha tabular. A base do exemplo é **sintético**, gerada pelo próprio código, com erro de propósito.

**Autor:** [Matheus Scherer](https://github.com/matheusscherer) · Porto Alegre

---

## O que faz

| | |
|---|---|
| **Entra** | CSV (`dados_vendas_bruto.csv` ou o teu) |
| **Checa** | duplicata · nulo em campo crítico · outlier (IQR) · negativo · data · texto com espaço · `qtd × unitário ≠ total` |
| **Sai** | Markdown + SQLite |

Sem CSV na pasta, gera 500 linhas sintéticas com seed 42 — só para ver o relatório.

---

## Stack

Python 3.10+ · Pandas · NumPy · SQLite · pytest · GitHub Actions · MIT

---

## Como executar

```bash
git clone https://github.com/matheusscherer/validador_dados.git
cd validador_dados
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m validador_dados.main
pytest -v
```

Regenerar o exemplo commitado:

```bash
PYTHONPATH=src python scripts/gerar_exemplo.py
```

---

## Evidência / demo

Relatório gerado **pelo código**, não escrito à mão:

- [docs/relatorio_exemplo.md](docs/relatorio_exemplo.md) — 505 linhas sintéticas, 89 registros com pelo menos um problema (17.6% nesta execução)
- Testes: cálculo que fecha **não** flagra; `3 × 10 ≠ 25` **flagra**; nulo crítico; duplicata; relatório contém o tipo do achado
- CI: pytest em Python 3.10 / 3.11 / 3.12

Isto **não** é resultado de cliente. É a saída do motor nesta base de exemplo.

---

## Limitações

- Outlier é IQR simples. Em distribuição assimétrica flagra demais — nesta execução, 61 outliers.
- Datas com recorte fixo 2020–2026 no `rodar_auditoria_completa`.
- Não é perfilador contínuo, não é Great Expectations, não tem schema versionado.
- SQLite é dump da execução, não warehouse.

---

## O que isto NÃO é

- Não é cliente real, case nem métrica de operação.
- Não é engenharia de dados corporativa (sem dbt, Airflow, warehouse).
- Não é antivírus de fraude.
- Não prova SQL além de `to_sql`.

---

Python 3.10+ · Pandas · SQLite · pytest · MIT
