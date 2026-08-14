"""
Frontier LLM inference — run models and save raw entities.

Calls Gemini, Claude, and/or Ollama models on test advisories, saves raw
entity responses to {model}-entities.jsonl. Span extraction happens
separately in frontier_extract.py.

Usage:
    PYTHONPATH=. python3 -m ner.frontier_infer \\
        --split data/split_slugs.json \\
        --markdown-dir data/alerts \\
        --output-dir data/frontier_results \\
        --models gemini-3.5-flash

    # Claude (needs ANTHROPIC_API_KEY): claude-sonnet / claude-opus / claude-haiku
    # map to specific model IDs via CLAUDE_MODEL_IDS below.
    PYTHONPATH=. python3 -m ner.frontier_infer \\
        --models claude-sonnet --chunk-size 15000

Output:
    data/frontier_results/{model}-entities.jsonl
    (one line per advisory: {slug, model, entities[], latency_sec, tokens})
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

from .frontier_llm_utils import (
    LABELS,
    load_clean_text,
    load_split,
)

CLAUDE_MODEL_IDS = {
    "claude-sonnet": "claude-sonnet-5",
    "claude-opus": "claude-opus-4-8",
    "claude-haiku": "claude-haiku-4-5-20251001",
}


def load_jsonl_records(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_labels_file(path: Path) -> list[str]:
    labels = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(labels, list) or not all(isinstance(l, str) for l in labels):
        print(f"{path} must be a JSON list of strings.", file=sys.stderr)
        sys.exit(1)
    return labels


def call_gemini(
    text: str,
    api_key: str,
    model: str = "gemini-3.5-flash",
    labels: list[str] | None = None,
) -> dict:
    """Call a Gemini model for NER via the google-genai SDK.

    Auth (pick one):
      - API key: GOOGLE_API_KEY / GEMINI_API_KEY (AI Studio billing + spend cap)
      - Vertex AI: GOOGLE_GENAI_USE_VERTEXAI=true + GOOGLE_CLOUD_PROJECT +
        GOOGLE_CLOUD_LOCATION, credentials from ADC
        (`gcloud auth application-default login`); bills the GCP project.

    Thinking is disabled (thinking_budget=0) — NER needs no reasoning tokens,
    and hidden thinking output is what made earlier runs slow (~100s/call)
    and expensive.
    """
    from google import genai
    from google.genai import types

    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true", "yes"):
        client = genai.Client(vertexai=True)  # project/location from env, auth from ADC
    else:
        client = genai.Client(api_key=api_key)

    label_list = ", ".join(labels if labels is not None else LABELS)
    prompt = f"""Extract named entities from the following cybersecurity text.
For each entity, return JSON with:
- text: the exact text of the entity (verbatim from the text)
- label: exactly one of these: {label_list}
- start_char: character index of the entity's first character
- end_char: character index right after the entity's last character

Be strict and precise. Prefer precision over recall — only extract entities that clearly match one of the given label types. Return the label EXACTLY as listed above (case-sensitive, lowercase).

Text:
{text}

Return a valid JSON array:
[{{"text": "...", "label": "...", "start_char": ..., "end_char": ...}}, ...]

