# Smart CS — AI 智能客服系统技术设计文档

## 1. 概述

Smart CS 是一个基于 RAG（检索增强生成）架构的 AI 智能客服系统，使用本地 Ollama 模型，支持低置信度问题自动转人工审核。

### 1.1 核心目标

- 利用本地 LLM 智能回复用户常见问题
- 多维度置信度评估，低分问题自动转入人工审核
- 人工审核面板支持编辑、采纳、历史追溯
- 知识库文档热加载，无需重启服务

### 1.2 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端框架 | FastAPI | API 路由与请求处理 |
| LLM | Ollama (qwen3.5:9b) | 对话生成 |
| 向量化 | OllamaEmbeddings (bge-m3) | 文本转向量 |
| 向量库 | ChromaDB | 知识检索 |
| RAG 框架 | LangChain | 文档切片、检索链 |
| 数据库 | SQLAlchemy + SQLite | 对话与审核持久化 |
| 前端 | 原生 HTML + JS | 用户聊天 + 审核面板 |

## 2. 系统架构

```
┌──────────────┐     ┌─────────────────────────────────────────────┐
│  前端 (用户)   │     │                 后端 FastAPI                  │
│  chat.html   │────▶│                                             │
│  review.html │     │  ┌─────────┐  ┌──────────┐  ┌────────────┐  │
└──────────────┘     │  │ Chat    │  │ Review   │  │ Ingest     │  │
                     │  │ Router  │  │ Router   │  │ Router     │  │
                     │  └────┬────┘  └────┬─────┘  └─────┬──────┘  │
                     │       │            │               │        │
                     │  ┌────▼────────────▼───────────────▼──────┐  │
                     │  │              RAG Pipeline               │  │
                     │  │  ┌──────────┐ ┌─────────┐ ┌─────────┐  │  │
                     │  │  │Retriever │ │Generator│ │Confidence│  │  │
                     │  │  │(Chroma)  │ │(Ollama) │ │Scorer   │  │  │
                     │  │  └──────────┘ └─────────┘ └─────────┘  │  │
                     │  └─────────────────────────────────────────┘  │
                     │              │           │                    │
                     │        ┌─────▼───────────▼──────┐             │
                     │        │    SQLite 数据库        │             │
                     │        │  conversations 表      │             │
                     │        └────────────────────────┘             │
                     └─────────────────────────────────────────────┘
```

## 3. 核心流程

### 3.1 用户问答流程

```
用户提问 → 向量检索知识库 (Chroma top-K)
         → LLM 生成回答 (参考知识 + Prompt)
         → 答案后处理 (检测禁止词汇)
         → 置信度评估 (检索分数 + LLM 自评分)
         → 高分: 直接返回 / 低分: 存入审核队列
```

### 3.2 文档入库流程

```
扫描 knowledge/ 目录 → 加载 .md/.txt 文件
                     → RecursiveCharacterTextSplitter 切片
                     → OllamaEmbeddings 向量化
                     → 存入 ChromaDB
```

## 4. 关键模块设计

### 4.1 RAG 生成器 (`backend/app/rag/generator.py`)

System Prompt 包含：
- 角色设定：真人客服，用口语回复
- 引用规则：只使用参考知识，不编造
- 未知话术模板：要求 LLM 在无法回答时一字不改地使用固定话术
- 禁止词汇：暂无信息、不太清楚、建议访问官网等
- 自信度评分：末尾标注 `[自信度: X]`

### 4.2 置信度评估 (`backend/app/rag/confidence.py`)

双路评估策略：

| 信号 | 来源 | 低分判定 |
|------|------|----------|
| 检索置信度 | Chroma similarity_score | < 0.65 |
| LLM 自评分 | Prompt 输出 `[自信度: X]` | < 6 |

任一触发 → `need_review = True`

### 4.3 答案后处理 (`backend/app/main.py`)

LLM 输出后检测禁止词汇列表，命中则自动替换为标准 Fallback 话术：

```python
_FALLBACK_ANSWER = "请稍等，我们正在查询，建议您拨打...客服热线..."
_UNWANTED_PATTERNS = ["暂无信息", "没有找到", "不太清楚", "建议访问官网", ...]
```

### 4.4 人工审核模块 (`backend/app/review/`)

| API 端点 | 方法 | 说明 |
|----------|------|------|
| `GET /api/review/pending` | 列表 | 待审核队列 |
| `GET /api/review/history` | 列表 | 审核历史 |
| `POST /api/review/submit` | 提交 | 编辑/采纳/拒绝 |

## 5. 数据库设计

### conversations 表

```sql
CREATE TABLE conversations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  VARCHAR(64) NOT NULL,
    question    TEXT NOT NULL,
    answer      TEXT,
    confidence  FLOAT,
    need_review BOOLEAN DEFAULT 0,
    reviewed    BOOLEAN DEFAULT 0,
    human_answer TEXT,
    created_at  DATETIME
);
```

## 6. 配置参数 (`backend/app/config.py`)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 地址 |
| `LLM_MODEL` | `qwen3.5:9b` | 对话模型 |
| `EMBED_MODEL` | `bge-m3:latest` | 向量模型 |
| `CHUNK_SIZE` | `512` | 切片大小 |
| `CHUNK_OVERLAP` | `64` | 切片重叠 |
| `RETRIEVAL_K` | `4` | top-K 检索 |
| `CONFIDENCE_RETRIEVAL_THRESHOLD` | `0.65` | 检索置信度阈值 |
| `CONFIDENCE_LLM_THRESHOLD` | `6` | LLM 自信度阈值 |

## 7. 项目文件映射

```
smart-cs/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口 + 路由 + 后处理
│   │   ├── config.py            # 配置
│   │   ├── database.py          # SQLAlchemy 模型
│   │   ├── models.py            # Pydantic 模型
│   │   ├── rag/                 # RAG 核心
│   │   │   ├── embedder.py      # 向量化
│   │   │   ├── retriever.py     # 向量检索
│   │   │   ├── generator.py     # LLM 生成 + Prompt
│   │   │   └── confidence.py    # 置信度评估
│   │   ├── ingest/pipeline.py   # 文档入库
│   │   └── review/              # 人工审核
│   │       ├── router.py        # 审核 API
│   │       └── service.py       # 审核逻辑
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── chat.html                # 用户聊天窗口
│   └── review.html              # 审核面板
├── knowledge/                   # 知识文档目录
│   └── 常见问题.md
├── docs/technical-design.md     # 本文档
├── AGENTS.md                    # opencode 项目指令
├── opencode.json                # opencode 配置
└── .opencode/agents/smart-cs-agent.md  # 项目 Agent
```

## 8. 部署

- Python 3.9+，安装 `requirements.txt` 依赖
- 本地运行 Ollama，模型：qwen3.5:9b + bge-m3
- 启动：`bash start.sh`
- 访问：http://localhost:8000/static/chat.html
- 审核面板：http://localhost:8000/static/review.html
