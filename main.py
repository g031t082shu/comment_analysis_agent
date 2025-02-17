from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Github: https://github.com/naotaka1128/llm_app_codes/chapter02/main.py
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from PIL import Image

from my_agent.agent import create_comment_analysis_agent
from my_agent.lib.get_comments3 import get_comments

###### dotenv を利用しない場合は消してください ######
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    import warnings
    warnings.warn("dotenv not found. Please make sure to set your environment variables manually.", ImportWarning)
################################################

agent = create_comment_analysis_agent()

start = True

def main():
    global start 
    global agent

    st.set_page_config(
        page_title="My Great ChatGPT",
        page_icon="🤗"
    )
    # st.header("My Great ChatGPT 🤗")

    # チャット履歴の初期化: message_history がなければ作成
    if "message_history" not in st.session_state:
        st.session_state.message_history = [
            # System Prompt を設定 ('system' はSystem Promptを意味する)
            # ("system", "You are a helpful assistant.")
        ]
        st.session_state.message_history.append(("ai", 'urlを入力してください。'))

    if (user_input := st.chat_input('YouTube動画のURLを入力してください')):
        # ユーザーの質問を履歴に追加 ('user' はユーザーの質問を意味する)
        st.session_state.message_history.append(("user", user_input))
        yt_id = user_input.split('=')[-1]
        df = get_comments(yt_id)
        agent = create_comment_analysis_agent(df)
        print(yt_id)
        st.session_state.message_history.append(("ai", 'urlが入力されました。'))
        
    # ユーザーの入力を監視
    if  (user_input := st.chat_input("データについて聞きたいことを入力してください。")):
        # ユーザーの質問を履歴に追加 ('user' はユーザーの質問を意味する)
        st.session_state.message_history.append(("user", user_input))

        with st.spinner("ChatGPT is typing ..."):
            config = {"configurable": {"thread_id": "1"}}
            response = agent.invoke(
                {
                    "messages": [

                        HumanMessage(content=user_input) 
                    ]
                },
                config,
                stream_mode="values",
            )

        # ChatGPTの回答を履歴に追加 ('assistant' はChatGPTの回答を意味する)
        st.session_state.message_history.append(("ai", response['messages'][-1].content))


    # チャット履歴の表示
    for role, message in st.session_state.get("message_history", []):
        if role == 'img':
            img = Image.open(message)
            st.chat_message('ai').image(img)
        
        else:
            st.chat_message(role).markdown(message)        

if __name__ == '__main__':
    main()
