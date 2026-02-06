# 📋 RPA Portaria UTFPR - SEI

Automação para coleta e agregação de dados de portarias pessoais extraídas do Sistema Eletrônico de Informações (SEI) da UTFPR.

## 📦 Componentes

### 1. **PortariaPessoal.py** - Sistema Principal
Script principal que realiza a coleta de informações de portarias:

**Funcionalidades:**
- ✅ Autenticação automática no SEI-UTFPR
- ✅ Busca paramétrica de portarias por período (data inicial e final)
- ✅ Filtragem por unidade emissora (GABIR, GADIR, etc.)
- ✅ Extração de dados estruturados de cada portaria:
  - Tipo de processo
  - Número do processo
  - Número do documento (SEI)
  - Data do Boletim de Serviço Eletrônico (BSE)
  - Número da portaria
  - Servidores afetados (por matrícula)
  - Descrição/resumo da portaria
  - Data de publicação no DOU
  - Indicação de republicação/retificação
  - Lotação/unidade responsável
  - Indicação se a portaria revoga outra

### 2. **split.py** - Pós-processamento de Dados
Utilitário para normalizar dados extraídos:

**Funcionalidades:**
- Explode (desagrega) múltiplos servidores em linhas separadas para os casos onde este formato é mais apropriado.

## 🚀 Como Usar

**Pré-requisitos:**
- Python 3.8+
- selenium 
- pillow 
- webdriver-manager 
- pandas

**Dependências do Sistema:**
- Google Chrome instalado (o script baixa o chromedriver automaticamente)
- Acesso à internet
- Credenciais válidas do SEI-UTFPR

### Instalação

1. **Clonar/Descarregar o projeto:**

2. **Instalar dependências Python:**
```bash
pip install -r requirements.txt
```
### Execução

```bash
python PortariaPessoal.py
```

A interface gráfica apresentará os seguintes campos:

| Campo | Descrição | Formato |
|-------|-----------|---------|
| **Usuário** | Seu usuário do SEI | Texto |
| **Senha** | Sua senha do SEI | Senha (oculta) |
| **Data Inicial** | Início do período de busca | DD/MM/YYYY |
| **Data Final** | Fim do período de busca | DD/MM/YYYY |
| **Unidade Emissora** | Gabinete/Diretoria responsável | Seleção em dropdown |

**Unidades Disponíveis:**
- GABIR (Gabinete do Reitor)
- GADIR-AP, GADIR-CM, GADIR-CP, GADIR-CT, GADIR-DV, GADIR-FB, GADIR-GP, GADIR-LD, GADIR-MD, GADIR-PB, GADIR-PG, GADIR-RT, GADIR-SH, GADIR-TD

#### **Para fazer o split no .csv resultante**

```bash
python split.py
```

Selecione o arquivo CSV gerado na etapa anterior. O script criará um arquivo `saida.csv` com os dados desagregados.

## 📊 Formato de Saída

O arquivo CSV gerado contém as seguintes colunas:

```csv
Tipo_Processo, No_Processo, No_Documento, Data_BSE, No_Portaria, Servidor, 
Descricao_Portaria, Data_DOU, Republicacao, Lotacao, Revoga
```

### Exemplo de Registro:

| Campo | Valor |
|-------|-------|
| Tipo_Processo | Portaria de Pessoal |
| No_Processo | 12345.123456/2025-12 |
| No_Documento | 1234567 |
| Data_BSE | 28/01/2025 |
| No_Portaria | 123 |
| Servidor | 1234567, 7654321 |
| Descricao_Portaria | Designa comissão para analisar... |
| Data_DOU | 29/01/2025 |
| Republicacao | Não |
| Lotacao | GABIR |
| Revoga | Não |

Os arquivos gerados incluem:
- `Portarias_[UNIDADE]_[DATA_INICIAL]_[DATA_FINAL].csv` - Resultado principal
- `erro_[TIMESTAMP].txt` - Logs de erro (se houver)
- `error_[TIMESTAMP].png` - Screenshot do erro (se houver)
- `page_[TIMESTAMP].html` - HTML da página com erro (se houver)


## 📋 Checklist de Uso

- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Google Chrome instalado
- [ ] Credenciais SEI válidas
- [ ] Período de busca definido
- [ ] Unidade emissora selecionada

## 📧 Suporte

Para problemas ou sugestões:
- Verifique o arquivo de erro gerado (contém stack trace completo)
- Analise o screenshot e HTML salvos em caso de falha
- Revise os logs no console da aplicação

