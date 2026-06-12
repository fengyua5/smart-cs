from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage
from app.config import OLLAMA_BASE_URL, LLM_MODEL

_llm = None

SYSTEM_PROMPT = """你是一个专业、友好的智能客服助手。请基于提供的参考知识回答用户问题。

要求：
1. 只使用提供的参考知识来回答问题，不要编造信息
2. 如果参考知识不足以回答，请如实告知
3. 回答需要简洁清晰、有礼貌
4. 在回答的末尾，给出一个 1-10 的整数自信度评分，格式为 [自信度: X]
   其中 X 表示你对自己回答的把握程度，1 为完全不确定，10 为非常确定"""


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.3,
        )
    return _llm


def generate_answer(question: str, contexts: list[str]) -> str:
    llm = get_llm()
    context_text = "\n\n".join(f"参考 {i+1}: {c}" for i, c in enumerate(contexts))

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"参考知识：\n{context_text}\n\n用户问题：{question}"
        ),
    ]
    response = llm.invoke(messages)
    return response.content
