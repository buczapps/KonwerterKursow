import requests
import pandas as pd
import json
from flask import Flask


application = Flask(__name__)

table = "A"
code = "USD"
topCount = 50

url_nbp = f"https://api.nbp.pl/api/exchangerates/rates/{table}/{code}/last/{topCount}/?format=json"

response_url_nbp = requests.get(url_nbp)

if response_url_nbp.status_code == 200:
    data_url_nbp = response_url_nbp.json()
else:
    raise Exception("Nie udało się pobrać danych")

df = pd.DataFrame(data_url_nbp['rates'])

df['effectiveDate'] = pd.to_datetime(df['effectiveDate'])
df_posortowany = df.sort_values(by='effectiveDate', ascending=False)

df_html = df_posortowany[['effectiveDate', 'mid']]
tabela_html = df_html.to_html(index=False)

sredni_kurs = df["mid"].mean()

print(sredni_kurs)



@application.route('/')
def hello_world():
    text = f'<h1>Konwerter kursów walut</h1><p>Historia USD dla 50 ostatnich wpisów</p><p> { tabela_html }</p>'
    return(text)


if __name__ == '__main__':
    application.run(debug=True)