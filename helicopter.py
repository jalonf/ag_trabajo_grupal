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


# ==========================================
# 6. ASIGNAR ÁREA DE SERVICIO A CADA HELIPUERTO
# ==========================================

# Crear un diccionario donde cada helipuerto tiene una lista de municipios asignados
areas_servicio = {h: [] for h in helipuertos.keys()}

for _, muni in df.iterrows():
    # Encontramos el helipuerto más cercano
    mejor_cluster = None
    mejor_dist = float("inf")

    for cluster_name, h in helipuertos.items():
        d = math.hypot(
            muni["CoordenadaX"] - h["CoordenadaX"],
            muni["CoordenadaY"] - h["CoordenadaY"]
        )
        if d < mejor_dist:
            mejor_dist = d
            mejor_cluster = cluster_name

    # Asignamos el municipio a su área de servicio
    areas_servicio[mejor_cluster].append(muni["Municipio"])

# Opcional: mostrar conteos
for cluster_name, lista in areas_servicio.items():
    print(f"Área de servicio de {helipuertos[cluster_name]['Municipio']} ({cluster_name}): {len(lista)} municipios")


# ==========================================
# 7. VISUALIZACIÓN: ÁREA DE SERVICIO EN EL GRÁFICO
# ==========================================

plt.figure(figsize=(16, 12))

# 1) Asignar cada municipio a su helipuerto más cercano
asignaciones = []
for _, muni in df.iterrows():
    dmin = float("inf")
    centro_asignado = None
    
    for cluster_name, h in helipuertos.items():
        d = math.hypot(
            muni["CoordenadaX"] - h["CoordenadaX"],
            muni["CoordenadaY"] - h["CoordenadaY"]
        )
        if d < dmin:
            dmin = d
            centro_asignado = cluster_name
    
    asignaciones.append(centro_asignado)

df["area_servicio"] = asignaciones

# 2) Colores para cada área
import matplotlib.colors as mcolors
colores = list(mcolors.TABLEAU_COLORS.values())
while len(colores) < len(helipuertos):
    colores += colores  # duplicar si hiciera falta

color_map = {name: colores[i] for i, name in enumerate(helipuertos.keys())}

# 3) Dibujar municipios coloreados por área
for area, group in df.groupby("area_servicio"):
    plt.scatter(
        group["CoordenadaX"],
        group["CoordenadaY"],
        s=25,
        alpha=0.65,
        color=color_map[area],
        label=f"Área {area}"
    )

# 4) Dibujar helipuertos encima
for cluster_name, muni in helipuertos.items():
    plt.scatter(
        muni["CoordenadaX"],
        muni["CoordenadaY"],
        s=300,
        marker="*",
        color="black",
        edgecolor="yellow",
        linewidth=1.7,
        zorder=10
    )
    plt.text(
        muni["CoordenadaX"] + 500,
        muni["CoordenadaY"] + 500,
        muni["Municipio"] + " (Helipuerto)",
        fontsize=10,
        fontweight="bold",
        zorder=11
    )

plt.title("Áreas de servicio asignadas por distancia al helipuerto (Voronoi discreto)")
plt.xlabel("Coordenada X")
plt.ylabel("Coordenada Y")
plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
plt.grid(True)
plt.tight_layout()
plt.show()
