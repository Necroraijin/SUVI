def format_search_query(query: str) -> dict:
    """
    Tool for the Browser Agent to format a Google search URL to be sent to the desktop.
    
    Args:
        query: The topic or question to search for.
        
    Returns:
        A dictionary containing the formatted URL for the desktop Executor.
    """
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.google.com/search?q={encoded_query}"
    
    print(f"[Tool: search_web] Formatted search URL: {search_url}")
    
    return {
        "action": "browser_navigate",
        "args": {"url": search_url}
    }