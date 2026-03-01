from typing import Literal
from langgraph.graph import StateGraph, END
from app.schema.state import GraphState
from app.agent.planner import planner_node
from app.agent.crawling import crawling_node
from app.agent.analysis import analysis_node

def decide_next_step(state: GraphState) -> Literal["crawler", "analysis", "end"]:
    next_action = state.get("next_action", "crawling")
    print("🔀 routing by next_action =", next_action)
    if next_action == "crawling":
        return "crawler"
    elif next_action == "analysis":
        return "analysis"
    elif next_action == "end":
        return "end"
    else:
        return "end"

def create_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("crawler", crawling_node)
    workflow.add_node("analysis", analysis_node)

    workflow.set_entry_point("planner")

    workflow.add_conditional_edges(
        "planner",
        decide_next_step,
        {
            "crawler": "crawler",
            "analysis": "analysis",
            "end": END
        }
    )

    workflow.add_edge("crawler", "planner")
    workflow.add_edge("analysis", "planner")

    return workflow.compile()