import { useRef, useState } from "react";

interface HumResult {
  midi_contour: number[];
  tonal_center: string;
  transpose_cents: number;
}

interface Props {
  onResult: (r: HumResult) => void;
}

const MAX_MS = 5000;

export default function HummingRecorder({ onResult }: Props) {
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState<string>("idle");

  async function start() {
    chunksRef.current = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mime = MediaRecorder.isTypeSupported("audio/webm")
      ? "audio/webm"
      : "audio/wav";
    const rec = new MediaRecorder(stream, { mimeType: mime });
    rec.ondataavailable = (e) => {
      if (e.data.size) chunksRef.current.push(e.data);
    };
    rec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunksRef.current, { type: mime });
      setStatus("uploading...");
      const fd = new FormData();
      fd.append("audio", blob, "humming.wav");
      const r = await fetch("/edit/humming", { method: "POST", body: fd });
      const data: HumResult = await r.json();
      setStatus(`tonal=${data.tonal_center}, transpose=${data.transpose_cents}c`);
      onResult(data);
    };
    rec.start();
    recRef.current = rec;
    setRecording(true);
    setStatus("recording...");
    setTimeout(() => {
      if (recRef.current && recRef.current.state === "recording") stop();
    }, MAX_MS);
  }

  function stop() {
    recRef.current?.stop();
    setRecording(false);
  }

  return (
    <div className="panel">
      <h2>6 · HUMMING (max 5s)</h2>
      <div className="btn-row">
        {!recording
          ? <button onClick={start}>Start humming</button>
          : <button onClick={stop}>Stop</button>}
      </div>
      <div className="humming-state">{status}</div>
    </div>
  );
}
