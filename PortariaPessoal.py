from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from bs4 import BeautifulSoup
from PIL import Image, ImageTk
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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

def save(results, arquivo):
    with open(arquivo, mode="w", newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["Tipo_Processo", "No_Processo", "No_Documento", "Data_BSE", "No_Portaria", "Servidor",
                        "Descricao_Portaria", "Data_DOU", "Republicacao"],
            quotechar='"',
            quoting=csv.QUOTE_ALL  # Aqui garantimos que todos os campos sejam cercados por aspas
        )
        writer.writeheader()
        for result in results:
            writer.writerow(result)



# Specify the path to your chromedriver
def transform_url(url):
    # Parse the URL
    parsed_url = urlparse(url)

    # Extract query parameters
    query_params = parse_qs(parsed_url.query)

    # Keep only the desired parameters
    desired_params = {
        "acao": "procedimento_trabalhar",
        "id_procedimento": query_params.get("id_procedimento", [None])[0],
        "id_documento": query_params.get("id_documento", [None])[0]
    }

    # Remove any None values (in case keys are missing)
    desired_params = {k: v for k, v in desired_params.items() if v is not None}

    # Reconstruct the URL
    new_query = urlencode(desired_params, doseq=True)
    transformed_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        '',
        new_query,
        ''
    ))

    return transformed_url

