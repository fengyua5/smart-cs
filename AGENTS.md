# Smart CS 项目规范

## 项目概览
Smart CS 是一个基于 RAG + Ollama 本地模型的 AI 智能客服系统，支持低置信度问题自动转人工审核。

## 技术栈
- **后端**: Python FastAPI + LangChain + ChromaDB + SQLAlchemy
- **LLM**: Ollama (qwen3.5:9b 对话 / bge-m3 向量化)
- **前端**: 原生 HTML + JS
- **数据库**: SQLite
- **部署**: 本地运行，`bash start.sh` 一键启动

## 目录结构
- `backend/app/` — FastAPI 后端核心代码
  - `main.py` — 入口、路由、答案后处理
  - `config.py` — 配置（模型名、阈值等）
  - `database.py` — SQLite 数据库模型
  - `rag/` — RAG 核心（检索、生成、置信度）
  - `ingest/` — 文档入库管道
  - `review/` — 人工审核模块
- `frontend/` — 前端页面（chat.html / review.html）
- `knowledge/` — 知识文档目录

## 关键规则
1. **Prompt 修改**在 `backend/app/rag/generator.py` 的 `SYSTEM_PROMPT` 中
2. **隐私配置**在 `backend/app/config.py` 中，不支持"暂无信息""建议访问官网"等表述
3. **置信度阈值**在 `backend/app/config.py` 中调整
4. **答案后处理禁止词汇**在 `backend/app/main.py` 的 `_UNWANTED_PATTERNS` 中
5. **新文档入库**: 放入 `knowledge/` 目录后调用 `POST /api/ingest`
6. **审核 API**: `backend/app/review/router.py`

## 启动方式
```bash
bash start.sh
# 聊天: http://localhost:8000/static/chat.html
# 审核: http://localhost:8000/static/review.html
```

## 编码规范
- 遵循现有代码风格
- import 分组：标准库 → 第三方 → 本地模块
- API 响应使用 Pydantic 模型
- 注释仅标注关键逻辑
