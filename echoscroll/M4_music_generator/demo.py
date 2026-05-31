"""
EchoScroll M4 demo.

Default path: instantiate :class:`MockMusicGenerator`, run a 10 s clip from a
hard-coded condition, write ``out.wav`` next to this file, print the path.

Pass ``--real`` to use the actual ``facebook/musicgen-small`` (downloads ~2 GB
on first run).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from generator import MockMusicGenerator, MusicGenWrapper


DEMO_CONDITION = {
    "text_prompt": "literati landscape, ink wash",
    "va": (-0.3, -0.5),
    "retrieved_context": ["Northern Song mountain monumentality"],
    "duration_s": 10,
    "control_descriptors": None,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="EchoScroll M4 demo")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real MusicGen-small (downloads ~2 GB on first run)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).parent / "out.wav",
        help="Output WAV path (default: ./out.wav)",
    )
    args = parser.parse_args()

    if args.real:
        print("[demo] --real specified: loading facebook/musicgen-small "
              "(this will download ~2 GB on first run)...")
        gen = MusicGenWrapper().load()
    else:
        print("[demo] Using MockMusicGenerator (CPU-only, no downloads).")
        gen = MockMusicGenerator().load()

    out = gen.generate(DEMO_CONDITION)
    path = gen.save_audio(out["wav"], args.out, sample_rate=out["sample_rate"])

    print(f"[demo] prompt sent to MusicGen: {out['prompt_used']!r}")
    print(f"[demo] sample_rate         : {out['sample_rate']} Hz")
    print(f"[demo] duration            : {len(out['wav']) / out['sample_rate']:.2f} s")
    print(f"[demo] saved waveform to   : {path.resolve()}")


if __name__ == "__main__":
    main()
