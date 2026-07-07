// Minimal, dependency-free client for the Nausica backend.

import type { AnalyzeResponse } from './types';

export function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.trim().replace(/\/+$/, '');
}

/** SHA-256 of note content, hex-encoded. The backend stores only this hash —
 * never the note text or path — keeping the local-first promise. */
export async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  let hex = '';
  for (const byte of new Uint8Array(digest)) {
    hex += byte.toString(16).padStart(2, '0');
  }
  return hex;
}

export async function analyzeText(
  baseUrl: string,
  text: string,
  authToken: string,
  fileHash: string,
): Promise<AnalyzeResponse> {
  const url = `${normalizeBaseUrl(baseUrl)}/analyze`;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  let res: Response;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({ text, source: 'obsidian', file_hash: fileHash }),
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : String(err);
    throw new Error(`Could not reach Nausica backend at ${url}: ${reason}`);
  }
  if (res.status === 401) {
    throw new Error('Nausica: unauthorized — log in via Settings → Nausica Cognitive Map.');
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`Nausica API ${res.status}: ${detail || res.statusText}`);
  }
  return (await res.json()) as AnalyzeResponse;
}

/** Exchange email+password for a JWT. Only the token is ever persisted. */
export async function loginForToken(
  baseUrl: string,
  email: string,
  password: string,
): Promise<string> {
  const url = `${normalizeBaseUrl(baseUrl)}/auth/login`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : String(err);
    throw new Error(`Could not reach Nausica backend at ${url}: ${reason}`);
  }
  const body = await res.text().catch(() => '');
  if (!res.ok) {
    let message = body || res.statusText;
    try {
      const parsed = JSON.parse(body) as { detail?: unknown };
      if (typeof parsed.detail === 'string') message = parsed.detail;
    } catch {
      // non-JSON body — keep raw text
    }
    throw new Error(`Nausica login failed: ${message}`);
  }
  return (JSON.parse(body) as { access_token: string }).access_token;
}
