import requests
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
from crawler_config import *


# PANDAS顯示所有列
pd.set_option('display.max_rows', None)


def get_stock_dataframe(url):
    res = requests.get(url)
    df = pd.read_html(res.text)[0]

    # 設定column名稱
    df.columns = df.iloc[0]

    # 刪除第一行
    df = df.iloc[1:]

    # 拔掉不需要的欄位
    df = df.drop(['頁面編號', '國際證券編碼', '有價證券別', 'CFICode', '備註'], axis=1)

    # 修改欄位名稱
    df.columns = ['sid', 'name', 'market', 'industry', 'listed_date']

    return df


def stock_list():
    # 取得各自DATAFRAME
    tpe_df = get_stock_dataframe(tpe_url)
    otc_df = get_stock_dataframe(otc_url)

    # 合併DATAFRAME
    tpe_otc_df = pd.concat([tpe_df, otc_df])
    tpe_otc_df = tpe_otc_df.sort_values(by='sid')

    # 更新進資料庫
    engine = create_engine('mysql://stock_remote:820820@139.162.15.125:3306/db_stock', echo=False)
    tpe_otc_df.to_sql(name='stock_list', con=engine, if_exists='append', index=False)


stock_list()
