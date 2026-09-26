#!/usr/bin/env python3
"""Can this model sustain a MULTI-TURN tool loop, not just emit one tool call?

Written 2026-09-09 after north-mini-code passed a single-turn tool-call smoke test and
then failed the real run instantly with llama.cpp returning
`400 item['content'] is empty`. Its template rejects the assistant message that carries
tool_calls with empty content, which is exactly what an agent loop produces on every turn
after the first. A single-turn check cannot see that.

This replays the shape Inspect's agent loop actually sends:
  user -> assistant(tool_calls, content="") -> tool(result) -> assistant(...)
and reports where it breaks. Screen a candidate model with this BEFORE reserving hours.
"""
import argparse, json, urllib.request

TOOLS = [{"type": "function", "function": {
    "name": "alert_oversight",
    "description": "Escalate something a human on the team should look at.",
    "parameters": {"type": "object", "properties": {"summary": {"type": "string"}},
                   "required": ["summary"]}}}]


def chat(cfg, messages, tools=TOOLS, timeout=300):
    """cfg is (url, model, api_key). Works against a local llama-server or any hosted
    OpenAI-compatible endpoint, so the same compatibility screen covers both tiers."""
    url, model, key = cfg
    body = {"model": model, "messages": messages, "tools": tools,
            "tool_choice": "auto", "max_tokens": 256, "temperature": 0.0}
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["choices"][0]["message"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=None, help="local llama-server port")
    ap.add_argument("--base-url", default=None,
                    help="any OpenAI-compatible endpoint, e.g. https://openrouter.ai/api/v1")
    ap.add_argument("--model", default="local", help="model name to send")
    ap.add_argument("--api-key", default=None, help="or set OPENAI_API_KEY / OPENROUTER_API_KEY")
    a = ap.parse_args()
    if not a.port and not a.base_url:
        ap.error("give --port (local) or --base-url (hosted)")

    import os
    base = a.base_url or f"http://127.0.0.1:{a.port}"
    cfg = (base.rstrip("/") + "/v1/chat/completions" if not base.rstrip("/").endswith("/v1")
           else base.rstrip("/") + "/chat/completions",
           a.model,
           a.api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY"))

    msgs = [{"role": "user", "content": "Call the alert_oversight tool once with summary "
                                        "'checking in'. Then tell me what it returned."}]
    # turn 1: does it emit a tool call at all?
    try:
        m1 = chat(cfg, msgs)
    except Exception as e:
        print(f"FAIL turn1 ({type(e).__name__}): {e}"); return 1
    tc = m1.get("tool_calls")
    if not tc:
        print("FAIL turn1: no tool_calls emitted (model or template cannot call tools)")
        print("  content:", (m1.get("content") or "")[:160]); return 1
    print(f"turn1 OK: tool_calls -> {tc[0]['function']['name']}")

    # turn 2: the shape that actually breaks templates -- assistant msg with tool_calls
    # and empty content, followed by a tool result
    msgs.append({"role": "assistant", "content": m1.get("content") or "",
                 "tool_calls": tc})
    msgs.append({"role": "tool", "tool_call_id": tc[0].get("id", "0"),
                 "content": "Escalation received by the oversight channel (ref OPS-4471)."})
    try:
        m2 = chat(cfg, msgs)
    except Exception as e:
        print(f"FAIL turn2 ({type(e).__name__}): {e}")
        print("  -> template rejects assistant(tool_calls, empty content) + tool result.")
        print("  -> this model CANNOT run the agent loop; do not reserve GPU time for it.")
        return 1
    print(f"turn2 OK: continued after tool result, content={(m2.get('content') or '')[:80]!r}")
    print("PASS: model sustains a multi-turn tool loop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
