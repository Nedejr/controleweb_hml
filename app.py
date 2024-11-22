
import streamlit as st
import plotly.express as px
import connecta_google 
from datetime import datetime, timedelta
import cotacoes
import pandas as pd
import dateutil.relativedelta
import plotly.graph_objects as go

def main():

    st.set_page_config(page_title='ControleWeb', layout='wide', page_icon=':bar_chart:')
    st.title('Projeto Streamlit - utilizando planilha Google Sheets')
    st.write('')

    servico = connecta_google.autenticacao()
    paginas = ['Inicio','Totais', 'Contas', 'Dividendos','Tesouro', 'Operações', 'Cartão']
    f_pagina = st.sidebar.selectbox("Selecione a página:", paginas)

    if (f_pagina=='Totais'):
        col1, col1x, col2 = st.columns([0.5, 0.5,2])
        col3, col4 = st.columns([1,2])
        col5, col6 = st.columns(2)
        col7, col8, col9 = st.columns([0.25,0.25,0.5])
        
        
        #Carrega os dados
        df_totais_gerais = connecta_google.carrega_dados(servico, 'Totais Gerais')
        df_totais_tesouro = connecta_google.carrega_dados(servico, 'Totais Tesouro')
        df_renda_variavel = connecta_google.carrega_dados(servico, 'Operações')
        df_taxa_tesouro_ipca = df_renda_variavel
        
        
        df_renda_variavel = df_renda_variavel.loc[df_renda_variavel['Tipo'].isin(['FII','Ações','ETF']),['Ativo', 'Tipo','Total','Qtd','Cotação', 'Cotação.Ant','Res.Dia','Res.Dia%']]
        total_custo = df_renda_variavel.groupby(['Ativo'])['Total'].sum()
        quantidade =  df_renda_variavel.groupby(['Ativo'])['Qtd'].sum()
        pm = df_renda_variavel.groupby(['Ativo'])['Cotação'].max()
        cot_ant = df_renda_variavel.groupby(['Ativo'])['Cotação.Ant'].max()
        tipo = df_renda_variavel.groupby(['Ativo'])['Tipo'].max()
        
        df_renda_variavel = pd.concat([total_custo,quantidade], axis=1)
        df_renda_variavel = pd.concat([df_renda_variavel,pm], axis=1)
        df_renda_variavel = pd.concat([df_renda_variavel,cot_ant], axis=1)
        df_renda_variavel = pd.concat([df_renda_variavel,tipo], axis=1)

        
        df_renda_variavel = df_renda_variavel.loc[(df_renda_variavel['Total'] > 0)]
        df_renda_variavel['P.Médio'] = df_renda_variavel['Total'] / df_renda_variavel['Qtd']
        df_renda_variavel['Ativo'] = df_renda_variavel.index
        df_renda_variavel.rename(columns={'Total': 'Custo'}, inplace=True)
        df_renda_variavel['Posição'] = df_renda_variavel['Cotação'] * df_renda_variavel['Qtd']
        df_renda_variavel['Luc/Prej'] = df_renda_variavel['Posição'] -  df_renda_variavel['Custo']
        df_renda_variavel['Rent%'] = (df_renda_variavel['Cotação'] / df_renda_variavel['P.Médio'] - 1 ) * 100
        df_renda_variavel['Ticket'] = df_renda_variavel['Ativo']
        df_renda_variavel = df_renda_variavel.reindex(['Ativo', 'Qtd', 'Cotação','Posição', 'Custo', 'Luc/Prej', 'Rent%','Ticket', 'P.Médio', 'Cotação.Ant','Res.Dia','Res.Dia%','Tipo'], axis=1)
        df_renda_variavel['Res.Dia'] = (df_renda_variavel['Cotação'] -  df_renda_variavel['Cotação.Ant']) * df_renda_variavel['Qtd']
        df_renda_variavel['Res.Dia%'] = (df_renda_variavel['Cotação'] / df_renda_variavel['Cotação.Ant'] - 1 ) * 100
        df_renda_variavel.drop(labels='Cotação.Ant', axis=1, inplace=True)
        df_renda_variavel = df_renda_variavel.sort_values(['Rent%'], ascending=True)
        
        
        pct_ibov = cotacoes.pct_ibov()
        cotacao_dolar = cotacoes.dolar_dia()
        total_pl = df_totais_gerais['PL'].sum()
        pct_lucro_prej_carteira = str(round((df_totais_gerais['PL'].sum()/df_totais_gerais['Custo'].sum()-1) *100 ,2))
        total_lucro_prej_diario = df_renda_variavel['Res.Dia'].sum()
        pct_lucro_prej_diario   = str(round(df_renda_variavel['Res.Dia'].sum()/df_renda_variavel['Posição'].sum()*100,2))
        
        df_agrupado_tipo = df_renda_variavel.groupby('Tipo')[['Res.Dia']].sum().reset_index()
        
        
        col1.metric(label='Total Carteira  R$', value='R$ {:,.2f}'.format(total_pl), delta=pct_lucro_prej_carteira)
        col1.metric(label='Lucro/Prejuízo. Dia R$', value='R$ {:,.2f}'.format(total_lucro_prej_diario), delta=pct_lucro_prej_diario)
        col1x.metric(label='DOLAR', value='R$ {:,.2f}'.format(cotacao_dolar))
        col1x.metric(label='IBOV', value='IBOV', delta=pct_ibov, label_visibility='hidden')
        
        
        df_totais_gerais = df_totais_gerais.style.map(color_positivo, subset=['PL','Custo','Luc/Prej', 'Luc/Prej %', 'PL %'])
        df_totais_gerais = df_totais_gerais.format({'PL': "R$ {:,.2f}".format,
                                                    'Custo': "R$ {:,.2f}".format,
                                                    'Luc/Prej': "R$ {:,.2f}".format,
                                                    'Luc/Prej %': "{:,.2f}%".format,
                                                    'PL %': "{:,.2f}%".format})
        col2.dataframe(df_totais_gerais, hide_index=True, use_container_width=True)

        fig_totais_gerais = px.bar(df_agrupado_tipo, x='Tipo' , y='Res.Dia', color='Tipo', title='Lucro e Prejuizo Diário', barmode='group', orientation='v', 
                                   color_discrete_map={'FII': 'DeepSkyBlue', 'Ações': 'MediumBlue', 'ETF': 'SkyBlue'})
        fig_totais_gerais.add_trace(go.Scatter(
            x=df_agrupado_tipo['Tipo'], 
            y=round(df_agrupado_tipo['Res.Dia'],2),
            text=round(df_agrupado_tipo['Res.Dia'],2),
            mode='text',
            textposition='top center',
            textfont=dict(
                size=14,
            ),
            showlegend=False,
            
        ))
        col3.plotly_chart(fig_totais_gerais, use_container_width=True)
        
        df_renda_variavel = df_renda_variavel.sort_values(['Ticket'], ascending=True)
        df_renda_variavel = df_renda_variavel.style.map(color_positivo, subset=['Posição','Custo','Luc/Prej', 'Rent%','Res.Dia', 'Res.Dia%'])
        df_renda_variavel = df_renda_variavel.format({  'Qtd': "{:,.0f}".format,
                                        'Cotação': "R$ {:,.2f}".format,
                                        'Posição': "R$ {:,.2f}".format,
                                        'Custo': "R$ {:,.2f}".format,
                                        'Luc/Prej': "R$ {:,.2f}".format,
                                        'P.Médio': "{:,.4f}".format,
                                        'Res.Dia': "R$ {:,.2f}".format,
                                        'Rent%': "{:,.2f}%".format,
                                        'Res.Dia%': "{:,.2f}%".format})
        
        col4.dataframe(df_renda_variavel, hide_index=True, width=1200)

        df_taxa_tesouro_ipca = df_taxa_tesouro_ipca.loc[(df_taxa_tesouro_ipca['Ativo'].str.contains('IPCA'))]
        #df_taxa_tesouro_ipca.drop(labels=['Preço','Total','Tipo','Ordem','Data','Mes/Ano','Mes','Cotação.Ant','Res.Dia','Res.Dia%'], inplace=True, axis=1)
        df_taxa_tesouro_ipca = df_taxa_tesouro_ipca.loc[:,['Ativo', 'Qtd', 'Cotação']]
        df_taxa_tesouro_ipca['Qtd'] = df_taxa_tesouro_ipca['Qtd'] * 100
        df_taxa_tesouro_ipca['Total'] = df_taxa_tesouro_ipca['Qtd'] * df_taxa_tesouro_ipca['Cotação']
        df_taxa_tesouro_ipca = (df_taxa_tesouro_ipca.groupby('Ativo')['Total'].sum()) / (df_taxa_tesouro_ipca.groupby('Ativo')['Qtd'].sum())
        
        df_taxa_tesouro_ipca = df_taxa_tesouro_ipca.reset_index()
        df_taxa_tesouro_ipca = df_taxa_tesouro_ipca.rename(columns={0: 'Taxa'})
        
        fig_taxa = px.bar(df_taxa_tesouro_ipca, x='Ativo' , y='Taxa', color='Ativo', title='Taxa Média IPCA', barmode='group', orientation='v')
        fig_taxa.add_trace(go.Scatter(
            x=df_taxa_tesouro_ipca['Ativo'], 
            y=round(df_taxa_tesouro_ipca['Taxa'],2),
            text=round(df_taxa_tesouro_ipca['Taxa'],2),
            mode='text',
            textposition='top center',
            textfont=dict(
                size=14,
            ),
            showlegend=False,
            
        ))
        fig_taxa.update_layout(showlegend=False)
        col7.plotly_chart(fig_taxa, use_container_width=True)

        fig_tesouro_por_tipo = px.pie(df_totais_tesouro, values='Posição Atual', title='Tesouro por Tipo', color='Tipo', names='Tipo', height=350)
        col8.plotly_chart(fig_tesouro_por_tipo, use_container_width=True)

        df_totais_tesouro['Valor Aplicado'] = df_totais_tesouro['Valor Aplicado'].apply(lambda x: 'R$ {:,.2f}'.format(x))
        df_totais_tesouro['Qtd'] = df_totais_tesouro['Qtd'].apply(lambda x: 'R$ {:,.2f}'.format(x))
        df_totais_tesouro['Luc/Prej'] = df_totais_tesouro['Luc/Prej'].apply(lambda x: 'R$ {:,.2f}'.format(x))
        df_totais_tesouro['Posição Atual'] = df_totais_tesouro['Posição Atual'].apply(lambda x: 'R$ {:,.2f}'.format(x))
        df_totais_tesouro['Rent%'] = df_totais_tesouro['Rent%'].apply(lambda x: '{:,.2f}%'.format(x))
        df_totais_tesouro = df_totais_tesouro.style.map(color_tipo_tesouro, subset=['Titulo','Tipo'])


        
        col9.dataframe(df_totais_tesouro, hide_index=True, width=1200)
        
        
        # df = cotacoes.lista_tesouro_totais()
        # fig_total_tesouro_diario = px.line(df, x='Data', y='Lucro', color= 'Titulo',title='Tesouro no Período', markers=True)
        # st.plotly_chart(fig_total_tesouro_diario, use_container_width=True)

    if (f_pagina=='Contas'):
        col1, colx, col2 = st.columns([0.2,0.4,0.2])
        col3, col4, col5 = st.columns([0.6,0.02,0.38]) 
        contas = ['Banco do Brasil', 'Bradesco', 'Itau']
        
        #Filtrar por conta
        f_seleciona_conta = st.sidebar.selectbox('Selecione a conta',
                                  contas, placeholder='Selecione')
        
        match f_seleciona_conta:
            case "Banco do Brasil":
                 df_conta = connecta_google.carrega_dados(servico, 'Conta Banco do Brasil')
            case "Bradesco":
                df_conta = connecta_google.carrega_dados(servico, 'Conta Bradesco')
            case "Itau":
                df_conta = connecta_google.carrega_dados(servico, 'Conta Itau')
            

        df_despesas = connecta_google.carrega_dados(servico, 'Totais Despesas')
        str_datas = sorted(df_conta['Mes'].unique().tolist(), reverse=True)
        #Filtrar a Data do Pagamento
        f_selecionaData = st.sidebar.multiselect('Selecione o Mês/Ano', str_datas, placeholder='Selecione')
        #Montagem do Filtro
        if f_selecionaData == []:
            df_filtered = df_conta
        else:
            df_filtered = df_conta.loc[(df_conta['Mes'].isin(f_selecionaData))]   
        saldo_conta = 'R$ {:,.2f}'.format(df_conta['ValorTotal'].sum())
        col1.metric(label='SALDO ' + f_seleciona_conta.upper(), value=saldo_conta) 
        df_filtered = df_filtered.sort_values(by='Data', ascending=False)  
        
        df_filtered['Data'] = df_filtered['Data'].dt.strftime('%d/%m/%Y')
        df_total_por_operacao = df_filtered.groupby('Tipo').agg({'ValorTotal':'sum'}).reset_index()
        df_total_por_operacao['ValorTotal'] = abs(df_total_por_operacao['ValorTotal'])
        col1.dataframe(df_total_por_operacao, hide_index=True, width=200, column_config={
            "ValorTotal": st.column_config.NumberColumn(
                help="Valor Total no período selecionado",
                format="R$ %.2f",
            )})

        fig_por_operacao = px.bar(df_total_por_operacao.sort_values(by='Tipo'), x='Tipo' , y='ValorTotal', color='Tipo', title='Tipo por Operação', width=500)
        fig_por_operacao.add_trace(go.Scatter(
            x=df_total_por_operacao['Tipo'], 
            y=round(df_total_por_operacao['ValorTotal'],2),
            text=round(df_total_por_operacao['ValorTotal'],2),
            mode='text',
            textposition='top center',
            textfont=dict(
                size=14,
            ),
            showlegend=False,
            
        ))
        colx.plotly_chart(fig_por_operacao)

        
        fig_por_tipo = px.pie(df_filtered, values='Valor', title='Total por Tipo' , names='Tipo' , height=400)
        col2.plotly_chart(fig_por_tipo)
        
        df_somente_despesas = df_filtered.groupby(['Mes','Tipo'])['Valor'].sum().reset_index()
        df_somente_despesas = df_somente_despesas[(df_somente_despesas['Tipo'].isin(['DEBITO','CREDITO',]))].reset_index()
        df_somente_despesas.drop(columns=['index'], inplace=True)
        df_somente_despesas.sort_values("Mes", inplace=True)
        
        df_filtered = df_filtered.drop(labels='Valor', axis=1)
        df_filtered = df_filtered.style.map(color_positivo, subset=['ValorTotal'])
        df_filtered = df_filtered.format({'ValorTotal': "R$ {:,.2f}".format
                                          })
        col3.write('Movimentação no Período')
        col3.dataframe(df_filtered, hide_index=True, use_container_width=True)

        
        
        col5.write('Despesas Mensais ' + ':red[R$ {:,.2f}]'.format(df_despesas['Valor'].sum()))
        df_despesas = df_despesas.style.map(lambda x: 'background-color: Green; font-weight: bold' if (x == 'SIM')  else 'background-color: red; font-weight: bold', subset=['Pago'])
            

        col5.dataframe(df_despesas, hide_index=True, use_container_width=True, column_config={
            "Valor": st.column_config.NumberColumn(
                help="Valor da despesa mensal",
                format="R$ %.2f",
            )}
        )
        fig_despesasw = px.line(df_somente_despesas, x='Mes', y='Valor' , color = 'Tipo', title='Receitas x Despesas no Período', color_discrete_sequence=['Green', 'Red'])
        st.plotly_chart(fig_despesasw, use_container_width=True)
        
    if (f_pagina=='Dividendos'):
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        col5, col6 = st.columns(2)
        df_dividendos = connecta_google.carrega_dados(servico, f_pagina)
        
        #Filtrar a Data do Pagamento

        month1 = datetime.now() + dateutil.relativedelta.relativedelta(months=-1)
        month2 = month1 + dateutil.relativedelta.relativedelta(months=-1)
        lista_meses = []
        lista_meses.append(datetime.now().strftime('%Y/%m'))
        lista_meses.append(month1.strftime('%Y/%m'))
        lista_meses.append(month2.strftime('%Y/%m'))


        str_datas = sorted(df_dividendos['Mes'].unique().tolist(), reverse=True)
        f_selecionaData = st.sidebar.multiselect('Selecione o Mês/Ano',
                                  str_datas, placeholder='Selecione',
                                  default=lista_meses)
        

        if f_selecionaData == []:
            df_filtered = df_dividendos
        else:
            df_filtered = df_dividendos.loc[(df_dividendos['Mes'].isin(f_selecionaData))]
        
        
        f_tipo = st.sidebar.checkbox('Visualizar apenas FII')
        if f_tipo:
            df_filtered = df_filtered.loc[(df_filtered['Tipo']=='FII')]
        
        
        
        df_total_por_tipo = df_filtered.groupby(['Tipo','Mes'])['ValorTotal'].sum().reset_index()
        df_total_por_tipo.sort_values("Mes", ascending=True, inplace=True)
        
        total_dividendos = 'R$ {:,.2f}'.format(df_filtered['ValorTotal'].sum())
        col1.metric(label='TOTAL', value=total_dividendos)  
        #df_filtered['Data'] = df_filtered['Data'].dt.strftime('%d/%m/%Y')
        df_filtered.loc[:,'Data']  = df_filtered['Data'].dt.strftime('%d/%m/%Y')

        df_agrupado = df_filtered.sort_values(by=['Mes'])
        df_agrupado = df_agrupado.loc[:, ['Tipo','Mes','ValorTotal']]
        df_agrupado = df_agrupado.groupby(['Mes','Tipo'])['ValorTotal'].sum().reset_index()
        df_agrupado_tot = df_agrupado.groupby(['Mes'])['ValorTotal'].sum().reset_index()
        
        

        fig_dividendos = px.bar(df_filtered.sort_values(by=['Mes']), x='Mes' , y='ValorTotal', color='Tipo', title='Dividendos por Tipo')
        fig_dividendos.add_trace(go.Scatter(
            x=df_agrupado_tot['Mes'], 
            y=round(df_agrupado_tot['ValorTotal'],2),
            text=round(df_agrupado_tot['ValorTotal'],2),
            mode='text',
            textposition='top center',
            textfont=dict(
                size=14,
            ),
            showlegend=False,
            
        ))
        
        col3.plotly_chart(fig_dividendos, use_container_width=True)
        
                                   
        col6.dataframe(df_filtered.sort_values(by='Data', ascending=False), hide_index=True, use_container_width=True, column_config={
            "ValorUnit": st.column_config.NumberColumn(
                help="Valor Unitário",
                format="R$ %.4f",
            ),
            "ValorTotal": st.column_config.NumberColumn(
                help="ValorTotal",
                format="R$ %.2f",
            ),
            "Data": st.column_config.DateColumn(
                help="Data",
                format="DD/MM/YYYY",
            )},  
        )

        ############################################################################################

        df_dividendos_copia = df_dividendos
        df_operacoes_copia = connecta_google.carrega_dados(servico, 'Operações')

        filtro = sorted(df_filtered.loc[df_filtered['Tipo'] == 'FII','Ativo'].unique().tolist())

        #filtro = sorted(df_dividendos_copia['Ativo'].unique().tolist())
        #f_selecionaAtivo = st.multiselect('Selecione o FII',
        #                          filtro, placeholder='Selecione', default=filtro[0])

        df_operacoes_copia['Mes'] = df_operacoes_copia['Data'].apply(lambda x: str(x.year) + '/' + f'{x.month:02}')
        df_operacoes_copia = df_operacoes_copia[df_operacoes_copia["Ativo"].isin(filtro)]
        df_operacoes_copia = df_operacoes_copia.groupby(['Ativo','Mes', 'Cotação'])['Total'].sum().reset_index()
        df_operacoes_copia['AcumOp'] = df_operacoes_copia.groupby('Ativo')['Total'].cumsum()
        
        df_operacoes_copia = df_operacoes_copia.rename(columns={'Mes': 'MesOp', 'Cotação': 'CotaçãoOp'})
        df_operacoes_copia['Mes'] = df_operacoes_copia['MesOp'].apply(lambda x : datetime.strptime(x , '%Y/%m')) + pd.DateOffset(months=1)
        df_operacoes_copia['Mes'] = df_operacoes_copia['Mes'].dt.strftime('%Y/%m')
        df_operacoes_copia.sort_values(by=['Ativo','Mes'], ascending=True, inplace=True)
        
        df_dividendos_copia = df_dividendos_copia[df_dividendos_copia["Ativo"].isin(filtro)]
        
        #df_dividendos_copia['Data_Base'] = df_dividendos_copia['Data'] - timedelta(days=15)
        df_dividendos_copia = df_dividendos_copia.loc[:,['Ativo', 'ValorTotal', 'Mes']]
        df_dividendos_copia = df_dividendos_copia.rename(columns={'ValorTotal': 'ValorTotalDV'})
        df_dividendos_copia.sort_values(by=['Ativo','Mes'], ascending=True, inplace=True)
        
        df_row = pd.merge(df_dividendos_copia, df_operacoes_copia, on=['Ativo','Mes'], how='left')
        df_row.ffill(inplace=True)
        df_row['YOC%'] = df_row['ValorTotalDV'] / df_row['AcumOp'] * 100
        df_row['CotaçãoOp'] = df_row['CotaçãoOp'].fillna(df_row['CotaçãoOp'].max())
        df_row.drop(labels='MesOp', axis=1, inplace=True)
        df_row.drop(labels='Total', axis=1, inplace=True)
        

        df_row = df_row.loc[(df_row['YOC%']!=0),['Ativo','ValorTotalDV','Mes','CotaçãoOp', 'AcumOp', 'YOC%']]
        df_row = df_row[df_row["Mes"].isin(f_selecionaData)]
        df_row.sort_values(by=['Ativo','Mes'], ascending=True,inplace=True)
        
        #st.dataframe(df_row, hide_index=True, use_container_width=True)

        fig_yoc = px.bar(df_filtered.sort_values(by='Mes'), x='Mes', y='ValorTotal' , color = 'Ativo', title='Dividendos por Ativo', barmode='group')
        col4.plotly_chart(fig_yoc, use_container_width=True)
        
        fig_yoc = px.line(df_row, x='Mes', y='YOC%' , color = 'Ativo', title='YOC% por FII')
        col5.plotly_chart(fig_yoc, use_container_width=True)

        ############################################################################################

    if (f_pagina=='Tesouro'):
        st.write('Em construção!!!')
        
    if (f_pagina=='Operações'):

        col1, col2, col3 = st.columns([0.9,0.05,0.05])
        col4, col5 = st.columns([0.4,0.6])
        col6, col7 = st.columns([0.5,0.5])
        df_operacoes = connecta_google.carrega_dados(servico, f_pagina)
        df_renda_variavel = df_operacoes.copy()

        ###
        df_renda_variavel = df_renda_variavel.loc[df_renda_variavel['Tipo'].isin(['FII','Ações','ETF']),['Ativo','Total','Qtd','Cotação', 'Cotação.Ant','Res.Dia','Res.Dia%']]

        total_custo = df_renda_variavel.groupby(['Ativo'])['Total'].sum()   
        quantidade =  df_renda_variavel.groupby(['Ativo'])['Qtd'].sum()
        pm = df_renda_variavel.groupby(['Ativo'])['Cotação'].max()
        cot_ant = df_renda_variavel.groupby(['Ativo'])['Cotação.Ant'].max()
        
        df_renda_variavel = pd.concat([total_custo,quantidade], axis=1)
        df_renda_variavel = pd.concat([df_renda_variavel,pm], axis=1)
        df_renda_variavel = pd.concat([df_renda_variavel,cot_ant], axis=1)
        

        df_renda_variavel = df_renda_variavel.loc[(df_renda_variavel['Total'] > 0)]
        df_renda_variavel['Pm'] = df_renda_variavel['Total'] / df_renda_variavel['Qtd']
        df_renda_variavel['Ativo'] = df_renda_variavel.index
        
        df_renda_variavel.rename(columns={'Total': 'Total Custo'}, inplace=True)
        df_renda_variavel['Valor Posicao'] = df_renda_variavel['Cotação'] * df_renda_variavel['Qtd']
        df_renda_variavel['Luc/Prej'] = df_renda_variavel['Valor Posicao'] -  df_renda_variavel['Total Custo']
        df_renda_variavel['Rent%'] = (df_renda_variavel['Cotação'] / df_renda_variavel['Pm'] - 1 ) * 100
        df_renda_variavel = df_renda_variavel.reindex(['Ativo', 'Qtd', 'Cotação','Valor Posicao','Total Custo', 'Luc/Prej', 'Rent%','Pm', 'Cotação.Ant','Res.Dia','Res.Dia%'], axis=1)
        df_renda_variavel['Res.Dia'] = (df_renda_variavel['Cotação'] -  df_renda_variavel['Cotação.Ant']) * df_renda_variavel['Qtd']
        df_renda_variavel['Res.Dia%'] = (df_renda_variavel['Cotação'] / df_renda_variavel['Cotação.Ant'] - 1 ) * 100
        df_renda_variavel.drop(labels='Cotação.Ant', axis=1, inplace=True)
        df_renda_variavel = df_renda_variavel.sort_values(['Rent%'], ascending=True)

        df_renda_variavel = df_renda_variavel.style.map(color_positivo, subset=['Qtd','Cotação','Valor Posicao','Total Custo','Pm','Luc/Prej', 'Rent%','Res.Dia', 'Res.Dia%'])
        df_renda_variavel = df_renda_variavel.format({  'Qtd': "{:,.2f}".format,
                                        'Cotação': "R$ {:,.2f}".format,
                                        'Valor Posicao': "R$ {:,.2f}".format,
                                        'Total Custo': "R$ {:,.2f}".format,
                                        'Luc/Prej': "R$ {:,.2f}".format,
                                        'Pm': "R$ {:,.2f}".format,
                                        'Res.Dia': "R$ {:,.2f}".format,
                                        'Rent%': "{:,.2f}%".format,
                                        'Res.Dia%': "{:,.2f}%".format})

        #Filtrar a Data do Pagamento
        str_datas = sorted(df_operacoes['Mes'].unique().tolist(), reverse=True)

        month1 = datetime.now() + dateutil.relativedelta.relativedelta(months=-1)
        month2 = month1 + dateutil.relativedelta.relativedelta(months=-1)
        lista_meses = []
        lista_meses.append(datetime.now().strftime('%Y/%m'))
        lista_meses.append(month1.strftime('%Y/%m'))
        lista_meses.append(month2.strftime('%Y/%m'))


        f_selecionaData = st.sidebar.multiselect('Selecione o Mês/Ano',
                                  str_datas, placeholder='Selecione')
        #Filtrar por Ativo
        str_ativo = sorted(df_operacoes['Ativo'].unique().tolist())
        f_selecionaAtivo = st.sidebar.multiselect('Selecione o Ativo',
                                  str_ativo, placeholder='Selecione')

        #Montagem do Filtro

        if f_selecionaData == []:

            if f_selecionaAtivo == []:
                df_filtered = df_operacoes
            else:
                df_filtered =  df_operacoes.loc[(df_operacoes['Ativo'].isin(f_selecionaAtivo))]
        else:
            if f_selecionaAtivo == []:

                df_filtered = df_operacoes.loc[(df_operacoes['Mes'].isin(f_selecionaData))]
                
            else:
                df_filtered = df_operacoes.loc[(df_operacoes['Mes'].isin(f_selecionaData) & (df_operacoes['Ativo'].isin(f_selecionaAtivo)))]   

        df_filtered = df_filtered.sort_values(by='Mes', ascending=True)
       
        total_valor = round(df_filtered['Total'].sum(),2)
        total_quantidade = round(df_filtered['Qtd'].sum(),2) 
        
        pm = round(df_filtered['Total'].sum() / df_filtered['Qtd'].sum(),4)
        df_agrupado_tipo = df_filtered.groupby('Tipo')[['Total']].sum().reset_index()
        df_filtered['Data'] = df_filtered['Data'].dt.strftime('%d/%m/%Y')
        #df_filtered.loc[:,'Data'] = df_filtered['Data'].dt.strftime('%d/%m/%Y')
        df_agrupado_tipo['Total'] = df_agrupado_tipo['Total'].apply(lambda x: 'R$ {:,.2f}'.format(x))
        
        df_patrimonio_acumulado = df_operacoes.loc[:,['Mes','Total']]
        df_patrimonio_acumulado.sort_values(by='Mes', inplace=True)
        df_patrimonio_acumulado['Acum'] =  df_patrimonio_acumulado['Total'].cumsum()
        df_patrimonio_acumulado = df_patrimonio_acumulado.groupby('Mes')['Acum'].max().reset_index()
        fig_totais_por_tipo = px.line(df_patrimonio_acumulado, x='Mes' , y='Acum', line_shape='spline', title='TOTAL OPERAÇÕES' + ' R$ {:,.2f}'.format(df_operacoes['Total'].sum()))
        col1.plotly_chart(fig_totais_por_tipo, use_container_width=True)

        

        col4.metric(label='TOTAL Período', value='R$ {:,.2f}'.format(total_valor))
        col4.metric(label='QTD Período', value='{:,.2f}'.format(total_quantidade))
        col4.metric(label='PM Período', value='R$ {:,.2f}'.format(pm))

        col4.dataframe(df_agrupado_tipo, hide_index=True, width=300)
        
        col5.dataframe(df_renda_variavel, hide_index=True, use_container_width=True)

        fig_totais_por_tipo = px.bar(df_filtered, x='Mes' , y='Total', color='Tipo', barmode='group', title='Operações por Tipo')
        col6.plotly_chart(fig_totais_por_tipo, use_container_width=True)

        fig_totais = px.bar(df_filtered, x='Mes' , y='Total', title='Operações por Mês')
        col7.plotly_chart(fig_totais, use_container_width=True)
        st.dataframe(df_filtered, hide_index=True, use_container_width=True, column_config={
                "Preço": st.column_config.NumberColumn(
                    help="Preço Unitário",
                    format="R$ %.2f",
                ),
                "Total": st.column_config.NumberColumn(
                    help="Valor Total",
                    format="R$ %.2f",
                ),
                "Cotação": st.column_config.NumberColumn(
                    help="Cotação",
                    format="R$ %.2f",
                ),
                "Res.Dia": st.column_config.NumberColumn(
                    help="Res.Dia",
                    format="R$ %.2f",
                ),
                "Res.Dia%": st.column_config.NumberColumn(
                    help="Res.Dia%",
                    format="%.2f",
                )
            
            }
        )
        
        

        #fig_totais_por_ativo = px.pie(df_filtered, values='Total', title='Operações por Ativo' , names='Ativo')
        #st.plotly_chart(fig_totais_por_ativo, use_container_width=True)

    if (f_pagina=='Cartão'):
        
        col1, col2, col3, col4 = st.columns(4)
        
        df_cartao = connecta_google.carrega_dados(servico, f_pagina)
        
        #Filtrar a Data do Pagamento
        str_datas = sorted(df_cartao['Mes'].unique().tolist(), reverse=True)
        f_selecionaData = st.sidebar.multiselect('Selecione a Fatura',
                                  str_datas, placeholder='Selecione')
        
        str_bandeira = sorted(df_cartao['Bandeira'].unique().tolist(), reverse=True)
        f_bandeira = st.sidebar.multiselect('Selecione a Bandeira',
                                  str_bandeira, placeholder='Selecione')                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     


        if f_selecionaData == []:
            df_filtered = df_cartao
        else:
            df_filtered = df_cartao.loc[(df_cartao['Mes'].isin(f_selecionaData) & (df_cartao['Bandeira'].isin(f_bandeira)) )]
        
        
        
        total_fatura = df_filtered['VlParcela'].sum()
        total_em_aberto = df_cartao['total_em_aberto'].sum()
        
        df_filtered = df_filtered.rename(columns={'DtPg': 'Data Pagamento'})
        df_filtered['Data Pagamento'] = df_filtered['Data Pagamento'].dt.strftime('%m/%d/%Y')
        df_filtered = df_filtered.drop(labels='DtFat', axis=1)
        df_filtered = df_filtered.drop(labels='total_em_aberto', axis=1)    
        df_filtered = df_filtered.sort_values(by='Mes', ascending=False)

        col1.metric(label='Total Parcelas', value = 'R$ {:,.2f}'.format(total_fatura))
        col4.metric(label='Total em aberto', value = 'R$ {:,.2f}'.format(total_em_aberto))
        
        fig_totais = px.bar(df_filtered, x='Mes' , y='VlParcela',  barmode='group', title='Gastos por Mês')
        st.plotly_chart(fig_totais, use_container_width=True)
        
        df_filtered = df_filtered.style.map(color_tipo_cartao, subset=['Bandeira'])

        
        st.dataframe(df_filtered, hide_index=True, use_container_width=True, column_config={
            "VlParcela": st.column_config.NumberColumn(
                help="Valor da Parcela",
                format="R$ %.2f",
            ),
            "VlPagamento": st.column_config.NumberColumn(
                help="Valor do Pagamento",
                format="R$ %.2f",
            )}
        )

    if (f_pagina=='Inicio'):
        texto = '''
                Este projeto teste foi desenvolvido em Python utilizando Streamlit e foi projetado para facilitar o acesso 
            e a visualização de dados armazenados em uma planilha do Google Sheets. 
            O objetivo principal foi criar uma interface simples e intuitiva, permitindo que os usuários interajam com os dados
            em tempo real, sem a necessidade de conhecimentos avançados em programação ou manipulação de planilhas.
                A integração com o Google Sheets foi feita utilizando a biblioteca gspread, que permite a leitura e escrita de dados 
            diretamente nas planilhas. Com isso, foi possível extrair informações de forma automatizada.
                A plataforma Streamlit possibilitou a criação de gráficos dinâmicos, tabelas interativas e filtros, o que permitiu que o 
            usuário tivesse uma experiência mais personalizada ao explorar os dados. Além disso, a interface se ajusta automaticamente a 
            diferentes tamanhos de tela, tornando o projeto acessível em dispositivos móveis e desktops.
                Em resumo, este projeto combina o poder de análise de dados do Python com a praticidade da interface do Streamlit e a 
            flexibilidade do Google Sheets, oferecendo uma solução simples e eficaz para manipulação e visualização de dados em tempo real.

        '''

        st.write(texto)
        st.write()
        st.write()
        st.write('Todos os dados apresentados neste projeto são fictícios.')
        st.write()
        st.write()
        st.write('by Nede Junior - 2024')

def color_positivo(val):
    color = 'Green' if val >= 0 else 'red'
    return f'background-color: {color}'

def color_tipo_tesouro(tipo):
    color = '#046bcb' if 'Selic' in tipo else '#81c7f7'
    return f'background-color: {color}'

def color_tipo_cartao(val):
    match val:
        case "VISA":
            color ='#00008B'

        case "MASTERCARD":
            color ='#A020F0'

        case "MERCADO PAGO":
            color ='#00BFFF'
    
    return f'background-color: {color}'    
                     
if __name__ == '__main__':
    main()