If no clear matches, return an empty array: []
"""

    # Thinking must stay OFF: hidden reasoning tokens bill at the output rate
    # and made earlier runs ~50x more expensive. Older models take
    # thinking_budget=0; Gemini 3.6+ rejects that and takes
    # thinking_level="minimal" instead. Never fall back to a bare config —
    # that silently re-enables default thinking.
    # Gemma models (API-served, e.g. gemma-4-31b-it) have no thinking at
    # all and reject any thinking_config; a bare config is safe for them.
    if model.startswith("gemma"):
        fallback_configs = [types.GenerateContentConfig(temperature=0.0)]
    else:
        fallback_configs = [
            types.GenerateContentConfig(
                temperature=0.0,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
            types.GenerateContentConfig(
                temperature=0.0,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            ),
        ]

    start = time.time()
    response = None
    for i, config in enumerate(fallback_configs):
        try:
            response = client.models.generate_content(
                model=model, contents=prompt, config=config
            )
            break
        except Exception as e:
            error_str = str(e).lower()
            is_config_error = "thinking" in error_str or "invalid_argument" in error_str or "400" in error_str
            if not is_config_error or i == len(fallback_configs) - 1:
                raise
    latency = time.time() - start

    # Parse JSON from response
    result_text = (response.text or "").strip()
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    try:
        entities = json.loads(result_text)
    except json.JSONDecodeError:
        print(f"  ⚠ Gemini JSON parse error: {result_text[:100]}", file=sys.stderr)
        entities = []

    usage = getattr(response, "usage_metadata", None)
    tokens = getattr(usage, "total_token_count", None) or len(text) // 4

    return {"entities": entities, "latency_sec": latency, "tokens": tokens}


def call_claude(
    text: str,
    api_key: str,
    model_id: str,
    labels: list[str] | None = None,
) -> dict:
    """Call a Claude model for NER via the Anthropic SDK.

    Same prompt contract as call_gemini (label list, JSON array, char
    offsets that scoring doesn't trust — extraction locates entities by
    text search, same as every other model in this pipeline) so results
    are directly comparable and go through the same frontier_extract.py /
    frontier_score.py path.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    label_list = ", ".join(labels if labels is not None else LABELS)
    prompt = f"""Extract named entities from the following cybersecurity text.
For each entity, return JSON with:
- text: the exact text of the entity (verbatim from the text)
- label: exactly one of these: {label_list}
- start_char: character index of the entity's first character
- end_char: character index right after the entity's last character

Be strict and precise. Prefer precision over recall — only extract entities that clearly match one of the given label types. Return the label EXACTLY as listed above (case-sensitive, lowercase).

Text:
{text}

Return a valid JSON array:
[{{"text": "...", "label": "...", "start_char": ..., "end_char": ...}}, ...]

If no clear matches, return an empty array: []
"""

    start = time.time()
    try:
        response = client.messages.create(
            model=model_id,
            max_tokens=8192,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.BadRequestError as e:
        # Newer models reject an explicit temperature; retry without it
        if "temperature" in str(e).lower():
            response = client.messages.create(
                model=model_id,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )
        else:
            raise
    latency = time.time() - start

    result_text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    try:
        entities = json.loads(result_text)
    except json.JSONDecodeError:
        print(f"  ⚠ Claude JSON parse error: {result_text[:100]}", file=sys.stderr)
        entities = []

    tokens = response.usage.input_tokens + response.usage.output_tokens
    return {"entities": entities, "latency_sec": latency, "tokens": tokens}


def call_kimi(
    text: str,
    api_key: str,
    model: str = "kimi-k2.6",
    labels: list[str] | None = None,
) -> dict:
    """Call a Kimi model (Moonshot) for NER via the OpenAI-compatible API.

    Kimi doesn't reliably output JSON, so we ask for markdown lists and parse them.
    Returns entities without character offsets (frontier_extract will locate them via text search).
    """
    from openai import OpenAI
    import re

    client = OpenAI(api_key=api_key, base_url="https://api.moonshot.ai/v1")

    active_labels = labels if labels is not None else LABELS
    label_lookup = {label.lower(): label for label in active_labels}
    label_list = ", ".join(active_labels)
    prompt = f"""Extract cybersecurity entities from this text. For each entity, list:
- The exact text (verbatim from the text)
- The label (one of: {label_list})

Be strict: only extract clear matches. Use lowercase labels exactly as listed.

Text:
{text}

Format your response as a list with one entity per line:
Entity: [text] | Label: [label]
Entity: [text] | Label: [label]

If no matches, respond with: No entities found"""

    start = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )
    latency = time.time() - start

    result_text = response.choices[0].message.content.strip()

    # Parse markdown-style entity list
    # Format: "Entity: [text] | Label: [label]"
    entities = []
    for line in result_text.split('\n'):
        line = line.strip()
        if 'Entity:' in line and 'Label:' in line:
            try:
                # Extract entity text and label from "Entity: X | Label: Y" format
                entity_part = line.split('Entity:')[1].split('|')[0].strip()
                label_part = line.split('Label:')[1].strip()

                # Clean up markdown formatting
                entity_text = entity_part.strip('*`"\'')
                label_text = label_part.strip('*`"\'').lower()
                canonical_label = label_lookup.get(label_text)

                # Validate label
                if canonical_label:
                    entities.append({
                        "text": entity_text,
                        "label": canonical_label,
                        "start_char": 0,  # Placeholder; frontier_extract will find actual position
                        "end_char": 0,
                    })
            except (IndexError, ValueError):
                continue

    tokens = response.usage.prompt_tokens + response.usage.completion_tokens
    return {"entities": entities, "latency_sec": latency, "tokens": tokens}


