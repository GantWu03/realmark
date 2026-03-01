import os
import json
import asyncio
import sys

# ⚡ Windows 环境修复
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 1️⃣ 使用你提供的 MultiServerMCPClient
from langchain_mcp_adapters.client import MultiServerMCPClient


class XHSClient:
    def __init__(self):
        self.mcp_client = None
        self.tools = []

    async def connect(self, timeout=60):
        """连接 MCP 服务端"""


        servers_cfg = {
            "xiaohongshu MCP": {
                "transport": "stdio",
                "command": "D:\\software\\python\\MyProject\\ai-agent-test\\.venv\\Scripts\\python.exe",
                "args": ["D:\\software\\python\MyProject\\ai-agent-test\\realmark\\mcp_server\\xiaohongshu\\server.py", "--stdio"],
                "env": {**os.environ}
            }
        }

        try:
            print("🔄 正在通过 MultiServerMCPClient 初始化连接...")

            # 初始化客户端（直接实例化，无需 async with）
            self.mcp_client = MultiServerMCPClient(servers_cfg)

            # 获取工具（此时内部会建立连接）
            self.tools = await asyncio.wait_for(
                self.mcp_client.get_tools(),
                timeout=timeout
            )

            print(f"✅ MCP Client 已连接，成功加载 {len(self.tools)} 个工具")
            print(f"🛠️ 可用工具: {[t.name for t in self.tools]}")

        except asyncio.TimeoutError:
            print("❌ 连接 MCP 服务端超时")
            self.mcp_client = None
            raise
        except Exception as e:
            print(f"❌ 连接 MCP 服务端失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.mcp_client = None
            raise

    async def _ensure_connected(self):
        """确保连接已建立"""
        if self.mcp_client is None:
            await self.connect()

    async def search_notes(self, keyword: str, limit: int = 2) -> list:
        """调用 search_notes 工具"""
        await self._ensure_connected()

        tool = next((t for t in self.tools if t.name == "search_notes"), None)

        if not tool:
            print("❌ 未在 MCP 服务中找到 search_notes 工具")
            return []

        try:
            result = await asyncio.wait_for(
                tool.ainvoke({"keywords": keyword, "limit": limit}),
                timeout=300  # 之前建议你加大的超时时间
            )

            # ✅ 新增：适配 langchain-mcp-adapters 返回的列表格式
            # result 可能是: [{'type': 'text', 'text': '{...json...}'}]
            result_text = ""
            if isinstance(result, list):
                for item in result:
                    if item.get("type") == "text":
                        result_text = item.get("text", "")
                        break
            else:
                result_text = result if isinstance(result, str) else str(result)

            try:
                data = json.loads(result_text)
                notes = data.get("notes", [])
                return [{"url": note["url"]} for note in notes]
            except json.JSONDecodeError:
                print(f"⚠️ 解析 search_notes 返回的 JSON 失败: {result_text[:100]}")
                return []

        except Exception as e:
            print(f"❌ MCP 调用 search_notes 失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_note_comments(self, url: str) -> dict:
        """调用 get_note_comments 工具"""
        await self._ensure_connected()

        tool = next((t for t in self.tools if t.name == "get_note_comments"), None)

        if not tool:
            print("❌ 未在 MCP 服务中找到 get_note_comments 工具")
            return {"comments_text": ""}

        try:
            result = await asyncio.wait_for(
                tool.ainvoke({"url": url}),
                timeout=120
            )

            result_text = result if isinstance(result, str) else str(result)

            return {
                "url": url,
                "comments_text": result_text
            }

        except Exception as e:
            print(f"❌ MCP 调用 get_note_comments 失败: {e}")
            return {"comments_text": ""}

    async def close(self):
        """关闭连接"""
        if self.mcp_client:
            # if hasattr(self.mcp_client, '__aexit__'):
            #     await self.mcp_client.__aexit__(None, None, None)
            # elif hasattr(self.mcp_client, 'close'):
            #     await self.mcp_client.close()
            # self.mcp_client = None
            # print("🔌 MCP Client 连接已关闭")

            print("🔌 MCP Client 引用已释放 (底层进程将随程序退出自动清理)")
            self.mcp_client = None
            self._tools_map.clear()

# 全局单例
xhs_client = XHSClient()