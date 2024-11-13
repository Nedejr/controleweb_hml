from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import numpy as np
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime


version_streamlit = False
load_dotenv()


tabelas = [
    {
    'nome' : 'Totais Gerais',
    'colunas': ['Tipo', 'PL', 'Custo', 'Luc/Prej', 'Luc/Prej %', 'Nan', 'PL %'],
    'range': 'TOTAIS!A2:G6'
    },
    {
    'nome' : 'Totais Contas',
    'colunas': ['Ativo', 'Data', 'Qtd', 'ValorUnit', 'ValorTotal', 'Tipo', 'Mes'],
    'range': 'TOTAIS!A10:B13'
    },
    {
    'nome' : 'Totais Renda Variável',
    'colunas': ['Ativo', 'Qtd', 'Cotação', 'Valor Posição', 'Luc/Prej', 'Nan', 'Rent', 'Tipo','PM', 'Res.Dia', 'Res.dia%'],
    'range': 'TOTAIS!A17:K29'
    },
    {
    'nome' : 'Totais Tesouro',
    'colunas': ['Titulo', 'Valor Aplicado', 'Qtd', 'Luc/Prej', 'Posição Atual', 'Nan', 'Rent%'],
    'range': 'TOTAIS!A33:G38'
    },
    {
    'nome' : 'Dividendos',
    'colunas': ['Ativo', 'Data', 'Qtd', 'ValorUnit', 'ValorTotal', 'Tipo', 'Mes'],
    'range': 'Dividendos!A3:G1000'
    },

    {
    'nome' : 'Operações',
    'colunas': ['Ativo', 'Tipo', 'Ordem', 'Corretora', 'Data', 'Qtd', 'Preço', 'Total', 'Origem', 'Total2', 'Mes/Ano','Cotação','Cotação.Ant'],
    'range': 'Operações!A5:M2000'
    },
    {
    'nome' : 'Conta Banco do Brasil',
    'colunas': ['Data', 'Descricao', 'Valor', 'Tipo'],
    'range': 'Banco do Brasil!A2:D10000'
    },
    {
    'nome' : 'Conta Bradesco',
    'colunas': ['Data', 'Descricao', 'Valor', 'Tipo'],
    'range': 'Bradesco!A2:D10000'
    },

    {
    'nome' : 'Conta Itau',
    'colunas': ['Data', 'Descricao', 'Valor', 'Tipo'],
    'range': 'Itau!A2:D10000'
    },
    
    {
    'nome' : 'Cartão',
    'colunas': ['Descricao', 'DtFat', 'Nr', 'NrTot', 'VlParcela', 'DtPg', 'VlPagamento','Mes', 'Bandeira'],
    'range': 'CartaoVencimentos!A3:I10000'
    },
    {
    'nome' : 'Totais Despesas',
    'colunas': ['Despesas', 'Mes', 'Valor', 'Pago'],
    'range': 'TOTAIS!M2:P11'
    },
]

def autenticacao():

    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    

    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    if os.getenv('STREAMLIT')=='PROD':
        info_st =   {
                    'refresh_token': os.getenv('REFRESH_TOKEN'),
                    'client_id': os.getenv('CLIENTE_ID'),
                    'client_secret': os.getenv('CLIENT_SECRET')
                    }
        creds = Credentials.from_authorized_user_info(info=info_st, scopes=SCOPES)
    else:
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    
    # If there are no (valid) credentials available, let the user log in.   
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    try:
        service = build("sheets", "v4", credentials=creds)
        
    except TypeError as err:
        print(err)
    return service
    
