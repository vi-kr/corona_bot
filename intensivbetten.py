import pandas
import requests
from datetime import datetime


intensiv_url = "https://diviexchange.blob.core.windows.net/%24web/bundesland-zeitreihe.csv"
r = requests.get(intensiv_url)
filename = "C:\\users\\vince\\Desktop\\betten.csv"
with open(filename,'wb') as f:
    f.write(r.content)
intensivdf = pandas.read_csv(filename).dropna()
intensivdf.Datum = intensivdf.Datum.map(lambda cell: datetime.strptime(cell[:-6], "%Y-%m-%dT%H:%M:%S"))
