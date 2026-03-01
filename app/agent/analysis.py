import json
from langchain_core.prompts import ChatPromptTemplate
from app.schema.state import GraphState
from app.model.qwen import get_qwen_llm

# 初始化千问模型
llm = get_qwen_llm(temperature=0.1)

analysis_prompt = ChatPromptTemplate.from_template("""
你是一个专业的电商产品测评分析师。

你将收到从社交媒体抓取的真实用户评论数据。

【产品列表及原始评论数据】：
{data_context}

你的任务：
1. 数据清洗：
   - 剔除明显水军评论、营销话术、AI 模板化评论
2. 观点提取：
   - 分别总结每个产品的核心优点和缺点（3–5 条）
3. 对比与推荐：
   - 给出产品之间的核心差异
   - 针对不同用户需求给出购买建议

请严格输出 JSON，不要输出任何解释或 Markdown：
{{
  "cleaning_status": "简要说明清洗情况",
  "products_analysis": [
    {{
      "name": "产品名称",
      "pros": ["优点1", "优点2"],
      "cons": ["缺点1", "缺点2"]
    }}
  ],
  "comparison_summary": "核心差异总结",
  "recommendation": "最终购买建议"
}}
""")

def _clean_json_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def _format_raw_data_for_llm(raw_data: list) -> str:
    if not raw_data:
        return "暂无数据"

    lines = []
    for item in raw_data:
        product = item.get("keyword", "未知产品")
        lines.append(f"====== 产品：{product} ======")

        comments = item.get("comments_details", [])
        if not comments:
            lines.append("(无评论)")
            continue

        for idx, block in enumerate(comments, 1):
            text = block.get("raw_comment_text", "")
            snippet = text[:2000] if text else "(空内容)"
            lines.append(f"[评论块 {idx}] {snippet}\n")

    return "\n".join(lines)

async def analysis_node(state: GraphState) -> GraphState:
    print("📊 Analysis Agent 正在分析评论数据...")

    raw_data = state.get("raw_data", [])
    data_context = _format_raw_data_for_llm(raw_data)

    if data_context == "暂无数据":
        state["plan"] = "没有可分析的数据，跳过分析阶段。"
        return state

    try:
        response = await llm.ainvoke(
            analysis_prompt.format(data_context=data_context)
        )

        cleaned = _clean_json_response(response.content)
        analysis_result = json.loads(cleaned)

        # ✅ 将分析结果写入 final_answer（供 Planner 或直接返回用户）
        state["final_answer"] = analysis_result
        state["plan"] = "评论分析完成，已生成结构化对比与推荐。"

        print("✅ Analysis Agent 完成分析")

    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 解析失败: {e}")
        state["final_answer"] = {
            "error": "分析失败，模型返回格式异常"
        }
        state["plan"] = "分析阶段失败。"

    except Exception as e:
        print(f"⚠️ Analysis Agent 异常: {e}")
        state["final_answer"] = {
            "error": str(e)
        }
        state["plan"] = "分析阶段发生异常。"

    return state
