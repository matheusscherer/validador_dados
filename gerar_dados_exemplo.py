"""
Gerador de dados sintéticos para demonstração do projeto de auditoria.
Cria uma base de vendas com inconsistências propositais (duplicatas,
valores nulos, outliers, formatos inconsistentes) para simular um
cenário real de auditoria de dados.
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

NOMES = [
    "João Silva", "Maria Oliveira", "Carlos Souza", "Ana Pereira",
    "Pedro Santos", "Juliana Costa", "Lucas Rodrigues", "Fernanda Lima",
    "Rafael Almeida", "Camila Ferreira", "Bruno Carvalho", "Larissa Gomes",
]

PRODUTOS = [
    ("Medicamento A", 25.90), ("Medicamento B", 45.50), ("Cosmético C", 89.90),
    ("Higiene D", 15.30), ("Suplemento E", 120.00), ("Medicamento F", 32.70),
]

FILIAIS = ["Porto Alegre - Centro", "Porto Alegre - Zona Sul", "Eldorado do Sul",
           "Canoas", "Gravataí", "São Leopoldo"]


def gerar_base_vendas(n_registros=500):
    registros = []
    data_inicio = datetime(2026, 1, 1)

    for i in range(n_registros):
        produto, preco_base = random.choice(PRODUTOS)
        qtd = random.randint(1, 10)
        data_venda = data_inicio + timedelta(days=random.randint(0, 210))

        registro = {
            "id_venda": i + 1,
            "data_venda": data_venda.strftime("%Y-%m-%d"),
            "filial": random.choice(FILIAIS),
            "vendedor": random.choice(NOMES),
            "produto": produto,
            "quantidade": qtd,
            "valor_unitario": preco_base,
            "valor_total": round(preco_base * qtd, 2),
        }
        registros.append(registro)

    df = pd.DataFrame(registros)

    # --- Injetando inconsistências propositais (simula dados reais sujos) ---

    # 1. Duplicatas exatas (5 registros duplicados)
    duplicatas = df.sample(5, random_state=1).copy()
    df = pd.concat([df, duplicatas], ignore_index=True)

    # 2. Valores nulos em campos importantes
    idx_nulos = df.sample(15, random_state=2).index
    df.loc[idx_nulos[:8], "vendedor"] = None
    df.loc[idx_nulos[8:], "valor_unitario"] = None

    # 3. Outliers - valores de venda absurdamente altos (erro de digitação)
    idx_outliers = df.sample(6, random_state=3).index
    df.loc[idx_outliers, "valor_total"] = df.loc[idx_outliers, "valor_total"] * 1000

    # 4. Quantidade negativa (erro de sistema)
    idx_negativos = df.sample(4, random_state=4).index
    df.loc[idx_negativos, "quantidade"] = -abs(df.loc[idx_negativos, "quantidade"])

    # 5. Datas fora do período esperado (inconsistência de digitação)
    idx_data_invalida = df.sample(3, random_state=5).index
    df.loc[idx_data_invalida, "data_venda"] = "2019-13-45"  # data inválida

    # 6. Inconsistência de formatação em texto (espaços, maiúsculas/minúsculas)
    idx_formato = df.sample(10, random_state=6).index
    df.loc[idx_formato, "filial"] = df.loc[idx_formato, "filial"].str.upper() + "  "

    # 7. Valor_total não bate com quantidade x valor_unitario (erro de cálculo)
    idx_calculo_errado = df.sample(8, random_state=7).index
    df.loc[idx_calculo_errado, "valor_total"] = df.loc[idx_calculo_errado, "valor_total"] + 999.99

    df = df.sample(frac=1, random_state=8).reset_index(drop=True)  # embaralha
    df["id_venda"] = range(1, len(df) + 1)  # reindexar id

    return df


if __name__ == "__main__":
    df = gerar_base_vendas(500)
    df.to_csv("dados_vendas_bruto.csv", index=False, encoding="utf-8")
    print(f"Base gerada com {len(df)} registros -> dados_vendas_bruto.csv")
    print(f"Inconsistências propositais injetadas: duplicatas, nulos, outliers,")
    print(f"quantidades negativas, datas inválidas, formatação e erros de cálculo.")
