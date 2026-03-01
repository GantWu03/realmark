import json
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from app.schema.state import GraphState
from app.model.qwen import get_qwen_llm
from app.mcp_client.xhs_client import xhs_client

# 初始化千问模型
llm = get_qwen_llm(temperature=0)

# Crawling Agent Prompt：只负责识别产品关键词
crawling_prompt = ChatPromptTemplate.from_template("""
你是一个产品测评推荐 AI 的 Crawling Agent。

用户需求：
{query}

你的任务：
1. 识别出用户想了解或对比的所有具体产品名称
2. 只输出产品名称，不要解释

请严格输出 JSON，不要输出多余内容：
{{
  "keywords": ["产品A", "产品B"],
  "plan": "一句话说明识别出的产品"
}}
""")

def _clean_json_response(text: str) -> str:
    """清理 LLM 输出中的 Markdown 包裹"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

async def crawling_node(state: GraphState) -> GraphState:
    print("🕷️ Crawling Agent 正在抓取评论数据...")

    query = state["query"]
    current_raw_data = state.get("raw_data", [])

    # 已抓取过的产品（用于去重）
    existing_products = {
        item.get("keyword")
        for item in current_raw_data
        if isinstance(item, dict)
    }

    # 1️⃣ 使用 LLM 提取产品关键词
    response = await llm.ainvoke(
        crawling_prompt.format(query=query)
    )

    try:
        cleaned = _clean_json_response(response.content)
        parsed = json.loads(cleaned)
        keywords = parsed.get("keywords", [])
        plan = parsed.get("plan", "")
    except Exception as e:
        print(f"⚠️ 关键词解析失败，回退使用原始 query: {e}")
        keywords = [query]
        plan = "解析失败，使用原始 query 作为关键词"

    print(f"📋 Crawling 计划: {plan}")
    print(f"🔍 识别到的产品关键词: {keywords}")

    new_data = []

    # 2️⃣ 遍历关键词，调用 MCP 抓取数据
    for keyword in keywords:
        if keyword in existing_products:
            print(f"⏭️ 已存在数据，跳过: {keyword}")
            continue

        print(f"📡 抓取产品: {keyword}")

        # A. 搜索相关笔记
        search_results = await xhs_client.search_notes(keyword, limit=2)

        if not search_results:
            print(f"⚠️ 未找到相关笔记: {keyword}")
            continue

        comments_details = []

        # B. 获取评论
        for note in search_results:
            url = note.get("url")
            if not url:
                continue

            comments = await xhs_client.get_note_comments(url)
            comments_details.append({
                "note_url": url,
                "raw_comment_text": comments.get("comments_text", "")
            })

            await asyncio.sleep(5)  # 简单防反爬

        product_data = {
            "keyword": keyword,
            "notes_count": len(search_results),
            "comments_details": comments_details
        }

        new_data.append(product_data)

    # 3️⃣ 更新 State（只写事实，不做流程决策）
    state["raw_data"] = current_raw_data + new_data
    state["plan"] = f"已抓取 {len(new_data)} 个产品的评论数据。"

    return state
