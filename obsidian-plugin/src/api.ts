// Minimal, dependency-free client for POST /analyze on the Nausica backend.

import type { AnalyzeResponse } from './types';

export function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.trim().replace(/\/+$/, '');
}

export async function analyzeText(baseUrl: string, text: string): Promise<AnalyzeResponse> {
  const url = `${normalizeBaseUrl(baseUrl)}/analyze`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : String(err);
    throw new Error(`Could not reach Nausica backend at ${url}: ${reason}`);
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`Nausica API ${res.status}: ${detail || res.statusText}`);
  }
  return (await res.json()) as AnalyzeResponse;
}
