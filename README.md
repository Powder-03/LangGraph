# LangGraph — Learning Workflows

This repository contains a set of small LangGraph workflows implemented as Jupyter notebooks and a helper app. These notebooks were created while learning LangGraph and demonstrate common patterns: stateful graphs, prompt chaining, structured output, conditional routing, and parallel reducers.

## Contents
Top-level files and notebooks in this repo:

- `1_bmi_workflow.ipynb` — BMI calculation and simple routing example.
- `2_simple_llm_workflow.ipynb` — Simple LLM question/answer workflow.
- `3_prompt_chaining.ipynb` — Prompt chaining pattern (outline -> blog post).
- `4_batsman_parallel_workflow.ipynb` — Parallel computation + reducer example.
- `5_UPSC_essay_workflow.ipynb` — Multi-evaluator essay evaluation pipeline.
- `6_quadratic_equation.ipynb` — Quadratic equation solver/workflow.
- `7_review_reply_workflow.ipynb` — Review analysis: sentiment, diagnosis, and response routing.
- `8_X_post_generation.ipynb` — Experimental/post-generation workflow.
- `day0_test_installation.ipynb` — Environment and dependency test steps.
- `requirements.txt` — Python dependencies used by the notebooks.

## High-level overview

Each notebook demonstrates a complete LangGraph workflow. Typical structure used across notebooks:

- Define a state type (TypedDict or Pydantic model).
- Implement node functions that accept and return (partial) state dictionaries.
- Build a `StateGraph`, add nodes and edges (including conditional edges when needed).
- Compile the graph and invoke it with an `initial_state` payload.

Notebooks that use LLMs rely on an API client and environment variables. See "Credentials & environment" below.

## Quick start

1) Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Provide LLM credentials and other secrets by creating a `.env` file in the repository root. Examples (fill with your real values):

```env
# Google or Gemini style credentials (example variable names used in notebooks)
GOOGLE_API_KEY=your_google_api_key
# Azure OpenAI (if using):
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_KEY=your_azure_key

# Optional data stores used by `app.py` or demos
DATABASE_URL=sqlite:///data.db
REDIS_URL=redis://localhost:6379/0
```

4) Open a notebook in Jupyter or VS Code and run its cells. Example: open `3_prompt_chaining.ipynb` and run all cells to see prompt chaining in action.

## How to run a workflow programmatically

The notebooks also include examples for running compiled graphs from Python. A minimal example:

```python
from langgraph.graph import StateGraph

# ... define your state type and nodes as shown in notebooks ...
graph = StateGraph(YourStateType)
# add nodes/edges
workflow = graph.compile()
initial_state = { 'title': 'My blog', 'review': '...' }
final_state = workflow.invoke(initial_state)
print(final_state)
```

`app.py` provides a concrete example (`SalesAgent`) showing how to assemble a graph in a regular Python script and invoke it.

## Notebooks summary (short)

- `1_bmi_workflow.ipynb` — Demonstrates simple numeric computation nodes and branching based on BMI label.
- `2_simple_llm_workflow.ipynb` — Shows how to call an LLM from a node and attach the response to the state.
- `3_prompt_chaining.ipynb` — Two-step pipeline: `create_outline` then `create_blog` (prompt chaining). Useful to see how to pass intermediate state between nodes.
- `4_batsman_parallel_workflow.ipynb` — Demonstrates parallel node execution and aggregation (useful for divide-and-conquer tasks).
- `5_UPSC_essay_workflow.ipynb` — Multi-evaluator pattern: run several critics (language, analysis, structure), then a final aggregator.
- `6_quadratic_equation.ipynb` — Parser and solver example for quadratic equations.
- `7_review_reply_workflow.ipynb` — Uses structured output (Pydantic) to reliably parse sentiment/diagnosis and routes to different response flows.
- `8_X_post_generation.ipynb` — Misc experiments with post-generation editing and filters.
- `day0_test_installation.ipynb` — Sanity checks for environment and quick dependency tests.

## Troubleshooting & tips

- Authentication (401) errors: check your provider-specific keys and endpoints in `.env`. Restart your kernel/terminal after editing `.env`.
- Slow responses (~15–40s): often caused by free-tier LLM subscriptions, network latency, or long content generation. Using a smaller/faster model or upgrading your plan reduces latency.
- `Literal` and typing: import `Literal` from the standard library `typing` for Python 3.8+:

```python
from typing import Literal
```

- If you see parsing failures when using `with_structured_output`, check the Pydantic model definitions and prompt format.

## Development notes

- The notebooks are intentionally self-contained and meant for exploration. If you want to convert any notebook into a script, extract the graph-building code and the invocation snippet.
- Consider adding unit tests for pure functions (non-LLM parts) to speed up iterative development.

## Next steps / suggestions

- I can expand any notebook's README subsection with concrete example payloads and expected outputs.
- I can also convert one notebook into a runnable script and add a small test harness.

## License
This repository is provided for learning and experimentation.

---

If you'd like, tell me which notebook to document next and I will add example payloads and expected outputs for it.
