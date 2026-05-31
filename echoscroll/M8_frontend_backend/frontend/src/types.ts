export type VA = { v: number; a: number };

export interface Descriptors {
  mode: string;
  tempo_bpm: number;
  instrumentation: string[];
  dynamics: string;
  texture: string;
  timbre: string;
  articulation: string;
  style_tags: string[];
}

export interface RetrievedDoc {
  doc_id: string;
  title: string;
  snippet: string;
  score: number;
}

export interface GenerateResponse {
  audio_url: string;
  va: [number, number];
  descriptors: Descriptors;
  retrieved_context: RetrievedDoc[];
}

export interface UploadResponse {
  painting_id: string;
  title: string | null;
  preview_url: string;
}
