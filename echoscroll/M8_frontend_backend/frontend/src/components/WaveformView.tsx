import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";

interface Props {
  url: string | null;
}

export default function WaveformView({ url }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const [playing, setPlaying] = useState(false);
  const [ready, setReady] = useState(false);

  // construct WaveSurfer once
  useEffect(() => {
    if (!containerRef.current) return;
    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "#c8b9a4",
      progressColor: "#8a3a2c",
      cursorColor: "#1b1b1b",
      height: 80,
      barWidth: 2,
      barRadius: 2,
      normalize: true,
    });
    ws.on("ready", () => setReady(true));
    ws.on("finish", () => setPlaying(false));
    wsRef.current = ws;
    return () => { ws.destroy(); wsRef.current = null; };
  }, []);

  // load new url
  useEffect(() => {
    if (!wsRef.current || !url) return;
    setReady(false);
    setPlaying(false);
    wsRef.current.load(url);
  }, [url]);

  function toggle() {
    const ws = wsRef.current;
    if (!ws || !ready) return;
    if (playing) ws.pause(); else ws.play();
    setPlaying(!playing);
  }

  return (
    <div className="panel">
      <h2>3 · WAVEFORM</h2>
      <div ref={containerRef} className="wave-container" />
      <div className="btn-row">
        <button onClick={toggle} disabled={!url || !ready}>
          {playing ? "Pause" : "Play"}
        </button>
        {url && (
          <a href={url} download="echoscroll.wav">
            <button type="button">Download</button>
          </a>
        )}
      </div>
    </div>
  );
}
