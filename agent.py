"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

import re

def run_agent(query: str, wardrobe: dict) -> dict:
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse the query with regex
    # Extract max_price — matches "under $30", "under 30", "$30", "max $30"
    price_match = re.search(r"(?:under|max|below|up to)?\s*\$?\s*(\d+(?:\.\d+)?)", query, re.IGNORECASE)
    max_price = float(price_match.group(1)) if price_match else None

    # Extract size — matches "size M", "size XL", standalone S/M/L/XL/XXS etc.
    size_match = re.search(r"\bsize\s+([A-Za-z0-9/]+)\b|\b(XXS|XS|S|M|L|XL|XXL|2XL|3XL)\b", query, re.IGNORECASE)
    size = (size_match.group(1) or size_match.group(2)) if size_match else None

    # Description: strip price and size tokens, use the rest as keywords
    description = re.sub(r"(?:under|max|below|up to)?\s*\$?\s*\d+(?:\.\d+)?", "", query, flags=re.IGNORECASE)
    description = re.sub(r"\bsize\s+[A-Za-z0-9/]+\b|\b(XXS|XS|S|M|L|XL|XXL|2XL|3XL)\b", "", description, flags=re.IGNORECASE)
    description = description.strip(" ,.")

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price,
    }

    # Step 3: Call search_listings — branch on empty results
    results = search_listings(
        description=description,
        size=size,
        max_price=max_price,
    )
    session["search_results"] = results

    if not results:
        session["error"] = (
            f"No listings found matching '{description}'"
            + (f" in size {size}" if size else "")
            + (f" under ${max_price:.2f}" if max_price else "")
            + ". Try broader keywords, a different size, or a higher price."
        )
        return session

    # Step 4: Select top result
    session["selected_item"] = results[0]

    # Step 5: Call suggest_outfit
    outfit_suggestion = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=session["wardrobe"],
    )
    session["outfit_suggestion"] = outfit_suggestion

    if not outfit_suggestion or not outfit_suggestion.strip():
        session["error"] = "Could not generate an outfit suggestion. Try a different item."
        return session

    # Step 6: Call create_fit_card
    fit_card = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )
    session["fit_card"] = fit_card

    # Step 7: Return session
    return session

# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
