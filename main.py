import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import pyodbc
import plotly.graph_objs as go
from bs4 import BeautifulSoup

extremist = ["META"]
db = pyodbc.connect(
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)}; DBQ=C:@@@@@;')     #< -- Вставьте путь к базе данных
cursor = db.cursor()
ticker = False
ticker_list = False


def get_url(text):
    cursor.execute(f"""SELECT (title), (link)
        FROM (stocks)
        WHERE (ticker) LIKE '%{text}%'
        OR (title) LIKE '%{text}%'""")
    return list(cursor.fetchall())


def get_ticker(ticker_url):
    cursor.execute(f"""SELECT (ticker)
            FROM (stocks)
            WHERE (link) = '{ticker_url}'""")
    return cursor.fetchall()[0][0]


st.title('Анализ финансовых данных компании')
ticker_list = st.text_input("Search..", value="AAPL")
ticker_list = get_url(ticker_list)
if ticker_list:
    dc = dict(ticker_list[:10:])
    ticker_url = dc[st.radio(
        "Компании",
        dc.keys())]
    ticker = get_ticker(ticker_url)
    cursor.commit()


def load_data(url):
    r = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
    data = pd.read_html(r.text)
    return data


def load_summary_data(ticker_url):
    summary_url = ticker_url
    summary_data = load_data(summary_url)
    data = [summary_data[0], summary_data[1]]
    data = pd.concat(summary_data)
    data.reset_index(drop=True, inplace=True)
    return data[:8:], data[8::]


def load_historical_data(ticker_url):
    historiscal_data = load_data(ticker_url.replace("?", "/history?"))
    data = historiscal_data[0]
    data = data.iloc[:-1, :]
    data = data[data["Open"].str.contains("Dividend") == False]
    data['Date'] = pd.to_datetime(data['Date'])
    numeric_columns = list(data.columns)[1::]
    for column_name in numeric_columns:
        data[column_name] = data[column_name].str.replace(',', '')
        data[column_name] = data[column_name].astype(np.float64)

    data.set_index('Date', inplace=True)
    data = data.reindex(index=data.index[::-1])
    return data


def load_statistics_mult(ticker_url):
    statistics_data = load_data(ticker_url.replace("?", "/key-statistics?"))
    data = statistics_data[0]
    data = data.iloc[:-1, :]
    data.reset_index(drop=True, inplace=True)
    df = data.transpose()
    df.columns = df.iloc[0]
    df = df.drop(0)
    df = df.reset_index(drop=True)
    return data, dict(df.to_dict())


def load_statistics_div(ticker_url):
    try:
        statistics_data = load_data(ticker_url.replace("?", "/key-statistics?"))
        data = statistics_data[2]
        data = data.iloc[:-1, :]
        data.reset_index(drop=True, inplace=True)
        return data
    except:
        return "Информации о дивидендах компании нет"


