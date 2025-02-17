from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import  BaseMessage
import google.generativeai as genai
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from my_agent.lib.db_utils import DBHandler
import pandas as pd
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI
import tiktoken
from tiktoken.core import Encoding
from my_agent.lib.db_utils import DB_PATH

# _model_name = "models/gemini-1.5-flash"
_model_name = "gpt-4o-mini-2024-07-18"
_input_token_limit = 128000

load_dotenv()

_llm = ChatOpenAI(model=_model_name, temperature=0)
# _llm = ChatGoogleGenerativeAI(
#     model=_model_name.split('/')[1],
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
#     # convert_system_message_to_human=True
#     # other params...
# )
# genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# _model_info = genai.get_model(_model_name)
# # (model_info.input_token_limit, model_info.output_token_limit)


class MrDataAnalyzer():
    def __init__(self, db_path: str):
        self.DB_PATH = db_path
        self._DB_HANDLER = DBHandler(db_path)

    def _calc_tokens(self, text: str) -> int:
        encoding: Encoding = tiktoken.encoding_for_model(_model_name)
        tokens = encoding.encode(text)
        tokens_count = len(tokens)

        return  tokens_count

    def _calc_data_per_chank(self, data: list) ->int:
        # 全コメントのトークン数を計算
        tokens = self._calc_tokens(f'{data}')

        if tokens < _input_token_limit:
            return len(data)
        else:
            # １コメントあたりの平均トークン数を計算
            tokens_per_data = tokens / len(data)
            # 1チャンクあたりのコメント数を計算
            # comments_per_chunk = int(len(comments) / tokens_per_comment)
            max_token = int(int(_input_token_limit) * 0.6)
            data_num_per_chunk = int(max_token / tokens_per_data)
            
            return data_num_per_chunk

    def _map(self, user_inpuut: str, data: list) -> BaseMessage:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "あなたはデータ分析の専門家です。あなたにはこれから分析すべきデータとユーザーからの質問が与えられるので、ユーザーの要求を満たす結果を出力してください。"),
            ("user", "質問 : {question}"
                    "データ : {data}")
        ])

        chain = prompt | _llm

        return chain.invoke({"question": user_inpuut, 'data': data})

    def _map_combine(self, user_input: str, texts,) -> BaseMessage:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "あなたの仕事は、与えられたテキストのリストを要約し適切な結果を出力することです。"
                       "あなたには以下の形式でテキストのリストが与えられます。"
                       "[text1, text2, text3, ...]"
                       "なお、出力結果は以下のユーザーからの質問の要求を満たす必要があることに注意してください。"
                       "質問：{question}"),
            ("user", "{texts}")
        ])

        chain = prompt | _llm

        return chain.invoke({"question": user_input, 'texts': texts, })


    def invoke(self, input: str) -> BaseMessage:
        maps: list[str] = []        
        data = self._DB_HANDLER.extract_data_from_prompt(input).to_numpy().tolist()  
        data_per_chank = self._calc_data_per_chank(data) # １チャンクあたりのデータ数

        # map処理
        for i in range(0, len(data), data_per_chank):
            res = self._map(input, data[i: i+data_per_chank]) # チャンクをLLMに入力し結果を得る
            maps.append(res.content)

        # collapse処理
        collapse_texts: list[str] = maps.copy()
        while 1:
            print('collapase')
            texts_token = self._calc_tokens(f"{collapse_texts}")
            if texts_token < _input_token_limit:
                break
            else:
                summaries: list[str] = []
                data_per_chank = self._calc_data_per_chank(f"{collapse_texts}")

                for i in range(0, len(collapse_texts), data_per_chank):
                    res = self._map_combine(input, collapse_texts[i: i+data_per_chank])
                    summaries.append(res.content)

                collapse_texts = summaries

        # reduce処理
        summary = self._map_combine(input, collapse_texts)

        return summary

mr_data_analyzer = MrDataAnalyzer(DB_PATH)

        





