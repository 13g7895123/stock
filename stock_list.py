import requests
import pandas as pd
from crawler_config import *

res = requests.get(stock_list_url)
df = pd.read_html(res.text)[0]

print(df)
