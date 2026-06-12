#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "=== Smart CS - AI 智能客服系统 ==="
echo ""

if ! command -v ollama &>/dev/null; then
    echo "[!] 未检测到 Ollama，请先安装: https://ollama.com"
    exit 1
fi

echo "[1/3] 检查 Ollama 模型..."
if ! ollama list 2>/dev/null | grep -q "qwen2.5"; then
    echo "   拉取 qwen2.5:7b..."
    ollama pull qwen2.5:7b
fi
if ! ollama list 2>/dev/null | grep -q "bge-m3"; then
    echo "   拉取 bge-m3..."
    ollama pull bge-m3
fi

echo "[2/3] 安装 Python 依赖..."
python3 -m pip install -r backend/requirements.txt -q

echo "[3/3] 导入知识库..."
PYTHONPATH="$DIR/backend" python3 -c "
from app.ingest.pipeline import ingest_all
n = ingest_all()
print(f'   导入 {n} 个文档片段')
"

echo ""
echo "=== 启动服务 ==="
echo "  聊天窗口: http://localhost:8000/static/chat.html"
echo "  审核面板: http://localhost:8000/static/review.html"
echo "  API 文档:  http://localhost:8000/docs"
echo ""

PYTHONPATH="$DIR/backend" python3 backend/run.py
