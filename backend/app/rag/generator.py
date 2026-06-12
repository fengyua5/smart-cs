from typing import Generator
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage
from app.config import OLLAMA_BASE_URL, LLM_MODEL

_llm = None

SYSTEM_PROMPT = '你是真人客服。根据参考知识用口语回复客户。参考知识不够时一律说：请稍等，我们正在查询，建议您拨打客服热线 400-888-8888 或联系在线客服咨询更多详情。末尾标注 [自信度: X]（1-10）。禁止暴露"暂无信息""没有相关""去官网看"等。'


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.3,
        )
    return _llm


def _build_messages(question: str, contexts: list[str]) -> list:
    context_text = "\n".join(contexts)
    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"参考知识：{context_text}\n\n问题：{question}"),
    ]


def generate_answer(question: str, contexts: list[str]) -> str:
    llm = get_llm()
    messages = _build_messages(question, contexts)
    return llm.invoke(messages).content


def generate_stream(question: str, contexts: list[str]) -> Generator[str, None, None]:
    llm = get_llm()
    messages = _build_messages(question, contexts)
    for chunk in llm.stream(messages):
        content = chunk.content
        if content:
            yield content
