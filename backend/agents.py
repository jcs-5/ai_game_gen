from typing import TypedDict, List, Dict, Optional
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field, ValidationError, field_validator
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Set up the Gemini API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")
os.environ["GOOGLE_API_KEY"] = api_key

# --- Pydantic Models for JSON Output ---

class StarterCard(BaseModel):
    name: str = Field(description="Name of the card")
    type: str = Field(description="e.g., Action, Creature, Resource")
    cost: str = Field(description="e.g., 3 Energy")
    text: str = Field(description="Description of the card's effect")
    flavor_text: Optional[str] = Field(default=None, description="Optional thematic text")

class GameDesign(BaseModel):
    game_name: str = Field(description="A creative name for the game")
    concept: str = Field(description="A 2-3 paragraph overview of the game, its theme, and what players do")
    core_mechanics: List[str] = Field(description="List of 3-5 key game mechanics")
    win_condition: str = Field(description="A clear description of how a player wins the game")
    game_flow: str = Field(description="A step-by-step description of a typical game turn")
    starter_cards: List[StarterCard] = Field(description="A list of starter cards")

class SuggestedCardChange(BaseModel):
    card_name: str = Field(description="Name of the card to change")
    suggested_change: str = Field(description="Specific change, e.g., 'Change cost to 4'")
    reasoning: str = Field(description="Brief explanation for why this change improves balance")

class BalanceAnalysis(BaseModel):
    balance_analysis: str = Field(description="A 2-3 paragraph analysis of the game's balance")
    suggested_card_changes: List[SuggestedCardChange] = Field(description="List of suggested card changes")

class Issue(BaseModel):
    issue: str = Field(description="A brief description of a specific issue found")
    location: str = Field(description="The document/area where the issue was found")
    suggestion: str = Field(description="A suggestion for how to resolve the issue")

class QAReport(BaseModel):
    qa_summary: str = Field(description="A brief, 2-4 sentence summary of your overall findings.")
    issues_found: List[Issue] = Field(description="List of issues found")

class Rulebook(BaseModel):
    rulebook: str = Field(description="The complete rulebook text in Markdown format.")

class ArtStyleGuide(BaseModel):
    art_style_guide: str = Field(description="The complete art style guide in Markdown format.")

class CardArt(BaseModel):
    artwork_description: str = Field(alias="artwork description")
    title_font: str = Field(alias="title font")
    body_font: str = Field(alias="body font")
    iconography: List[str]

    @field_validator('iconography', mode='before')
    def coerce_to_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v

class CardArtwork(BaseModel):
    artwork: Dict[str, CardArt]


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
    model_provider: str

    # Workflow control
    revision_count: int
    max_revisions: int

    # Generated content
    game_design: Optional[GameDesign]
    rulebook: Optional[Rulebook]
    card_list: List[StarterCard]
    art_style_guide: Optional[ArtStyleGuide]
    card_artwork: Optional[CardArtwork]
    balance_analysis: Optional[BalanceAnalysis]
    qa_report: Optional[QAReport]

# --- AI Agents ---
def get_llm(model_provider: str):
    """Returns the appropriate LLM based on the model_provider."""
    if model_provider == "ollama":
        OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llama3.2:1b")
        print(f"Using Ollama model: {OLLAMA_MODEL_NAME}")
        return ChatOllama(model=OLLAMA_MODEL_NAME, temperature=0.7, format="json")
    else:
        print("Using Gemini model: gemini-2.0-flash-lite")
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0.7)

def game_designer_agent(state: GameState):
    """Generates or revises the game design based on user inputs and feedback."""
    print(f"--- Running Game Designer Agent (Revision {state.get('revision_count', 0)}) ---")
    model_provider = state["model_provider"]
    llm = get_llm(model_provider)

    if state.get('balance_analysis') or state.get('qa_report'):
        revision_prompt = "This is a revision..."
    else:
        revision_prompt = ""

    prompt = f"""You are an expert board game designer. Your task is to design a complete card game based on the following user-provided parameters.
    {revision_prompt}

    **Game Parameters:**
    - **Theme:** {state["game_theme"]}
    - **Game Type:** {state["game_type"]}
    - **Player Count:** {state["player_count"][0]}-{state["player_count"][1]} players
    - **Play Time:** {state["play_time"]}
    - **Complexity:** {state["complexity"]}
    - **Play Style:** {state["play_style"]}
    - **Art Style:** {state["art_style"]}
    - **Additional Notes:** {state["additional_notes"]}
    """

    if model_provider == "ollama":
        prompt_with_json_instructions = prompt + "\n\nYour response must be in JSON format."
        result_str = llm.invoke(prompt_with_json_instructions).content
        result_dict = json.loads(result_str)
        result = GameDesign.model_validate(result_dict)
    else:
        structured_llm = llm.with_structured_output(GameDesign)
        result = structured_llm.invoke(prompt)

    state["game_design"] = result
    state["card_list"] = result.starter_cards
    state["revision_count"] = state.get("revision_count", 0) + 1
    print("--- Game Design Generated ---")
    return state

