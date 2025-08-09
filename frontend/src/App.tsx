
import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import GeneratedGame from "@/components/GeneratedGame";
import { dummyGameState } from "@/lib/dummy-data"; // Import the dummy data

const USE_DUMMY_DATA = true; // Set to true to use dummy data

function App() {
  const [playerCount, setPlayerCount] = React.useState<[number, number]>([2, 4]);
  const [gameTheme, setGameTheme] = React.useState("");
  const [gameType, setGameType] = React.useState("");
  const [playTime, setPlayTime] = React.useState("");
  const [complexity, setComplexity] = React.useState("");
  const [playStyle, setPlayStyle] = React.useState("");
  const [artStyle, setArtStyle] = React.useState("");
  const [additionalNotes, setAdditionalNotes] = React.useState("");

  const [loading, setLoading] = React.useState(false);
  const [generatedGame, setGeneratedGame] = React.useState(null);

  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/game-status/${jobId}`);
        const data = await response.json();

        if (data.status === "complete") {
          setGeneratedGame(data.result);
          setLoading(false);
          clearInterval(interval);
        } else if (data.status === "failed") {
          console.error("Game generation failed:", data.result);
          setLoading(false);
          clearInterval(interval);
        }
      } catch (error) {
        console.error("Error polling job status:", error);
        setLoading(false);
        clearInterval(interval);
      }
    }, 5000); // Poll every 5 seconds
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setGeneratedGame(null);

    if (USE_DUMMY_DATA) {
      setTimeout(() => {
        setGeneratedGame(dummyGameState as any);
        setLoading(false);
      }, 1000); // Simulate a 1-second delay
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/generate-game/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          game_theme: gameTheme,
          game_type: gameType,
          player_count: playerCount,
          play_time: playTime,
          complexity: complexity,
          play_style: playStyle,
          art_style: artStyle,
          additional_notes: additionalNotes,
        }),
      });

      const data = await response.json();
      if (data.job_id) {
        pollJobStatus(data.job_id);
      } else {
        setLoading(false);
      }
    } catch (error) {
      console.error("Error starting game generation:", error);
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-svh flex-col items-center p-4 md:p-8">
      <Card className="w-full max-w-3xl">
        <CardHeader>
          <CardTitle>AI Board Game Generator</CardTitle>
          <CardDescription>
            Create a complete, printable card game using AI agents.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="grid gap-6">
            {/* ... (form fields are unchanged) ... */}
            <div className="grid gap-2">
              <Label htmlFor="game-theme">Game Theme</Label>
              <Input id="game-theme" placeholder="e.g., Space Exploration, Medieval Fantasy" value={gameTheme} onChange={(e) => setGameTheme(e.target.value)} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="grid gap-2">
                <Label htmlFor="game-type">Game Type</Label>
                <Select onValueChange={setGameType} value={gameType}>
                  <SelectTrigger id="game-type">
                    <SelectValue placeholder="Select a game type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="deck-building">Deck-building</SelectItem>
                    <SelectItem value="trading-card-game">Trading Card Game</SelectItem>
                    <SelectItem value="drafting">Drafting</SelectItem>
                    <SelectItem value="engine-building">Engine Building</SelectItem>
                    <SelectItem value="trick-taking">Trick-taking</SelectItem>
                    <SelectItem value="social-deduction">Social Deduction</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="player-count">Player Count</Label>
                <div className="flex items-center gap-4">
                  <Slider
                    id="player-count"
                    min={1}
                    max={6}
                    step={1}
                    value={playerCount}
                    onValueChange={setPlayerCount}
                  />
                  <div className="text-sm font-medium">
                    {playerCount[0]} - {playerCount[1]} players
                  </div>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="grid gap-2">
                <Label htmlFor="play-time">Estimated Play Time</Label>
                <Select onValueChange={setPlayTime} value={playTime}>
                  <SelectTrigger id="play-time">
                    <SelectValue placeholder="Select play time" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="15-30">15-30 minutes</SelectItem>
                    <SelectItem value="30-60">30-60 minutes</SelectItem>
                    <SelectItem value="60-90">60-90 minutes</SelectItem>
                    <SelectItem value="90+">90+ minutes</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="complexity">Complexity Level</Label>
                <Select onValueChange={setComplexity} value={complexity}>
                  <SelectTrigger id="complexity">
                    <SelectValue placeholder="Select complexity" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="heavy">Heavy</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="play-style">Play Style</Label>
              <Select onValueChange={setPlayStyle} value={playStyle}>
                <SelectTrigger id="play-style">
                  <SelectValue placeholder="Select play style" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="co-operative">Co-operative</SelectItem>
                  <SelectItem value="competitive">Competitive</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="art-style">Art Style Preferences</Label>
              <Input id="art-style" placeholder="e.g., Minimalist, Detailed Illustrations, Pixel Art" value={artStyle} onChange={(e) => setArtStyle(e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="additional-notes">Additional Notes</Label>
              <Textarea id="additional-notes" placeholder="Any other details or specific requests..." value={additionalNotes} onChange={(e) => setAdditionalNotes(e.target.value)} />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Generating..." : "Generate Game"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {loading && (
        <div className="mt-8 text-center">
          <p>Generating your game, please wait...</p>
          {/* You can add a spinner or a more complex loading indicator here */}
        </div>
      )}

      {generatedGame && <GeneratedGame gameState={generatedGame} />}
    </div>
  );
}

export default App;
