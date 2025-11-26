import pandas as pd
import matplotlib.pyplot as plt
import math
import matplotlib.colors as mcolors

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
        candidatos = municipios

    best_center = None
    best_max_dist = float("inf")

    for m_i in candidatos:
        max_d = max(dist(m_i, m_j) for m_j in municipios)
        if max_d < best_max_dist:
            best_max_dist = max_d
            best_center = m_i

    helipuertos[cluster_name] = best_center

# ==========================================
# 5. ASIGNAR ÁREA DE SERVICIO (VORONOI DISCRETO)
# ==========================================
areas_servicio = {cl: [] for cl in helipuertos.keys()}
asignaciones = []
distancias = []

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
    distancias.append(dmin)

    # GUARDAR EN ÁREAS DE SERVICIO
    areas_servicio[centro_asignado].append(muni["Municipio"])

df["area_servicio"] = asignaciones
df["distancia_helipuerto"] = distancias
df["helipuerto_municipio"] = df["area_servicio"].apply(lambda cl: helipuertos[cl]["Municipio"])

# ==========================================
# 6. MOSTRAR ÁREAS DE SERVICIO EN CONSOLA
# ==========================================
for cluster_name, lista in areas_servicio.items():
    print(f"Área de servicio de {helipuertos[cluster_name]['Municipio']} ({cluster_name}): {len(lista)} municipios")

# ==========================================
# 7. CSV LIMPIO
# ==========================================
df_export = df[
    [
        "Municipio",
        "Provincia",
        "Comarca",
        "cluster",
        "CoordenadaX",
        "CoordenadaY",
        "Población",
        "area_servicio",
        "helipuerto_municipio",
        "distancia_helipuerto"
    ]
]

df_export.to_csv("helipuertos_con_asignacion.csv", index=False)
print("CSV creado: helipuertos_con_asignacion.csv")

# ==========================================
# 8. GRÁFICA FINAL (NOMBRES + ÁREAS)
# ==========================================

plt.figure(figsize=(18, 13))

# Colores por área
colores = list(mcolors.TABLEAU_COLORS.values())
while len(colores) < len(helipuertos):
    colores += colores

color_map = {name: colores[i] for i, name in enumerate(helipuertos.keys())}

# Dibujar municipios según área
for area, group in df.groupby("area_servicio"):
    plt.scatter(
        group["CoordenadaX"],
        group["CoordenadaY"],
        s=25,
        alpha=0.65,
        color=color_map[area],
        label=f"Área: {area}"
    )

# ===== ETIQUETAS SIN SOLAPAMIENTO =====
def offset_label(x, y, i):
    offsets = [
        (1800, 1800), (-2000, 1800),
        (1800, -2000), (-2000, -2000),
        (1500, 2500), (-1500, 2500),
    ]
    return (x + offsets[i % len(offsets)][0], y + offsets[i % len(offsets)][1])

# Dibujar helipuertos + nombres SIN FONDO
for i, (cluster_name, muni) in enumerate(helipuertos.items()):
    plt.scatter(
        muni["CoordenadaX"],
        muni["CoordenadaY"],
        s=400,
        marker="*",
        color="black",
        edgecolor="yellow",
        linewidth=1.8,
        zorder=10
    )

    ox, oy = offset_label(muni["CoordenadaX"], muni["CoordenadaY"], i)

    plt.text(
        ox,
        oy,
        f"{muni['Municipio']} ({cluster_name})",
        fontsize=11,
        fontweight="bold",
        color="black",
        zorder=11
    )

plt.title("Áreas de servicio por helipuerto (Modelo P-Center)\nCon nombres de helipuertos y zonas coloreadas", fontsize=15)
plt.xlabel("Coordenada X")
plt.ylabel("Coordenada Y")
plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
plt.grid(True)
plt.tight_layout()
plt.show()
