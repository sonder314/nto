import streamlit as st
import pandas as pd
import numpy as np
import requests
import lxml

st.title('Анализ финансовых данных компании')

ticker = 'AAPL'

def load_data(url):
  r = requests.get(url,headers ={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
  data = pd.read_html(r.text)
  return data

def load_summary_data(ticker):
    summary_url = f'https://finance.yahoo.com/quote/{ticker}?p={ticker}'
    summary_data = load_data(summary_url)
    data = [summary_data[0], summary_data[1]]
    data = pd.concat(summary_data)
    data.reset_index(drop=True, inplace=True)
    df = data.transpose()
    df.columns = df.iloc[0]
    df = df.drop(0)
    df = df.reset_index(drop=True)
    return df

def load_historical_data(ticker):
    historiscal_url= f'https://finance.yahoo.com/quote/{ticker}/history?p={ticker}'
    historiscal_data = load_data(historiscal_url)
    data = historiscal_data[0]
    data = data.iloc[:-1 , :]
    data = data[data["Open"].str.contains("Dividend") == False]
    
    data['Date'] = pd.to_datetime(data['Date'])
    numeric_columns = list(data.columns)[1::]
    for column_name in numeric_columns:
        data[column_name] = data[column_name].str.replace(',', '')
        data[column_name] = data[column_name].astype(np.float64)
    
    data.set_index('Date',inplace=True)
    data = data.reindex(index=data.index[::-1])
    return data
    
    
#загрузим общую информацию
data_load_state = st.text('Загружаем базовую информацию...')
df = load_summary_data(ticker)
data_load_state.text('Информация... Загружена!')

st.subheader('Общая информация')
st.write(pd.DataFrame(df.to_dict()))

history_load_state = st.text('Загружаем историческую информацию...')
history = load_historical_data(ticker)
history_load_state.text('Информация... Загружена!')

st.subheader('Историческая информация')
st.text('Изменение биржевых котировок:')
st.line_chart(history['Adj Close**'])

st.text('Изменение объема торгов:')
st.line_chart(history['Volume'])

ma_day = [10,20,30]

for ma in ma_day:
    column_name = "MA for %s days" %(str(ma))
    history[column_name] = history['Adj Close**'].rolling(window=ma,center=False).mean()
    
st.text('Скользящие средние:')
st.line_chart(history[['Adj Close**','MA for 10 days','MA for 20 days','MA for 30 days']])
