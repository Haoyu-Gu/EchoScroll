"""
M6 Prompt Translator.

Translates colloquial user prompts (zh/en) into structured musical control
descriptors that MusicGen can consume.

Backends, auto-detected at construction time (priority order):
    1. Anthropic API   (env ANTHROPIC_API_KEY)
    2. OpenAI API      (env OPENAI_API_KEY)
    3. Local Qwen      (transformers, lazy-loaded)
    4. Rule-based fallback (always available, zero dependencies)

Public surface:
    PromptTranslator(backend=None).translate(user_prompt, current_state, context)
    RuleBasedTranslator().translate(...)
    VOCAB                       -- allowed values for every slot
"""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from typing import Optional

# ---------------------------------------------------------------------------
# Allowed vocabulary -- the LLM is pinned to these values; the rule-based path
# only emits these values; downstream MusicGen prompt assembler can rely on it.
# ---------------------------------------------------------------------------

VOCAB = {
    "tempo": ["very slow", "slow", "moderate", "fast", "very fast"],
    "mode": [
        "major",
        "minor",
        "pentatonic_gong",   # gong / 宫 -- bright, stable
        "pentatonic_shang",  # shang / 商 -- resolute
        "pentatonic_jue",    # jue / 角 -- lyrical
        "pentatonic_zhi",    # zhi / 徵 -- warm, joyful
        "pentatonic_yu",     # yu / 羽 -- melancholic
        "dorian",
        "mixolydian",
    ],
    "meter": ["4/4", "3/4", "6/8", "free"],
    "register": ["low", "mid", "high"],
    "instrumentation": [
        # Western
        "piano", "strings", "violin", "cello", "flute", "clarinet", "harp",
        "acoustic_guitar", "synth_pad", "drums",
        # Chinese traditional
        "guqin", "guzheng", "pipa", "erhu", "dizi", "xiao", "ruan",
        "yangqin", "sheng", "percussion_chinese",
    ],
    "texture": ["sparse", "moderate", "dense"],
    "articulation": ["legato", "staccato", "detache"],
    "dynamics": ["ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"],
}

SLOTS = ("tempo", "mode", "meter", "register",
         "instrumentation", "texture", "articulation", "dynamics")


# Reasonable neutral default; used when no current_state is supplied.
DEFAULT_STATE = {
    "tempo": "moderate",
    "mode": "major",
    "meter": "4/4",
    "register": "mid",
    "instrumentation": ["piano"],
    "texture": "moderate",
    "articulation": "legato",
    "dynamics": "mp",
}


# ---------------------------------------------------------------------------
# Rule-based fallback
# ---------------------------------------------------------------------------

