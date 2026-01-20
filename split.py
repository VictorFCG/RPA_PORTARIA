import pandas as pd
from tkinter import Tk, filedialog

def spit_csv(filename):
    df = pd.read_csv(filename)

    df["Servidor"] = df["Servidor"].str.split(", ")
    df = df.explode("Servidor")

    df["Servidor"] = df["Servidor"].str.strip()

    df.to_csv("saida.csv", index=False)


if __name__ == "__main__":
    Tk().withdraw()

    # Abre o Explorer para selecionar o arquivo
    arquivo_entrada = filedialog.askopenfilename(
        title="Selecione o arquivo CSV",
        filetypes=[("Arquivos CSV", "*.csv")]
    )

    # Se o usuário cancelar, o caminho vem vazio
    if not arquivo_entrada:
        raise SystemExit("Nenhum arquivo selecionado.")
    spit_csv(arquivo_entrada)