def load_analysys_data(df):
    analys = []
    if df.get('Trailing P/E'):
        if float(df['Trailing P/E'][0]) > 16:
            analys += ['По маркеру P/E (Цена (Price)/Чистая прибыль (Earnings Ratio)) компания переоценена.']
        elif 12 <= df.get(float(df['Trailing P/E'][0])) <= 15:
            analys += ['По маркеру P/E (Цена (Price)/Чистая прибыль (Earnings Ratio)) компания оценена справедливо.']
        elif df.get(float(df['Trailing P/E'][0])) < 12:
            analys += ['По маркеру P/E (Цена (Price)/Чистая прибыль (Earnings Ratio)) компания недооценена.']
    if df.get('Price/Sales (ttm)'):
        if 1 < float(df['Price/Sales (ttm)'][0]) <= 2:
            analys += ['По маркеру P/S (Рыночная стоимость компании (Price)/Объем продаж (Sales)) компания быстро окупается и соответствует своей цене.']
        elif float(df['Price/Sales (ttm)'][0]) >= 2:
            analys += ['По маркеру P/S (Рыночная стоимость компании (Price)/Объем продаж (Sales)) компания медленно окупается и переоценена.']
        elif float(df['Price/Sales (ttm)'][0]) <= 1:
            analys += ['По маркеру P/S (Рыночная стоимость компании (Price)/Объем продаж (Sales)) компания очень быстро окупается и недооценена.']
    if df.get('Price/Book (mrq)'):
        if float(df['Price/Book (mrq)'][0]) < 1:
            analys += ['По маркеру P/B (Рыночная стоимость компании (Price)/Балансовая стоимость активов компании (Book)) компания недоооценена.']
        elif float(df['Price/Book (mrq)'][0]) > 5:
            analys += ['По маркеру P/B (Рыночная стоимость компании (Price)/Балансовая стоимость активов компании (Book)) компания переоценена.']
        elif 1 < float(df['Price/Book (mrq)'][0]) < 5:
            analys += ['По маркеру P/B (Рыночная стоимость компании (Price)/Балансовая стоимость активов компании (Book)) компания соответствует своей цене.']
    if df.get('Enterprise Value/Revenue'):
        if float(df['Enterprise Value/Revenue'][0]) < 0:
            analys += ['По маркеру PEG P(Market Cap (Капитализация))/E (Earnings(Чистая прибыль))/EGR (Годовой прогноз EPS(Earnings Per Share(ожидаемый рост прибыли на акцию)) компания имеет отрицательную чистую прибыль. Критерий не может адекватно оценить ее потенциал.']
        elif 0 < float(df['Enterprise Value/Revenue'][0]) < 1:
            analys += ['По маркеру PEG P(Market Cap (Капитализация))/E (Earnings(Чистая прибыль))/EGR (Годовой прогноз EPS(Earnings Per Share(ожидаемый рост прибыли на акцию)) компания недооценена инвестиционно, это привлекательно для инвестора.']
        elif 3 > float(df['Enterprise Value/Revenue'][0]) > 1:
            analys += ['По маркеру PEG P(Market Cap (Капитализация))/E (Earnings(Чистая прибыль))/EGR (Годовой прогноз EPS(Earnings Per Share(ожидаемый рост прибыли на акцию)) компания оценена оптимально.']
        elif float(df['Enterprise Value/Revenue'][0]) > 3:
            analys += ['По маркеру PEG P(Market Cap (Капитализация))/E (Earnings(Чистая прибыль))/EGR (Годовой прогноз EPS(Earnings Per Share(ожидаемый рост прибыли на акцию)) компания не привлекательная для инвестора из-за высокой перекупленности.']
    return analys

def load_SPCE(ticker_url):
    statistics_data = load_data(ticker_url)
    data = statistics_data[5][:4]
    data = data.iloc[:-1, :]
    df = data.transpose()
    return data


# загрузим общую информацию
if ticker and ticker != "SPCE":
    df1, df2 = load_summary_data(ticker_url)
    if ticker in extremist:
        st.write(f'Организация признана экстремистской и запрещена на территории Российской Федерации.')
    st.subheader('Общая информация о компании')
    cl1, cl2 = st.columns(2)
    cl1.write(df1)
    cl2.write(df2)

    history = load_historical_data(ticker_url)
    statistic_mult, value = load_statistics_mult(ticker_url)
    statistic_div = load_statistics_div(ticker_url)

    st.subheader('Статистика')
    stt1, stt2 = st.columns(2)
    with stt1:
        stt1 = st.expander('Мультипликаторы')
        stt1.write(statistic_mult)
    with stt2:
        stt2 = st.expander('Дивиденды')
        stt2.write(statistic_div)

    st.subheader('Историческая информация')
    st.text('Изменение биржевых котировок:')
    st.line_chart(history['Adj Close**'])

    st.text('Изменение объема торгов:')
    st.line_chart(history['Volume'])

    ma_day = number = st.slider("Выберите промежуток дней", 1, 30)

    column_name = "MA for %s days" % (str(ma_day))
    history[column_name] = history['Adj Close**'].rolling(window=ma_day, center=True).mean()

    st.text('Скользящая средняя:')
    st.line_chart(history[['Adj Close**', 'MA for %s days' % (str(ma_day))]])

    st.subheader('Финальная аналитика компании')
    for i in load_analysys_data(value):
        st.write(i)

elif ticker == "SPCE":
    st.write(load_SPCE(ticker_url))