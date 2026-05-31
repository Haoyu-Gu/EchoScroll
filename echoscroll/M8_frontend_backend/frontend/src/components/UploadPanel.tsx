import { useRef, useState } from "react";
import type { UploadResponse } from "../types";

interface Props {
  onUploaded: (resp: UploadResponse) => void;
}

export default function UploadPanel({ onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [title, setTitle] = useState("");
  const [artist, setArtist] = useState("");
  const [dynasty, setDynasty] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  function handleFile(f: File) {
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  async function submit() {
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("image", file);
      if (title) fd.append("title", title);
      if (artist) fd.append("artist", artist);
      if (dynasty) fd.append("dynasty", dynasty);
      if (text) fd.append("text", text);
      const r = await fetch("/upload", { method: "POST", body: fd });
      const data: UploadResponse = await r.json();
      onUploaded(data);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>1 · UPLOAD PAINTING</h2>
      <div
        className={"dropzone" + (dragging ? " drag" : "")}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const f = e.dataTransfer.files?.[0];
          if (f) handleFile(f);
        }}
      >
        {preview
          ? <img src={preview} alt="preview" />
          : <span>Drop a Chinese painting here, or click to select.</span>}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          style={{ display: "none" }}
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
      </div>

      <div className="meta-row">
        <input placeholder="Title"   value={title}   onChange={(e) => setTitle(e.target.value)} />
        <input placeholder="Artist"  value={artist}  onChange={(e) => setArtist(e.target.value)} />
        <input placeholder="Dynasty" value={dynasty} onChange={(e) => setDynasty(e.target.value)} />
      </div>
      <div className="meta-row">
        <input
          placeholder="Optional inscription or description (text)"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </div>

      <div className="btn-row">
        <button onClick={submit} disabled={!file || busy}>
          {busy ? "Uploading..." : "Upload"}
        </button>
      </div>
    </div>
  );
}
