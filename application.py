import requests
import pandas as pd
from flask import Flask, render_template, request
from collections import deque
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

application = Flask(__name__)
STATIC_FOLDER = 'static'
application.config['STATIC_FOLDER'] = STATIC_FOLDER

def zapisz_wykres_kursu(df: pd.DataFrame, waluta_kod: str, filename: str):
    plt.figure(figsize=(6, 6))
    plt.plot(df['Data'], df[waluta_kod], marker='o', linestyle='-')
    plt.title(f'Kurs {waluta_kod} (10 ostatnich notowań)')
    plt.xlabel('Data')
    plt.ylabel(f'Kurs {waluta_kod}')
    plt.grid(True)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(filename)  # Zapisanie wykresu do pliku
    plt.close()  # Zamknięcie figury, aby zwolnić pamięć


def pobierz_i_wyswietl_kursy_nbp_html(code_from: str, code_to: str, topcount: int = 10, table: str = "A") -> str:

    df_from = None
    df_to = None

    url_nbp_from = f"https://api.nbp.pl/api/exchangerates/rates/{table}/{code_from}/last/{topcount}/?format=json"
    url_nbp_to = f"https://api.nbp.pl/api/exchangerates/rates/{table}/{code_to}/last/{topcount}/?format=json"

    code_kurs = code_from + "/" + code_to

    try:
        if code_from[0:3] != "PLN":
            response_url_nbp_from = requests.get(url_nbp_from)
            response_url_nbp_from.raise_for_status()  # Rzuć wyjątek dla nieudanych odpowiedzi (status code != 200)
            data_url_nbp_from = response_url_nbp_from.json()
            df_from = pd.DataFrame(data_url_nbp_from['rates'])
            df_from['effectiveDate'] = pd.to_datetime(df_from['effectiveDate'])
            df_from = df_from.sort_values(by='effectiveDate', ascending=False)

        if code_to[0:3] != "PLN":
            response_url_nbp_to = requests.get(url_nbp_to)
            response_url_nbp_to.raise_for_status()  # Rzuć wyjątek dla nieudanych odpowiedzi (status code != 200)
            data_url_nbp_to = response_url_nbp_to.json()
            df_to = pd.DataFrame(data_url_nbp_to['rates'])
            df_to['effectiveDate'] = pd.to_datetime(df_to['effectiveDate'])
            df_to = df_to.sort_values(by='effectiveDate', ascending=False)


        if code_from[0:3] != "PLN" and code_to[0:3] != "PLN":
            df_polaczony = pd.merge(df_from, df_to, left_index=True, right_index=True, how='inner')
            df_polaczony['kurs'] = df_polaczony['mid_x'] / df_polaczony['mid_y']
            df_html_kurs = df_polaczony[['effectiveDate_x', 'kurs']].rename(
                columns={'effectiveDate_x': 'Data', 'kurs': code_kurs})
            print(df_html_kurs)

        elif code_from[0:3] != "PLN" and code_to[0:3] == "PLN":
            df_from['kurs'] = df_from['mid'] / 1
            df_html_kurs = df_from[['effectiveDate', 'kurs']].rename(
                columns={'effectiveDate': 'Data', 'kurs': code_kurs})
            print(df_html_kurs)

        else: # code_from[0:3] == "PLN" and code_to[0:3] != "PLN":
            df_to['kurs'] = 1 / df_to['mid']
            df_html_kurs = df_to[['effectiveDate', 'kurs']].rename(
                columns={'effectiveDate': 'Data', 'kurs': code_kurs})
            print(df_html_kurs)

        filename = os.path.join(application.config['STATIC_FOLDER'], f'kurs.png')
        zapisz_wykres_kursu(df_html_kurs, code_kurs, filename)

        tabela_html = df_html_kurs.to_html(index=False, classes=['table', 'text-center-table'])
        return tabela_html

    except requests.exceptions.RequestException as e:
        print(f"Błąd pobierania danych z NBP dla kodu {code_to}: {e}")
        return ""
    except KeyError as e:
        print(f"Błąd parsowania danych JSON dla kodu {code_to}: Brak klucza {e}")
        return ""



def polacz_code_currency(row):
    return f"{row['code']} - {row['currency']}"



ostatnie_przeliczenia = deque(maxlen=6)

@application.route('/', methods=['GET', 'POST'])
def index():
    global ostatnie_przeliczenia
    url_currency = "https://api.nbp.pl/api/exchangerates/tables/A/?format=json"
    response_url_currency = requests.get(url_currency)
    if response_url_currency.status_code == 200:
        data_url_currency = response_url_currency.json()
    else:
        raise Exception("Nie udało się pobrać danych")

    df = pd.DataFrame(data_url_currency[0]['rates'])
    df['code_pelny'] = df.apply(polacz_code_currency, axis=1)
    df['code'] = df['code_pelny']
    df = df.drop(columns=['code_pelny'])
    nbp_date = data_url_currency[0]['effectiveDate']
    raw_currency_data = df[['code', 'mid']].to_dict()
    currency_data = {}
    for index, code in raw_currency_data['code'].items():
        if index in raw_currency_data['mid']:
            currency_data[code] = raw_currency_data['mid'][index]
    currency_data["PLN - polski złoty"] = 1
    # print(currency_data)
    currency_list = list(currency_data.keys())
    selected_currency_to = 'EUR - euro'
    selected_currency_from = 'PLN - polski złoty'
    podsumowanie = None
    tabela_html = None
    wykres_url = None

    if request.method == 'GET':
        ostatnie_przeliczenia = deque(maxlen=6)  # Resetuj globalną kolejkę

    if request.method == 'POST':
        # pobranie Kwoty
        selected_ammount = float(request.form['kwota'])
        # pobranie wybranej waluty od i jej kursu
        selected_currency_from = request.form['waluta_z']
        val_currency_from = float(currency_data[selected_currency_from])
        # pobranie wybranej waluty do i jej kursu
        selected_currency_to = request.form['waluta_do']
        val_currency_to = float(currency_data[selected_currency_to])
        # obliczenie wyniku i utworzenie stringa do wyświetlenia
        sum_ammount = selected_ammount * val_currency_from / val_currency_to
        wynik_przeliczenia = f"{selected_ammount:.2f} {selected_currency_from[0:3]} = {sum_ammount:.2f} {selected_currency_to[0:3]}"
        # obliczenie kursu do podsumowania i utworzenie stringa do wyświetlenia
        sum_ammount = 1 * val_currency_from / val_currency_to
        podsumowanie = f"{1:.2f} {selected_currency_from[0:3]} = {sum_ammount:.2f} {selected_currency_to[0:3]}, wg kursu NBP z dnia {nbp_date}"
        # dodanie wyniku do listy ostatnich przeliczeń
        ostatnie_przeliczenia.appendleft(wynik_przeliczenia)
        # przygotowanie tabeli do historii i przypisanie nazwy pliku wykresu
        tabela_html = pobierz_i_wyswietl_kursy_nbp_html(selected_currency_from[0:3], selected_currency_to[0:3])
        wykres_url='kurs.png'

    return render_template('index.html', currencies=currency_list, text=list(ostatnie_przeliczenia),
                           sel_cur_to=selected_currency_to, sel_cur_from=selected_currency_from, summary=podsumowanie,
                           tab_html=tabela_html, wykres_url=wykres_url)


if __name__ == '__main__':
    application.run(debug=True)