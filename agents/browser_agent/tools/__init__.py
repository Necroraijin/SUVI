from .search_web import format_search_query
from .extract_content import extract_page_text

BROWSER_TOOLS = [
    format_search_query,
    extract_page_text
]

__all__ = ["format_search_query", "extract_page_text", "BROWSER_TOOLS"]