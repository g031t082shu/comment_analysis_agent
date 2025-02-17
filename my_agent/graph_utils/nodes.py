from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

import functools

from my_agent.graph_utils.tools import *
from my_agent.lib.db_utils import *

# from tools import *
# from lib.db_utils import *

_llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18", temperature=0)

# _llm = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
#     # convert_system_message_to_human=True
#     # other params...
# )

def _create_agent(llm: ChatOpenAI, tools: list, system_prompt: str):
    # Each worker node will be given a name and some tools.
    
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),  # ユーザーからの質問とllmからの出力の履歴がここに入る
            MessagesPlaceholder(variable_name="agent_scratchpad"), # agent_scratchpad：アクションとツールの出力メッセージを保存しておくために必要
        ]
    )
    agent = create_openai_tools_agent(llm, tools, prompt, )
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return executor

# agent node
def _agent_node(state, agent, name):
    result = agent.invoke(state)

    # print(state)

    # 最初のコードサンプルはHumanMessageになってた(正しいのはAImessageじゃないの？)
    # geminiの場合、messagesのロールはhumanから始まってai, humanと交互にする必要があるため、結局こっちが正しいかも
    # return {"messages": [HumanMessage(content=result["output"], name=name)]}
    return {"messages": [AIMessage(content=result["output"], name=name)]}



_analyzer_by_llm_agent = _create_agent(_llm, analyzer_by_llm_tools, "データベースのデータをLLMを用いて分析します。")
analyzer_by_llm_node = functools.partial(_agent_node, agent=_analyzer_by_llm_agent, name="analyzer_by_llm")

system_prompt = f"""
入力となる質問が与えられたら、質問に答えるためのpythonコードを生成し、実行して結果を返してください。
コードを生成するにあたっては、積極的に外部ライブラリを使用し、より精度の高い結果を出力できるようにしてください。

Pythonのコードを生成するにあたり、必ず以下の事項を参照してください。

・コードの中では、必要に応じて以下に示すsqlite3データベースのデータを使用することができます:
{sql_toolkit.get_context()['table_info']}

・pythonのコードを生成する際には必ず以下のコードを含めてください:
import matplotlib_fontja

・wordcloudを使用する際は以下のfont pathを設定してください:
"./Arial Unicode.ttf"

・上記のデータベースにアクセスするためのpythonコード例は以下の通りです:
import pandas as pd
import sqlite3

conn = sqlite3.connect({DB_PATH})
df = pd.read_sql('SQL Query to run', conn)
conn.close()

・結果を出力する際は以下のコード使用するようにしてください:
print(value)

・グラフや図など画像を表示する際は必ず以下のコードを全て使用してください。:
import matplotlib.pyplot as plt
import matplotlib_fontja
import datetime
import streamlit as st

now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f')
img_path = "./imgs/" + now + ".png"
plt.savefig(img_path)
st.session_state.message_history.append(("img", img_path))

・グラフや図などの画像の生成のタスクでは、最終的な回答は以下のようなテキストを出力してください:
悪い例：ワードクラウドを生成しました。画像のパスは `./imgs/20250109_103226086739.png` です。
回答に画像ファイルのパスを含める必要はありません。
良い例：ワードクラウドを生成しました。
必要な情報のみを回答として出力してください。また、必要に応じて生成されたグラフや図などの画像の説明も含めてください。

"""

# code_agent = create_agent(llm, [python_repl_tool], "データを分析し、matplotlibを使用してグラフを生成するための安全なPythonコードを生成することができます。")
_analyzer_by_code_agent = _create_agent(_llm, [python_repl_tool], system_prompt)
analyzer_by_code_node = functools.partial(_agent_node, agent=_analyzer_by_code_agent, name="analyzer_by_code")
