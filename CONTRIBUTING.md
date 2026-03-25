# Contributing to Alpha Pipeline

Thank you for your interest in contributing to Alpha Pipeline. 

As an open-source research tool focused on quantitative finance and market microstructure, maintaining the mathematical integrity and architectural stability of this pipeline is our highest priority. We welcome contributions, whether they are bug fixes, new agent logic, or integrations with new LLM providers, provided they adhere strictly to our engineering standards.

## Architectural Constraints & Philosophy

Before writing any code, please understand the core principles of this repository. Pull Requests (PRs) that violate these principles will not be merged.

1. **Strict Functional-Core:** Agents (located in `src/agents/`) must remain pure functions. They must not execute direct network calls, mutate external state, or contain side-effects. All LLM interactions must be passed through the dependency-injected `LLMGateway` protocol.
2. **Deterministic Output:** LLM hallucinations are a systemic risk. All LLM outputs must be coerced and validated through rigid `Pydantic` schemas. Do not rely on loose dictionary parsing.
3. **No Silent Failures:** Do not use standard Python `try/except` blocks to handle domain logic or routing. You must use the `Result` monad (`Ok`, `Err`). If a mathematical constraint is violated (e.g., Look-Ahead Bias), return an explicit `Err` so the LangGraph state machine can trigger the appropriate circuit breaker.
4. **Type Safety:** This project enforces strict type hinting. Your code must pass `mypy --strict` without exceptions.

## Development Environment Setup

We use `uv` for deterministic dependency management.

1. Fork the repository to your own GitHub account.
2. Clone your fork locally:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/alpha_pipeline.git](https://github.com/YOUR_USERNAME/alpha_pipeline.git)
   cd alpha_pipeline
   ```
3. Sync the environment and install all development dependencies:
   ```bash
   uv sync --all-extras
   ```
4. Set up your local `.env` file with the necessary API keys for testing.

## The Contribution Workflow

1. Branching: Create a new branch for your work. Use a descriptive naming convention:
   ```bash
   git checkout -b feature/add-anthropic-gateway
   # or
   git checkout -b fix/sa-agent-latex-rendering
   ```
2. Development: Write your code. Ensure you add corresponding unit tests in the tests/ directory for any new logic.
3. Pre-Commit Validation: Before committing, you MUST run the entire validation suite locally. Our Continuous Integration (CI) pipeline will reject your PR if any of these fail:
   ```bash
   # Format the code
   uv run ruff format .
   # Run the linter
   uv run ruff check .
   # Verify static types
   uv run mypy src/
   # Run the test suite
   uv run pytest -v tests/
   ```
4. Commit & Push: Commit your changes with clear, descriptive commit messages. Push the branch to your fork.
5. Pull Request: Open a Pull Request against the main branch of the upstream repository.

## Pull Request Guidelines

When opening a PR, please include the following in your description:

    Objective: What problem does this PR solve?
    Architectural Changes: Did you modify any types, schemas, or routing logic?
    Testing: Confirm that you have run the validation suite and added new tests if necessary.

## Reporting Issues

If you discover a bug or have a feature request, please open an Issue on GitHub. Include:
* A clear description of the problem or proposal.
* Steps to reproduce the bug.
* Expected vs. actual behavior.
* Relevant system logs or error traces.

Thank you for helping us build a more robust and scientifically rigorous quantitative research pipeline.
