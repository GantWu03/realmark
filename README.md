# realmark

realmark 是一个 AI 驱动的产品测评与推荐系统。

## 核心能力
- 自动抓取社交媒体（小红书）真实用户评论（基于 MCP Server）
- 利用大模型对评论进行清洗、去水军、去 AI 评论
- 对比多个产品的优缺点并给出推荐结论

## 技术架构
- 多智能体架构（Planner / Crawling / Analysis）
- LangGraph 用于 Agent 调度与状态管理
- MCP（Model Context Protocol）用于外部能力接入
- 千问 Qwen3-Max 作为核心推理模型

## 当前状态
- [x] MCP Server（小红书）已接入
- [ ] MCP Client（Python）开发中
- [ ] Planner Agent
- [ ] Crawling Agent
- [ ] Analysis Agent
- [ ] Web / CLI 交互界面

## 运行环境
- Python >= 3.10（推荐 3.11）
