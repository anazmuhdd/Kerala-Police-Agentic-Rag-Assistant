from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

# Initialize
crawler = WebCrawler()
crawler.warmup()

# Define a strict instruction
extraction_strategy = LLMExtractionStrategy(
    provider="openai/gpt-4o-mini",  # or your preferred model (e.g., "ollama/llama3.1")
    instruction=(
        "Extract only the main body content of the article or page. "
        "Include headings, paragraphs, and essential text that conveys the core information. "
        "Do NOT include: navigation menus, sidebars, footers, advertisements, author bios, "
        "related articles, or ANY links (including URLs, anchor texts, or markdown links like [text](url)). "
        "Return clean, readable text in markdown format with no extraneous elements."
    )
)

# Run the crawl
result = crawler.run(
    url="https://example.com/article",
    extraction_strategy=extraction_strategy,
    bypass_cache=True
)

# Get the clean output
clean_markdown = result.extracted_content  # This will follow your instruction
print(clean_markdown)