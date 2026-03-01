
from typing import List, Dict, TypedDict, Literal

class GraphState(TypedDict):
    query: str
    current_agent: Literal[
        "planner",
        "analysis",
        "crawler",
        "end"
    ]                                   # 当前应执行的 agent
    next_action: Literal[
        "analysis",
        "crawling",
        "end"
    ]
    plan: str                           # Planner 的 reasoning / 决策说明
    raw_data: List[Dict]                # Crawling Agent 抓取的原始评论
    final_answer: str                   # 最终返回给用户的内容
