from core.llm import get_llm, get_prompt_template
from tools.file_writer import write_file
from langchain.messages import HumanMessage, AIMessage

def run_writer_agent(content: str, filename: str = "note", history: list = []) -> str:
    try:
        prompt_template = get_prompt_template(
            system="""You are a Writer Agent. Your job is to structure and 
            format content clearly into well written markdown.
            Always use proper headings, bullet points where needed.
            Be concise but complete."""
        )
        
        llm = get_llm()
        chain = prompt_template | llm
        
        response = chain.invoke({
            "history": _build_history(history),
            "input": f"Format and structure this content into clean markdown:\n\n{content}"
        })
        
        formatted_content = response.content
        file_status = write_file(filename, formatted_content)
        
        return f"{formatted_content}\n\n---\n{file_status}"
    except Exception as e:
        return f"Writer agent failed: {str(e)}"

def _build_history(history: list) -> list:
    messages = []
    for msg in history:
        if msg["role"] == "human":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            messages.append(AIMessage(content=msg["content"]))
    return messages