# Each rule = (regex, patch_dict, gloss_fragment). Order matters: earlier rules
# win for conflicting slots; later rules only fill what earlier rules left.
# Regex flags: IGNORECASE; Chinese chars are literal.
_RULES = [
    # ---------- Density / space ----------
    (r"再?空一?点|稀疏|留白|空灵|空旷|更空", {"texture": "sparse"},
     "texture sparser"),
    (r"more spacious|sparser|airier|less\s+dense|emptier",
     {"texture": "sparse"}, "texture sparser"),
    (r"再?密一?点|更密|繁密|稠密|更厚|更满",
     {"texture": "dense"}, "texture denser"),
    (r"thicker|denser|busier|fuller",
     {"texture": "dense"}, "texture denser"),

    # ---------- Intensity / energy ----------
    (r"更?激烈|更?猛|更?燥|更?狂|更?有力|更?爆发|更?震撼",
     {"dynamics": "f", "articulation": "staccato", "tempo": "fast"},
     "more intense"),
    (r"more\s+intense|more\s+energetic|more\s+aggressive|more\s+powerful|punchier|harder",
     {"dynamics": "f", "articulation": "staccato", "tempo": "fast"},
     "more intense"),
    (r"更?温柔|更?柔和|更?轻一点|更?轻柔|更?舒缓|更?平静|更?安静",
     {"dynamics": "p", "articulation": "legato", "tempo": "slow"},
     "gentler"),
    (r"gentler|softer|calmer|quieter|more\s+peaceful|more\s+relaxed|more\s+tender",
     {"dynamics": "p", "articulation": "legato", "tempo": "slow"},
     "gentler"),

    # ---------- Tempo ----------
    (r"更?快(一?点)?|加快|提速|急促",
     {"tempo": "fast"}, "faster"),
    (r"\bfaster\b|speed\s+up|quicker",
     {"tempo": "fast"}, "faster"),
    (r"更?慢(一?点)?|放慢|缓慢|拖一点",
     {"tempo": "slow"}, "slower"),
    (r"\bslow(er|ly)?\b|slow\s+down|slacker",
     {"tempo": "slow"}, "slower"),

    # ---------- Mood ----------
    (r"欢快|喜悦|开心|愉悦|明亮一?点|阳光",
     {"mode": "major", "tempo": "fast", "dynamics": "mf",
      "articulation": "staccato"},
     "joyful"),
    (r"joyful|cheerful|happy|bright|sunny|uplifting",
     {"mode": "major", "tempo": "fast", "dynamics": "mf",
      "articulation": "staccato"},
     "joyful"),
    (r"悲伤|忧郁|哀愁|凄凉|惆怅|忧伤",
     {"mode": "minor", "tempo": "slow", "dynamics": "p",
      "articulation": "legato"},
     "melancholic"),
    (r"sad|melancholic|mournful|sorrowful|wistful|blue\b",
     {"mode": "minor", "tempo": "slow", "dynamics": "p",
      "articulation": "legato"},
     "melancholic"),
    (r"紧张|焦虑|不安|压抑",
     {"mode": "minor", "tempo": "fast", "dynamics": "f",
      "articulation": "staccato"},
     "tense"),
    (r"tense|anxious|uneasy|nervous",
     {"mode": "minor", "tempo": "fast", "dynamics": "f",
      "articulation": "staccato"},
     "tense"),
    (r"energetic|lively|动感|有活力|有劲",
     {"tempo": "fast", "dynamics": "f", "articulation": "staccato"},
     "energetic"),

    # ---------- Cultural / stylistic ----------
    (r"古风|古意|古典中国|国风|中国风|水墨",
     {"mode": "pentatonic_gong",
      "instrumentation_add": ["guqin", "xiao"],
      "meter": "free"},
     "guqin-xiao Chinese-traditional palette"),
    (r"chinese\s+(traditional|classical)|guqin|xiao\b|pentatonic",
     {"mode": "pentatonic_gong",
      "instrumentation_add": ["guqin", "xiao"]},
     "Chinese pentatonic palette"),
    (r"加点?琴|来点?琴|要琴",
     {"instrumentation_add": ["guqin"]}, "add guqin"),
    (r"piano",
     {"instrumentation_set": ["piano"]}, "piano only"),
    (r"钢琴",
     {"instrumentation_set": ["piano"]}, "piano only"),
    (r"strings?|弦乐",
     {"instrumentation_add": ["strings"]}, "add strings"),
    (r"flute|笛子|dizi",
     {"instrumentation_add": ["dizi"]}, "add dizi"),
    (r"erhu|二胡",
     {"instrumentation_add": ["erhu"]}, "add erhu"),
    (r"pipa|琵琶",
     {"instrumentation_add": ["pipa"]}, "add pipa"),
    (r"guzheng|古筝",
     {"instrumentation_add": ["guzheng"]}, "add guzheng"),
    (r"drums?|鼓|打击",
     {"instrumentation_add": ["drums"]}, "add drums"),

    # ---------- Register ----------
    (r"低沉|低音|更低",
     {"register": "low"}, "lower register"),
    (r"\blow(er)?\s+register|deep(er)?\s+sound|bassier",
     {"register": "low"}, "lower register"),
    (r"高亢|更高|高音",
     {"register": "high"}, "higher register"),
    (r"\bhigh(er)?\s+register|brighter\s+register",
     {"register": "high"}, "higher register"),

    # ---------- Meter ----------
    (r"三拍|华尔兹|3/4|waltz",
     {"meter": "3/4"}, "triple meter"),
    (r"6/8",
     {"meter": "6/8"}, "compound duple"),
    (r"自由(节奏|拍)|散板|无拍|rubato",
     {"meter": "free"}, "free rhythm"),

    # ---------- Articulation ----------
    (r"连贯|连音|绵延|legato",
     {"articulation": "legato"}, "legato"),
    (r"跳音|断奏|短促|staccato",
     {"articulation": "staccato"}, "staccato"),
]


