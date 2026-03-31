from core.llm import get_llm, get_prompt_template
from tools.web_search import web_search
from langchain.messages import HumanMessage, AIMessage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_research_agent(query: str, history: list = []) -> str:
    try:
        search_results = web_search(query)
        
        prompt_template = get_prompt_template(
            system="""You are a Research Agent. Your job is to analyze search results 
            and provide a clear, concise, and accurate summary.
            Always cite the sources you used.
            If search results are not relevant, say so clearly."""
        )
        
        llm = get_llm()
        chain = prompt_template | llm
        
        response = chain.invoke({
            "history": _build_history(history),
            "input": f"User query: {query}\n\nSearch Results:\n{search_results}"
        })
        
        return response.content
    except Exception as e:
        return f"Research agent failed: {str(e)}"

def _build_history(history: list) -> list:
    messages = []
    for msg in history:
        if msg["role"] == "human":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            messages.append(AIMessage(content=msg["content"]))
    return messages