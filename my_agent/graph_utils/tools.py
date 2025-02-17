import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from langchain_experimental.tools import PythonREPLTool
from langchain_core.tools import tool
from dotenv import load_dotenv
from lib.db_utils import db_handler
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
from langchain_experimental.utilities import PythonREPL
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_google_genai import ChatGoogleGenerativeAI
from lib.db_utils import db_handler

# Import things that are needed generically
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool

from my_agent.lib.mr_data_analyzer2 import mr_data_analyzer

load_dotenv()

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


# This executes code locally, which can be unsafe
# pythonを実行するツール
# from langchain_experimental.tools import PythonREPLTool
# python_repl_tool = PythonREPLTool()

# This executes code locally, which can be unsafe
# pythonを実行するツール
# python_repl_tool = PythonREPLTool()

repl = PythonREPL()

sql_toolkit = SQLDatabaseToolkit(db=db_handler.DB, llm=_llm)

@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute."],
):
    """Use this to execute python code and do math. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"
    return result_str


# -----comments summariserで使うツール------

@tool("analysis_by_llm_tool", return_direct=False)
def analysis_by_llm_tool(input: str) -> str:
    """
    データベースのデータをLLMを用いて分析します。
    """

    return mr_data_analyzer.invoke(input).content

# def _analysis_by_llm(user_input: str) -> str:
#     """
#     データベースのデータをLLMを用いて分析します。
#     """

#     return mr_data_analyzer.invoke(user_input).content

# class _AnalysisByLlmToolInput(BaseModel):
#     user_input: str = Field(description="shold be a user's question of text")

# analysis_by_llm_tool = StructuredTool.from_function(
#     func=_analysis_by_llm,
#     name="analysis_by_llm_tool",
#     description="データベースのデータをLLMを用いて分析します。",
#     args_schema=_AnalysisByLlmToolInput,
#     return_direct=True,
# )

# @tool("display_img_tool", return_direct=False)
# def display_img_tool(img_path: str) -> None:
#     """
#     グラフや図などの画像を表示します。
#     """
#     import streamlit as st
#     st.session_state.message_history.append(("img", img_path))


analyzer_by_llm_tools = [analysis_by_llm_tool]

