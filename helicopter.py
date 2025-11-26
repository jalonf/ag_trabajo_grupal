import pandas as pd
import matplotlib.pyplot as plt
import math

# ================================
# 1. Cargar CSV y limpiar BOM
# ================================
df = pd.read_csv("municipios.csv", sep=";", encoding="utf-8-sig")
df.columns = df.columns.str.replace("\ufeff", "", regex=False)

# ================================
# 2. Crear clusters (provincias + Bierzo)
# ================================
df["cluster"] = df.apply(
    lambda row: "BIERZO"
    if row["Provincia"] == "LEÓN" and row["Comarca"] == "COMARCA DE EL BIERZO"
    else row["Provincia"],
    axis=1
)

# ================================
# 3. Distancia euclídea
# ================================
def dist(a, b):
    return math.hypot(a["CoordenadaX"] - b["CoordenadaX"], a["CoordenadaY"] - b["CoordenadaY"])

# ================================
# 4. ALGORITMO P-CENTER POR PROVINCIA
# ================================
helipuertos = {}

for cluster_name, subdf in df.groupby("cluster"):

    municipios = list(subdf.to_dict("records"))

    # Candidatos válidos (≥ 300 hab)
    candidatos = [m for m in municipios if m["Población"] >= 300]
    if not candidatos:
        candidatos = municipios  # fallback si ninguna cumple

    best_center = None
    best_max_dist = float("inf")

    for m_i in candidatos:
        # coste p-center = distancia máxima a otro municipio
        max_d = max(dist(m_i, m_j) for m_j in municipios)

        if max_d < best_max_dist:
            best_max_dist = max_d
            best_center = m_i

    helipuertos[cluster_name] = best_center

# ================================
# 5. GRÁFICA FINAL: solo centros nombrados
# ================================
plt.figure(figsize=(16, 12))

# Dibujar punto por municipio
for cluster_name, group in df.groupby("cluster"):
    plt.scatter(group["CoordenadaX"], group["CoordenadaY"], s=18, alpha=0.5, label=cluster_name)

# Dibujar helipuertos
for cluster_name, muni in helipuertos.items():
    plt.scatter(
        muni["CoordenadaX"], muni["CoordenadaY"],
        s=260, marker="*", color="black", edgecolor="yellow", linewidth=1.5
    )
    plt.text(
        muni["CoordenadaX"] + 600,
        muni["CoordenadaY"] + 600,
        muni["Municipio"] + " (Helipuerto)",
        fontsize=10,
        fontweight="bold"
    )

plt.title("Modelo P-Center por Provincia (minimización del tiempo máximo de respuesta)")
plt.xlabel("Coordenada X")
plt.ylabel("Coordenada Y")
plt.grid(True)
plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
plt.tight_layout()
plt.show()
