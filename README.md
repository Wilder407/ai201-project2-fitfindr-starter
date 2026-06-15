# FitFindr — Starter Kit

---

## Tools

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
The `search_listings` tool takes in a user input, sets the input parameters with keywords from the input. `search_listings` returns 3 matching listings sorted by relevance.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): style type and item category
- `size` (str): wardrobe item size 
- `max_price` (float): maximun item price

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
The result is a dict object with the features for the top result. Fields are item title, price as USD, platform and item condition. Format "item title - <$price>, platform, condition"

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
After `search_listings` runs, check if results is empty. If yes, set an error message in the session and return early. If no, set `selected_item = results[0]` and proceed to `suggest_outfit`.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool takes the item from `search_listings` and items in the user's wardrode. The tools suggests one ore more complete outfits combinations. Must be able to handle empty wardrobe or minimal items. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): item returned from search_listings
- `wardrobe` (dict): existing items in the user's wardrobe

**What it returns:**
<!-- Describe the return value -->
Suggest_outfit returns natural language text that suggests an item in the existing wardrobe to pair the new item with. It also may suggest styling details. If there isn't an item to pair with, only suggest styling notes for the item. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

After `suggest_outfit` runs, check if results is empty. If yes, set an error message in the session and return early. If no, set `outfit_suggestion = "result"` and proceed to `create_fit_card`.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
 Generates a short, shareable description of a complete outfit — the kind of thing someone would caption an Instagram post with. Must produce something different each time for different inputs.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): result from suggest_outfit

**What it returns:**
<!-- Describe the return value -->
A natural language text string for social media sharing, includes reference to the new item, the platform  and the price. Includes one sentence highlighting satisfaction for the item and that may connect back to the user's original input. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
After `create_fit_card` runs, check if results is empty. If yes, set an error message in the session and return early. If no, set fit_card = "result" and return session results.

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The LLM that is driving the agent reads the conversation or context about what's been accomplished so far and decides what is still required to meet the goal.The agent adds to it's memory at each step and uses this collection of information to decide which tool it should use next. This project follows a linear path and doesn't require branching but that would be a consideration the LLM would make if necessary. 

The LLM can determine when to move to the next step by reviewing which results are stored. If there is nothing returned for `search_listings`, the LLM will know to quit and provide the user with an error message. I'm excited to see how the agent can retain the input and stay within a tool instead of jumping out entirely. 

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
When the tools return output, those results are added into the agent's context. Not all contents of the output are passed to the next tool but can be helpful in the output for that function. For example, `suggest_outfit` connects the new item to one in the wardrobe. The return string also shares styling information that can be inferred form the user's input or existing wardrobe items. The structured result from ``earch_listing` is stored in context and is passed as `new_item` to `suggest_outfit`.The structured result from `suggest_outfit` is stored in context and is passed as `outfit` to `create_fit_card`.  
Wardrobe is stored as json records and is loaded at the time the user input in entered. The information is passed via a pipeline that passes outputs automatically. 

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No results match the query | The "vintage graphic tee" query returned an empty list because the dataset didn't have that exact match — I updated the test query to "vintage band tee" to get results. |
| `suggest_outfit` | Wardrobe is empty | Agent suggested sytling tips instead of connecting to an item in an empty wardrobe. |
| `create_fit_card` | Outfit input is missing or incomplete | The no-results path in the Gradio UI correctly showing the error message and leaving the other two panels empty |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```
     user query
     |
     v
+--[ PLANNING LOOP ]---------------------------+
|                                              |
|  search_listings(desc, size, max_price)      |
|       |                                      |
|  results = []  -->  [ERROR] "No listings     |
|                       found." --> EXIT       |
|       |                                      |
|  results = [item, ...]                       |
|  session: selected_item = results[0]         |
|       |                                      |
|  suggest_outfit(selected_item, wardrobe)     |
|       |                                      |
|  outfit_suggestion = ""  --> [ERROR]         |
|                       "Try another item"     |
|                            --> EXIT          |
|       |                                      |
|  session: outfit_suggestion = "..."          |
|       |                                      |
|  create_fit_card(outfit_suggestion,          |
|                  selected_item)              |
|       |                                      |
|  session: fit_card = "..."                   |
|                                              |
+----------------------------------------------+
     |
     v
 return session
