"""Demo for M6 Prompt Translator.

Runs the deterministic rule-based path on six colloquial requests so the demo
works on any laptop with NO API keys and NO local model download. If
ANTHROPIC_API_KEY is also set, runs one extra LLM round to show the live path.

    python demo.py
"""

from __future__ import annotations

import json
import os

from translator import PromptTranslator, RuleBasedTranslator


DEMO_INPUTS = [
    "再空一点",
    "更激烈",
    "make it gentler",
    "古风一点，加点琴",
    "slow piano",
    "joyful and energetic",
]


def _pretty(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, indent=2)


def run_rule_based():
    print("=" * 60)
    print("Rule-based path (works with NO api keys)")
    print("=" * 60)
    rule = RuleBasedTranslator()
    # Start every call from the same neutral state to make the patches visible.
    base_state = {
        "tempo": "moderate",
        "mode": "major",
        "meter": "4/4",
        "register": "mid",
        "instrumentation": ["piano"],
        "texture": "moderate",
        "articulation": "legato",
        "dynamics": "mp",
    }
    for prompt in DEMO_INPUTS:
        out = rule.translate(prompt, current_state=base_state)
        print(f"\n>>> prompt: {prompt!r}")
        print(_pretty(out))


def run_llm_round_if_available():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n(ANTHROPIC_API_KEY not set; skipping live LLM round.)")
        return
    print("\n" + "=" * 60)
    print("LLM path (Anthropic) -- one round on a representative prompt")
    print("=" * 60)
    try:
        tr = PromptTranslator(backend="anthropic")
        out = tr.translate(
            "古风一点，加点琴",
            current_state={
                "tempo": "moderate",
                "mode": "major",
                "meter": "4/4",
                "register": "mid",
                "instrumentation": ["piano"],
                "texture": "moderate",
                "articulation": "legato",
                "dynamics": "mp",
            },
            context=["literati landscape; misty mountains; Song dynasty"],
        )
        print(_pretty(out))
    except Exception as e:  # noqa: BLE001
        print(f"LLM round failed: {type(e).__name__}: {e}")


if __name__ == "__main__":
    run_rule_based()
    run_llm_round_if_available()
