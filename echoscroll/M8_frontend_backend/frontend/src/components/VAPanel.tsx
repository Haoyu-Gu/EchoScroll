import { useEffect, useRef } from "react";
import type { VA } from "../types";

interface Props {
  va: VA;
  onChange: (va: VA) => void;
  onCommit?: (va: VA) => void; // fired on pointerup, for triggering /edit/va
}

/**
 * 2D V-A circumplex. The four quadrants are tinted:
 *   Q1 (v>0, a>0) — joy / energetic         (warm yellow)
 *   Q2 (v<0, a>0) — tense / angry           (warm red)
 *   Q3 (v<0, a<0) — sad / melancholic       (cool blue)
 *   Q4 (v>0, a<0) — calm / serene           (soft green)
 */
export default function VAPanel({ va, onChange, onCommit }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const draggingRef = useRef(false);

  useEffect(() => { draw(); });

  function draw() {
    const c = canvasRef.current;
    if (!c) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = c.getBoundingClientRect();
    c.width = rect.width * dpr;
    c.height = rect.height * dpr;
    const ctx = c.getContext("2d")!;
    ctx.scale(dpr, dpr);

    const W = rect.width, H = rect.height;
    const cx = W / 2, cy = H / 2;

    // tints
    const tints = [
      { x: cx, y: 0,  w: cx, h: cy, c: "rgba(245, 200, 90, 0.35)"  },  // Q1 top-right
      { x: 0,  y: 0,  w: cx, h: cy, c: "rgba(220, 100, 90, 0.30)"  },  // Q2 top-left
      { x: 0,  y: cy, w: cx, h: cy, c: "rgba(110, 140, 200, 0.35)" },  // Q3 bot-left
      { x: cx, y: cy, w: cx, h: cy, c: "rgba(150, 195, 140, 0.35)" },  // Q4 bot-right
    ];
    for (const t of tints) {
      ctx.fillStyle = t.c;
      ctx.fillRect(t.x, t.y, t.w, t.h);
    }

    // axes
    ctx.strokeStyle = "rgba(0,0,0,0.35)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, cy); ctx.lineTo(W, cy);
    ctx.moveTo(cx, 0); ctx.lineTo(cx, H);
    ctx.stroke();

    // unit circle
    ctx.strokeStyle = "rgba(0,0,0,0.15)";
    ctx.beginPath();
    ctx.arc(cx, cy, Math.min(cx, cy) - 4, 0, Math.PI * 2);
    ctx.stroke();

    // labels
    ctx.fillStyle = "rgba(0,0,0,0.55)";
    ctx.font = "11px serif";
    ctx.textAlign = "center";
    ctx.fillText("arousal +", cx, 12);
    ctx.fillText("arousal -", cx, H - 4);
    ctx.textAlign = "left";
    ctx.fillText("valence +", W - 56, cy - 4);
    ctx.textAlign = "right";
    ctx.fillText("- valence", 56, cy - 4);

    // current point
    const px = cx + va.v * (cx - 4);
    const py = cy - va.a * (cy - 4);
    ctx.fillStyle = "#8a3a2c";
    ctx.strokeStyle = "white";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(px, py, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }

  function pointFromEvent(e: React.PointerEvent<HTMLCanvasElement>): VA {
    const rect = canvasRef.current!.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const v = (x - rect.width / 2) / (rect.width / 2 - 4);
    const a = -(y - rect.height / 2) / (rect.height / 2 - 4);
    return {
      v: Math.max(-1, Math.min(1, v)),
      a: Math.max(-1, Math.min(1, a)),
    };
  }

  return (
    <div className="panel">
      <h2>2 · V-A AFFECT</h2>
      <canvas
        ref={canvasRef}
        className="va-canvas"
        onPointerDown={(e) => {
          (e.target as HTMLCanvasElement).setPointerCapture(e.pointerId);
          draggingRef.current = true;
          onChange(pointFromEvent(e));
        }}
        onPointerMove={(e) => {
          if (draggingRef.current) onChange(pointFromEvent(e));
        }}
        onPointerUp={(e) => {
          if (draggingRef.current) {
            draggingRef.current = false;
            const p = pointFromEvent(e);
            onChange(p);
            onCommit?.(p);
          }
        }}
      />
      <div className="va-readout">
        valence = {va.v.toFixed(2)} &nbsp;·&nbsp; arousal = {va.a.toFixed(2)}
      </div>
    </div>
  );
}