def exec(numer, nome, dataInicio, dataFinal, usuario, senha):
    nome = "Portarias_" + nome + "_" + dataInicio.replace("/", "").replace("\\", "") + "_" + dataFinal.replace("/", "").replace("\\", "") + ".csv"
    numero = str(numer)
    PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromedriver.exe")
    service = Service(PATH)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-popup-blocking')
    download_dir = os.getcwd()

    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-popup-blocking")
    prefs = {
        #"plugins.always_open_pdf_externally": True,
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    try:
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://sei.utfpr.edu.br/")

        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pwdSenha"))).send_keys(senha)
        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "txtUsuario"))).send_keys(
            usuario)
        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "sbmAcessar"))).click()
       
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//img[@title='Pesquisa Rápida']"))
        ).click()
        today_date = datetime.today().strftime('%d/%m/%Y')
        start_date = dataInicio
        end_date = dataFinal
        tipo_processo = "100000556"

        select_element = Select(driver.find_element(By.ID, "selSeriePesquisa"))
        select_element.select_by_value(numero)

        select_element = Select(driver.find_element(By.ID, "selTipoProcedimentoPesquisa"))
        select_element.select_by_value(tipo_processo)#Futuramente dar opção para escolher o tipo de processo

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
        with open(file_name, 'w') as file:
            file.write(error_message)
        print(f"Error saved to {file_name}")
        exit(1)


    while True:
        try:
            j = 0;
            i = 10;

            td_elements = driver.find_elements(By.CLASS_NAME, "pesquisaTituloDireita")
            td_titulos = driver.find_elements(By.CLASS_NAME, "pesquisaTituloEsquerda")

            z = 0
            for td_element in td_elements:
                if z % 30 == 0:
                    save(results, nome)
                try:
                    link = td_element.find_element(By.TAG_NAME, "a")
                    link_url = link.get_attribute('href')
                    if len(link_url) >= 5 and '.' in link_url[-5:]:
                        continue
                    document = link.text;
                    titulo = td_titulos[z].text
                    index = titulo.find("Nº")
                    detalhes = titulo[:index].strip() if index != -1 else titulo.strip()
                    numero = "N/A"
                    #numero = titulo[index + 1:].strip() if index != -1 else ""
                    #paren_index = numero.find("(")
                    #if paren_index != -1:
                    #    numero = numero[:paren_index].strip()

                    link.click()
                    WebDriverWait(driver, 8).until(EC.number_of_windows_to_be(2))
                    new_window = [window for window in driver.window_handles if window != original_window][0]
                    driver.switch_to.window(new_window)
                    if "procedimento_trabalhar" in driver.current_url:
                        driver.close()
                        driver.switch_to.window(original_window)
                        continue
                    time.sleep(0.3)
                    try:
                        print(1)
                        texto_completo = driver.find_element(By.XPATH, "//table[@border='0']").text
                        print(2)
                        try:
                            boletimData = (match.group(0) if (match := re.search(r'\d{2}/\d{2}/\d{4}', driver.find_element(By.XPATH, "//div[contains(text(), 'Boletim de Serviço Eletrônico')]").text)) else "Data não encontrada")
                            print(boletimData)
                        except:
                            boletimData = "N/A"
                        print(3)
                        try:
                            Portaria = "Nº" + re.search(r"Portaria de Pessoal (.+?), de", driver.page_source).group(1).replace("</strong><strong>", "")
                            Portaria = re.sub(r'<.*?>|\[.*?\]', '', Portaria)
                            Portaria = ''.join(filter(str.isdigit, Portaria))
                        except:
                            Portaria = "N/A"
                        print(Portaria)
                        print(33)
                        try:
                            data = re.search(r", de (.+?)</strong>", driver.page_source).group(1)
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

                        element = driver.find_element(By.XPATH, "//td[contains(., 'Referência: Processo nº')]")

                        # Extract the text content of the element
                        text = element.text

                        # Use a regular expression to extract the process number
                        pattern = r'Processo nº ([0-9./-]+)'
                        match = re.search(pattern, text)

                        if match:
                            numero = match.group(1)

                        retificada = "Nao"
                        if "ntRodape_item" in driver.page_source and "retificada" in driver.page_source:
                            retificada = "Sim"
                        print(data)
                        print(4)
                        paragrafo = (re.search(r"R E S O L V E(.*?)PUBLIQUE-SE E REGISTRE-SE", driver.find_element(By.TAG_NAME, "body").text, re.DOTALL).group(1))
                        # print(re.search(r"R E S O L V E(.+?)PUBLIQUE-SE E REGISTRE-SE", driver.find_element(By.TAG_NAME, "body").text).group(1))
                        print(driver.current_url)
                        substituicoes = {
                            "Matrícula": "matrícula",
                            "Matricula": "matricula",
                            "SERVIDOR": "matrícula",
                            "Servidor": "matrícula",
                            "servidor": "matrícula",
                            "Servidora": "matrícula",
                            "servidora": "matrícula",
                            "Habilitada": "matrícula",
                            "Habilitado": "matrícula",
                            "habilitada": "matrícula",
                            "habilitado": "matrícula",
                            "Ocupante": "ocupante",
                            "ocupante do cargo efetivo": "matrícula",
                            "habilitado": "matrícula",
                            "ocupante": "matrícula",
                            " RA ": "matricula",
                            " matrícula": ", matrícula",
                            ",,": ",",
                            "Assistente": "matrícula",
                            "Professor": "matrícula",
                            "Professora": "matrícula",
                            "professor": "matrícula",
                            "professora": "matrícula",
                            "assistente": "matrícula",
                            "SIAPE": "matrícula",
                            "siape": "matrícula",
                            "Siape": "matrícula",
                            "Nome do Servidor": "matrícula",
                            "Campus de Lotação": "matrícula",
                            "DESIGNAÇÃO": "matrícula",
                            "DE LOTACAO": "",
                            "SEI SICITE": ""
                        }

                        substituicoesServe = {
                            "NOME": "",
                            "SIAPE": "",
                            "CAMPUS": "",
                            "DESIGNACAO": "",
                            ", ,": ",",
                            "DE LOTACAO": ""
                        }

                        paragrafoCompleto = paragrafo

                        if "Nome do Servidor" in paragrafo:
                            start = paragrafo.find("Nome do Servidor") + len("Nome do Servidor")
                            end_match = re.search(r'\n ', paragrafo[start:])

                            # If the line break followed by space exists, proceed with uppercase transformation
                            if end_match:
                                end = start + end_match.start()
                                # Convert the text in the range to uppercase
                                paragrafo = paragrafo[:start] + paragrafo[start:end].upper() + paragrafo[end:]
                                paragrafo = re.sub(r'(\d{7})', r'\n\1', paragrafo)


                        # Função para substituir as palavras
                        pattern = re.compile("|".join(map(re.escape, substituicoes.keys())))
                        paragrafo = unidecode( pattern.sub(lambda match: substituicoes[match.group(0)], paragrafo)).replace(",,",",").replace("\n", ", ")




                        paragrafo = re.sub(r"\b\d{7}\b", "matricula", paragrafo).replace(", ,", ",")
                        Servidor = ', '.join(re.findall(r'([A-Z\s]{10,})(?=,\s*matr(?:icula)?\s*|\s*\d+)',(paragrafo)))

                        pattern = re.compile("|".join(map(re.escape, substituicoesServe.keys())))
                        Servidor = unidecode(pattern.sub(lambda match: substituicoesServe[match.group(0)], Servidor)).strip()
                        if Servidor.startswith(","):
                            Servidor = Servidor[1:]
                        print(paragrafo)
                        print(9)
                        print(Servidor)
                        print(9)
                        print(5)
                        try:
                            conteudo = paragrafoCompleto
                        except:
                            conteudo = "N/A"
                        S = (", " + ', '.join(re.findall(r'“([A-Z\s]+)”', conteudo))).strip(', ')
                        if len(S) > 6:
                            Servidor += S
                        if len(Servidor) < 5:
                            Servidor = "N/A"
                        print(Servidor)
                        print(6)
                    except:
                        driver.close()
                        driver.switch_to.window(original_window)
                        continue



                    results.append({"Tipo_Processo": detalhes,"No_Processo": numero, "No_Documento": document, "Data_BSE": boletimData, "No_Portaria": Portaria, "Servidor": Servidor, "Descricao_Portaria": conteudo, "Data_DOU": dou, "Republicacao": retificada})
                    driver.close()
                    time.sleep(0.15)
                    driver.switch_to.window(original_window)
                    time.sleep(0.15)
                    j = 0
                except Exception as e:
                    save(results, nome)
                    j += 1
                    print("Error processing link:", e)
                z += 1 #incremento movido
        except Exception as e:

            save(results, nome)
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            error_message = str(e) + "\n" + traceback.format_exc()
            file_name = f"erro_{current_time}.txt"
            with open(file_name, 'w') as file:
                file.write(error_message)
            print(f"Error saved to {file_name}")
            exit(1)

        try:
            next_buttons = driver.find_elements(By.XPATH, "//a[contains(@href, 'javascript:navegar')]")
            if next_buttons:
                last_next_button = next_buttons[-1]
                if last_next_button.text != "Próxima":
                    break
                last_next_button.click()
                time.sleep(0.05)
        except Exception as e:
            save(results, nome)
            print("?", e)
    save(results, nome)






