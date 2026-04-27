from core.llm import invoke_llm
from tools.web_search import web_search


def run_research_tool(query: str, history: list | None = None) -> str:
    try:
        search_results = web_search(query)

        system_prompt = """You are a research tool.
Analyze the search results and provide a clear, concise, accurate summary.
Always cite the sources you used.
If the search results are not relevant, say so clearly.
Do not make up information that is not present in the results."""

        prompt = f"User query: {query}\n\nSearch Results:\n{search_results}"

        response = invoke_llm(
            prompt=prompt,
            system=system_prompt,
            history=history or []
        )

        return response
    except Exception as exc:
        return f"Research tool failed: {str(exc)}"
