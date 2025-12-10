# Mini Agent Workflow Engine (FastAPI)

This is a small backend project for the **AI Engineering Internship assignment**.  
It implements a minimal workflow/graph engine using **FastAPI**.:contentReference[oaicite:1]{index=1}  

## Features

- Nodes = Python functions (tools) that read and modify a shared state (dict).
- State = JSON/dict that flows from node to node.
- Edges = mapping of which node runs next.
- Branching = a node can choose the next node using `_next_node` in state.
- Looping = a node can loop by setting `_next_node` to itself (or any node).
- FastAPI endpoints:
  - `POST /graph/create`
  - `POST /graph/run`
  - `GET /graph/state/{run_id}`

Example workflow implemented: **Code Review Mini-Agent**  
(Option A from the assignment: extract functions → check complexity → detect issues → suggest improvements → loop until `quality_score >= threshold`).

---

## How to run (step-by-step)

### 1. Install Python

Make sure you have **Python 3.9+** installed.

Check:

```bash
python --version