def call_ollama_model(
    text: str,
    model_name: str,
    ollama_base: str = "http://localhost:11434",
    labels: list[str] | None = None,
) -> dict:
    """Call Ollama model for NER."""
    # Ollama tags use "name:tag", not "name-tag" -- the dash-style entries
    # below were never verified against an actually-pulled model and don't
    # match real Ollama Hub naming (found when gemma3:27b needed adding).
    model_map = {
        "gemma-2-27b": "gemma2:27b",
        "gemma-4-9b-qat": "gemma4:9b-qat",
        "gemma-4-12b-qat": "gemma4:12b-qat",
        "gemma-4-27b-qat": "gemma4:27b-qat",
        "gemma-4-e2b-qat": "gemma4:e2b-qat",
        "gemma3-27b": "gemma3:27b",
        "qwen-3.6-27b": "qwen3.6:27b",
    }
    ollama_model = model_map.get(model_name, model_name)

    label_list = ", ".join(labels if labels is not None else LABELS)
    prompt = f"""Extract named entities from the following cybersecurity text.
For each entity, return JSON with:
- text: the exact text of the entity (verbatim from the text)
- label: exactly one of these: {label_list}
- start_char: character index of the entity's first character
- end_char: character index right after the entity's last character

Be strict and precise. Prefer precision over recall — only extract entities that clearly match one of the given label types. Return the label EXACTLY as listed above (case-sensitive, lowercase).

Text:
{text}

Return a valid JSON array:
[{{"text": "...", "label": "...", "start_char": ..., "end_char": ...}}, ...]

If no clear matches, return an empty array: []
"""

    start = time.time()
    try:
        response = requests.post(
            f"{ollama_base}/api/generate",
            json={
                "model": ollama_model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1,
            },
            # A single 15k-char chunk measured at 368s on gemma3:27b locally
            # (~5 tok/s generation); 300s would time out mid-chunk on
            # anything but the shortest documents.
            timeout=1800,
        )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as e:
        print(f"  ⚠ {model_name} request error: {e}", file=sys.stderr)
        return {"entities": [], "latency_sec": time.time() - start, "tokens": 0}

    latency = time.time() - start

    # Parse JSON from response
    result_text = result.get("response", "").strip()
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    try:
        entities = json.loads(result_text)
    except json.JSONDecodeError:
        print(f"  ⚠ {model_name} JSON parse error: {result_text[:100]}", file=sys.stderr)
        entities = []

    tokens = result.get("eval_count", 0)
    return {"entities": entities, "latency_sec": latency, "tokens": tokens}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run frontier LLM inference on CTI test set.")
    parser.add_argument("--split", default="data/split_slugs.json",
                        help="Train/val/test split manifest")
    parser.add_argument("--markdown-dir", default="data/alerts",
                        help="Directory with {slug}/{slug}.md files")
    parser.add_argument("--output-dir", default="data/frontier_results",
                        help="Output directory for predictions JSONL")
    parser.add_argument("--models", required=True,
                        help="Comma-separated list of models to run")
    parser.add_argument("--subset", default="test", choices=["train", "val", "test"])
    parser.add_argument("--max-text-len", type=int, default=4000,
                        help="Max chars to send to LLM (ignored with --chunk-size)")
    parser.add_argument("--chunk-size", type=int, default=0,
                        help="If >0, cover the FULL document in chunks of this many chars "
                             "(500-char overlap) instead of truncating; entities are merged")
    parser.add_argument("--ollama-base", default="http://localhost:11434")
    parser.add_argument("--labels-file",
                        help="Optional JSON list of labels to use in prompts")
    parser.add_argument("--input-jsonl",
                        help="Optional pre-tokenized eval JSONL; one record = one model call")
    parser.add_argument("--limit", type=int, default=0,
                        help="If >0, run only the first N sorted slugs/records")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_labels = load_labels_file(Path(args.labels_file)) if args.labels_file else None
    markdown_dir = Path(args.markdown_dir)
    input_records = None
    if args.input_jsonl:
        input_records = sorted(
            load_jsonl_records(Path(args.input_jsonl)), key=lambda r: r["slug"]
        )
        if args.limit > 0:
            input_records = input_records[:args.limit]
        items = [
            {
                "slug": rec["slug"],
                "text": " ".join(rec["tokenized_text"]),
                "external": True,
            }
            for rec in input_records
        ]
        print(f"Running inference on {len(items)} pre-tokenized records")
    else:
        split = load_split(Path(args.split))
        subset_slugs = sorted(split[args.subset])
        if args.limit > 0:
            subset_slugs = subset_slugs[:args.limit]
        items = [
            {"slug": slug, "text": None, "external": False}
            for slug in subset_slugs
        ]
        print(f"Running inference on {args.subset} split ({len(items)} advisories)")
    print(f"Models: {args.models}")
    print()

    models_to_run = [m.strip() for m in args.models.split(",")]

    for model_name in models_to_run:
        print(f"Running {model_name}...")
        start_time = time.time()

        entities_file = output_dir / f"{model_name}-entities.jsonl"

        # Resume support: skip slugs already in the output file, so a failed
        # run (network, spending cap) never wastes completed API calls
        done_slugs = set()
        if entities_file.exists():
            with open(entities_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        done_slugs.add(json.loads(line)["slug"])
            if done_slugs:
                print(f"  Resuming: {len(done_slugs)} slugs already done, skipping them")

        for i, item in enumerate(items, 1):
            slug = item["slug"]
            if slug in done_slugs:
                continue
            if item["external"]:
                chunks = [item["text"]]
            else:
                # Load markdown with gold annotations stripped (leaking them to the
                # LLM would contaminate the evaluation)
                full_text = load_clean_text(slug, markdown_dir)
                if not full_text:
                    print(f"  ⚠ {slug}: markdown not found, skipping", file=sys.stderr)
                    continue

                # Build the list of texts to send: either one truncated window,
                # or overlapping chunks covering the full document
                if args.chunk_size > 0:
                    overlap = 500
                    chunks = []
                    pos = 0
                    while pos < len(full_text):
                        chunks.append(full_text[pos:pos + args.chunk_size])
                        if pos + args.chunk_size >= len(full_text):
                            break
                        pos += args.chunk_size - overlap
                    inference_text = full_text  # spans/scoring cover the whole doc
                else:
                    inference_text = full_text[:args.max_text_len] if len(full_text) > args.max_text_len else full_text
                    chunks = [inference_text]

            def call_one(chunk_text: str) -> dict:
                if model_name.startswith("gemini"):
                    use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true", "yes")
                    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
                    if not api_key and not use_vertex:
                        print("  ⚠ Set GOOGLE_API_KEY/GEMINI_API_KEY, or GOOGLE_GENAI_USE_VERTEXAI=true with ADC",
                              file=sys.stderr)
                        sys.exit(1)
                    return call_gemini(chunk_text, api_key, model_name, prompt_labels)
                elif model_name.startswith("claude"):
                    api_key = os.environ.get("ANTHROPIC_API_KEY")
                    if not api_key:
                        print("  ⚠ Set ANTHROPIC_API_KEY", file=sys.stderr)
                        sys.exit(1)
                    return call_claude(chunk_text, api_key, CLAUDE_MODEL_IDS.get(model_name, model_name), prompt_labels)
                elif model_name.startswith("kimi"):
                    api_key = os.environ.get("MOONSHOT_API_KEY") or os.environ.get("KIMI_API_KEY")
                    if not api_key:
                        print("  ⚠ Set MOONSHOT_API_KEY (or KIMI_API_KEY)", file=sys.stderr)
                        sys.exit(1)
                    return call_kimi(chunk_text, api_key, model_name, prompt_labels)
                elif model_name.startswith("gemma-4"):
                    # API-served Gemma (e.g. gemma-4-31b-it) goes through the
                    # Gemini API; Ollama-style names (gemma3:27b) stay local.
                    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
                    if not api_key:
                        print("  ⚠ Set GOOGLE_API_KEY/GEMINI_API_KEY", file=sys.stderr)
                        sys.exit(1)
                    return call_gemini(chunk_text, api_key, model_name, prompt_labels)
                elif model_name.startswith("gemma") or model_name.startswith("qwen"):
                    return call_ollama_model(chunk_text, model_name, args.ollama_base, prompt_labels)
                print(f"  ⚠ Unknown model: {model_name}", file=sys.stderr)
                return {"entities": [], "latency_sec": 0.0, "tokens": 0}

            # Call model per chunk; merge entities (dedupe by text+label — span
            # extraction locates all occurrences by text search anyway)
            merged: dict = {"entities": [], "latency_sec": 0.0, "tokens": 0}
            seen_ents = set()
            for ci, chunk_text in enumerate(chunks, 1):
                r = call_one(chunk_text)
                merged["latency_sec"] += r["latency_sec"]
                merged["tokens"] += r["tokens"]
                for ent in r["entities"]:
                    if not isinstance(ent, dict):
                        continue
                    key = (ent.get("text", "").strip().lower(), ent.get("label", ""))
                    if key[0] and key not in seen_ents:
                        seen_ents.add(key)
                        merged["entities"].append(ent)
                if len(chunks) > 1:
                    print(f"    chunk {ci}/{len(chunks)}: +{len(r['entities'])} entities",
                          file=sys.stderr)
            result = merged

            # Append the record immediately — a later failure must not lose
            # this doc's (paid) API calls
            record = {
                "slug": slug,
                "model": model_name,
                "entities": result["entities"],
                "latency_sec": round(result["latency_sec"], 3),
                "tokens": result["tokens"],
            }
            with open(entities_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

            print(
                f"  [{i}/{len(items)}] {slug}: "
                f"{len(result['entities'])} entities, {result['latency_sec']:.2f}s",
                file=sys.stderr
            )

        elapsed = time.time() - start_time
        print(f"  → Wrote {entities_file} ({elapsed:.1f}s)")
        print()


if __name__ == "__main__":
    main()