```

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

I will provide Claude with the Spec block from tools.py and specific constraints like load_listings() and failure modes. I will ask it to implement each function individually using the spec in tools.py. Before running, I will check that the parameters match, that the code properly handles the failure mode (outlined in planning.md) and stub signature.

`suggest_outfit` will use Groq to generate output based on the new_item and existing wardrobe. Groq will generate an outfit suggestion or If empty, suggest styling details instead of a returning an empty string. `create_fit_card` will check for temperature/variation for each output caption response.

I'll test inputs where a wrong result would be obvious - for example, a low max_price where any result over that amount would indicate the price filter isn't working correctly. The same validation would apply to size and description.

**Milestone 4 — Planning loop and state management:**

I will provide Claude with the `agent.py` file and have it generate the `run_agent` function. I will verify that the correct parameters are being called and stored in the session, I will ask Claude to implement `run_agent` following the numbered steps in the `planning.md` file (State Management). Verification includes: checking that branching is correct, that it stores a dict session, that the three tools are not called unconditionally.

I will have Claude call `handle_query()` in `app.py` calls `run_agent()` and maps the session dict to the three output panels. I will also have the code printsession["selected_item"] and confirming it's the exact same dict passed into suggest_outfit. Claude will also ensure that the test cases have the expected agent response (i.e. `agent.p`y and check that the no-results path (the second test case already in the file) returns an error message in `session["error"]` and leaves `session["fit_card"]` as `None`).

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent calls `search_listings` with description=vintage graphic tee, max_price=30.00, size=None. An list of items is returned and the best match is the input for setp 2. 

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
`suggest_outfit` takes in `new_item` dict and `wardrobe` (example or empty depending on user selection) to create an outfit and styling instrctions. This ouput is passed to `create_fit_card`. An example could be "This vantage graphic tee makes the simplest of statements and looks best shrug off the shoulder with your baggy jeans."

**Step 3:**
<!-- Continue until the full interaction is complete -->
`outfit` is passed to `create_fit_card` as a str. Returned is a natural language text string for social media sharing, includes reference to the new item, the platform  and the price. 

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees three panels: the listing result (item title, price, platform, condition), the outfit suggestion ("This vintage graphic tee looks best shrugged off the shoulder with your baggy jeans..."), and the fit card caption ("I can't wait to rock this new look from Depop for only $26!").

## Spec Reflection 
I originally was missing new_item from the `create_fit_card` spec information. This missing information was detected when I was working through the Step Management section of `planning.md`. Going through the input and output variables helped me clear up the way the session data moved through the program. Not catching this would have stopped the final tool from generating a fit card. 

Having the pseducode failure mode blocks created a clear set of guidelines for Claude to operate within. Writing out the input and tracing how the file connect to the JSON databases and the tools gave me a better tracing for the session data. For example including in the table for `search_listings`, if results is empty → return early which shaped the logic in the `run_agent()` function. 

There were many new concepts within this project that broadened my knownledge of AI agents. I've never created one before and it was nice to understand how they differ from a RAG pipeline from last week. The information in the lecture was very valuable but working through the spec highlighted that I was very new to many parts of agent buidling. For exampple, I didn't know what temperature was in relation to the variance of outputs. Learning this beforehand would have helped me understand how to provide guiderails throughout the spec. 

I caught a data schema mismatch during implementation — Claude used "color" and "type" but your wardrobe JSON used "colors" and "category". I could have specced these more precisely upfront by including the actual field names from your JSON files in your tool specs.

##AI Tool Instances
1. I gave Claude the Tool 1 spec block from tools.py (inputs, return value, TODO steps) and the constraint to use load_listings() from `utils/data_loader.py`. Claude generated a working implementation with keyword scoring and filtering logic. Before using it, I identified two things to fix: the brand field could be `None` which broke the string join, and the indentation was incorrect throughout the function. I corrected both before running tests.

2. I gave Claude the Tool 2 spec block from `tools.py`, the Groq model requirement (llama-3.3-70b-versatile), and the empty wardrobe failure mode. Claude generated an implementation with two distinct prompt branches. Before using it, I caught a schema mismatch — Claude used "color" and "type" as field names but your actual wardrobe JSON used "colors" (a list) and "category". You overrode those field references to match your real data schema before running tests.