import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("features.csv")

features = [
    "gray_median",
    "V_mean",
    "glcm_contrast"
]

for f in features:

    plt.figure(figsize=(5,4))
    plt.hist(df[f], bins=20)

    plt.title(f)
    plt.ylabel(f)
    plt.xlabel("Nombre d'images")

plt.show()