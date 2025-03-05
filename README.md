# 概要
「ソーシャルメディアにおけるコメントデータの分析を行うLLMマルチエージェントの提案」において述べているLLMマルチエージェントのプログラムです。streamlitのウェブアプリのデモを試せます。

# 注意
pythonのバージョンは3.11.0を必ず使用する

# 使い方
ターミナルで以下のコマンドを実行
1. $python3 -m venv venv
2. $pip3 install -r requirements.txt<br>
-------仮想環境が用意できている場合はここから下-------
3. $touch .env
4. .envに以下の値を設定<br>
OPENAI_API_KEY = YOUR API KEY<br>
YOUTUBE_DEVELOPER_KEY = YOUR API KEY
------api keyの設定ができている場合はこのコマンドだけ実行-----
5. $streamlit run main.py