def balance_math_agent(state: GameState):
    """Analyzes the initial game design and suggests balance changes."""
    print("--- Running Balance & Math Agent ---")
    model_provider = state["model_provider"]
    llm = get_llm(model_provider)

    game_design = state["game_design"]
    starter_cards_str = json.dumps([card.model_dump() for card in game_design.starter_cards])

    prompt = f"""You are a quantitative game designer specializing in game balance.
    Your task is to analyze the provided game design and its starter cards, then suggest initial balance adjustments.

    **Game Design Document:**
    - **Game Name:** {game_design.game_name}
    - **Concept:** {game_design.concept}
    - **Core Mechanics:** {", ".join(game_design.core_mechanics)}
    - **Win Condition:** {game_design.win_condition}
    - **Game Flow (Turn Structure):** {game_design.game_flow}
    - **Starter Cards:** {starter_cards_str}
    """

    if model_provider == "ollama":
        prompt_with_json_instructions = prompt + "\n\nYour response must be in JSON format."
        result_str = llm.invoke(prompt_with_json_instructions).content
        result_dict = json.loads(result_str)
        result = BalanceAnalysis.model_validate(result_dict)
    else:
        structured_llm = llm.with_structured_output(BalanceAnalysis)
        result = structured_llm.invoke(prompt)

    state["balance_analysis"] = result
    print("--- Balance Analysis Generated ---")
    return state

def rules_writer_agent(state: GameState):
    """Generates a complete rulebook based on the game design."""
    print("--- Running Rules Writer Agent ---")
    model_provider = state["model_provider"]
    llm = get_llm(model_provider)

    game_design = state["game_design"]
    starter_cards_str = json.dumps([card.model_dump() for card in game_design.starter_cards])

    prompt = f"""You are a professional rulebook writer for board games. Your task is to write a clear, concise, and comprehensive rulebook for a new card game.
    Use the provided game design document to structure the rulebook.

    **Game Design Document:**
    - **Game Name:** {game_design.game_name}
    - **Concept:** {game_design.concept}
    - **Core Mechanics:** {", ".join(game_design.core_mechanics)}
    - **Win Condition:** {game_design.win_condition}
    - **Game Flow (Turn Structure):** {game_design.game_flow}
    - **Starter Cards:** {starter_cards_str}

    **Rulebook Structure:**
    1.  **Introduction:** Briefly introduce the theme and objective of the game.
    2.  **Components:** List the components of the game (e.g., "X number of cards").
    3.  **Setup:** Provide step-by-step instructions on how to set up the game for the specified number of players.
    4.  **Goal of the Game:** Clearly state the win condition.
    5.  **Gameplay:** Detail the turn structure and the actions players can take. Explain the core mechanics in detail.
    6.  **Card Explanations:** Briefly explain the different types of cards and clarify any keywords from the starter card list.
    7.  **End of Game:** Explain how the game ends and how a winner is determined.

    Write the rulebook in a friendly and easy-to-understand tone. Use markdown for formatting (e.g., headings, bold text, lists, and paragraphs).
    """

    if model_provider == "ollama":
        prompt_with_json_instructions = prompt + "\n\nYour response must be in JSON format."
        result_str = llm.invoke(prompt_with_json_instructions).content
        result_dict = json.loads(result_str)
        result = Rulebook.model_validate(result_dict)
    else:
        structured_llm = llm.with_structured_output(Rulebook)
        result = structured_llm.invoke(prompt)

    state["rulebook"] = result
    print("--- Rulebook Generated ---")
    return state

def art_director_agent(state: GameState):
    """Generates an art style guide based on the game's theme and art style."""
    print("--- Running Art Director Agent ---")
    model_provider = state["model_provider"]
    llm = get_llm(model_provider)

    game_design = state["game_design"]

    prompt = f"""You are an expert art director for board games. Your task is to create a concise art style guide for a new card game.
    The guide should help artists understand the visual identity of the game.

    **Game Information:**
    - **Game Name:** {game_design.game_name}
    - **Game Concept:** {game_design.concept}
    - **Requested Art Style:** {state["art_style"]}

    **Art Style Guide Structure:**
    1.  **Overall Vision:** A brief paragraph describing the intended mood and feeling of the artwork.
    2.  **Color Palette:** Suggest a primary color palette (5-7 colors with hex codes) that fits the theme and style.
    3.  **Typography:** Suggest a font style for card titles and body text (e.g., "Serif font like Lora", "Sans-serif like Montserrat").
    4.  **Iconography:** Describe the style for any icons or symbols (e.g., "Clean and minimalist", "Ornate and detailed").
    5.  **Card Layout:** Briefly describe the layout of the cards (e.g., "Illustration-focused with text overlay", "Structured with clear sections for art, title, and text").
    6.  **Inspirational Keywords:** Provide a list of 5-10 keywords to guide the artists (e.g., "Mystical, Ethereal, Flowing, Dark, Ancient").
    """

    if model_provider == "ollama":
        prompt_with_json_instructions = prompt + "\n\nYour response must be in JSON format."
        result_str = llm.invoke(prompt_with_json_instructions).content
        result_dict = json.loads(result_str)
        result = ArtStyleGuide.model_validate(result_dict)
    else:
        structured_llm = llm.with_structured_output(ArtStyleGuide)
        result = structured_llm.invoke(prompt)

    state["art_style_guide"] = result
    print("--- Art Style Guide Generated ---")
    return state

