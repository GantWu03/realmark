from langchain_core.prompts import ChatPromptTemplate
from app.schema.state import GraphState
from app.model.qwen import get_qwen_llm

llm = get_qwen_llm(temperature=0)

# 简化后的 Prompt：不再要求 LLM 输出 next_action，只生成解释文本
planner_prompt = ChatPromptTemplate.from_template("""
你是一个产品测评推荐 AI 的 Planner Agent。

用户需求：{query}

当前阶段：{stage}

请生成一句话，简洁说明当前系统正在做什么。
例如：
- "正在为您抓取 iPhone 15 的用户评论..."
- "正在分析两款产品的优缺点对比..."
- "已完成测评，为您生成推荐建议。"

""")

async def planner_node(state: GraphState) -> GraphState:
    print("🧠 Planner Agent 正在决策...")

    raw_data = state.get("raw_data", [])
    final_result = state.get("final_answer")

    # 1️⃣ 代码决定 Stage (硬逻辑，绝对安全)
    if final_result and isinstance(final_result, dict) and "error" not in final_result:
        stage = "end"
        action = "end"
    elif raw_data:
        stage = "analysis"
        action = "analysis"
    else:
        stage = "crawling"
        action = "crawling"

    # 2️⃣ 调用 LLM 生成 Plan (纯文本，无需 JSON 解析)
    try:
        response = await llm.ainvoke(
            planner_prompt.format(query=state["query"], stage=stage)
        )
        plan_text = response.content.strip()
    except Exception as e:
        print(f"⚠️ LLM 生成 Plan 失败: {e}")
        plan_text = f"系统正在执行 {stage} 阶段。"

    # 3️⃣ 更新 State
    state["plan"] = plan_text
    state["next_action"] = action

    print(f"🧠 Planner 决策: {plan_text} -> [{action}]")
    return state