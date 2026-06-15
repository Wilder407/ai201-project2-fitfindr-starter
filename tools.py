"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    try:
        listings = load_listings()
    except Exception:
        return []

    filtered = []
    for item in listings:
        if max_price is not None and item.get("price", 0) > max_price:
            continue
        if size is not None:
            item_size = item.get("size", "")
            if size.lower() not in item_size.lower():
                continue
        filtered.append(item)

    keywords = description.lower().split()
    scored = []
    for item in filtered:
        searchable = " ".join([
            item.get("title", "") or "",
            item.get("description", "") or "",
            item.get("category", "") or "",
            " ".join(item.get("style_tags", []) or []),
            " ".join(item.get("colors", []) or []),
            item.get("brand", "") or "",
        ]).lower()
        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    try:
        client = _get_groq_client()
    except ValueError:
        return "Unable to generate outfit suggestions: API key not configured."

    item_summary = (
        f"Item: {new_item.get('title', 'Unknown item')}\n"
        f"Category: {new_item.get('category', 'N/A')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}\n"
        f"Brand: {new_item.get('brand', 'N/A')}\n"
        f"Condition: {new_item.get('condition', 'N/A')}"
    )

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        # Empty wardrobe — general styling advice
        prompt = (
            f"A user just thrifted this item:\n{item_summary}\n\n"
            "They don't have a wardrobe on file yet. Suggest 1–2 complete outfits "
            "by describing the kinds of pieces that would pair well with this item "
            "(bottoms, shoes, accessories, layering). Keep it specific to the item's "
            "vibe, colors, and style tags. Be concise and conversational."
        )
    else:
        # Format wardrobe into readable list
        wardrobe_lines = []
        for i, piece in enumerate(wardrobe_items, 1):
            wardrobe_lines.append(
                f"{i}. {piece.get('name', 'Unknown')} — "
                f"{', '.join(piece.get('colors', []))}, {piece.get('category', 'N/A')}"
            )

        wardrobe_text = "\n".join(wardrobe_lines)

        prompt = (
            f"A user just thrifted this item:\n{item_summary}\n\n"
            f"Their current wardrobe includes:\n{wardrobe_text}\n\n"
            "Suggest 1–2 complete outfits that pair the new item with specific pieces "
            "from their wardrobe. Reference items by name. If helpful, add a brief "
            "styling tip (shoes, accessories, how to wear it). Be concise and conversational."
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a personal stylist who specializes in thrifted and "
                        "vintage fashion. Give practical, specific outfit suggestions "
                        "in a friendly, casual tone. Keep responses to 3–5 sentences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=300,
        )
        result = response.choices[0].message.content.strip()
        return result if result else "Could not generate a suggestion — try again."
    except Exception:
        return "Outfit suggestion unavailable right now. Try again shortly."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Step 1: Guard against empty or whitespace-only outfit string
    if not outfit or not outfit.strip():
        return (
            "Unable to generate a fit card: outfit suggestion is missing or empty. "
            "Make sure suggest_outfit() returned a valid result before calling create_fit_card()."
        )

    try:
        client = _get_groq_client()
    except ValueError:
        return "Unable to generate fit card: API key not configured."

    title = new_item.get("title", "this thrifted find")
    price = new_item.get("price", "unknown price")
    platform = new_item.get("platform", "a thrift platform")

    price_str = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)

    prompt = (
        f"Write a 2–4 sentence Instagram or TikTok caption for this outfit.\n\n"
        f"Thrifted item: {title}\n"
        f"Price: {price_str}\n"
        f"Platform: {platform}\n"
        f"Outfit: {outfit}\n\n"
        "Guidelines:\n"
        "- Sound like a real person posting their OOTD, not a product listing\n"
        "- Mention the item name, price, and platform naturally — each exactly once\n"
        "- Capture the specific vibe of the outfit (don't use generic phrases like 'cute look')\n"
        "- Be casual, confident, and fun\n"
        "- No hashtags"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write short, authentic outfit captions for social media. "
                        "Every caption should feel fresh and specific — never generic. "
                        "Match the energy of someone genuinely excited about a thrift find."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=1.2,
            max_tokens=150,
        )
        result = response.choices[0].message.content.strip()
        return result if result else "Could not generate a fit card — try again."
    except Exception:
        return "Fit card unavailable right now. Try again shortly."
