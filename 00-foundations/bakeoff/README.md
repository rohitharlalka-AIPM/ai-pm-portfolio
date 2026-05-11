# LLM Bake-off

Run the same prompts across Gemini 2.5 Flash, Gemini 2.5 Pro, and Groq's `llama-3.3-70b-versatile`, and produce a Markdown comparison report.

## Setup

Put your keys in `~/.ai-pm-secrets.env`:

```
GEMINI_API_KEY=...
GROQ_API_KEY=...
```

Edit `prompts.json` if you want different prompts.

## Run

```
uv run bakeoff.py
```

`uv` reads `pyproject.toml`, sets up an isolated environment, and executes the script. No global installs, no venv activation.

## Outputs

- `results.json` — raw per-cell results (latency, tokens, response, error).
- `results.md` — summary table, per-prompt detail, and per-model metrics.
- stdout — one line per model with median latency and error count.
