from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

from .engine import engine
from .models import (
    GraphCreateRequest,
    GraphCreateResponse,
    GraphRunRequest,
    GraphRunResponse,
    GraphStateResponse,
)
from .workflows import DEFAULT_GRAPH_ID


app = FastAPI(
    title="Mini Agent Workflow Engine",
    description="A small workflow/graph engine for the AI Engineering assignment.",
    version="1.0.0",
)

# Determine project root and static folder
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Mount /static to serve index.html and other assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def root() -> Dict[str, Any]:
    """
    Simple root endpoint to check if the API is running.
    """
    return {
        "message": "Mini workflow engine is running 🚀",
        "example_graph_id": DEFAULT_GRAPH_ID,
        "hint": "Use POST /graph/run with this graph_id and your code.",
    }


@app.get("/ui")
def ui_redirect():
    """
    Redirect to the static UI page.
    """
    return RedirectResponse(url="/static/index.html")


@app.post("/graph/create", response_model=GraphCreateResponse)
def create_graph(request: GraphCreateRequest) -> GraphCreateResponse:
    graph_id = engine.create_graph(request)
    return GraphCreateResponse(graph_id=graph_id)


@app.post("/graph/run", response_model=GraphRunResponse)
def run_graph(request: GraphRunRequest) -> GraphRunResponse:
    try:
        run_record = engine.run_graph(request.graph_id, request.initial_state)
    except KeyError:
        raise HTTPException(status_code=404, detail="Graph not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return GraphRunResponse(
        run_id=run_record.run_id,
        final_state=run_record.current_state,
        log=run_record.log,
    )


@app.get("/graph/state/{run_id}", response_model=GraphStateResponse)
def get_state(run_id: str) -> GraphStateResponse:
    run_record = engine.get_run(run_id)
    if run_record is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    return GraphStateResponse(
        run_id=run_id,
        current_state=run_record.current_state,
        log=run_record.log,
    )