def is_valid_date(date_text):
    # Regular expression to match strictly DD/MM/YYYY format
    pattern = r"^\d{2}/\d{2}/\d{4}$"
    if not re.match(pattern, date_text):
        return False

    try:
        # Check if the date is valid
        datetime.strptime(date_text, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def long_running_task(numer, filename, start_date, final_date, usuario, senha):
    # Simulate a long-running task (replace with your Selenium task)
    import time
    time.sleep(5)  # Simulating a 5-second task
    print(f"Task {numer} completed with {filename}, {start_date}, {final_date}, {usuario}, {senha}")

def executar(entry_start_date, entry_final_date, entry_password, entry_user, option_var):
    # Retrieve inputs from the fields
    start_date = entry_start_date.get()
    final_date = entry_final_date.get()
    senha = entry_password.get()
    usuario = entry_user.get()
    numer = option_var.get()

    # Validate the dates
    if not is_valid_date(start_date):
        messagebox.showwarning("Data Inválida",
                               "A Data Inicial deve estar no formato DD/MM/YYYY e ser uma data válida.")
        return
    if not is_valid_date(final_date):
        messagebox.showwarning("Data Inválida",
                               "A Data Final deve estar no formato DD/MM/YYYY e ser uma data válida.")
        return

    # Validate the filename
    #if not filename.endswith(".csv"):
    #    messagebox.showwarning("Arquivo Inválido", "O nome do arquivo deve terminar com '.csv'.")
   #     return

    # Start the task in a separate thread
    if numer == "GABIR":
        threading.Thread(target=exec, args=(10, "GABIR", start_date, final_date, usuario, senha), daemon=True).start()
    if numer == "GADIR":
        threading.Thread(target=exec, args=(290, "GADIR", start_date, final_date, usuario, senha), daemon=True).start()

def fechar(root):
    # Close the application
    root.destroy()
    sys.exit()




def show_tooltip_popup(text, parent):
    """Show a popup box with tooltip text."""
    popup = Toplevel(parent)
    popup.wm_title("Ajuda")
    popup.geometry("+%d+%d" % (parent.winfo_rootx() + 200, parent.winfo_rooty() + 100))
    popup.resizable(False, False)

    label = tk.Label(popup, text=text, font=("Arial", 12), wraplength=300, justify="left", padx=10, pady=10)
    label.pack()

    close_btn = tk.Button(popup, text="Fechar", command=popup.destroy, font=("Arial", 10))
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
        command=lambda: show_tooltip_popup(text, root)
    )
    button.place(
        x=widget.winfo_x() + widget.winfo_width() + 5,  # Position to the right of the widget
        y=widget.winfo_y(),
        height=widget.winfo_height()
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
        eproc_img = Image.open("images\\eproc.png").resize((168, 90), Image.Resampling.LANCZOS)
        eproc_logo = ImageTk.PhotoImage(eproc_img)
        tk.Label(header_frame, image=eproc_logo).grid(row=0, column=1, sticky="e")

        utfpr_img = Image.open("images\\utfpr.png").resize((185, 79), Image.Resampling.LANCZOS)
        utfpr_logo = ImageTk.PhotoImage(utfpr_img)
        tk.Label(header_frame, image=utfpr_logo).grid(row=0, column=0, sticky="w")

    except Exception as e:
        print(f"Error loading images: {e}")

    # Title
    tk.Label(root, text="Coleta de informações de Portarias SEI-UTFPR", font=("Arial", 20, "bold")).grid(
        row=1, column=0, columnspan=2, pady=(0, 14), sticky="n"
    )

    # Input fields with tooltips
    tk.Label(root, text="Usuário:", font=("Arial", 14)).grid(row=2, column=0, sticky="w", padx=10, pady=10)
    entry_user = tk.Entry(root, font=("Arial", 14))
    entry_user.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
    root.after(50, add_tooltip_button, root, entry_user, "Insira o seu nome de usuário.")

    tk.Label(root, text="Senha:", font=("Arial", 14)).grid(row=3, column=0, sticky="w", padx=10, pady=10)
    entry_password = tk.Entry(root, show="*", font=("Arial", 14))
    entry_password.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
    root.after(50, add_tooltip_button, root, entry_password, "Insira a sua senha.")

    tk.Label(root, text="Data Inicial (DD/MM/YYYY):", font=("Arial", 14)).grid(row=4, column=0, sticky="w", padx=10, pady=10)
    entry_start_date = tk.Entry(root, font=("Arial", 14))
    entry_start_date.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
    root.after(50, add_tooltip_button, root, entry_start_date, "Insira a data inicial no formato DD/MM/YYYY.")

    tk.Label(root, text="Data Final (DD/MM/YYYY):", font=("Arial", 14)).grid(row=5, column=0, sticky="w", padx=10, pady=10)
    entry_final_date = tk.Entry(root, font=("Arial", 14))
    entry_final_date.grid(row=5, column=1, padx=10, pady=10, sticky="ew")
    root.after(50, add_tooltip_button, root, entry_final_date, "Insira a data final no formato DD/MM/YYYY.")

    tk.Label(root, text="Selecione a Unidade Emissora da Portaria:", font=("Arial", 14)).grid(row=7, column=0, sticky="w", padx=10, pady=10)
    option_var = tk.StringVar(value="GABIR")
    units = ["GABIR","GADIR-AP","GADIR-CM","GADIR-CP","GADIR-CT","GADIR-DV","GADIR-FB","GADIR-GP","GADIR-LD","GADIR-MD","GADIR-PB","GADIR-PG","GADIR-RT","GADIR-SH","GADIR-TD"]
    option_menu = ttk.Combobox(root, textvariable=option_var, values=units, font=("Arial", 14), state="readonly")
    option_menu.grid(row=7, column=1, padx=10, pady=10, sticky="ew")
    root.after(50, add_tooltip_button, root, option_menu, "Selecione a unidade emissora da portaria.")

    # Buttons
    button_frame = tk.Frame(root)
    button_frame.grid(row=8, column=0, columnspan=2, pady=14, sticky="ew")
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)

    button_execute = tk.Button(
        button_frame, text="Executar",
        command=lambda: executar(entry_start_date, entry_final_date, entry_password, entry_user, option_var),
        font=("Arial", 14)
    )
    button_execute.grid(row=0, column=0, padx=10, pady=14, sticky="e")

    button_close = tk.Button(button_frame, text="Fechar", command=lambda: fechar(root), font=("Arial", 14))
    button_close.grid(row=0, column=1, padx=10, pady=14, sticky="w")

    root.mainloop()


interface()






'''
thread1 = threading.Thread(target=exec, args=("10", "GABIR.csv")) #GABIR
thread2 = threading.Thread(target=exec, args=("290", "GADIR.csv"))
thread3 = threading.Thread(target=exec, args=("1119", "GABIRnormativa.csv"))
thread4 = threading.Thread(target=exec, args=("1136", "GADIRnormativa.csv"))
thread1.start()
time.sleep(4)
thread2.start()
time.sleep(4)
thread3.start()
time.sleep(4)
thread4.start()


thread1.join()
thread2.join()
thread3.join()
thread4.join()'''