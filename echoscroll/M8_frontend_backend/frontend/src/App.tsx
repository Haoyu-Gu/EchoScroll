import { useCallback, useState } from "react";
import UploadPanel from "./components/UploadPanel";
import VAPanel from "./components/VAPanel";
import WaveformView from "./components/WaveformView";
import PromptBox from "./components/PromptBox";
import HummingRecorder from "./components/HummingRecorder";
import type { Descriptors, RetrievedDoc, VA, UploadResponse } from "./types";

export default function App() {
  const [paintingId, setPaintingId] = useState<string | null>(null);
  const [paintingTitle, setPaintingTitle] = useState<string | null>(null);
  const [va, setVA] = useState<VA>({ v: 0, a: 0 });
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [descriptors, setDescriptors] = useState<Descriptors | null>(null);
  const [retrieved, setRetrieved] = useState<RetrievedDoc[]>([]);
  const [generating, setGenerating] = useState(false);

  const onUploaded = useCallback((r: UploadResponse) => {
    setPaintingId(r.painting_id);
    setPaintingTitle(r.title);
    setAudioUrl(null);
    setDescriptors(null);
    setRetrieved([]);
  }, []);

  async function generate() {
    if (!paintingId) return;
    setGenerating(true);
    try {
      const r = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ painting_id: paintingId, duration_s: 10 }),
      });
      const data = await r.json();
      setVA({ v: data.va[0], a: data.va[1] });
      setAudioUrl(data.audio_url);
      setDescriptors(data.descriptors);
      setRetrieved(data.retrieved_context || []);
    } finally {
      setGenerating(false);
    }
  }

  async function commitVA(p: VA) {
    if (!paintingId) return;
    const r = await fetch("/edit/va", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ painting_id: paintingId, va_target: [p.v, p.a] }),
    });
    const data = await r.json();
    // Force WaveSurfer to reload by busting the URL
    setAudioUrl(data.audio_url + (data.audio_url.includes("?") ? "&" : "?") + "t=" + Date.now());
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>EchoScroll</h1>
        <span className="tag">Chinese painting → V-A → soundtrack</span>
      </header>

      <UploadPanel onUploaded={onUploaded} />

      {paintingId && (
        <div className="panel">
          <h2>STATE</h2>
          <div className="kv">
            <span className="k">painting_id</span><span>{paintingId}</span>
            <span className="k">title</span><span>{paintingTitle ?? "(untitled)"}</span>
          </div>
          <div className="btn-row">
            <button onClick={generate} disabled={generating}>
              {generating ? "Generating..." : "Generate soundtrack"}
            </button>
          </div>
        </div>
      )}

      <div className="grid">
        <VAPanel va={va} onChange={setVA} onCommit={commitVA} />
        <WaveformView url={audioUrl} />
      </div>

      <PromptBox
        paintingId={paintingId}
        onResult={(d, v, url) => {
          setDescriptors(d);
          setVA({ v: v[0], a: v[1] });
          setAudioUrl(url + (url.includes("?") ? "&" : "?") + "t=" + Date.now());
        }}
      />

      <HummingRecorder
        onResult={(h) => {
          // For the skeleton we just surface the result; a real wire-up
          // would re-trigger generation using h.tonal_center / transpose.
          console.log("humming result", h);
        }}
      />

      {descriptors && (
        <div className="panel">
          <h2>4 · MUSICAL DESCRIPTORS</h2>
          <div className="kv">
            <span className="k">mode</span>          <span>{descriptors.mode}</span>
            <span className="k">tempo</span>         <span>{descriptors.tempo_bpm} bpm</span>
            <span className="k">instrumentation</span><span>{descriptors.instrumentation.join(", ")}</span>
            <span className="k">dynamics</span>      <span>{descriptors.dynamics}</span>
            <span className="k">texture</span>       <span>{descriptors.texture}</span>
            <span className="k">timbre</span>        <span>{descriptors.timbre}</span>
            <span className="k">articulation</span>  <span>{descriptors.articulation}</span>
            <span className="k">style_tags</span>    <span>{descriptors.style_tags.join(", ")}</span>
          </div>
        </div>
      )}

      {retrieved.length > 0 && (
        <div className="panel">
          <h2>7 · ART-HISTORY CONTEXT</h2>
          {retrieved.map((d) => (
            <div className="rag-item" key={d.doc_id}>
              <div className="t">{d.title} <span className="s">· score {d.score.toFixed(2)}</span></div>
              <div className="s">{d.snippet}</div>
            </div>
          ))}
        </div>
      )}

      <div className="footer">EchoScroll · M8 frontend + backend skeleton</div>
    </div>
  );
}
