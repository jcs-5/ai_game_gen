from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

# Set up the Gemini API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")
os.environ["GOOGLE_API_KEY"] = api_key

# --- Agent State ---
class GameState(TypedDict):
    # User inputs
    game_theme: str
    game_type: str
    player_count: List[int]
    play_time: str
    complexity: str
    play_style: str
    art_style: str
    additional_notes: str

    # Workflow control
    revision_count: int
    max_revisions: int

    # Generated content
    game_design: Dict # Detailed output from the game designer agent
    rulebook: str
    card_list: List[Dict] # Now a list of structured card data
    art_style_guide: str
    card_artwork: List[Dict] # Each dict will contain the card name and a description of the artwork
    balance_analysis: Dict
    qa_report: Dict

# --- AI Agents ---
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.7)

def game_designer_agent(state: GameState):
    """Generates or revises the game design based on user inputs and feedback."""
    print(f"--- Running Game Designer Agent (Revision {state['revision_count']}) ---")

    # Determine if this is a revision and build the prompt accordingly
    if state.get('balance_analysis') or state.get('qa_report'):
        revision_prompt = "This is a revision. Please address the following feedback while preserving the core game theme and vision:\n"
        if state.get('balance_analysis') and state['balance_analysis'].get('suggested_card_changes'):
            revision_prompt += "\n**Balance Feedback:**\n"
            for change in state['balance_analysis']['suggested_card_changes']:
                revision_prompt += f"- Card '{change['card_name']}': {change['suggested_change']} (Reason: {change['reasoning']})\n"
        
        if state.get('qa_report') and state['qa_report'].get('issues_found'):
            revision_prompt += "\n**QA Feedback:**\n"
            for issue in state['qa_report']['issues_found']:
                # Critical instruction to the model to weigh feedback against the theme
                revision_prompt += f"- Issue: {issue['issue']} at '{issue['location']}'. Suggestion: '{issue['suggestion']}'. IMPORTANT: Only apply this suggestion if it aligns with the core game theme of '{state['game_theme']}'. If it contradicts the theme, disregard the suggestion and explain why in your analysis.\n"
    else:
        revision_prompt = ""

    prompt_template = PromptTemplate(
        template="""
        You are an expert board game designer. Your task is to design a complete card game based on the following user-provided parameters. 
        {revision_prompt}

        **Game Parameters:**
        - **Theme:** {game_theme}
        - **Game Type:** {game_type}
        - **Player Count:** {player_count_min}-{player_count_max} players
        - **Play Time:** {play_time}
        - **Complexity:** {complexity}
        - **Play Style:** {play_style}
        - **Art Style:** {art_style}
        - **Additional Notes:** {additional_notes}

        **Output Format:**
        Your response MUST be a JSON object with the following structure. Use Markdown for formatting within the string fields (e.g., for lists, bolding, etc.).
        {{ 
            "game_name": "[A creative name for the game]",
            "concept": "[A 2-3 paragraph overview of the game, its theme, and what players do]",
            "core_mechanics": ["[List of 3-5 key game mechanics, e.g., Deck Building, Hand Management, Set Collection]"],
            "win_condition": "[A clear description of how a player wins the game]",
            "game_flow": "[A step-by-step description of a typical game turn, using Markdown for lists and bolding]",
            "starter_cards": [
                {{ "name": "[Card Name]", "type": "[e.g., Action, Creature, Resource]", "cost": "[e.g., 3 Energy]", "text": "[Description of the card's effect]", "flavor_text": "[Optional thematic text]" }},
                {{ "name": "[Card Name]", "type": "[e.g., Action, Creature, Resource]", "cost": "[e.g., 3 Energy]", "text": "[Description of the card's effect]", "flavor_text": "[Optional thematic text]" }}
            ]
        }}
        """,
        input_variables=["game_theme", "game_type", "player_count_min", "player_count_max", "play_time", "complexity", "play_style", "art_style", "additional_notes", "revision_prompt"],
    )

    parser = JsonOutputParser()
    chain = prompt_template | llm | parser

    result = chain.invoke({
        "game_theme": state["game_theme"],
        "game_type": state["game_type"],
        "player_count_min": state["player_count"][0],
        "player_count_max": state["player_count"][1],
        "play_time": state["play_time"],
        "complexity": state["complexity"],
        "play_style": state["play_style"],
        "art_style": state["art_style"],
        "additional_notes": state["additional_notes"],
        "revision_prompt": revision_prompt,
    })

    state["game_design"] = result
    state["card_list"] = result.get("starter_cards", [])
    state["revision_count"] = state.get("revision_count", 0) + 1
    print("--- Game Design Generated ---")
    return state


