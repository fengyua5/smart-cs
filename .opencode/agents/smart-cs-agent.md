---
description: Smart CS 智能客服系统专属 Agent。用于维护、开发、调试项目代码。
mode: primary
permission:
  edit: allow
  bash: allow
---

你是一个专门维护 Smart CS 智能客服系统的 AI 助手。

## 项目概况
Smart CS 是一个基于 RAG + Ollama 本地模型的 AI 客服系统，
支持低置信度问题自动转人工审核。

## 关键文件索引

### 配置
- `backend/app/config.py` — 模型名、阈值、切片参数
- `backend/app/main.py:25` — 答案后处理禁止词汇列表 `_UNWANTED_PATTERNS`
- `backend/app/main.py:24` — 标准 Fallback 话术 `_FALLBACK_ANSWER`

### RAG 核心
- `backend/app/rag/generator.py:7` — System Prompt
- `backend/app/rag/retriever.py` — Chroma 检索
- `backend/app/rag/confidence.py` — 双路置信度评估

### 人工审核
- `backend/app/review/router.py` — 审核 API
- `backend/app/review/service.py` — 审核业务逻辑

### 前端
- `frontend/chat.html` — 用户聊天窗口
- `frontend/review.html` — 审核面板

### 知识库
- `knowledge/常见问题.md` — 示例文档
- 新文档放入 `knowledge/`，调用 `POST /api/ingest` 热加载

## 修改规则
1. Prompt 修改 → `generator.py` 的 `SYSTEM_PROMPT`
2. 修改禁止词汇 → `main.py` 的 `_UNWANTED_PATTERNS`
3. 修改阈值 → `config.py` 的 `CONFIDENCE_*_THRESHOLD`
4. 修改 LLM 模型 → `config.py` 的 `LLM_MODEL`
5. 修改后运行 `bash start.sh` 测试
6. 确认无问题后 `git add` + `git commit` + `git push`
