# Automação de auditoria — base suja → o que está errado

CSV entra. Sai relatório: duplicata, nulo, outlier, data inválida, conta que não fecha. Gravado em SQLite.

O exemplo é venda. O motor serve qualquer planilha que a operação ainda confia no olho.

**Autor:** [Matheus Scherer](https://github.com/matheusscherer) — automação de processos com Python.

---

## Processo

| | |
|---|---|
| **Entra** | CSV (`dados_vendas_bruto.csv` ou o teu) |
| **Checa** | duplicata · nulo em campo crítico · outlier (IQR) · negativo · data · texto · `qtd × unitário ≠ total` |
| **Sai** | `relatorio_auditoria.md` (por severidade) + `auditoria.db` |

Sem CSV na pasta, gera uma base sintética com erro de propósito — só pra ver o relatório.

---

## Como roda

```bash
git clone https://github.com/matheusscherer/validador_dados.git
cd validador_dados
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m validador_dados.main
pytest -v
```

---

Python 3.10+ · Pandas · SQLite · pytest · MIT
