from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from bs4 import BeautifulSoup
from PIL import Image, ImageTk
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from unidecode import unidecode
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from tkinter import ttk, Toplevel
from PIL import Image, ImageTk
import sys
import threading
import traceback
import csv
import time
import re
import os
import requests
import pdfplumber

def modal_handle(driver, results, nome, unidade):
    #faltantes - inicialização temporária
    detalhes = numero = boletimData = Portaria = Servidor = dou = retificada = "N/A"
    
    # 1. Aguarda o iframe carregar e o localiza
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "modal-frame"))
    )
    driver.switch_to.frame(iframe)

    #num documento
    texto_tabela = driver.find_element(By.XPATH, "/html/body/table").text
    padrao_sei = r"(?<=SEI nº\s)\d+"
    resultado = re.search(padrao_sei, texto_tabela)
    if resultado:
        document = resultado.group(0)
        print(f"Documento: {document}")
    else:
        print("Num do documento não encontrado.")
        document = "N/A"

    body_text = driver.find_element(By.TAG_NAME, "body").text
    match = re.search(
        r"R\s*E\s*S\s*O\s*L\s*V\s*E(.*?)(PUBLIQUE-?SE\s*E\s*REGISTRE-?SE|PUBLIQUE-?SE|PUBLIQUE)",
        body_text,
        flags=re.IGNORECASE | re.DOTALL,
        )
    if match:
        paragrafo = limpar_texto(match.group(1))
    else:
        print("Aviso: padrão 'R E S O L V E ... PUBLIQUE-SE' não encontrado, salvando conteúdo bruto")
        paragrafo = "N/A" 

    print(paragrafo)

    Servidor = extrair_servidores(paragrafo)
    print("Servidor(es):", Servidor)

    driver.switch_to.default_content()

    # 1. Localiza o elemento select pelo XPath fornecido
    elemento_select = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/form/div[13]/div[2]/select")
    # 2. Cria um objeto Select para interagir com o dropdown
    detalhes = Select(elemento_select).first_selected_option.text
    print(f"Detalhes: {detalhes}")

    results.append(
        {
            "Tipo_Processo": detalhes,
            "No_Processo": numero,
            "No_Documento": document,
            "Data_BSE": boletimData,
            "No_Portaria": Portaria,
            "Servidor": Servidor,
            "Descricao_Portaria": paragrafo,
            "Data_DOU": dou,
            "Republicacao": retificada,
            "Lotacao": unidade,
        })
    save(results, nome)

def limpar_texto(texto: str) -> str:
    if not texto:
        return ""

    texto = re.sub(r"^[^0-9A-Za-zÀ-ÿ]+", "", texto)
    texto = texto.replace("\xa0", " ")
    texto = texto.strip()
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{2,}", "\n", texto)

    return texto

def extrair_servidores(conteudo: str) -> str:
    # 1. Busca sequências de 7 a 8 dígitos que NÃO tenham dígitos antes ou depois
    # (?<!\d)  -> Lookbehind negativo: garante que não há um dígito antes
    # \d{7,8}  -> Corresponde a exatamente 7 ou 8 dígitos
    # (?!\d)   -> Lookahead negativo: garante que não há um dígito depois
    padrao = r"(?<!\d)\d{7,8}(?!\d)"
    
    # 2. Encontra todas as ocorrências no texto
    matches = re.findall(padrao, conteudo)
    
    # 3. Remove duplicatas usando set() e mantém uma ordem (opcional)
    # Se a ordem de aparição for importante, usamos dict.fromkeys()
    sequencias_unicas = list(dict.fromkeys(matches))
    
    # 4. Retorna as sequências unidas por vírgula e espaço
    return ", ".join(sequencias_unicas)

def save(results, arquivo):
    with open(arquivo, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "Tipo_Processo",
                "No_Processo",
                "No_Documento",
                "Data_BSE",
                "No_Portaria",
                "Servidor",
                "Descricao_Portaria",
                "Data_DOU",
                "Republicacao",
                "Lotacao",
            ],
            quotechar='"',
            quoting=csv.QUOTE_ALL, 
        )
        writer.writeheader()
        for result in results:
            writer.writerow(result)


