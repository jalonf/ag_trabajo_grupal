import pandas as pd
import matplotlib.pyplot as plt
import math
import matplotlib.colors as mcolors

# ================================
# 1. Cargar CSV y limpiar BOM (caracter invisible csv)
# ================================
df = pd.read_csv("municipios.csv", sep=";", encoding="utf-8-sig")
df.columns = df.columns.str.replace("\ufeff", "", regex=False)

# ================================
# 2. Crear clusters (provincias + Bierzo)
# ================================

"""
Se crea una nueva columna 'cluster' en el DataFrame df.
El contenido de 'cluster' para cada municipio es:
- Si el municipio está en la provincia de LEÓN y en la comarca de EL BIERZO,
    entonces el valor de 'cluster' será "BIERZO".
- En caso de que no cumpla la condición previa, el valor 
    de 'cluster' será el nombre de la provincia del municipio.    
"""
df["cluster"] = df.apply(
    lambda row: "BIERZO"
    if row["Provincia"] == "LEÓN" and row["Comarca"] == "COMARCA DE EL BIERZO"
    else row["Provincia"],
    axis=1
)

# ================================
# 3. Distancia euclídea
# ================================

# Calcula la distancia euclídea entre dos puntos (ciudades) a y b,
# usando sus coordenadas 'CoordenadaX' y 'CoordenadaY'.
# math.hypot(dx, dy) = sqrt(dx**2 + dy**2)
def dist(a, b):
    return math.hypot(a["CoordenadaX"] - b["CoordenadaX"], a["CoordenadaY"] - b["CoordenadaY"])

# ================================
# 4. ALGORITMO P-CENTER POR PROVINCIA
# ================================

# Defino la lista de helipuertos.
helipuertos = {}

for cluster_name, subdf in df.groupby("cluster"):

    """
    Convertimos las filas del cluster en una lista de diccionarios (municipios)
    Ejemplo de un municipio dentro del diccionario:
    municipio = {
    "Municipio": "ANDAVÍAS",                      
    "Cod_Municipio": 9,                          
    "Provincia": "ZAMORA",                        
    "Cod_Provincia": 49, 
    .
    .
    .
    cluster: "ZAMORA"       # Columna añadida en el paso 2
    }                          
    """
    municipios = list(subdf.to_dict("records"))

    # Cogemos como candidatos solo los municipios con al menos 300 habitantes.
    candidatos = [m for m in municipios if m["Población"] >= 300]
    # Si ningún municipio llega a 300 habitantes (no debería ocurrir), usamos todos los municipios del cluster
    if not candidatos:
        candidatos = municipios

    best_center = None          # Mejor municipio encontrado como centro
    best_max_dist = float("inf")  # Mejor (mínima) distancia máxima encontrada

    # Para cada candidato calculamos la peor distancia a cualquier municipio del cluster.
    for m_i in candidatos:
        max_d = max(dist(m_i, m_j) for m_j in municipios)
        # Nos quedamos con el candidato cuya peor distancia sea la menor posible.
        if max_d < best_max_dist:
            best_max_dist = max_d
            best_center = m_i

    # Guardamos, para cada cluster, el municipio elegido como centro del helipuerto.
    helipuertos[cluster_name] = best_center


# ==========================================
# 5. ASIGNAR ÁREA DE SERVICIO (VORONOI DISCRETO)
# ==========================================

# Diccionario donde, para cada helipuerto (clave = nombre del cluster),
# guardaremos la lista de municipios que quedan en su área de servicio.
areas_servicio = {cl: [] for cl in helipuertos.keys()}

# Listas auxiliares para ir guardando, para cada municipio del DataFrame,
# a qué área de servicio se asigna y a qué distancia está de su helipuerto.
asignaciones = []
distancias = []

# Recorremos todos los municipios del DataFrame
for _, muni in df.iterrows():
    # Inicializamos la mejor distancia encontrada como infinito
    # y sin helipuerto asignado aún.
    dmin = float("inf")
    centro_asignado = None

    # Comparamos el municipio con cada helipuerto disponible
    for cluster_name, h in helipuertos.items():
        # Calculamos la distancia euclídea entre el municipio y el helipuerto
        d = math.hypot(
            muni["CoordenadaX"] - h["CoordenadaX"],
            muni["CoordenadaY"] - h["CoordenadaY"]
        )

        # Si esta distancia es menor que la mejor encontrada hasta ahora,
        # actualizamos la distancia mínima y el helipuerto asignado.
        if d < dmin:
            dmin = d
            centro_asignado = cluster_name

    # Al terminar el bucle de helipuertos, ya sabemos cuál es el más cercano:
    # guardamos el área de servicio (cluster_name) y la distancia mínima.
    asignaciones.append(centro_asignado)
    distancias.append(dmin)

    # Añadimos el municipio actual a la lista de municipios atendidos
    # por el helipuerto más cercano (su área de servicio).
    areas_servicio[centro_asignado].append(muni["Municipio"])

# Añadimos al DataFrame la columna con el área de servicio asignada
df["area_servicio"] = asignaciones

# Añadimos la distancia desde cada municipio a su helipuerto
df["distancia_helipuerto"] = distancias

# Añadimos el nombre del municipio que actúa como helipuerto asignado
# (buscándolo en el diccionario 'helipuertos' a partir del área de servicio).
df["helipuerto_municipio"] = df["area_servicio"].apply(
    lambda cl: helipuertos[cl]["Municipio"]
)

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
