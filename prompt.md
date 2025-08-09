# Create a Complete AI Board Game Generator Application
I want you to build a comprehensive web application that generates complete, printable card games using AI agents. The app should work as follows:
## Core Functionality:

User provides inputs: game theme (e.g., "space exploration," "medieval fantasy"), game type (cooperative, competitive, deck-building, drafting, etc.), player count (2-6 players), estimated play time, complexity level (light/medium/heavy), and art style preferences
A coordinated team of AI agents processes these inputs to generate a complete, balanced, and playable card game
Output includes full rulebook, complete card set with artwork, and print-ready PDFs

## Required AI Agent Team Structure:

Game Designer Agent: Creates core mechanics, win conditions, game flow, and ensures the design fits the specified parameters
Balance & Math Agent: Calculates card costs, power levels, probability distributions, and ensures fair gameplay
Rules Writer Agent: Produces clear, comprehensive rulebooks with examples and edge case clarifications
Art Director Agent: Generates consistent visual themes, card layouts, iconography, and art style guidelines
Asset Generator Agent: Creates all card artwork, icons, and visual elements in the specified style
Quality Assurance Agent: Reviews the complete game for consistency, playability issues, and rule clarity

## Technical Requirements:

Modern web interface with intuitive input forms
Real-time progress tracking as agents work
Interactive preview of generated cards before final output
Export functionality for print-ready PDFs (standard card sizes: 2.5" x 3.5" poker size)
Ability to regenerate specific cards or adjust balance
Save/load projects for iteration

# Output Specifications:

Complete rulebook (PDF format, 4-12 pages)
Full card set (typically 60-120 cards depending on game type)
Quick reference guide/player aids
All cards formatted for home printing with cut guides
Optional: Box art and component designs

# Game Types to Support:

Deck-building (like Dominion)
Trading card game mechanics (like Magic: The Gathering)
Drafting games (like Sushi Go)
Engine building (like Star Realms)
Trick-taking (like Fox in the Forest)
Cooperative card games
Social deduction card games

# Key Features:

Balancing algorithms to ensure no overpowered cards
Playtesting simulation to identify potential issues
Multiple art style options (minimalist, detailed illustrations, pixel art, etc.)
Customizable card templates and layouts
Integration with print-on-demand services (optional)

Build this as a single-page application using modern web technologies. Focus on creating a seamless user experience where someone can go from initial concept to printed game in under an hour. The AI agents should work collaboratively, with each agent's output informing the others to create a cohesive final product.
Include error handling, input validation, and the ability to refine outputs through iterative feedback. Make the interface intuitive enough for non-game-designers to use effectively.

Use simple front and back end technologies, do not over complicate things
Use gemini llms for the models, this would be for both rule / game / card design agents as well as image. 
Use shadcn-ui 
Use a fastapi back end 
Use an agent framework that works well with google gemini models (ex. langgraph or google agent sdk)