# Specify the path to your chromedriver
def transform_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    desired_params = {
        "acao": "procedimento_trabalhar",
        "id_procedimento": query_params.get("id_procedimento", [None])[0],
        "id_documento": query_params.get("id_documento", [None])[0],
    }

    desired_params = {k: v for k, v in desired_params.items() if v is not None}

    new_query = urlencode(desired_params, doseq=True)
    transformed_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", new_query, "")
    )

    return transformed_url


def exec(numer, nome, dataInicio, dataFinal, usuario, senha, unidade):
    nome = (
        "Portarias_"
        + unidade
        + "_"
        + dataInicio.replace("/", "").replace("\\", "")
        + "_"
        + dataFinal.replace("/", "").replace("\\", "")
        + ".csv"
    )
    numero = str(numer)
    PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromedriver.exe")
    service = Service(PATH)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    download_dir = os.getcwd()

    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-popup-blocking")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    try:
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )
        driver.get("https://sei.utfpr.edu.br/")

        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pwdSenha"))
        ).send_keys(senha)
        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtUsuario"))
        ).send_keys(usuario)
        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "sbmAcessar"))
        ).click()

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//img[@title='Pesquisa Rápida']"))
        ).click()
        today_date = datetime.today().strftime("%d/%m/%Y")
        start_date = dataInicio
        end_date = dataFinal
        tipo_processo = "100000556"  # Geral: Comissão ou grupo de trabalho

        select_element = Select(driver.find_element(By.ID, "selSeriePesquisa"))
        select_element.select_by_value(numero)

        select_element = Select(
            driver.find_element(By.ID, "selTipoProcedimentoPesquisa")
        )
        select_element.select_by_value(
            tipo_processo
        )  # Futuramente dar opção para escolher o tipo de processo

        if unidade != "GABIR":
            input_unidade = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "txtUnidade"))
            )
            input_unidade.clear()
            input_unidade.send_keys(unidade)
            time.sleep(1)
            input_unidade.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.3)
            input_unidade.send_keys(Keys.RETURN)
            time.sleep(0.3)


        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtDataInicio"))
        ).send_keys(start_date)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtDataFim"))
        ).send_keys(end_date)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "sbmPesquisar"))
        ).click()

        results = []

        original_window = driver.current_window_handle
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        error_message = str(e) + "\n" + traceback.format_exc()
        file_name = f"erro_{current_time}.txt"
        with open(file_name, "w") as file:
            file.write(error_message)
        print(f"Error saved to {file_name}")
        exit(1)

    while True:
        try:
            j = 0
            i = 10

            td_elements = driver.find_elements(By.CLASS_NAME, "pesquisaTituloDireita")
            td_titulos = driver.find_elements(By.CLASS_NAME, "pesquisaTituloEsquerda")
            if not td_elements:
                modal_handle(driver, results, nome, unidade)
                break

            z = 0
            for td_element in td_elements:
                if z % 30 == 0:
                    save(results, nome)
                try:
                    link = td_element.find_element(By.TAG_NAME, "a")
                    link_url = link.get_attribute("href")
                    if len(link_url) >= 5 and "." in link_url[-5:]:
                        continue
                    document = link.text
                    titulo = td_titulos[z].text
                    index = titulo.find("Nº")
                    detalhes = titulo[:index].strip() if index != -1 else titulo.strip()
                    numero = "N/A"

                    try:
                        driver.execute_script("var e = document.getElementById('btnInfraTopo'); if(e) e.style.display='none';")
                        time.sleep(0.1)
                        link.click()
                    except Exception:
                                # se tudo falhar, apenas logue e pule
                                print('Falha ao clicar no link via todos os métodos')
                                save(results, nome)
                                continue
                    
                    WebDriverWait(driver, 8).until(EC.number_of_windows_to_be(2))
                    new_window = [
                        window
                        for window in driver.window_handles
                        if window != original_window
                    ][0]
                    driver.switch_to.window(new_window)
                    if "procedimento_trabalhar" in driver.current_url:
                        driver.close()
                        driver.switch_to.window(original_window)
                        continue
                    time.sleep(0.3)
                    try:
                        print("Texto:")
                        texto_completo = driver.find_element(
                            By.XPATH, "//table[@border='0']"
                        ).text
                        print("Data do Boletim:")
                        try:
                            boletimData = (
                                match.group(0)
                                if (
                                    match := re.search(
                                        r"\d{2}/\d{2}/\d{4}",
                                        driver.find_element(
                                            By.XPATH,
                                            "//div[contains(text(), 'Boletim de Serviço Eletrônico')]",
                                        ).text,
                                    )
                                )
                                else "Data não encontrada"
                            )
                            print(boletimData)
                        except:
                            boletimData = "N/A"
                            print(boletimData)
                        print("Num portaria:")
                        try:
                            Portaria = "Nº" + re.search(
                                r"Portaria de Pessoal (.+?), de", driver.page_source
                            ).group(1).replace("</strong><strong>", "")
                            Portaria = re.sub(r"<.*?>|\[.*?\]", "", Portaria)
                            Portaria = "".join(filter(str.isdigit, Portaria))
                        except:
                            Portaria = "N/A"
                        print(Portaria)
                        print("Data da portaria:")
                        try:
                            data = re.search(
                                r", de (.+?)</strong>", driver.page_source
                            ).group(1)
                        except:
                            data = "N/A"
                        dou = ""
                        try:
                            pattern = r"DOU de (\d{2}/\d{2}/\d{4}), se"
                            match = re.search(pattern, driver.page_source)
                            if match:
                                dou = match.group(1)
                            else:
                                dou = "N/A"
                        except:
                            dou = "N/A"

                        element = driver.find_element(
                            By.XPATH, "//td[contains(., 'Referência: Processo nº')]"
                        )

                        text = element.text

                        pattern = r"Processo nº ([0-9./-]+)"
                        match = re.search(pattern, text)

                        if match:
                            numero = match.group(1)

                        retificada = "Nao"
                        if (
                            "ntRodape_item" in driver.page_source
                            and "retificada" in driver.page_source
                        ):
                            retificada = "Sim"
                        print(data)
                        print("Num documento:")
                        print(document)
                        
                        body_text = driver.find_element(By.TAG_NAME, "body").text
                        match = re.search(
                            r"R\s*E\s*S\s*O\s*L\s*V\s*E(.*?)(PUBLIQUE-?SE\s*E\s*REGISTRE-?SE|PUBLIQUE-?SE|PUBLIQUE)",
                            body_text,
                            flags=re.IGNORECASE | re.DOTALL,
                            )
                        if match:
                            paragrafo = limpar_texto(match.group(1))
                        else:
                            print("Aviso: padrão 'R E S O L V E ... PUBLIQUE-SE' não encontrado, salvando conteúdo bruto")
                            paragrafo = "N/A" 
                        
                        print(driver.current_url)

                        conteudo = paragrafo

                        '''testar aqui'''
                        Servidor = extrair_servidores(conteudo)
                        print("Servidor(es):", Servidor)
                        
                    except Exception as e:
                        print("Erro ao processar documento:", e)
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        # salvar snapshot para investigação
                        try:
                            driver.save_screenshot(f"error_{ts}.png")
                            with open(f"page_{ts}.html", "w", encoding="utf-8") as f:
                                f.write(driver.page_source)
                        except Exception as ex:
                            print("Falha ao salvar snapshot:", ex)

                        # Fechar apenas se estivermos numa janela diferente da original
                        try:
                            if driver.current_window_handle != original_window:
                                driver.close()
                                driver.switch_to.window(original_window)
                            else:
                                # se estivermos na mesma aba, tente voltar para a lista
                                try:
                                    driver.back()
                                    WebDriverWait(driver, 5).until(
                                        EC.presence_of_element_located((By.CLASS_NAME, "pesquisaTituloDireita"))
                                    )
                                except Exception:
                                    pass
                        except Exception as ex:
                            print("Aviso cleanup janela:", ex)
                        save(results, nome)
                        continue

                    
                    results.append(
                        {
                            "Tipo_Processo": detalhes,
                            "No_Processo": numero,
                            "No_Documento": document,
                            "Data_BSE": boletimData,
                            "No_Portaria": Portaria,
                            "Servidor": Servidor,
                            "Descricao_Portaria": conteudo,
                            "Data_DOU": dou,
                            "Republicacao": retificada,
                            "Lotacao": unidade,
                        }
                    )
                    driver.close()
                    time.sleep(0.15)
                    driver.switch_to.window(original_window)
                    time.sleep(0.15)
                    j = 0
                except Exception as e:
                    save(results, nome)
                    j += 1
                    print("Error processing link:", e)
                z += 1 
        except Exception as e:

            save(results, nome)
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            error_message = str(e) + "\n" + traceback.format_exc()
            file_name = f"erro_{current_time}.txt"
            with open(file_name, "w") as file:
                file.write(error_message)
            print(f"Error saved to {file_name}")
            exit(1)

        try:
            next_buttons = driver.find_elements(
                By.XPATH, "//a[contains(@href, 'javascript:navegar')]"
            )
            if not next_buttons:
                break
            
            last_next_button = next_buttons[-1]
            if last_next_button.text != "Próxima":
                break
            last_next_button.click()
            #time.sleep(0.05)
            WebDriverWait(driver, 5).until(EC.staleness_of(last_next_button))
        except Exception as e:
            save(results, nome)
            print("?", e)
    save(results, nome)


