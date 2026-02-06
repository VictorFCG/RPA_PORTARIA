import pandas as pd
from tkinter import Tk, filedialog

def spit_csv(filenames):
    # Lista para armazenar os DataFrames de cada arquivo
    lista_df = []

    for arquivo in filenames:
        df_temp = pd.read_csv(arquivo)
        lista_df.append(df_temp)

    # Junta todos os arquivos em um único DataFrame
    # O concat ignora os cabeçalhos internos e mantém apenas o primeiro
    df = pd.concat(lista_df, ignore_index=True)

    # --- Mesma operação que você já fazia ---
    if "Servidor" in df.columns:
        df["Servidor"] = df["Servidor"].astype(str).str.split(", ")
        df = df.explode("Servidor")
        df["Servidor"] = df["Servidor"].str.strip().str[:7]
    # ----------------------------------------

    # Salva o resultado consolidado
    df.to_csv("saida_consolidada.csv", index=False, encoding='utf-8-sig')
    print(f"Sucesso! {len(filenames)} arquivos processados em 'saida_consolidada.csv'")


if __name__ == "__main__":
    Tk().withdraw()

    # Abre o Explorer para selecionar o arquivo
    arquivo_entrada = filedialog.askopenfilenames(
        title="Selecione o(s) arquivo(s) CSV",
        filetypes=[("Arquivos CSV", "*.csv")]
    )

    # Se o usuário cancelar, o caminho vem vazio
    if not arquivo_entrada:
        raise SystemExit("Nenhum arquivo selecionado.")
    spit_csv(arquivo_entrada)