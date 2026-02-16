"""LangMem configuration for long-term memory.

Memory is stored in Postgres-backed LangGraph Store with namespaces:
- ("user", "{user_id}", "semantic")    — general facts about the user
- ("user", "{user_id}", "episodic")    — conversation episode summaries
- ("user", "{user_id}", "constraints") — hard constraints (allergies, etc.)
- ("user", "{user_id}", "preferences") — soft preferences
"""


def get_memory_namespace(user_id: str, category: str) -> tuple[str, ...]:
    return ("user", user_id, category)


MEMORY_CATEGORIES = ["semantic", "episodic", "constraints", "preferences"]