def carrega_dados(service, nome_tabela):    

    tabela = busca_tabela(nome_tabela)
    
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (sheet.values().get(spreadsheetId=os.getenv('SAMPLE_SPREADSHEET_ID_HML'), range=tabela['range']).execute())
    dados = result.get("values", [])
    df = pd.DataFrame(dados, columns=tabela['colunas']) 

    if tabela['nome'] == 'Totais Gerais':
        df['PL'] = df['PL'].str.replace('.','')
        df['PL'] = df['PL'].str.replace(',','.')
        df['PL'] = df['PL'].astype(float)
        df['Custo'] = df['Custo'].str.replace('.','')
        df['Custo'] = df['Custo'].str.replace(',','.')
        df['Custo'] = df['Custo'].astype(float)
        df['Luc/Prej'] = df['Luc/Prej'].str.replace('.','')
        df['Luc/Prej'] = df['Luc/Prej'].str.replace(',','.')
        df['Luc/Prej'] = df['Luc/Prej'].astype(float)
        df['Luc/Prej %'] = round((df['PL']/df['Custo']-1) * 100, 2)
        df['PL %'] = round(df['PL']/df['PL'].sum()*100,2)
        df.drop(labels='Nan', axis=1, inplace=True)
    
    if tabela['nome'] == 'Totais Contas':
        df['Saldo'] = df['Saldo'].str.replace('.','')
        df['Saldo'] = df['Saldo'].str.replace(',','.')
        df['Saldo'] = df['Saldo'].astype(float)
    
    if tabela['nome'] == 'Totais Renda Variável':
        
        df['Qtd'] = df['Qtd'].astype(int)
        df['Cotação'] = df['Cotação'].str.replace('.','')
        df['Cotação'] = df['Cotação'].str.replace(',','.')
        df['Cotação'] = df['Cotação'].astype(float)
        df['Valor Posição'] = df['Valor Posição'].str.replace('.','')
        df['Valor Posição'] = df['Valor Posição'].str.replace(',','.')
        df['Valor Posição'] = df['Valor Posição'].astype(float)
        df['Luc/Prej'] = df['Luc/Prej'].str.replace('.','')
        df['Luc/Prej'] = df['Luc/Prej'].str.replace(',','.')
        df['Luc/Prej'] = df['Luc/Prej'].astype(float)
        df['PM'] = df['PM'].str.replace('.','')
        df['PM'] = df['PM'].str.replace(',','.')
        df['PM'] = df['PM'].astype(float)
        df['Rent'] = (df['Cotação']/df['PM']-1) * 100
        df['Res.Dia'] = df['Res.Dia'].str.replace('.','')
        df['Res.Dia'] = df['Res.Dia'].str.replace(',','.')
        df['Res.Dia'] = df['Res.Dia'].astype(float)
        df['Res.dia%'] = df['Res.dia%'].str.replace(',','.')
        df['Res.dia%'] = df['Res.dia%'].str.replace('%','')
        df['Res.dia%'] = df['Res.dia%'].astype(float)
        df.drop(labels='Nan', axis=1, inplace=True)
        
    if tabela['nome'] == 'Totais Tesouro':
        df['Valor Aplicado'] = df['Valor Aplicado'].str.replace('.','')
        df['Valor Aplicado'] = df['Valor Aplicado'].str.replace(',','.')
        df['Valor Aplicado'] = df['Valor Aplicado'].astype(float)
        df['Qtd'] = df['Qtd'].str.replace('.','')
        df['Qtd'] = df['Qtd'].str.replace(',','.')
        df['Qtd'] = df['Qtd'].astype(float)
        df['Luc/Prej'] = df['Luc/Prej'].str.replace('.','')
        df['Luc/Prej'] = df['Luc/Prej'].str.replace(',','.')
        df['Luc/Prej'] = df['Luc/Prej'].astype(float)
        df['Posição Atual'] = df['Posição Atual'].str.replace('.','')
        df['Posição Atual'] = df['Posição Atual'].str.replace(',','.')
        df['Posição Atual'] = df['Posição Atual'].astype(float)
        df['Rent%'] = round((df['Posição Atual']/df['Valor Aplicado']-1) * 100, 2)
        df.drop(labels='Nan', axis=1, inplace=True)
        df['Tipo'] = np.where(df['Titulo'].str.contains('Selic'), 'Selic', 'IPCA +')
     
    if tabela['nome'] == 'Totais Despesas':
        df['Valor'] = df['Valor'].str.replace('.','')
        df['Valor'] = df['Valor'].str.replace(',','.')
        df['Valor'] = df['Valor'].astype(float)
   
    if tabela['nome'] == 'Dividendos':

        df['ValorUnit'] = df['ValorUnit'].str.replace('.','')
        df['ValorUnit'] = df['ValorUnit'].str.replace(',','.')
        df['ValorUnit'] = df['ValorUnit'].astype(float)
        df['Qtd'] = pd.to_numeric(df['Qtd'])
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
        df['ValorTotal'] = df['ValorUnit'] * df['Qtd']
        df['Mes'] = df['Data'].apply(lambda x: str(x.year) + '/' + f'{x.month:02}')

    if tabela['nome'] == 'Operações':
        
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
        df['Qtd'] = df['Qtd'].str.replace('.','')
        df['Qtd'] = df['Qtd'].str.replace(',','.')
        df['Qtd'] = df['Qtd'].astype(float)
        df['Preço'] = df['Preço'].str.replace('.','')
        df['Preço'] = df['Preço'].str.replace(',','.')
        df['Preço'] = df['Preço'].astype(float)
        df['Total'] = df['Total'].str.replace('.','')
        df['Total'] = df['Total'].str.replace(',','.')
        df['Total'] = df['Total'].astype(float)
        df['Cotação'] = df['Cotação'].replace('#N/A',0)
        df['Cotação'] = df['Cotação'].str.replace('.','')
        df['Cotação'] = df['Cotação'].str.replace(',','.')
        df['Cotação'] = df['Cotação'].astype(float)
        df['Cotação.Ant'] = df['Cotação.Ant'].replace('#N/A',0)
        df['Cotação.Ant'] = df['Cotação.Ant'].str.replace('.','')
        df['Cotação.Ant'] = df['Cotação.Ant'].str.replace(',','.')
        df['Cotação.Ant'] = df['Cotação.Ant'].astype(float)
        df['Res.Dia'] = (df['Cotação']-df['Cotação.Ant']) * df['Qtd']
        df['Res.Dia%'] = (df['Cotação']/df['Cotação.Ant']-1) * 100 
        df['Mes'] = df['Data'].apply(lambda x: str(x.year) + '/' + f'{x.month:02}')

        df.drop(labels='Corretora', axis=1, inplace=True)
        df.drop(labels='Origem', axis=1, inplace=True)
        df.drop(labels='Total2', axis=1, inplace=True)
    
    if tabela['nome'] == 'Conta Banco do Brasil':
        
        df['Data'] = pd.to_datetime(df['Data'],  format='mixed', errors='coerce')
        df['Valor'] = df['Valor'].str.replace('.','')
        df['Valor'] = df['Valor'].str.replace(',','.')
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
        df['ValorTotal'] = df.apply(lambda x: x['Valor'] if x['Tipo'] == 'CREDITO' else x['Valor'] * -1 , axis =1)
        df['Mes'] = df['Data'].apply(lambda x: str(x.year) + '/' + f'{x.month:02}')
        
    if tabela['nome'] == 'Conta Bradesco':

        
        df['Data'] = pd.to_datetime(df['Data'],  format='mixed' , errors='coerce')
        #df['Data'] = pd.to_datetime(df['Data'])
        df['Valor'] = df['Valor'].str.replace('.','')
        df['Valor'] = df['Valor'].str.replace(',','.')
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
        df['ValorTotal'] = df.apply(lambda x: x['Valor'] if x['Tipo'] == 'CREDITO' else x['Valor'] * -1 , axis =1)
        df['Mes'] = df['Data'].apply(lambda x: str(x.year) + '/' + f'{x.month:02}')

    if tabela['nome'] == 'Conta Itau':
         
        #df['Data'] = pd.to_datetime(df['Data'],  format='mixed')
        df['Data'] = pd.to_datetime(df['Data'] , errors='coerce')
        df['Valor'] = df['Valor'].str.replace('.','')
        df['Valor'] = df['Valor'].str.replace(',','.')
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
        df['ValorTotal'] = df.apply(lambda x: x['Valor'] if x['Tipo'] == 'CREDITO' else x['Valor'] * -1 , axis =1)
        df['Mes'] = df['Data'].apply(lambda x: str(x.year) + '/' + f'{x.month:02}')
        print(df)
    
    if tabela['nome'] == 'Cartão':
        
        #['Descricao', 'DtFat', 'Nr', 'NrTot', 'VlParcela', 'DtPg', 'VlPagamento','Mes', 'Bandeira'], 
        df['DtFat'] = pd.to_datetime(df['DtFat'], dayfirst=True)
        df['Nr'] = df['Nr'].astype(int)
        df['NrTot'] = df['NrTot'].astype(int)
        df['DtPg'] = pd.to_datetime(df['DtPg'], format='mixed')
        df['VlParcela'] = df['VlParcela'].str.replace('.','')
        df['VlParcela'] = df['VlParcela'].str.replace(',','.')
        df['VlParcela'] = df['VlParcela'].astype(float)
        df['VlPagamento'] = df['VlPagamento'].str.replace('.','')
        df['VlPagamento'] = df['VlPagamento'].str.replace(',','.')
        df['VlPagamento'] = df['VlPagamento'].astype(float)
        #df.drop(labels='Id', axis=1, inplace=True)
        df['Mes'] = df['DtFat'].apply(lambda x: str(x.year) + '/' + f'{x.month:02}')
        df['total_em_aberto'] = np.where(df['DtPg'].isnull(),df['VlParcela'],0)
    
    return df

def busca_tabela(nome_tabela):
  for tabela in tabelas:
    if tabela['nome'] == nome_tabela:
      return tabela
  return {} 
