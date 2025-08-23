import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';

interface GeneratedGameProps {
  gameState: any; // The entire final_state from the backend
}

const GeneratedGame: React.FC<GeneratedGameProps> = ({ gameState }) => {
  if (!gameState) {
    return null;
  }

  const { game_design, rulebook, art_style_guide, card_artwork, balance_analysis, qa_report } = gameState;

  return (
    <div className="w-full max-w-3xl mx-auto mt-8">
      <Accordion type="single" collapsible defaultValue='game-design' className="w-full">
        {game_design && (
          <AccordionItem value="game-design">
            <AccordionTrigger className='text-2xl font-bold'>{game_design.game_name}</AccordionTrigger>
            <AccordionContent>
              <Card>
                <CardHeader>
                  <CardTitle>Game Concept</CardTitle>
                </CardHeader>
                <CardContent>
                  <ReactMarkdown rehypePlugins={[rehypeRaw]}>{game_design.concept}</ReactMarkdown>
                  <h3 className="font-bold mt-4">Core Mechanics:</h3>
                  <ul className='list-disc pl-5'>
                    {game_design.core_mechanics.map((mechanic: string) => <li key={mechanic}>{mechanic}</li>)}
                  </ul>
                  <h3 className="font-bold mt-4">Win Condition:</h3>
                  <ReactMarkdown rehypePlugins={[rehypeRaw]}>{game_design.win_condition}</ReactMarkdown>
                  <h3 className="font-bold mt-4">Game Flow:</h3>
                  <ReactMarkdown rehypePlugins={[rehypeRaw]}>{game_design.game_flow}</ReactMarkdown>
                </CardContent>
              </Card>
            </AccordionContent>
          </AccordionItem>
        )}

        {rulebook && (
          <AccordionItem value="rulebook">
            <AccordionTrigger className='text-xl font-bold'>Rulebook</AccordionTrigger>
            <AccordionContent>
                <Card>
                    <CardContent className='pt-6'>
                        <ReactMarkdown rehypePlugins={[rehypeRaw]}>{rulebook.rulebook}</ReactMarkdown>
                    </CardContent>
                </Card>
            </AccordionContent>
          </AccordionItem>
        )}

        {art_style_guide && (
          <AccordionItem value="art-style-guide">
            <AccordionTrigger className='text-xl font-bold'>Art Style Guide</AccordionTrigger>
            <AccordionContent>
                <Card>
                    <CardContent className='pt-6'>
                        <ReactMarkdown rehypePlugins={[rehypeRaw]}>{art_style_guide.art_style_guide}</ReactMarkdown>
                    </CardContent>
                </Card>
            </AccordionContent>
          </AccordionItem>
        )}

        {game_design && game_design.starter_cards && game_design.starter_cards.length > 0 && (
          <AccordionItem value="starter-cards">
            <AccordionTrigger className='text-xl font-bold'>Starter Cards</AccordionTrigger>
            <AccordionContent>
                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                    {game_design.starter_cards.map((card: any) => (
                        <Card key={card.name}>
                            <CardHeader>
                                <CardTitle>{card.name}</CardTitle>
                                <p className='text-sm text-muted-foreground'>{card.type} - Cost: {card.cost}</p>
                            </CardHeader>
                            <CardContent>
                                <p>{card.text}</p>
                                {card.flavor_text && <p className='text-sm italic text-muted-foreground mt-2'>{card.flavor_text}</p>}
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </AccordionContent>
          </AccordionItem>
        )}

        {card_artwork && card_artwork.artwork && Object.keys(card_artwork.artwork).length > 0 && (
          <AccordionItem value="card-artwork">
            <AccordionTrigger className='text-xl font-bold'>Card Artwork Descriptions</AccordionTrigger>
            <AccordionContent>
                <Card>
                    <CardContent className='pt-6'>
                        <ul className='list-disc pl-5'>
                        {Object.keys(card_artwork.artwork).map((cardName) => (
                            <li key={cardName} className='mb-2'>
                            <strong>{cardName}:</strong>
                            <ReactMarkdown rehypePlugins={[rehypeRaw]}>{card_artwork.artwork[cardName].artwork_description}</ReactMarkdown>
                            <p className='text-sm text-muted-foreground'>Title Font: {card_artwork.artwork[cardName].title_font}</p>
                            <p className='text-sm text-muted-foreground'>Body Font: {card_artwork.artwork[cardName].body_font}</p>
                            <p className='text-sm text-muted-foreground'>Iconography: {card_artwork.artwork[cardName].iconography.join(', ')}</p>
                            </li>
                        ))}
                        </ul>
                    </CardContent>
                </Card>
            </AccordionContent>
          </AccordionItem>
        )}

        {balance_analysis && (
          <AccordionItem value="balance-analysis">
            <AccordionTrigger className='text-xl font-bold'>Balance Analysis</AccordionTrigger>
            <AccordionContent>
                <Card>
                    <CardContent className='pt-6'>
                        <ReactMarkdown rehypePlugins={[rehypeRaw]}>{balance_analysis.balance_analysis}</ReactMarkdown>
                        <h3 className="font-bold mt-4">Suggested Changes:</h3>
                        <ul className='list-disc pl-5'>
                        {balance_analysis.suggested_card_changes.map((change: any) => (
                            <li key={change.card_name} className='mb-2'>
                            <strong>{change.card_name}:</strong> {change.suggested_change} - <em className='text-muted-foreground'>{change.reasoning}</em>
                            </li>
                        ))}
                        </ul>
                    </CardContent>
                </Card>
            </AccordionContent>
          </AccordionItem>
        )}

        {qa_report && (
          <AccordionItem value="qa-report">
            <AccordionTrigger className='text-xl font-bold'>QA Report</AccordionTrigger>
            <AccordionContent>
                <Card>
                    <CardContent className='pt-6'>
                        <ReactMarkdown rehypePlugins={[rehypeRaw]}>{qa_report.qa_summary}</ReactMarkdown>
                        {qa_report.issues_found && qa_report.issues_found.length > 0 &&
                            <>
                                <h3 className="font-bold mt-4">Issues Found:</h3>
                                <ul className='list-disc pl-5'>
                                {qa_report.issues_found.map((issue: any) => (
                                    <li key={issue.issue} className='mb-2'>
                                    <strong>{issue.issue}:</strong> ({issue.location}) - <span className='text-muted-foreground'>{issue.suggestion}</span>
                                    </li>
                                ))}
                                </ul>
                            </>
                        }
                    </CardContent>
                </Card>
            </AccordionContent>
          </AccordionItem>
        )}
      </Accordion>
    </div>
  );
};

export default GeneratedGame;
