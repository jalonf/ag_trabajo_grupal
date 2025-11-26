import pandas as pd
import matplotlib.pyplot as plt

# 1. Cargar CSV (ajusta sep en función de tu archivo)
df = pd.read_csv("municipios.csv", sep=";", engine="python")

# 2. Crear columna 'cluster' separando Bierzo del resto de León
df["cluster"] = df.apply(
    lambda row: (
        "BIERZO"
        if (row["Provincia"] == "LEÓN" and row["Comarca"] == "COMARCA DE EL BIERZO")
        else row["Provincia"]
    ),
    axis=1
)

# 3. Dibujar gráfica de puntos coloreados por cluster
plt.figure(figsize=(10, 8))

for cluster_name, group in df.groupby("cluster"):
    plt.scatter(
        group["CoordenadaX"],
        group["CoordenadaY"],
        label=cluster_name,
        alpha=0.7,
        s=20
    )

plt.title("Clusters de Municipios (Provincias + Bierzo)")
plt.xlabel("Coordenada X")
plt.ylabel("Coordenada Y")
plt.legend()
plt.grid(True)

plt.show()
