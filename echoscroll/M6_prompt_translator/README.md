# M6 Prompt Translator

Maps colloquial user requests (zh / en) into an 8-slot musical descriptor that
MusicGen can consume. Backends are auto-detected at construction time in this
priority order: Anthropic API -> OpenAI API -> local Qwen2.5-7B-Instruct ->
rule-based fallback. The fallback runs with zero dependencies, so `demo.py`
works on a stock MacBook with no API keys.

## I/O contract

```python
from translator import PromptTranslator
tr = PromptTranslator()                                # auto-pick backend
out = tr.translate("再空一点", current_state=None, context=None)
# -> {tempo, mode, meter, register, instrumentation, texture, articulation,
#     dynamics, gloss}
```

## Run

```
python demo.py
```

The demo prints rule-based outputs for: `再空一点`, `更激烈`, `make it gentler`,
`古风一点，加点琴`, `slow piano`, `joyful and energetic`. If `ANTHROPIC_API_KEY`
is set, it also issues one live LLM call (`claude-3-5-sonnet-latest`).

## Vocabulary

- **tempo**: `very slow | slow | moderate | fast | very fast`
- **mode**: `major | minor | pentatonic_gong | pentatonic_shang | pentatonic_jue | pentatonic_zhi | pentatonic_yu | dorian | mixolydian`
- **meter**: `4/4 | 3/4 | 6/8 | free`
- **register**: `low | mid | high`
- **instrumentation** (multi-select): `piano, strings, violin, cello, flute, clarinet, harp, acoustic_guitar, synth_pad, drums, guqin, guzheng, pipa, erhu, dizi, xiao, ruan, yangqin, sheng, percussion_chinese`
- **texture**: `sparse | moderate | dense`
- **articulation**: `legato | staccato | detache`
- **dynamics**: `ppp | pp | p | mp | mf | f | ff | fff`

Plus a `gloss` field: short English sentence explaining what changed.

## Backends used

`PromptTranslator().backend` reports which path is active. The LLM path uses a
JSON-mode prompt that pins all slot vocabularies; on any parse/network error
the call silently falls back to `RuleBasedTranslator` so the system never
returns a malformed descriptor.