def balance_math_agent(state: GameState):
    """Analyzes the initial game design and suggests balance changes."""
    print("--- Running Balance & Math Agent ---")

    prompt_template = PromptTemplate(
        template='''
        You are a quantitative game designer specializing in game balance.
        Your task is to analyze the provided game design and its starter cards, then suggest initial balance adjustments.

        **Game Design Document:**
        - **Game Name:** {game_name}
        - **Concept:** {concept}
        - **Core Mechanics:** {core_mechanics}
        - **Win Condition:** {win_condition}
        - **Game Flow (Turn Structure):** {game_flow}
        - **Starter Cards:** {starter_cards}

        **Analysis Task:**
        1.  **Review the Cards:** Examine the costs and effects of the starter cards. Are there any obvious outliers that seem too strong or too weak?
        2.  **Assess the Core Loop:** Based on the game flow and mechanics, is there a clear path to victory? Does it seem too fast or too slow?
        3.  **Provide Feedback:** Write a brief analysis (2-3 paragraphs) of the current balance.
        4.  **Suggest Changes:** Propose specific, actionable changes to the starter cards. For each change, explain your reasoning. You can suggest changes to cost, text, or any other numerical value.

        **Output Format:**
        Your response MUST be a JSON object with the following structure. Use Markdown for formatting within the string fields.
        {{
            "balance_analysis": "[Your 2-3 paragraph analysis of the game's balance, formatted with Markdown]",
            "suggested_card_changes": [
                {{
                    "card_name": "[Name of the card to change]",
                    "suggested_change": "[Specific change, e.g., 'Change cost to 4', 'Modify text to read: ...']",
                    "reasoning": "[Brief explanation for why this change improves balance]"
                }}
            ]
        }}
        ''',
        input_variables=["game_name", "concept", "core_mechanics", "win_condition", "game_flow", "starter_cards"],
    )

    parser = JsonOutputParser()
    chain = prompt_template | llm | parser

    game_design = state["game_design"]
    starter_cards_str = "\n".join([f"- **{card['name']}** (Cost: {card['cost']}): {card['text']}" for card in game_design.get("starter_cards", [])])

    result = chain.invoke({
        "game_name": game_design.get("game_name"),
        "concept": game_design.get("concept"),
        "core_mechanics": ", ".join(game_design.get("core_mechanics", [])),
        "win_condition": game_design.get("win_condition"),
        "game_flow": game_design.get("game_flow"),
        "starter_cards": starter_cards_str,
    })

    # For now, we'll just store the analysis. A future step could apply these changes.
    state["balance_analysis"] = result
    print("--- Balance Analysis Generated ---")
    return state


def rules_writer_agent(state: GameState):
    """Generates a complete rulebook based on the game design."""
    print("--- Running Rules Writer Agent ---")

    prompt_template = PromptTemplate(
        template="""
        You are a professional rulebook writer for board games. Your task is to write a clear, concise, and comprehensive rulebook for a new card game.
        Use the provided game design document to structure the rulebook.

        **Game Design Document:**
        - **Game Name:** {game_name}
        - **Concept:** {concept}
        - **Core Mechanics:** {core_mechanics}
        - **Win Condition:** {win_condition}
        - **Game Flow (Turn Structure):** {game_flow}
        - **Starter Cards:** {starter_cards}

        **Rulebook Structure:**
        1.  **Introduction:** Briefly introduce the theme and objective of the game.
        2.  **Components:** List the components of the game (e.g., "X number of cards").
        3.  **Setup:** Provide step-by-step instructions on how to set up the game for the specified number of players.
        4.  **Goal of the Game:** Clearly state the win condition.
        5.  **Gameplay:** Detail the turn structure and the actions players can take. Explain the core mechanics in detail.
        6.  **Card Explanations:** Briefly explain the different types of cards and clarify any keywords from the starter card list.
        7.  **End of Game:** Explain how the game ends and how a winner is determined.

        Write the rulebook in a friendly and easy-to-understand tone. Use markdown for formatting (e.g., headings, bold text, lists, and paragraphs).

        **Output:**
        Your response should be a single string containing the full text of the rulebook, formatted with Markdown.
        """,
        input_variables=["game_name", "concept", "core_mechanics", "win_condition", "game_flow", "starter_cards"],
    )

    chain = prompt_template | llm

    game_design = state["game_design"]
    starter_cards_str = "\n".join([f"- **{card['name']}**: {card['text']}" for card in game_design.get("starter_cards", [])])

    result = chain.invoke({
        "game_name": game_design.get("game_name"),
        "concept": game_design.get("concept"),
        "core_mechanics": ", ".join(game_design.get("core_mechanics", [])),
        "win_condition": game_design.get("win_condition"),
        "game_flow": game_design.get("game_flow"),
        "starter_cards": starter_cards_str,
    })

    state["rulebook"] = result.content
    print("--- Rulebook Generated ---")
    return state


