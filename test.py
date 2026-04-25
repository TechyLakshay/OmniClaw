"""Simple local script for testing DDGS search."""

import logging

from tools.web_search import run_ddgs_search


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def test_ddgs_search() -> None:
    """Run one simple DDGS search through the local wrapper."""
    try:
        logger.info("Testing DDGS search wrapper")

        # This directly exercises the existing DDGS search path.
        search_result = run_ddgs_search("What are the latest advancements in renewable energy?")

        print("DDGS search result:")
        print(search_result)

    except Exception as exc:
        logger.error("DDGS search test failed: %s", str(exc))
        print(f"DDGS search test failed: {str(exc)}")


def main() -> None:
    """Run the DDGS search test."""
    test_ddgs_search()


if __name__ == "__main__":
    main()