def asset_generator_agent(state: GameState):
    """Generates detailed art prompts for each card in a single batch."""
    print("--- Running Asset Generator Agent (Batch Mode) ---")
    model_provider = state["model_provider"]
    llm = get_llm(model_provider)

    cards_to_prompt = []
    for card in state["card_list"]:
        card_details = (
            f"- Card Name: {card.name}\n"
            f"  - Type: {card.type}\n"
            f"  - Text: {card.text}\n"
            f"  - Flavor Text: {card.flavor_text}"
        )
        cards_to_prompt.append(card_details)
    all_cards_str = "\n".join(cards_to_prompt)

    prompt = f"""You are a creative assistant generating art prompts for a card game.
    Your task is to create a detailed visual description for EACH card in the list below, based on the game's art style guide.
    Your output should be a JSON object where each key is the card name and the value is an object containing the artwork description, title font, body font, and iconography.
    The keys for the inner object must be "artwork_description", "title_font", "body_font", and "iconography".
    The iconography field should always be a list of strings, even if there is only one item.

    **Art Style Guide:**
    {state["art_style_guide"].art_style_guide}

    **Card List:**
    {all_cards_str}

    **Example Output:**
    ```json
    {{
      "Card Name 1": {{
        "artwork_description": "A detailed description of the artwork.",
        "title_font": "A font name",
        "body_font": "A font name",
        "iconography": ["icon1", "icon2"]
      }},
      "Card Name 2": {{
        "artwork_description": "A detailed description of the artwork.",
        "title_font": "A font name",
        "body_font": "A font name",
        "iconography": ["icon3"]
      }}
    }}
    ```
    """

    if model_provider == "ollama":
        prompt_with_json_instructions = prompt + "\n\nYour response must be in JSON format."
        result_str = llm.invoke(prompt_with_json_instructions).content
        result_dict = json.loads(result_str)
        result = CardArtwork.model_validate(result_dict)
    else:
        result_str = llm.invoke(prompt).content
        print(f"Asset Generator Agent Raw Result: {result_str}")

        # Manually parse the JSON string
        try:
            # The output might have markdown ```json ... ```, so we need to extract the json part
            if "```json" in result_str:
                result_str = result_str.split("```json")[1].split("```")[0]
            result_dict = json.loads(result_str)
            # Wrap the dictionary in another dictionary with the key "artwork"
            result = CardArtwork.model_validate({"artwork": result_dict})
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Error parsing asset generator agent result: {e}")
            # Handle the error appropriately, maybe by returning a default value or raising an exception
            raise e

    state["card_artwork"] = result
    print("--- All Card Artwork Descriptions Generated (Batch) ---")
    return state

def qa_agent(state: GameState):
    """Reviews all generated content for quality and consistency."""
    print("--- Running QA Agent ---")
    model_provider = state["model_provider"]
    llm = get_llm(model_provider)

    prompt = f"""You are a QA specialist for a game design studio.
    Your task is to review the complete set of generated materials for a new card game to ensure everything is coherent, consistent, and high-quality.
    Your output should be a JSON object.

    **Generated Materials:**
    - **Game Design:** {json.dumps(state["game_design"].model_dump())}
    - **Rulebook:** {json.dumps(state["rulebook"].model_dump())}
    - **Art Style Guide:** {json.dumps(state["art_style_guide"].model_dump())}
    - **Balance Analysis:** {json.dumps(state["balance_analysis"].model_dump())}
    - **Card Art Prompts:** {json.dumps(state["card_artwork"].model_dump())}
    """

    if model_provider == "ollama":
        prompt_with_json_instructions = prompt + "\n\nYour response must be in JSON format."
        result_str = llm.invoke(prompt_with_json_instructions).content
        result_dict = json.loads(result_str)
        result = QAReport.model_validate(result_dict)
    else:
        structured_llm = llm.with_structured_output(QAReport)
        result = structured_llm.invoke(prompt)

    state["qa_report"] = result
    print("--- QA Report Generated ---")
    return state

# --- Graph Definition ---

def should_revise(state: GameState) -> str:
    """Determines whether to revise the game design or end the process."""
    print("--- Checking for Revisions ---")
    if state.get("revision_count", 0) >= state.get("max_revisions", 1):
        print("--- Max Revisions Reached ---")
        return "end"

    balance_analysis = state.get('balance_analysis')
    qa_report = state.get('qa_report')

    if balance_analysis and balance_analysis.suggested_card_changes:
        print("--- Balance Issues Found, Revising ---")
        return "revise"

    if qa_report and qa_report.issues_found:
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