def is_valid_date(date_text):
    pattern = r"^\d{2}/\d{2}/\d{4}$"
    if not re.match(pattern, date_text):
        return False

    try:
        datetime.strptime(date_text, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def executar(
    entry_start_date, entry_final_date, entry_password, entry_user, option_var
):
    start_date = entry_start_date.get()
    final_date = entry_final_date.get()
    senha = entry_password.get()
    usuario = entry_user.get()
    numer = option_var.get()

    if not is_valid_date(start_date):
        messagebox.showwarning(
            "Data Inválida",
            "A Data Inicial deve estar no formato DD/MM/YYYY e ser uma data válida.",
        )
        return
    if not is_valid_date(final_date):
        messagebox.showwarning(
            "Data Inválida",
            "A Data Final deve estar no formato DD/MM/YYYY e ser uma data válida.",
        )
        return

    if numer == "GABIR":
        threading.Thread(
            target=exec,
            args=(10, "GABIR", start_date, final_date, usuario, senha, numer),
            daemon=True,
        ).start()
    if numer.upper().startswith("GADIR"):
        threading.Thread(
            target=exec,
            args=(290, "GADIR", start_date, final_date, usuario, senha, numer),
            daemon=True,
        ).start()


def fechar(root):
    root.destroy()
    sys.exit()


def show_tooltip_popup(text, parent):
    """Show a popup box with tooltip text."""
    popup = Toplevel(parent)
    popup.wm_title("Ajuda")
    popup.geometry("+%d+%d" % (parent.winfo_rootx() + 200, parent.winfo_rooty() + 100))
    popup.resizable(False, False)

    label = tk.Label(
        popup,
        text=text,
        font=("Arial", 12),
        wraplength=300,
        justify="left",
        padx=10,
        pady=10,
    )
    label.pack()

    close_btn = tk.Button(
        popup, text="Fechar", command=popup.destroy, font=("Arial", 10)
    )
    close_btn.pack(pady=(0, 10))


def add_tooltip_button(root, widget, text):
    """Create a clickable tooltip button next to the widget."""
    button = tk.Button(
        root,
        text="?",
        font=("Arial", 10, "bold"),
        background="yellow",
        relief="solid",
        borderwidth=1,
        command=lambda: show_tooltip_popup(text, root),
    )
    button.place(
        x=widget.winfo_x()
        + widget.winfo_width()
        + 5,  # Position to the right of the widget
        y=widget.winfo_y(),
        height=widget.winfo_height(),
    )


def interface():
    root = tk.Tk()
    root.title("Coleta de Informações SEI-UTFPR")
    root.geometry("700x500")  # Adjust window size

    try:
        root.iconbitmap("images\\sei.ico")
    except Exception as e:
        print(f"Error setting icon: {e}")

    # Header with logos
    header_frame = tk.Frame(root)
    header_frame.grid(row=0, column=0, columnspan=2, padx=14, pady=14, sticky="ew")
    header_frame.columnconfigure(0, weight=1)
    header_frame.columnconfigure(1, weight=1)

    # Load and display images
    try:
        eproc_img = Image.open("images\\eproc.png").resize(
            (168, 90), Image.Resampling.LANCZOS
        )
        eproc_logo = ImageTk.PhotoImage(eproc_img)
        tk.Label(header_frame, image=eproc_logo).grid(row=0, column=1, sticky="e")

        utfpr_img = Image.open("images\\utfpr.png").resize(
            (185, 79), Image.Resampling.LANCZOS
        )
        utfpr_logo = ImageTk.PhotoImage(utfpr_img)
        tk.Label(header_frame, image=utfpr_logo).grid(row=0, column=0, sticky="w")

    except Exception as e:
        print(f"Error loading images: {e}")

    # Title
    tk.Label(
        root,
        text="Coleta de informações de Portarias SEI-UTFPR",
        font=("Arial", 20, "bold"),
    ).grid(row=1, column=0, columnspan=2, pady=(0, 14), sticky="n")

    # Input fields with tooltips
    tk.Label(root, text="Usuário:", font=("Arial", 14)).grid(
        row=2, column=0, sticky="w", padx=10, pady=10
    )
    entry_user = tk.Entry(root, font=("Arial", 14))
    entry_user.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
    root.after(
        50, add_tooltip_button, root, entry_user, "Insira o seu nome de usuário."
    )

    tk.Label(root, text="Senha:", font=("Arial", 14)).grid(
        row=3, column=0, sticky="w", padx=10, pady=10
    )
    entry_password = tk.Entry(root, show="*", font=("Arial", 14))
    entry_password.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
    root.after(50, add_tooltip_button, root, entry_password, "Insira a sua senha.")

    tk.Label(root, text="Data Inicial (DD/MM/YYYY):", font=("Arial", 14)).grid(
        row=4, column=0, sticky="w", padx=10, pady=10
    )
    entry_start_date = tk.Entry(root, font=("Arial", 14))
    entry_start_date.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
    root.after(
        50,
        add_tooltip_button,
        root,
        entry_start_date,
        "Insira a data inicial no formato DD/MM/YYYY.",
    )

    tk.Label(root, text="Data Final (DD/MM/YYYY):", font=("Arial", 14)).grid(
        row=5, column=0, sticky="w", padx=10, pady=10
    )
    entry_final_date = tk.Entry(root, font=("Arial", 14))
    entry_final_date.grid(row=5, column=1, padx=10, pady=10, sticky="ew")
    root.after(
        50,
        add_tooltip_button,
        root,
        entry_final_date,
        "Insira a data final no formato DD/MM/YYYY.",
    )

    tk.Label(
        root, text="Selecione a Unidade Emissora da Portaria:", font=("Arial", 14)
    ).grid(row=7, column=0, sticky="w", padx=10, pady=10)
    option_var = tk.StringVar(value="GABIR")
    units = [
        "GABIR",
        "GADIR-AP",
        "GADIR-CM",
        "GADIR-CP",
        "GADIR-CT",
        "GADIR-DV",
        "GADIR-FB",
        "GADIR-GP",
        "GADIR-LD",
        "GADIR-MD",
        "GADIR-PB",
        "GADIR-PG",
        "GADIR-RT",
        "GADIR-SH",
        "GADIR-TD",
    ]
    option_menu = ttk.Combobox(
        root,
        textvariable=option_var,
        values=units,
        font=("Arial", 14),
        state="readonly",
    )
    option_menu.grid(row=7, column=1, padx=10, pady=10, sticky="ew")
    root.after(
        50,
        add_tooltip_button,
        root,
        option_menu,
        "Selecione a unidade emissora da portaria.",
    )

    # Buttons
    button_frame = tk.Frame(root)
    button_frame.grid(row=8, column=0, columnspan=2, pady=14, sticky="ew")
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)

    button_execute = tk.Button(
        button_frame,
        text="Executar",
        command=lambda: executar(
            entry_start_date, entry_final_date, entry_password, entry_user, option_var
        ),
        font=("Arial", 14),
    )
    button_execute.grid(row=0, column=0, padx=10, pady=14, sticky="e")

    button_close = tk.Button(
        button_frame, text="Fechar", command=lambda: fechar(root), font=("Arial", 14)
    )
    button_close.grid(row=0, column=1, padx=10, pady=14, sticky="w")

    root.mainloop()


interface()


