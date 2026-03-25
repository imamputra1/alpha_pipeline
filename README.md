# Hypothesis_Gen

> An autonomous quantitative research orchestrator designed to reverse-engineer market inefficiencies using market microstructure principles.
> 
> *Note: This is an experimental research tool. It is designed for alpha discovery and hypothesis generation, not for direct live-execution trading.*

Hypothesis_Gen is a state-machine-driven agentic framework built for quantitative researchers. It automates the tedious process of transforming raw market observations, academic papers, or Exploratory Data Analysis (EDA) into mathematically rigorous, falsifiable trading signals. 

Built with a strict adherence to software engineering best practices, it prioritizes deterministic outputs, type safety, and memory stability over rapid, reckless LLM generation.

## Architectural Philosophy

Unlike standard LLM wrappers, Hypothesis_Gen is engineered using a strict **Functional-Core, Imperative-Shell** architecture.

* **Deterministic State Machines:** Orchestrated via `LangGraph`, the pipeline strictly enforces a multi-agent workflow (Market Asymmetry -> Hypothesis Engineering -> Signal Architecture).
* **Fail-Safe Domain Logic:** Utilizing the `Result` monad (`Ok` / `Err`), business logic routing relies on pattern matching rather than unstructured `try/except` blocks. Domain errors (e.g., Look-Ahead Bias, Non-Stationarity) trigger graceful circuit breakers, preventing silent logic failures.
* **Strict Type Enforcement:** Native integration with `Pydantic` ensures that LLM hallucinations are caught at the infrastructure layer. If the model fails to return a valid JSON matching the exact mathematical schema, the agent automatically loops for a correction.
* **Model-Agnostic Dependency Injection:** The LLM client is abstracted behind a `Protocol`. The core logic does not depend on Google, OpenAI, or Anthropic—allowing seamless model swapping via the UI without touching the core source code.

## Core Features

* **MAD (Market Asymmetry Detective):** Parses input documents to identify the counterparty, limits to arbitrage, and microstructural rationale.
* **HE (Hypothesis Engineer):** Translates economic rationales into strict Null and Alternative hypotheses, defining the target variable and execution horizon.
* **SA (Signal Architect):** The crown jewel. Constructs the mathematical signal formulation (in LaTeX), execution logic, and variable dictionary, heavily guarded against Look-Ahead Bias.
* **Streamlit Shell:** A local, imperative web UI providing native PDF/CSV parsing, session state management, and real-time LaTeX rendering.

## Installation

This project utilizes `uv` for lightning-fast, reproducible dependency management.

```bash
# 1. Clone the repository
git clone https://github.com/imamputra1/hypothesis_gen.git
cd hypothesis_gen

# 2. Sync dependencies and build the virtual environment
uv sync --all-extras

# 3. Configure Credentials
# Create a .env file in the root directory
echo 'GEMINI_API_KEY="your_api_key_here"' > .env
```

## Usage

Hypothesis_Gen hides complex LangGraph orchestration behind a clean Streamlit interface.

To start the local research laboratory:

```bash
uv run streamlit run app.py
```

1. Open the provided localhost URL in your browser.
2. Enter your API Key (if not already set in .env).
3. Upload a research paper (.pdf) or an EDA summary (.csv).
4. Execute the pipeline and observe the real-time compilation of your quantitative architecture.

## Programmatic Access (Headless Mode)

If you wish to bypass the UI and use Hypothesis_Gen inside your own scripts or Jupyter Notebooks:

```python
from src.infrastructure.gemini_gateway import GeminiGateway
from src.workflow.graph_builder import build_alpha_graph
from src.types.state import PipelineState

# 1. Initialize the Gateway
gateway = GeminiGateway(model_name="gemini-2.5-pro")

# 2. Compile the Graph
graph = build_alpha_graph(gateway)

# 3. Define the Initial State
initial_state: PipelineState = {
    "raw_input": "Order book imbalance over 50ms implies toxic flow...",
    "error_logs": [],
    "retry_count": 0
}

# 4. Execute
final_state = graph.invoke(initial_state)
print(final_state["signal_architecture"]["formula_latex"])
```

## Development & CI/CD

We maintain a strict 100% pass rate for our Continuous Integration pipeline. If you are developing locally, ensure all checks pass before committing.
```bash
# 1. Format and Lint
uv run ruff format .
uv run ruff check .

# 2. Static Type Checking (Strict Mode)
uv run mypy src/

# 3. Test Suite (Unit & Integration)
uv run pytest -v tests/
```

## Roadmap

    [x] V1.0: Core Architecture, Result Monads, LangGraph Orchestration, Streamlit UI.
    [ ] V2.0: Multi-Document Memory (RAG integration via VectorDB for cross-referencing multiple journals).
    [ ] V2.1: Multi-Vendor API Routing Matrix (dynamic switching between OpenAI, Anthropic, and Local models per agent).
    [ ] V3.0: Cloud-native transition (migration from Streamlit to SvelteKit + FastAPI backend for multi-user scaling).

## Disclaimer

This software is provided for educational and research purposes only. The mathematical signals and hypotheses generated by this AI system do not constitute financial advice. Algorithmic trading involves significant risk of loss.

## License

This project is licensed under the GNU AGPLv3 License.

This is a strong copyleft license. You are free to use, modify, and distribute this software. However, if you modify the code and provide it as a service over a network (e.g., hosting a modified version on a web server), you must publicly share your modified source code under the same AGPLv3 license.

For more details, see the `LICENSE` file.
