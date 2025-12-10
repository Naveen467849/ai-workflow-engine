from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class GraphCreateRequest(BaseModel):
    """
    Request body for POST /graph/create

    Example JSON:
    {
      "nodes": ["extract_functions", "check_complexity"],
      "edges": {
        "extract_functions": "check_complexity",
        "check_complexity": null
      },
      "start_node": "extract_functions"
    }
    """
    nodes: List[str]
    edges: Dict[str, Optional[str]]
    start_node: str


class GraphCreateResponse(BaseModel):
    graph_id: str


class GraphRunRequest(BaseModel):
    """
    Request body for POST /graph/run

    Example JSON:
    {
      "graph_id": "some-id",
      "initial_state": {
        "code": "def hello():\n    print('hi')",
        "quality_threshold": 0.8
      }
    }
    """
    graph_id: str
    initial_state: Dict[str, Any] = {}


class ExecutionStep(BaseModel):
    step_number: int
    node: str
    state_snapshot: Dict[str, Any]


class GraphRunResponse(BaseModel):
    run_id: str
    final_state: Dict[str, Any]
    log: List[ExecutionStep]


class GraphStateResponse(BaseModel):
    run_id: str
    current_state: Dict[str, Any]
    log: List[ExecutionStep]
