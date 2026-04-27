"""Quick local test for the qwen2.5:7b model response."""

from core.llm import invoke_llm


def main() -> None:
    """Call the configured LLM and print the response."""
    prompt = "Say hello in one short sentence."
    system = "You are a concise assistant."

    response = invoke_llm(prompt=prompt, system=system, history=[])
    print("Model:", "qwen2.5:7b")
    print("Prompt:", prompt)
    print("Response:", response)


if __name__ == "__main__":
    main()
