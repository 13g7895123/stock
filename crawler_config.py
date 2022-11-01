import os

# 取得當前路徑
now_path = os.getcwd()

# 確認檔案存在
file_name = 'crawler_url.txt'
file_path = now_path + '\\' + file_name
if os.path.isfile(file_path):

    # 開啟檔案並讀取內容
    file = open(file_name)
    for line in file.readlines():
        signal = ': '
        now_content = line.split(signal)[0]
        if now_content == 'tpe_url':
            tpe_url = line.split(signal)[1]
        if now_content == 'otc_url':
            otc_url = line.split(signal)[1]
    file.close()

