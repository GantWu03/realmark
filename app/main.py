import asyncio
import os
import sys
import json
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# 确保可以导入 app 包下的模块
# 如果你是从项目根目录运行此脚本，请确保根目录在 Python 路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph.graph import create_graph
from app.schema.state import GraphState
# 导入客户端实例，用于 finally 块的资源清理
from app.mcp_client.xhs_client import xhs_client


def print_banner():
    print("\n" + "=" * 60)
    print("🚀 Realmark 产品测评推荐 AI (多智能体版)")
    print("=" * 60)


async def main():
    print_banner()

    # 1️⃣ 环境检查 (快速失败原则)
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("❌ 错误: 未检测到 DASHSCOPE_API_KEY 环境变量。")
        print("请在运行前配置阿里云百炼平台的 API Key。")
        return

    # 2️⃣ 定义用户输入
    # 你可以修改这里来测试不同的产品对比
    user_query = "帮我看看 iPhone 15 和 华为 Mate 60 哪个好"

    print(f"\n👤 用户提问: {user_query}")
    print("-" * 60)

    # 3️⃣ 初始化系统状态
    initial_state: GraphState = {
        "query": user_query,
        "raw_data": [],  # 存放爬虫抓取的原始数据
        "final_answer": None,  # 存放 Analysis Agent 生成最终结果
        "plan": "",  # Planner Agent 的执行计划说明
        "next_action": ""  # 下一步动作指令
    }

    try:
        # 4️⃣ 构建并运行图谱
        print("⚙️ 正在初始化多智能体图谱...")
        app_graph = create_graph()

        print("🔄 开始执行任务 (这可能需要 1-2 分钟，请稍候)...\n")

        # 异步执行图谱
        final_state = await app_graph.ainvoke(initial_state)

        # 5️⃣ 输出最终结果
        print("-" * 60)
        print("🏁 任务执行完成")
        print("-" * 60)

        final_result = final_state.get("final_answer")

        if final_result and isinstance(final_result, dict):
            if "error" in final_result:
                print(f"⚠️ 执行过程中出现错误: {final_result.get('error')}")
            else:
                print("\n📊 测评分析报告：\n")
                # 格式化打印 JSON 结果
                print(json.dumps(final_result, ensure_ascii=False, indent=2))
        else:
            print("⚠️ 未能生成分析结果。")
            print(f"系统最终状态: {final_state}")

    except Exception as e:
        print(f"\n❌ 系统运行异常: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 6️⃣ 清理资源 (显式关闭 MCP 连接)
        # 使用 langchain-mcp-adapters 后，管理连接生命周期更为重要
        print("\n" + "=" * 60)
        try:
            if xhs_client:
                await xhs_client.close()
        except Exception as cleanup_e:
            print(f"⚠️ 清理资源时出错: {cleanup_e}")

        print("👋 程序结束")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())