def art_director_agent(state: GameState):
    """Generates an art style guide based on the game's theme and art style."""
    print("--- Running Art Director Agent ---")

    prompt_template = PromptTemplate(
        template="""
        You are an expert art director for board games. Your task is to create a concise art style guide for a new card game.
        The guide should help artists understand the visual identity of the game.

        **Game Information:**
        - **Game Name:** {game_name}
        - **Game Concept:** {concept}
        - **Requested Art Style:** {art_style}

        **Art Style Guide Structure:**
        1.  **Overall Vision:** A brief paragraph describing the intended mood and feeling of the artwork.
        2.  **Color Palette:** Suggest a primary color palette (5-7 colors with hex codes) that fits the theme and style.
        3.  **Typography:** Suggest a font style for card titles and body text (e.g., "Serif font like Lora", "Sans-serif like Montserrat").
        4.  **Iconography:** Describe the style for any icons or symbols (e.g., "Clean and minimalist", "Ornate and detailed").
        5.  **Card Layout:** Briefly describe the layout of the cards (e.g., "Illustration-focused with text overlay", "Structured with clear sections for art, title, and text").
        6.  **Inspirational Keywords:** Provide a list of 5-10 keywords to guide the artists (e.g., "Mystical, Ethereal, Flowing, Dark, Ancient").

        **Output:**
        Your response should be a single string containing the full text of the art style guide, formatted with markdown (e.g., headings, bold text, lists).
        """,
        input_variables=["game_name", "concept", "art_style"],
    )

    chain = prompt_template | llm

    game_design = state["game_design"]

    result = chain.invoke({
        "game_name": game_design.get("game_name"),
        "concept": game_design.get("concept"),
        "art_style": state["art_style"],
    })

    state["art_style_guide"] = result.content
    print("--- Art Style Guide Generated ---")
    return state

def asset_generator_agent(state: GameState):
    """Generates detailed art prompts for each card based on the art style guide."""
    print("--- Running Asset Generator Agent ---")

    # This agent will generate a description for each card, one by one.
    card_artwork_list = []

    for card in state["card_list"]:
        print(f"--- Generating art description for: {card['name']} ---")
        prompt_template = PromptTemplate(
            template="""
            You are a creative assistant generating art prompts for a card game.
            Your task is to create a detailed visual description for a single card based on its details and the game's art style guide.

            **Art Style Guide:**
            {art_style_guide}

            **Card Details:**
            - **Card Name:** {card_name}
            - **Card Type:** {card_type}
            - **Card Text:** {card_text}
            - **Flavor Text:** {flavor_text}

            **Instructions:**
            Based on all the information above, write a single, detailed paragraph describing the artwork for this card. 
            Focus on the visual elements, composition, color, and mood. 
            Do not repeat the card details, instead, interpret them to create a compelling visual scene.

            **Output:**
            A single paragraph of descriptive text, formatted with Markdown.
            """,
            input_variables=["art_style_guide", "card_name", "card_type", "card_text", "flavor_text"],
        )

        chain = prompt_template | llm

        result = chain.invoke({
            "art_style_guide": state["art_style_guide"],
            "card_name": card.get("name"),
            "card_type": card.get("type"),
            "card_text": card.get("text"),
            "flavor_text": card.get("flavor_text", ""), # Handle optional flavor text
        })

        card_artwork_list.append({
            "card_name": card.get("name"),
            "artwork_description": result.content
        })

    state["card_artwork"] = card_artwork_list
    print("--- All Card Artwork Descriptions Generated ---")
    return state