class RuleBasedTranslator:
    """Deterministic dictionary translator.

    Walks `_RULES` in order. For each match it patches the working state.
    Only slots that no rule has touched fall back to current_state / default.
    """

    def __init__(self):
        # pre-compile regexes
        self._rules = [(re.compile(p, re.IGNORECASE), patch, gloss)
                       for p, patch, gloss in _RULES]

    def translate(self,
                  user_prompt: str,
                  current_state: Optional[dict] = None,
                  context: Optional[list] = None) -> dict:
        # base state
        state = deepcopy(current_state) if current_state else deepcopy(DEFAULT_STATE)
        # normalize instrumentation list shape if user passed something weird
        if isinstance(state.get("instrumentation"), str):
            state["instrumentation"] = [state["instrumentation"]]

        touched = set()
        gloss_parts = []

        for regex, patch, gloss in self._rules:
            if not regex.search(user_prompt):
                continue
            applied_anything = False

            for k, v in patch.items():
                if k == "instrumentation_add":
                    cur = list(state.get("instrumentation") or [])
                    added = [x for x in v if x not in cur]
                    if added:
                        state["instrumentation"] = cur + added
                        applied_anything = True
                elif k == "instrumentation_set":
                    state["instrumentation"] = list(v)
                    touched.add("instrumentation")
                    applied_anything = True
                else:
                    if k in touched:
                        continue  # earlier rule wins
                    if k not in SLOTS:
                        continue
                    if v not in VOCAB[k]:
                        continue
                    state[k] = v
                    touched.add(k)
                    applied_anything = True

            if applied_anything:
                gloss_parts.append(gloss)

        # validate instrumentation against vocab
        state["instrumentation"] = [
            ins for ins in (state.get("instrumentation") or [])
            if ins in VOCAB["instrumentation"]
        ] or ["piano"]

        # ensure every slot is filled & in-vocab
        state = _coerce_to_vocab(state)

        state["gloss"] = ("; ".join(gloss_parts)
                          if gloss_parts
                          else "no rule matched; state unchanged")
        return state


# ---------------------------------------------------------------------------
# LLM-backed translator
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a musical prompt translator for the EchoScroll system.
Convert a user's colloquial request (Chinese or English) into a strict JSON
object that controls a MusicGen-based audio generator.

Return JSON ONLY, no prose, no markdown, no code fences. The JSON must contain
exactly these keys:

  tempo:          one of {tempo}
  mode:           one of {mode}
  meter:          one of {meter}
  register:       one of {register}
  instrumentation: a non-empty list, each element drawn from {instrumentation}
  texture:        one of {texture}
  articulation:   one of {articulation}
  dynamics:       one of {dynamics}
  gloss:          a short English sentence describing what changed vs. current_state

Rules:
- If a slot is not implied by the user's request, keep the value from
  current_state (provided in the user turn). If current_state is empty, pick
  a musically sensible default.
- Never invent values outside the allowed vocabularies above.
- For Chinese-painting / 古风 / 水墨 / 国风 cues prefer pentatonic modes and
  Chinese instruments (guqin, xiao, erhu, dizi, pipa, guzheng).
