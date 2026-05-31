import { useState } from "react";
import type { Descriptors } from "../types";

interface Props {
  paintingId: string | null;
  onResult: (descriptors: Descriptors, va: [number, number], audioUrl: string) => void;
}

export default function PromptBox({ paintingId, onResult }: Props) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!paintingId || !text.trim()) return;
    setBusy(true);
    try {
      const r = await fetch("/edit/prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ painting_id: paintingId, colloquial_prompt: text }),
      });
      const data = await r.json();
      onResult(data.descriptors, data.va, data.audio_url);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>5 · COLLOQUIAL PROMPT</h2>
      <div className="prompt-row">
        <input
          value={text}
          placeholder='e.g. "make it slower and more meditative"'
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button onClick={submit} disabled={!paintingId || !text.trim() || busy}>
          {busy ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
