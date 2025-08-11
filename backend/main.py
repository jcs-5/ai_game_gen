from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Dict
from fastapi.middleware.cors import CORSMiddleware
from backend.agents import app as agent_app
import uuid

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GameParameters(BaseModel):
    game_theme: str
    game_type: str
    player_count: Tuple[int, int]
    play_time: str
    complexity: str
    play_style: str
    art_style: str
    additional_notes: str

# In-memory storage for job status and results
job_storage: Dict[str, Dict] = {}

def run_agent_workflow(job_id: str, params: dict):
    """Helper function to run the agent workflow in the background."""
    print(f"--- Starting Agent Workflow for job {job_id} ---")
    job_storage[job_id] = {"status": "running", "result": None}
    try:
        final_state = agent_app.invoke(params)
        job_storage[job_id] = {"status": "complete", "result": final_state}
        print(f"--- Agent Workflow Complete for job {job_id} ---")
    except Exception as e:
        job_storage[job_id] = {"status": "failed", "result": str(e)}
        print(f"--- Agent Workflow Failed for job {job_id}: {e} ---")

@app.post("/generate-game/")
def generate_game(params: GameParameters, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    initial_state = params.dict()
    initial_state["revision_count"] = 0
    initial_state["max_revisions"] = 3 # Set the max number of revisions
    background_tasks.add_task(run_agent_workflow, job_id, initial_state)
    return {"job_id": job_id}

@app.get("/game-status/{job_id}")
def get_game_status(job_id: str):
    job = job_storage.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/")
def read_root():
    return {"Hello": "World"}