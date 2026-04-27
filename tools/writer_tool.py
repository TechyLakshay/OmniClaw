from core.llm import invoke_llm
from tools.file_writer import write_file


def run_writer_tool(content: str, filename: str = "note", history: list | None = None) -> str:
    try:
        system_prompt = """You are a writer tool.
Structure and format content clearly into well-written markdown.
Use headings and bullet points only when they improve readability.
Be concise but complete."""

        prompt = f"Format and structure this content into clean markdown:\n\n{content}"

        formatted_content = invoke_llm(
            prompt=prompt,
            system=system_prompt,
            history=history or []
        )

        file_status = write_file(filename, formatted_content)

        return f"{formatted_content}\n\n---\n{file_status}"
    except Exception as exc:
        return f"Writer tool failed: {str(exc)}"
