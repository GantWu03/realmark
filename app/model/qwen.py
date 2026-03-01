import os
from langchain_openai import ChatOpenAI


def get_qwen_llm(temperature: float = 0.7) -> ChatOpenAI:
    """
    初始化通义千问模型

    Returns:
        ChatOpenAI: 配置好的模型实例
    """
    api_key = os.environ.get("DASHSCOPE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "❌ 缺少 DASHSCOPE_API_KEY 环境变量，请先配置阿里云百炼 API Key"
        )

    return ChatOpenAI(
        model="qwen3-max",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=temperature,
        api_key=api_key  # ✅ 使用原生参数名，符合 langchain-openai 规范
    )