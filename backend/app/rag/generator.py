from typing import Generator
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage
from app.config import OLLAMA_BASE_URL, LLM_MODEL

_llm = None

SYSTEM_PROMPT = """你是一个真人客服，正在用企业客服系统回复用户咨询。请根据提供的参考知识回答。

核心规则：
1. 只使用提供的参考知识来回答问题，不要编造信息
2. 如果参考知识中能找到对应的答案，请用自然的口语回复
3. 如果参考知识中找不到问题答案，请严格按照下面的话术回复（一字不改）：
   "请稍等，我们正在查询，建议您拨打客服热线 400-888-8888 或联系在线客服咨询更多详情。"
   ⚠️ 绝对不能说：暂无信息、不太清楚、没有相关、建议访问官网、建议去网站看
4. 回答末尾标出自信度评分，格式 [自信度: X]，X 为 1-10 整数"""


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
    context_text = "\n\n".join(f"参考 {i+1}: {c}" for i, c in enumerate(contexts))
    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"参考知识：\n{context_text}\n\n用户问题：{question}"),
    ]


def generate_answer(question: str, contexts: list[str]) -> str:
    llm = get_llm()
    messages = _build_messages(question, contexts)
    return llm.invoke(messages).content


def generate_stream(question: str, contexts: list[str]) -> Generator[str, None, None]:
    """逐 token 流式生成回答"""
    llm = get_llm()
    messages = _build_messages(question, contexts)
    for chunk in llm.stream(messages):
        content = chunk.content
        if content:
            yield content