def qa_agent(state: GameState):
    """Reviews all generated content for quality and consistency."""
    print("--- Running QA Agent ---")

    prompt_template = PromptTemplate(
        template="""
        You are a QA specialist for a game design studio.
        Your task is to review the complete set of generated materials for a new card game to ensure everything is coherent, consistent, and high-quality.

        **Generated Materials:**
        - **Game Design:** {game_design}
        - **Rulebook:** {rulebook}
        - **Art Style Guide:** {art_style_guide}
        - **Balance Analysis:** {balance_analysis}
        - **Card Art Prompts:** {card_artwork}

        **Review Checklist:**
        1.  **Coherence:** Does the rulebook accurately reflect the core mechanics and game flow from the game design document?
        2.  **Consistency:** Is the art style guide consistent with the game's theme and concept? Are the card art prompts aligned with the art style guide?
        3.  **Clarity:** Is the rulebook easy to understand? Is the language clear and unambiguous?
        4.  **Completeness:** Are there any obvious missing pieces of information?
        5.  **Balance:** Does the balance analysis seem reasonable? (You don't need to re-do the analysis, just check if it makes sense in context).

        **Output Format:**
        Your response MUST be a JSON object with the following structure. Use Markdown for formatting within the string fields.
        {{
            "qa_summary": "[A brief, 2-4 sentence summary of your overall findings.]",
            "issues_found": [
                {{
                    "issue": "[A brief description of a specific issue found]",
                    "location": "[The document/area where the issue was found (e.g., Rulebook, Art Style Guide)]",
                    "suggestion": "[A suggestion for how to resolve the issue]"
                }}
            ]
        }}
        If no issues are found, the "issues_found" list should be empty.
        """,
        input_variables=["game_design", "rulebook", "art_style_guide", "balance_analysis", "card_artwork"],
    )

    parser = JsonOutputParser()
    chain = prompt_template | llm | parser

    # Prepare the inputs, ensuring they are in a string format that the prompt can handle.
    game_design_str = str(state.get("game_design", {}))
    rulebook_str = str(state.get("rulebook", ""))
    art_style_guide_str = str(state.get("art_style_guide", ""))
    balance_analysis_str = str(state.get("balance_analysis", {}))
    card_artwork_str = "\n".join([f"- {item['card_name']}: {item['artwork_description']}" for item in state.get("card_artwork", [])])

    result = chain.invoke({
        "game_design": game_design_str,
        "rulebook": rulebook_str,
        "art_style_guide": art_style_guide_str,
        "balance_analysis": balance_analysis_str,
        "card_artwork": card_artwork_str,
    })

    state["qa_report"] = result
    print("--- QA Report Generated ---")
    return state


# --- Graph Definition ---

def should_revise(state: GameState) -> str:
    """Determines whether to revise the game design or end the process."""
    print("--- Checking for Revisions ---")
    if state["revision_count"] >= state["max_revisions"]:
        print("--- Max Revisions Reached --- ")
        return "end"

    if state.get('balance_analysis') and state['balance_analysis'].get('suggested_card_changes'):
        print("--- Balance Issues Found, Revising ---")
        return "revise"

    if state.get('qa_report') and state['qa_report'].get('issues_found'):
        print("--- QA Issues Found, Revising ---")
        return "revise"

    print("--- No Issues Found, Ending ---")
    return "end"

workflow = StateGraph(GameState)

workflow.add_node("game_designer", game_designer_agent)
workflow.add_node("balance_math", balance_math_agent)
workflow.add_node("rules_writer", rules_writer_agent)
workflow.add_node("art_director", art_director_agent)
workflow.add_node("asset_generator", asset_generator_agent)
workflow.add_node("qa", qa_agent)

workflow.set_entry_point("game_designer")

workflow.add_edge("game_designer", "balance_math")
workflow.add_edge("balance_math", "rules_writer")
workflow.add_edge("rules_writer", "art_director")
workflow.add_edge("art_director", "asset_generator")
workflow.add_edge("asset_generator", "qa")

workflow.add_conditional_edges(
    "qa",
    should_revise,
    {
        "revise": "game_designer",
        "end": END,
    },
)

app = workflow.compile()