- "更激烈" / "more intense" => louder dynamics + faster tempo + staccato.
- "再空一点" / "more spacious" => sparse texture, possibly softer dynamics.
- Output MUST be parseable by json.loads.
"""


def _format_system_prompt() -> str:
    return _SYSTEM_PROMPT.format(
        tempo=VOCAB["tempo"],
        mode=VOCAB["mode"],
        meter=VOCAB["meter"],
        register=VOCAB["register"],
        instrumentation=VOCAB["instrumentation"],
        texture=VOCAB["texture"],
        articulation=VOCAB["articulation"],
        dynamics=VOCAB["dynamics"],
    )


def _format_user_turn(user_prompt: str,
                      current_state: Optional[dict],
                      context: Optional[list]) -> str:
    payload = {
        "user_prompt": user_prompt,
        "current_state": current_state or {},
        "retrieval_context": context or [],
    }
    return ("Translate the following request to the 8-slot descriptor JSON.\n"
            + json.dumps(payload, ensure_ascii=False, indent=2))


class PromptTranslator:
    """Front-door translator. Auto-detects the strongest available backend.

    backend: one of {"anthropic", "openai", "qwen", "rule", None}.
        None => auto.
    """

    def __init__(self,
                 backend: Optional[str] = None,
                 anthropic_model: str = "claude-3-5-sonnet-latest",
                 openai_model: str = "gpt-4o-mini",
                 qwen_model: str = "Qwen/Qwen2.5-7B-Instruct"):
        self.anthropic_model = anthropic_model
        self.openai_model = openai_model
        self.qwen_model = qwen_model
        self._rule = RuleBasedTranslator()
        self._qwen_pipe = None  # lazy

        if backend is None:
            backend = self._auto_detect_backend()
        self.backend = backend

    # ---- backend selection ----

    @staticmethod
    def _auto_detect_backend() -> str:
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                import anthropic  # noqa: F401
                return "anthropic"
            except ImportError:
                pass
        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai  # noqa: F401
                return "openai"
            except ImportError:
                pass
        try:
            import transformers  # noqa: F401
            import torch  # noqa: F401
            return "qwen"
        except ImportError:
            return "rule"

    # ---- public API ----

    def translate(self,
                  user_prompt: str,
                  current_state: Optional[dict] = None,
                  context: Optional[list] = None) -> dict:
        if not user_prompt or not user_prompt.strip():
            out = deepcopy(current_state) if current_state else deepcopy(DEFAULT_STATE)
            out = _coerce_to_vocab(out)
            out["gloss"] = "empty prompt; state unchanged"
            return out

        try:
            if self.backend == "anthropic":
                raw = self._call_anthropic(user_prompt, current_state, context)
            elif self.backend == "openai":
                raw = self._call_openai(user_prompt, current_state, context)
            elif self.backend == "qwen":
                raw = self._call_qwen(user_prompt, current_state, context)
            else:
                return self._rule.translate(user_prompt, current_state, context)
        except Exception as e:  # noqa: BLE001
            out = self._rule.translate(user_prompt, current_state, context)
            out["gloss"] = f"[{self.backend} failed: {type(e).__name__}] " + out["gloss"]
            return out

        parsed = _safe_parse_json(raw)
        if parsed is None:
            out = self._rule.translate(user_prompt, current_state, context)
            out["gloss"] = f"[{self.backend} returned non-JSON] " + out["gloss"]
            return out

        # merge into base state so missing keys are filled
        base = deepcopy(current_state) if current_state else deepcopy(DEFAULT_STATE)
        base.update({k: v for k, v in parsed.items() if k in SLOTS})
        base = _coerce_to_vocab(base)
        base["gloss"] = parsed.get("gloss", "updated by LLM")
        return base

    # ---- backend implementations ----

    def _call_anthropic(self, user_prompt, current_state, context) -> str:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=self.anthropic_model,
            max_tokens=512,
            system=_format_system_prompt(),
            messages=[{"role": "user",
                       "content": _format_user_turn(user_prompt, current_state, context)}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")

    def _call_openai(self, user_prompt, current_state, context) -> str:
        import openai
        client = openai.OpenAI()
        resp = client.chat.completions.create(
            model=self.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _format_system_prompt()},
                {"role": "user",
                 "content": _format_user_turn(user_prompt, current_state, context)},
            ],
        )
        return resp.choices[0].message.content or ""

    def _call_qwen(self, user_prompt, current_state, context) -> str:
        # Lazy import + lazy load.
        if self._qwen_pipe is None:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            tok = AutoTokenizer.from_pretrained(self.qwen_model)
            mdl = AutoModelForCausalLM.from_pretrained(
                self.qwen_model,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto",
            )
            self._qwen_pipe = (tok, mdl)
        tok, mdl = self._qwen_pipe
        messages = [
            {"role": "system", "content": _format_system_prompt()},
            {"role": "user",
             "content": _format_user_turn(user_prompt, current_state, context)},
        ]
        text = tok.apply_chat_template(messages, tokenize=False,
                                       add_generation_prompt=True)
        inputs = tok([text], return_tensors="pt").to(mdl.device)
        out = mdl.generate(**inputs, max_new_tokens=512, do_sample=False)
        gen = tok.decode(out[0][inputs["input_ids"].shape[1]:],
                         skip_special_tokens=True)
        return gen


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_parse_json(raw: str) -> Optional[dict]:
    if not raw:
        return None
    raw = raw.strip()
    # strip code fences if any
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw,
                     flags=re.IGNORECASE | re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # fish for the first {...} block
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _coerce_to_vocab(state: dict) -> dict:
    """Force every slot into a valid vocab value, filling missing ones from
    DEFAULT_STATE. Unknown extra keys are dropped, except 'gloss'."""
    out = {}
    for slot in SLOTS:
        v = state.get(slot, DEFAULT_STATE[slot])
        if slot == "instrumentation":
            if isinstance(v, str):
                v = [v]
            v = [ins for ins in (v or []) if ins in VOCAB["instrumentation"]]
            if not v:
                v = list(DEFAULT_STATE["instrumentation"])
            out[slot] = v
        else:
            if v not in VOCAB[slot]:
                v = DEFAULT_STATE[slot]
            out[slot] = v
    if "gloss" in state:
        out["gloss"] = state["gloss"]
    return out
