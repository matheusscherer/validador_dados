# Relatório de Auditoria de Dados

**Base analisada:** `vendas_farmacia_2026`  
**Data da auditoria:** 2026-08-15 21:47:39  
**Total de registros analisados:** 505  
**Registros com pelo menos um problema:** 89 (17.6%)  
**Total de ocorrências identificadas:** 112  

---

## Resumo dos Achados

| Tipo de Problema | Severidade | Registros Afetados |
|---|---|---|
| Duplicatas | Alta | 2 |
| Valores Nulos | Alta | 8 |
| Valores Nulos | Alta | 7 |
| Outliers | Alta | 61 |
| Valores Negativos | Alta | 4 |
| Erro de Cálculo | Alta | 17 |
| Datas Inválidas | Média | 3 |
| Formatação Inconsistente | Baixa | 10 |

---

## Detalhamento dos Achados

### Duplicatas — Severidade: Alta

Registros duplicados encontrados (considerando: data_venda, filial, vendedor, produto, quantidade, valor_unitario, valor_total)

- **Registros afetados:** 2
- **Amostra de índices (linhas do DataFrame):** [445, 503]

### Valores Nulos — Severidade: Alta

Coluna 'vendedor' possui valores ausentes

- **Registros afetados:** 8
- **Amostra de índices (linhas do DataFrame):** [85, 106, 111, 113, 231]

### Valores Nulos — Severidade: Alta

Coluna 'valor_unitario' possui valores ausentes

- **Registros afetados:** 7
- **Amostra de índices (linhas do DataFrame):** [149, 194, 199, 343, 382]

### Outliers — Severidade: Alta

Coluna 'valor_total' possui valores fora do padrão estatístico (limites esperados: -278.25 a 749.35)

- **Registros afetados:** 61
- **Amostra de índices (linhas do DataFrame):** [9, 10, 16, 17, 18]

### Valores Negativos — Severidade: Alta

Coluna 'quantidade' possui valores negativos inválidos

- **Registros afetados:** 4
- **Amostra de índices (linhas do DataFrame):** [6, 77, 231, 420]

### Erro de Cálculo — Severidade: Alta

'valor_total' não corresponde a 'quantidade' × 'valor_unitario' em 17 registros

- **Registros afetados:** 17
- **Amostra de índices (linhas do DataFrame):** [6, 16, 17, 19, 60]

### Datas Inválidas — Severidade: Média

Coluna 'data_venda' possui datas inválidas ou fora do período esperado

- **Registros afetados:** 3
- **Amostra de índices (linhas do DataFrame):** [187, 223, 399]

### Formatação Inconsistente — Severidade: Baixa

Coluna 'filial' possui espaços extras ou capitalização inconsistente, prejudicando agrupamentos

- **Registros afetados:** 10
- **Amostra de índices (linhas do DataFrame):** [62, 102, 208, 236, 312]

---

## Recomendações

- Implementar validação de unicidade na origem dos dados (ex: constraint de chave única).
- Tornar campos críticos obrigatórios no formulário/sistema de entrada de dados.
- Investigar manualmente os outliers identificados; podem indicar fraude ou erro de digitação.
- Revisar a lógica de cálculo no sistema de origem; valores podem estar sendo alterados manualmente após o cálculo automático.
- Reexecutar esta auditoria periodicamente (ex: rotina semanal) para monitoramento contínuo da qualidade dos dados.