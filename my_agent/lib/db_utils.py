import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
from langchain.agents import create_openai_tools_agent
from langchain.agents.agent import AgentExecutor
from langchain_community.agent_toolkits.sql.prompt import SQL_FUNCTIONS_SUFFIX
from langchain_core.messages import AIMessage
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

load_dotenv()

DB_PATH = 'database.db'


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

class _SQLGenerateResponse(BaseModel):
    sql: str = Field(description="SQL to execute.")

def create_db_from_df(db_path: str, df: pd.DataFrame) -> SQLDatabase:
    # SQLiteデータベースに接続（ファイルがない場合は自動的に作成）
    conn = sqlite3.connect(db_path)

    # DataFrameをSQLiteのテーブルに登録
    df.to_sql('data', conn, if_exists='replace', index=False)

    # # 登録確認のためデータを取得して表示
    # result = pd.read_sql('SELECT * FROM users', conn)
    # print(result)

    # 接続を閉じる
    conn.close()

    engine = create_engine(f"sqlite:///{db_path}")

    return SQLDatabase(engine)

def create_db_agent(llm: ChatGoogleGenerativeAI, system_prompt: str):
    toolkit = SQLDatabaseToolkit(db=DB_PATH, llm=llm)
    context = toolkit.get_context()
    tools = toolkit.get_tools()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            AIMessage(content=SQL_FUNCTIONS_SUFFIX),            
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    ).partial(**context)
    
    agent = create_openai_tools_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
    agent=agent,
    tools=toolkit.get_tools(),
    verbose=True,
    )

    return agent_executor


class DBHandler():
    def __init__(self, db_path: str) -> None:
         self.DB: SQLDatabase  = SQLDatabase.from_uri(f"sqlite:///{db_path}")
         self.DB_PATH: str = db_path
         self.sql_toolkit: SQLDatabaseToolkit = SQLDatabaseToolkit(db=self.DB, llm=_llm)
         self.TABLE_INFO: str = self.sql_toolkit.get_context()['table_info']
         

    def generate_sql_from_nl(self, input: str) -> dict[str, str]:
          """
          return {"sql": "SELECT * FROM Sample;"}
          """

          query = input + "\nなお指示がない限り基本的にlimitは使わないでください。"
          chain = create_sql_query_chain(_llm, self.DB)
          res = chain.invoke({"question": query})
          sql = res.split(':')[-1]

          return {'sql': sql}
    
    def read_by_nl(self, input: str) -> pd.DataFrame:
         sql = self.generate_sql_from_nl(input)['sql']   
         
         return self.read_by_sql(sql)
    
    def read_by_sql(self, sql: str) -> pd.DataFrame:
        conn = sqlite3.connect(self.DB_PATH)
        df = pd.read_sql(sql, conn)
        conn.close()

        return df       

    def extract_sql_from_prompt(self, user_input: str) -> dict[str, str]:
        """
        return {"sql": "SELECT * FROM Sample;"}
        """

        system_prompt = """
        入力となる質問が与えられたら、質問に答えるために必要なデータを取得するSQLを生成してください。

        データベースのテーブルは以下の通りです。

        {table_info}
        
        SQLを生成する際は以下の事項に注意してください。
        ・あなたは単にデータを読み込むSQLの生成のみを行う必要があります。
        ・あなたはSQLを使ってデータをフィルタリングしようとしないでください。
        ・存在しないテーブル名やカラム名を使用してはいけません。

        以下に入力に対する良い出力と悪い出力の例を示します。

        質問例１
        質問 : ユーザーコメントを200字以内で要約してください。
        良い出力 : SELECT comment FROM table;
        悪い出力 : SELECT author, a FROM data WHERE LENGTH(a) <= 200;

        上記の悪い出力の"WHERE LENGTH(a) <= 200"はSQLに含めてはいけません。
        200字以内に要約する処理はユーザーが行います。

        質問例2
        質問：建設的なコメントとを１０個抽出してください。また、そのユーザーも表示してください。
        良い出力 :  SELECT comment, author FROM table;
        悪い出力 : SELECT a FROM data WHERE a LIKE '%良い%' OR a LIKE '%素晴らしい%' OR a LIKE '%魅力のある%';

        上記の"WHERE a LIKE '%良い%' OR a LIKE '%素晴らしい%' OR a LIKE '%魅力のある%'"はSQLに含めてはいけません。
        建設的なコメントを抽出する処理はユーザーが行います。

        {format_instructions}

        {input}

        """

        # Set up a parser + inject instructions into the prompt template.
        parser = JsonOutputParser(pydantic_object=_SQLGenerateResponse)

        prompt = PromptTemplate(
            template=system_prompt,
            input_variables=["input"],
            partial_variables={"format_instructions": parser.get_format_instructions(), 'table_info': self.TABLE_INFO},
        )

        chain = prompt | _llm | parser

        res = chain.invoke({"input": user_input})

        return {'sql': res['sql']}
    
    def extract_data_from_prompt(self, user_input: str) -> pd.DataFrame:
        sql = self.extract_sql_from_prompt(user_input)['sql']

        return self.read_by_sql(sql)
    

# df = get_comments('cajYUGxzybo')
# db = create_db(df)
db_handler = DBHandler(DB_PATH)
