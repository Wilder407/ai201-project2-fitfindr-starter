# FitFindr

An AI shopping agent that finds a secondhand clothing listing matching your style and budget, suggests how to pair it with what you already own, and generates a ready-to-post caption for it — all from a single natural language request.

[Watch the Demo](https://vimeo.com/1211039153?fl=ip&fe=ec)

## Overview

Tell FitFindr what you're looking for ("vintage graphic tee under $30, I mostly wear baggy jeans and chunky sneakers") and it chains three tools together to go from search to a shareable outfit post:

1. **Finds a listing** that matches your description, size, and budget
2. **Suggests how to style it** against your existing wardrobe (or gives standalone styling notes if your wardrobe is empty)
3. **Writes a caption** for sharing the finished look

Built with Groq (`llama-3.3-70b-versatile`) for generation and Gradio for the interface.

## Architecture

```
                  user query
                       |
                       v
        +--[ PLANNING LOOP ]------------------------+
        |                                            |
        |  search_listings(desc, size, max_price)    |
        |       |                                     |
        |  no results --> [ERROR] "No listings        |
        |                  found." --> EXIT           |
        |       |                                     |
        |  results found                              |
        |  session: selected_item = results[0]        |
        |       |                                     |
        |  suggest_outfit(selected_item, wardrobe)    |
        |       |                                     |
        |  no suggestion --> [ERROR]                  |
        |                  "Try another item" --> EXIT|
        |       |                                     |
        |  session: outfit_suggestion = "..."         |
        |       |                                     |
        |  create_fit_card(outfit_suggestion,         |
        |                   selected_item)             |
        |       |                                     |
        |  session: fit_card = "..."                   |
        |                                            |
        +--------------------------------------------+
                       |
                       v
                 return session
```

The agent runs a linear tool chain, but each step checks the previous tool's output before proceeding — an empty result at any stage short-circuits to an error message rather than passing bad data downstream.

## Tools

**`search_listings(description, size, max_price)`** — Matches keywords against a listings dataset and returns the top result as a formatted dict (title, price, platform, condition). Empty results end the session early with an error rather than falling through to the next tool.

**`suggest_outfit(new_item, wardrobe)`** — Pairs the new item with something in the user's existing wardrobe, or falls back to standalone styling notes if the wardrobe is empty or has too few items to pair against.

**`create_fit_card(outfit)`** — Generates a shareable, Instagram-style caption referencing the item, platform, and price. Uses temperature variation so repeated calls produce different phrasing rather than a templated-sounding output.

## State Management

Each tool's structured output is stored in session state and passed as a typed input to the next tool — `search_listings` → `selected_item` → `suggest_outfit` → `outfit_suggestion` → `create_fit_card` → `fit_card`. Wardrobe data is loaded from JSON at query time. Nothing more than the fields each downstream tool actually needs gets passed forward, keeping the interface between tools narrow.

## Error Handling

| Tool | Failure mode | Behavior |
|------|-------------|----------|
| `search_listings` | No results match the query | Session ends early with an error message; nothing downstream is called |
| `suggest_outfit` | Wardrobe is empty | Falls back to standalone styling notes instead of failing |
| `create_fit_card` | Outfit input missing/incomplete | UI shows the error state and leaves the outfit/caption panels empty |

## Catching a Schema Mismatch

While wiring `suggest_outfit`, an early implementation used field names `color` and `type` — but the actual wardrobe JSON used `colors` (a list) and `category`. This surfaced during testing rather than at the spec stage, which was the fix going forward: pinning down actual field names from the real data files before handing a spec to an AI tool for implementation, instead of after. The same read-the-output-before-trusting-it approach caught a second bug — a `None` brand field breaking a string join in `search_listings` — before it reached test runs.

## Example Interaction

**Query:** *"I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"*

1. `search_listings(description="vintage graphic tee", max_price=30.00, size=None)` → returns a matching listing
2. `suggest_outfit(selected_item, wardrobe)` → *"This vintage graphic tee makes the simplest of statements and looks best shrugged off the shoulder with your baggy jeans."*
3. `create_fit_card(outfit_suggestion)` → *"I can't wait to rock this new look from Depop for only $26!"*

**User sees:** three panels — the listing (title, price, platform, condition), the outfit suggestion, and the shareable caption.

## Development Notes

Built with Claude as an implementation partner: given a tool's spec (inputs, return shape, failure mode) plus the relevant data-loading constraints, then verified against test queries designed to make a wrong result obvious — e.g., a low `max_price` where any returned item over budget would flag a broken filter. The planning-loop and session-state logic were verified the same way: checking that tools weren't called unconditionally, that the session dict held the expected keys at each step, and that the no-results path actually left downstream fields empty instead of silently populating them.

## What I'd Improve

- Spec out real data field names upfront instead of catching schema mismatches during testing
- Add branching logic for cases beyond the current linear tool chain (e.g., multiple wardrobe items worth suggesting)
