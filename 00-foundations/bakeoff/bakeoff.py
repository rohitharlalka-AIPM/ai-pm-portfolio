"""LLM bake-off: run the same prompts across multiple models and report results."""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
SECRETS_PATH = Path.home() / ".ai-pm-secrets.env"
PROMPTS_PATH = HERE / "prompts.json"
RESULTS_JSON = HERE / "results.json"
RESULTS_MD = HERE / "results.md"

TEMPERATURE = 0.2
MAX_TOKENS = 800

MODELS = [
    {"label": "gemini-2.5-flash", "provider": "gemini", "model": "gemini-2.5-flash"},
    {"label": "gemini-2.5-pro", "provider": "gemini", "model": "gemini-2.5-pro"},
    {"label": "llama-3.3-70b-versatile", "provider": "groq", "model": "llama-3.3-70b-versatile"},
]


def call_gemini(client: Any, model: str, prompt: str) -> dict[str, Any]:
    from google.genai import types

    cfg = types.GenerateContentConfig(temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
    resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
    text = getattr(resp, "text", None) or ""
    usage = getattr(resp, "usage_metadata", None)
    in_tok = getattr(usage, "prompt_token_count", None) if usage else None
    out_tok = getattr(usage, "candidates_token_count", None) if usage else None
    return {"text": text, "input_tokens": in_tok, "output_tokens": out_tok}


def call_groq(client: Any, model: str, prompt: str) -> dict[str, Any]:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    text = resp.choices[0].message.content or ""
    usage = getattr(resp, "usage", None)
    in_tok = getattr(usage, "prompt_tokens", None) if usage else None
    out_tok = getattr(usage, "completion_tokens", None) if usage else None
    return {"text": text, "input_tokens": in_tok, "output_tokens": out_tok}


def run_one(provider_clients: dict[str, Any], spec: dict[str, str], prompt: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        if spec["provider"] == "gemini":
            out = call_gemini(provider_clients["gemini"], spec["model"], prompt)
        elif spec["provider"] == "groq":
            out = call_groq(provider_clients["groq"], spec["model"], prompt)
        else:
            raise ValueError(f"unknown provider {spec['provider']}")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "model": spec["label"],
            "latency_ms": latency_ms,
            "input_tokens": out["input_tokens"],
            "output_tokens": out["output_tokens"],
            "response_text": out["text"],
            "error": None,
        }
    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "model": spec["label"],
            "latency_ms": latency_ms,
            "input_tokens": None,
            "output_tokens": None,
            "response_text": "",
            "error": f"{type(e).__name__}: {e}",
        }


def build_clients() -> dict[str, Any]:
    load_dotenv(SECRETS_PATH)
    clients: dict[str, Any] = {}
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    if not gemini_key:
        raise SystemExit("GEMINI_API_KEY missing in ~/.ai-pm-secrets.env")
    if not groq_key:
        raise SystemExit("GROQ_API_KEY missing in ~/.ai-pm-secrets.env")
    from google import genai
    from groq import Groq

    clients["gemini"] = genai.Client(api_key=gemini_key)
    clients["groq"] = Groq(api_key=groq_key)
    return clients


def cell_verdict(cell: dict[str, Any]) -> str:
    if cell["error"]:
        return "❌ error"
    tok = cell["output_tokens"]
    tok_s = f"{tok} tok" if tok is not None else "? tok"
    return f"✅ {cell['latency_ms']}ms · {tok_s}"


def render_markdown(prompts: list[dict[str, str]], results: list[dict[str, Any]]) -> str:
    model_labels = [m["label"] for m in MODELS]
    by_prompt = {r["prompt_id"]: r for r in results}

    lines: list[str] = ["# LLM Bake-off Report", ""]
    lines.append("## Summary")
    lines.append("")
    lines.append("| Prompt | " + " | ".join(model_labels) + " |")
    lines.append("|" + "---|" * (len(model_labels) + 1))
    for p in prompts:
        row = by_prompt[p["id"]]
        cells = [cell_verdict(row["cells"][m]) for m in model_labels]
        lines.append(f"| `{p['id']}` ({p['category']}) | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Per-prompt detail")
    lines.append("")
    for p in prompts:
        row = by_prompt[p["id"]]
        lines.append(f"### {p['id']} — {p['category']}")
        lines.append("")
        lines.append(f"> {p['prompt']}")
        lines.append("")
        for m in model_labels:
            c = row["cells"][m]
            lines.append(f"#### {m}")
            lines.append("")
            if c["error"]:
                lines.append(f"**Error:** {c['error']}")
            else:
                lines.append(
                    f"_latency_: {c['latency_ms']}ms · _input_tokens_: {c['input_tokens']} · "
                    f"_output_tokens_: {c['output_tokens']}"
                )
                lines.append("")
                lines.append(c["response_text"].strip() or "_(empty response)_")
            lines.append("")

    lines.append("## Metrics summary")
    lines.append("")
    lines.append("| Model | Median latency (ms) | Mean output tokens | Errors |")
    lines.append("|---|---|---|---|")
    for m in model_labels:
        cells = [by_prompt[p["id"]]["cells"][m] for p in prompts]
        latencies = [c["latency_ms"] for c in cells if not c["error"]]
        outs = [c["output_tokens"] for c in cells if not c["error"] and c["output_tokens"] is not None]
        errs = sum(1 for c in cells if c["error"])
        med = int(statistics.median(latencies)) if latencies else None
        mean_out = round(statistics.mean(outs), 1) if outs else None
        lines.append(f"| {m} | {med if med is not None else '-'} | {mean_out if mean_out is not None else '-'} | {errs} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not PROMPTS_PATH.exists():
        raise SystemExit(f"prompts file not found: {PROMPTS_PATH}")
    prompts = json.loads(PROMPTS_PATH.read_text())
    clients = build_clients()

    results: list[dict[str, Any]] = []
    for p in prompts:
        cells: dict[str, Any] = {}
        for spec in MODELS:
            cells[spec["label"]] = run_one(clients, spec, p["prompt"])
        results.append({"prompt_id": p["id"], "category": p["category"], "prompt": p["prompt"], "cells": cells})

    RESULTS_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    RESULTS_MD.write_text(render_markdown(prompts, results))

    for spec in MODELS:
        label = spec["label"]
        cells = [r["cells"][label] for r in results]
        latencies = [c["latency_ms"] for c in cells if not c["error"]]
        errs = sum(1 for c in cells if c["error"])
        med = int(statistics.median(latencies)) if latencies else -1
        print(f"model={label} median_latency={med} errors={errs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
