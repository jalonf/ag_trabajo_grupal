import pandas as pd
import matplotlib.pyplot as plt
import math

# ================================
# 1. Cargar CSV y limpiar BOM
# ================================
df = pd.read_csv("municipios.csv", sep=";", encoding="utf-8-sig")
df.columns = df.columns.str.replace('\ufeff', '', regex=False)

# ================================
# 2. Crear clusters (provincias + Bierzo)
# ================================
df["cluster"] = df.apply(
    lambda row: "BIERZO"
    if (row["Provincia"] == "LEÓN" and row["Comarca"] == "COMARCA DE EL BIERZO")
    else row["Provincia"],
    axis=1
)

# ================================
# 3. Distancia euclídea
# ================================
def dist(a, b):
    return math.hypot(a["CoordenadaX"] - b["CoordenadaX"], a["CoordenadaY"] - b["CoordenadaY"])

# ================================
# 4. CALCULAR 1-MEDIANA NO PONDERADA
#    Después aplicar filtro población ≥ 300
# ================================
helipuertos = {}

for cluster_name, subdf in df.groupby("cluster"):
    municipios = list(subdf.to_dict("records"))

    # 4.1 Encontrar 1-mediana NO ponderada
    best_center = None
    best_cost = float("inf")

    for i, m_i in enumerate(municipios):
        cost = 0
        for j, m_j in enumerate(municipios):
            if i != j:
                cost += dist(m_i, m_j)

        if cost < best_cost:
            best_cost = cost
            best_center = m_i  # centro ideal no ponderado

    # 4.2 Si tiene ≥ 300 habitantes, lo usamos
    if best_center["Población"] >= 300:
        helipuertos[cluster_name] = best_center
        continue

    # 4.3 Si NO, buscamos el municipio ≥ 300 más cercano al centro ideal
    candidatos = [m for m in municipios if m["Población"] >= 300]

    # Si no hay ninguno ≥ 300, usamos el más poblado
    if not candidatos:
        helipuertos[cluster_name] = max(municipios, key=lambda m: m["Población"])
        continue

    mejor = min(candidatos, key=lambda m: dist(m, best_center))
    helipuertos[cluster_name] = mejor

# ================================
# 5. GRÁFICA FINAL (solo nombre del helipuerto)
# ================================
plt.figure(figsize=(16, 12))

# Dibujar todos los municipios
for cluster_name, group in df.groupby("cluster"):
    plt.scatter(group["CoordenadaX"], group["CoordenadaY"], s=20, alpha=0.6)

# Dibujar helipuertos
for cluster_name, muni in helipuertos.items():
    plt.scatter(
        muni["CoordenadaX"],
        muni["CoordenadaY"],
        s=260,
        marker="*",
        color="black",
        edgecolor="yellow",
        linewidth=1.5,
    )

    plt.text(
        muni["CoordenadaX"] + 600,
        muni["CoordenadaY"] + 600,
        muni["Municipio"] + " (Helipuerto)",
        fontsize=10,
        fontweight="bold"
    )

plt.title("Helipuertos óptimos por provincia\n1-mediana no ponderada + filtro población ≥ 300")
plt.xlabel("Coordenada X")
plt.ylabel("Coordenada Y")
plt.grid(True)
plt.tight_layout()
plt.show()
