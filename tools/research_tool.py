"""Research tool that uses the search router and summarizes results."""

import logging

from langchain.messages import AIMessage, HumanMessage

from core.llm import get_llm, get_prompt_template
from tools.search_router import run_search


logger = logging.getLogger(__name__)


def run_research_tool(query: str, history: list | None = None) -> str:
    """Run the research tool by searching first, then summarizing with the LLM."""
    try:
        logger.info("Running research tool search step")
        search_results = run_search(query)

        logger.info("Building research prompt template")
        prompt_template = get_prompt_template(
            system="""You are a research tool.
Analyze the search results and provide a clear, concise, accurate summary.
Always cite the sources you used.
If the search results are not relevant, say so clearly.
Do not make up information that is not present in the results.""",
        )

        logger.info("Loading LLM for research tool")
        llm = get_llm()
        chain = prompt_template | llm

        logger.info("Invoking LLM with routed search results")
        response = chain.invoke(
            {
                "history": _build_history(history or []),
                "input": f"User query: {query}\n\nSearch Results:\n{search_results}",
            }
        )

        logger.info("Research tool completed successfully")
        return response.content
    except Exception as exc:
        logger.error("Research tool failed: %s", str(exc))
        return f"Research tool failed: {str(exc)}"


def _build_history(history: list) -> list:
    """Convert plain history dictionaries into LangChain message objects."""
    messages = []

    for msg in history:
        # Each history item is converted into the matching LangChain message type.
        if msg["role"] == "human":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            messages.append(AIMessage(content=msg["content"]))

    return messages
