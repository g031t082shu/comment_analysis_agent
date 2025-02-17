import langgraph
import pandas as pd
from langgraph.graph import StateGraph, END
from my_agent.graph_utils.state import AgentState
from my_agent.graph_utils.nodes import *
from my_agent.graph_utils.supervisor import supervisor_node
from my_agent.graph_utils.agent_member import *
from my_agent.lib.db_utils import create_db_from_df
from langgraph.checkpoint.memory import MemorySaver
from my_agent.lib.db_utils import DB_PATH

# from graph_utils.state import AgentState
# from graph_utils.nodes import *
# from graph_utils.supervisor import supervisor_node
# from graph_utils.agent_member import *
# from lib.db_utils import create_db

def create_comment_analysis_agent(df: pd.DataFrame = pd.DataFrame()):
    if df.empty == False:
        create_db_from_df(DB_PATH, df)

    # ワークフローの作成
    workflow = StateGraph(AgentState)
    workflow.add_node("analyzer_by_llm", analyzer_by_llm_node)
    workflow.add_node("analyzer_by_code", analyzer_by_code_node)
    # workflow.add_node('SQL_Agent', sql_agent_node)
    workflow.add_node("supervisor", supervisor_node)    

    # エッジの作成
    for member in list(members.keys()):
        # We want our workers to ALWAYS "report back" to the supervisor when done
        workflow.add_edge(member, "supervisor") # add one edge for each of the agents

    # 条件分岐のエッジを作成
    # The supervisor populates the "next" field in the graph state
    # which routes to a node or finishes
    conditional_map = {k: k for k in list(members.keys())}
    conditional_map["FINISH"] = END
    workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)

    # エントリーポイントの設定
    workflow.set_entry_point("supervisor")

    memory = MemorySaver()

    # ワークフローをコンパイルする
    graph = workflow.compile(checkpointer=memory)

    return graph


