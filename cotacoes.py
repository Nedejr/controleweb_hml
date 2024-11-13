import requests
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
import time
import requests
import json
from pymongo import MongoClient
from dotenv import load_dotenv
import os

url_dolar = 'https://economia.awesomeapi.com.br/json/last/USD-BRL'

url_ibov = 'https://www.google.com/search?q=google+ibov'
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}

def dolar_dia():
    #Capturando a cotação
    dados = requests.get(url_dolar).content
    #Extraindo a cotação
    dic = json.loads(dados)
    cotacao = round(float(dic['USDBRL']['bid']),2)
    return cotacao

def ibov_dia():
    requisicao = requests.get(url_ibov, headers=headers)
    site = BeautifulSoup(requisicao.text, "html.parser")
    pontos_ibov = site.find("span", class_='IsqQVc NprOob wT3VGc')
    pontos_ibov = float(pontos_ibov.get_text().replace('.','').replace(',','.'))
    return (pontos_ibov)

def pct_ibov():
    url_ibov = 'https://www.infomoney.com.br/cotacoes/b3/indice/ibovespa/'
    requisicao = requests.get(url_ibov, headers=headers)
    site = BeautifulSoup(requisicao.text, "html.parser")
    pct_ibov = site.find("div",  class_="percentage")
    try:
        pct_ibov = float(pct_ibov.find("p").get_text().replace('\n','').replace(' ','').replace('%',''))
    except:
        pct_ibov =0
    
    return pct_ibov

def cotacao_diaria(ticket):
    url_ticket = 'https://www.google.com/search?q=google+' + ticket
    requisicao = requests.get(url_ticket, headers=headers)
    site = BeautifulSoup(requisicao.text, "html.parser")
    cotacao = site.find("span", class_='IsqQVc NprOob wT3VGc')
    cotacao = round(float(cotacao.get_text().replace(',','.')),2)
    return cotacao

def cotacao_dia_ant(ticket):
    
    url_ticket = 'https://www.google.com/finance/quote/'+  ticket +':BVMF?sa=X' 
    requisicao = requests.get(url_ticket, headers=headers)
    site = BeautifulSoup(requisicao.text, "html.parser")
    cotacao = site.find("div", class_='P6K39c')
    cotacao = round(float(cotacao.get_text().replace('R$','').replace(',','.')),2)
    return cotacao

def cotacao_finance(ticket):

    ticket = yf.Ticker(ticket + ".SA")
    df_hist = ticket.history(period='max')['Close'].reset_index()
    df_hist['Date'] =  pd.to_datetime(df_hist['Date'].dt.date)
    df_hist['Mes'] = df_hist['Date'].apply(lambda x: str(x.year) + '/' + f'{x.month:02}')
    df_primeiro_dia_mes = df_hist.groupby('Mes')['Date'].max().reset_index()
    df_ultima_dia_mes = df_hist.groupby('Mes')['Date'].max().reset_index()
    df = pd.merge(df_ultima_dia_mes, df_hist, on=['Date'])
    
        
    df.rename(columns={'Mes_x': 'Mes', 'Close':'Fechamento'}, inplace=True)
    df.drop(columns=['Mes_y', 'Date'], inplace=True)
    df['Rent'] = round(df['Fechamento'].pct_change() * 100,2)

    df = df.loc[df['Mes'].isin(['2019/12','2020/01','2020/02'])]
    return df

     # get all stock info
    #print(msft.info)
    #print(itsa4.dividends)
    # get historical market data
    #['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']

def cotacao_finance_lista():
    
    

    lista_acoes = ['ITSA4.SA', 'CSAN3.SA', 'SOJA3.SA','TAEE11.SA','GOAU4.SA','WIZC3.SA','VALE3.SA']
    
    # access each ticker using (example)
    df_hist = yf.download(lista_acoes, start='2020-01-01')['Close'].reset_index()
    df_hist['Date'] =  pd.to_datetime(df_hist['Date'].dt.date)
    df_hist['Mes'] = df_hist['Date'].apply(lambda x: str(x.year) + '/' + f'{x.month:02}')
    df_ultima_dia_mes = df_hist.groupby('Mes')['Date'].max().reset_index()
    df = pd.merge(df_ultima_dia_mes, df_hist, on=['Date'])
    df.rename(columns={'Mes_x': 'Mes'}, inplace=True)
    df.drop(columns=['Mes_y','Date'], inplace=True)
    df = df.rename(columns={'CSAN3.SA': 'CSAN3', 
                            'GOAU4.SA': 'GOAU4',
                            'ITSA4.SA': 'ITSA4',
                            'SOJA3.SA': 'SOJA3',
                            'TAEE11.SA': 'TAEE11',
                            'VALE3.SA': 'VALE3',
                            'WIZC3.SA': 'WIZC3'
                            })
    df.dropna(inplace=True)    
    df['soma'] = df['CSAN3'] + df['GOAU4'] + df['ITSA4'] + df['SOJA3'] + df['TAEE11'] + df['VALE3'] + df['WIZC3']
    df['Rent'] = round(df['soma'].pct_change() * 100,2)
    return df
    
    # df_geral =pd.DataFrame()

    # for ativo in df.columns:
    #     df_x =pd.DataFrame()
    #     if ativo != 'Mes':

    #         df_x['Mes'] = df['Mes']
    #         df_x['Ativo'] = ativo
    #         df_x['UltCotMes'] = df[ativo]
    #         df_geral = pd.concat([df_geral, df_x])
    
    return df_geral

def lista_tesouro_totais():
    load_dotenv()
    cliente = MongoClient(f"mongodb+srv://{os.getenv('MONGO_DATABASE')}:{os.getenv('MONGO_PASSW')}@clustercontroleweb.dfrs4.mongodb.net/?retryWrites=true&w=majority&appName=ClusterControleWeb")
    database = cliente['db_controleweb']
    collection = database['Tesouro']
    
    df = pd.DataFrame(list(collection.find()))
    df = df.sort_values(by='Data')
    df_agrupado_dia = df.groupby('Data')['Posição Atual'].sum().reset_index()
    df_agrupado_dia['Lucro'] = df_agrupado_dia['Posição Atual'].diff().round(2).astype(str)
    df_agrupado_dia['Data'] = pd.to_datetime(df_agrupado_dia['Data'])
    df_agrupado_dia['Data'] = df_agrupado_dia['Data'].dt.strftime('%d/%m/%Y')


    lista = df['Titulo'].unique().tolist()
    df_total = pd.DataFrame()

    for ativo in lista:

        df1 = df.loc[df['Titulo']==ativo]
        df1.loc[:,['Lucro']] = df1['Posição Atual'].diff()
        #df1.loc[:,['Dif']] = df1['Unit'].diff()
        #df1.loc[:,['Rent%']] = df1['Unit'].pct_change() * 100
        #fig_tesouro = px.line(df1, x='Data', y='Lucro', color= 'Titulo',title='Tesouro no Período ' + ativo)
        #fig_tesouro.show()
        df_total = pd.concat([df_total, df1], axis=0)
        df1 = df1.loc[:,['Titulo','Lucro']].style.hide()
        #display(df1)
        
    return df_total
if __name__ == "__main__":
    start_time = time.time()
    # Coloque o código principal do seu programa aqui
    print(dolar_dia())
    execution_time = time.time() - start_time
    print()
    print()    
    print("--- %s segundos ---" % execution_time)
