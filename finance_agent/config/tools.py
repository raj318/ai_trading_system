TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_fundamentals",
            "description": "Search company financial documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                },
                "required": ["question"],
            },
        },
    }
]