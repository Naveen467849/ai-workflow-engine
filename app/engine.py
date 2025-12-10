from typing import Dict, Callable, Any, Optional, List
from uuid import uuid4

from .models import GraphCreateRequest, ExecutionStep


ToolFunc = Callable[[Dict[str, Any]], Dict[str, Any]]


class GraphDefinition:
    """
    Represents a workflow graph: nodes, edges, and a starting node.
    """
    def __init__(
        self,
        graph_id: str,
        nodes: List[str],
        edges: Dict[str, Optional[str]],
        start_node: str,
    ):
        self.graph_id = graph_id
        self.nodes = nodes
        self.edges = edges
        self.start_node = start_node


class RunRecord:
    """
    Represents a single execution (run) of a graph.
    """
    def __init__(self, run_id: str, graph_id: str):
        self.run_id = run_id
        self.graph_id = graph_id
        self.log: List[ExecutionStep] = []
        self.current_state: Dict[str, Any] = {}


class GraphEngine:
    """
    Minimal workflow / graph engine.

    - tool_registry: maps node name -> Python function
    - graphs: stores GraphDefinition objects
    - runs: stores past run records
    """
    def __init__(self):
        self.tool_registry: Dict[str, ToolFunc] = {}
        self.graphs: Dict[str, GraphDefinition] = {}
        self.runs: Dict[str, RunRecord] = {}

    # ---------- Tool registry ----------

    def register_tool(self, name: str, func: ToolFunc) -> None:
        """
        Register a Python function as a tool / node.
        """
        self.tool_registry[name] = func

    # ---------- Graph management ----------

    def create_graph(self, request: GraphCreateRequest) -> str:
        """
        Create and store a new graph from a GraphCreateRequest.
        """
        graph_id = str(uuid4())
        graph = GraphDefinition(
            graph_id=graph_id,
            nodes=request.nodes,
            edges=request.edges,
            start_node=request.start_node,
        )
        self.graphs[graph_id] = graph
        return graph_id

    # ---------- Execution ----------

    def run_graph(
        self,
        graph_id: str,
        initial_state: Dict[str, Any],
        max_steps: int = 100,
    ) -> RunRecord:
        """
        Run a graph end-to-end.

        Supports:
        - Shared state dict
        - Branching: node can set state["_next_node"]
        - Looping: node can set state["_next_node"] = same node name
        - Stopping: node can set state["_stop"] = True
        """
        if graph_id not in self.graphs:
            raise KeyError(f"Graph {graph_id} not found")

        graph = self.graphs[graph_id]
        run_id = str(uuid4())
        run_record = RunRecord(run_id=run_id, graph_id=graph_id)

        state = dict(initial_state)
        current_node = graph.start_node
        step_number = 0

        while current_node is not None and step_number < max_steps:
            tool = self.tool_registry.get(current_node)
            if tool is None:
                raise ValueError(f"No tool registered for node '{current_node}'")

            # Run the node/tool
            state = tool(state)

            # Record step
            snapshot = dict(state)
            run_record.current_state = snapshot
            run_record.log.append(
                ExecutionStep(
                    step_number=step_number,
                    node=current_node,
                    state_snapshot=snapshot,
                )
            )

            # Decide next node: first check for special keys in state
            if state.get("_stop"):
                current_node = None
            else:
                next_from_state = state.pop("_next_node", None)
                if next_from_state is not None:
                    current_node = next_from_state
                else:
                    # Fall back to static edges
                    current_node = graph.edges.get(current_node)

            step_number += 1

        self.runs[run_id] = run_record
        return run_record

    # ---------- Run lookup ----------

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        return self.runs.get(run_id)


# Global engine instance used by the FastAPI app
engine = GraphEngine()
