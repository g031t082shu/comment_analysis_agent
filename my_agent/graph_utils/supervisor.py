from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from pydantic import BaseModel, Field

from my_agent.graph_utils.agent_member import *
# from agent_member import *

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

# system_prompt = (
#     "あなたは以下のエージェント間の会話を管理するスーパーバイザーです。"
#     "{members}"
#     "ユーザーからの質問に応じて、次に行動するエージェントを決定してください。"
#     "各エージェントはタスクを実行し、その結果とステータスを応答します。"
#     "処理が終了したら FINISHを応答してください。"
#     "なお、回答を生成する際、１つのエージェントのみでの回答が難しい場合は、複数のエージェントを使用することを検討してください。"
#     "例えば以下のようなタスクは２つのエージェントを使用した方がより適切な回答を生成することができます："
#     "入力：コメントをポジティブ、ネガティブ、中立の３つに分類し、グラフ表示してください。"
#     "上記の入力例では以下の手順で処理すると適切な回答を得ることができます。"
#     "1. analyzer_by_llmを用いてコメントを分類"
#     "2. 1での分類結果をもとに、analyzer_by_codeを用いてグラフを生成する"   
#     ""
# )


system_prompt = (
    "あなたは以下のエージェント間の会話を管理するスーパーバイザーです。"
    "{members}"
    "ユーザーからの質問に応じて、次に行動するエージェントを決定してください。"
    "各エージェントはタスクを実行し、その結果とステータスを応答します。"
    "処理が終了したら FINISHを応答してください。"  
    ""
)


class routeResponse(BaseModel):
    """
    Next Workder.
    """
    next : str = Field(..., description=f'次に実行するべきエージェント。エージェントは次から選んでください:{options}')

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "上記の会話を踏まえて、次にどのエージェントを実行するべきか、以下から選んでください。"
            "{options}"
            "なお、結果がユーザーの質問を満たすと判断した場合は、FINISHを選択してください。"
            "また、以下の事項に注意してください。"
            "・不必要にエージェントを実行しないでください。。"
            "・必ずユーザーの質問に応じた結果を出力するようにしてください。。"
        ),
    ]
).partial(options=options, members=members)

# function_def
supervisor_chain = (
        prompt | _llm.with_structured_output(routeResponse)
)

def supervisor_node(state):
    # print(state['messages'])
    res = supervisor_chain.invoke(state).model_dump()
    print(res)
    return res


# {'next': 'Comments_Summariser'}




