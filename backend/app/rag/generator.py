from typing import Generator
import httpx
from app.config import OLLAMA_BASE_URL, LLM_MODEL

CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"

SYSTEM_PROMPT = '你是企业客服。根据参考知识直接回答问题，简洁礼貌，不加修饰词。不知道答案时说：请稍等，我们正在查询，建议您拨打客服热线 400-888-8888 或联系在线客服咨询更多详情。末尾标注 [自信度: X]（1-10）。禁止暴露"暂无信息""没有相关""去官网看"等。'


def _build_ollama_messages(question: str, contexts: list[str]) -> list[dict]:
    context_text = "\n".join(contexts)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"参考知识：{context_text}\n\n问题：{question}"},
    ]


def generate_answer(question: str, contexts: list[str]) -> str:
    return "".join(generate_stream(question, contexts))


def generate_stream(question: str, contexts: list[str]) -> Generator[str, None, None]:
    messages = _build_ollama_messages(question, contexts)
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.1, "num_predict": 300},
    }
    with httpx.stream("POST", CHAT_URL, json=payload, timeout=None) as resp:
        for line in resp.iter_lines():
            if not line:
                continue
            data = httpx.codes.OK  # fallback
            import json
            data = json.loads(line)
            if data.get("done"):
                return
            yield data.get("message", {}).get("content", "")
