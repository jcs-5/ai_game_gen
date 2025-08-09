export const dummyGameState = {
  game_design: {
    game_name: "Cosmic Rift",
    concept: "A fast-paced, competitive deck-building game where players take on the role of celestial beings vying for control of the cosmos. Players use their influence to acquire powerful artifacts, manipulate stellar events, and ultimately shatter their opponent's celestial core.",
    core_mechanics: ["Deck Building", "Hand Management", "Direct Attack"],
    win_condition: "The first player to reduce their opponent's celestial core from 20 to 0 is the winner.",
    game_flow: "\n*   **Start of Game:** Each player starts with a deck of 10 basic cards (7 'Stardust' for energy, 3 'Rift Bolt' for attack).\n*   **The Turn:** A player's turn consists of three phases:\n    1.  **Draw Phase:** Draw 5 cards from your deck.\n    2.  **Main Phase:** Play cards from your hand to generate energy, attack the opponent, or acquire new cards from the central 'Nebula' row.\n    3.  **End Phase:** Discard your hand and any unused energy.", 
    starter_cards: [
        { name: "Stardust", type: "Resource", cost: "0", text: "Gain 1 Energy.", flavor_text: "The raw essence of creation."},
        { name: "Rift Bolt", type: "Attack", cost: "1", text: "Deal 1 damage to the opponent.", flavor_text: "A simple, yet effective tear in reality." },
        { name: "Nebula Worm", type: "Creature", cost: "3", text: "Deal 3 damage. You may banish a card from your discard pile.", flavor_text: "It feasts on dying stars."}
    ]
  },
  rulebook: "\n# Cosmic Rift Rulebook\n\n## Introduction\nWelcome to Cosmic Rift! You are a celestial being, a master of cosmic energy. Your goal is to shatter your opponent's core while protecting your own.\n\n## Gameplay\nPlayers take turns playing cards, generating energy, and attacking. The central 'Nebula' contains powerful cards that can be acquired to improve your deck.\n\n## Winning\nReduce the opponent's core health to 0 to win the game!\n",
  art_style_guide: "\n# Art Style Guide: Cosmic Rift\n\n## Vision\nThe art should feel vast, ethereal, and powerful. Think nebulae, galaxies, and strange cosmic phenomena. The mood is one of awe and conflict.\n\n## Color Palette\n-   Deep Purples (#483D8B)\n-   Starlight Gold (#FFD700)\n-   Nebula Pink (#EE82EE)\n-   Cosmic Black (#000000)\n",
  card_artwork: [
    { card_name: "Stardust", artwork_description: "A gentle swirl of shimmering, golden dust against a dark, starry background." },
    { card_name: "Rift Bolt", artwork_description: "A jagged tear in space, with bright purple energy crackling from the edges." },
    { card_name: "Nebula Worm", artwork_description: "A massive, iridescent worm-like creature with a gaping maw, coiling through a pink and purple nebula." }
  ],
  balance_analysis: {
    balance_analysis: "The initial balance seems reasonable for a fast-paced game. The cost-to-effect ratio of the starter cards is a good baseline. The Nebula Worm might be slightly too powerful for its cost, offering both damage and a secondary effect.",
    suggested_card_changes: [
      { card_name: "Nebula Worm", suggested_change: "Increase cost from 3 to 4.", reasoning: "This brings its power level more in line with other cards that might be available in the early game." }
    ]
  },
  qa_report: {
    qa_summary: "Overall, the generated content is coherent and consistent. The rulebook clearly explains the core concepts, and the art style guide provides a strong vision. The balance analysis correctly identifies a potential outlier.",
    issues_found: []
  }
};