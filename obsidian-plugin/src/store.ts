// Pure cache logic — deliberately free of any 'obsidian' imports so it can
// be unit-tested in plain Node (see smoke.mjs).

import type { NausicaCache, NoteAnalysis } from './types';

function isNoteAnalysis(value: unknown): value is NoteAnalysis {
  if (typeof value !== 'object' || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.cfi === 'number' &&
    typeof v.analyzedAt === 'string' &&
    typeof v.distortions === 'object' &&
    v.distortions !== null
  );
}

export class AnalysisStore {
  private cache: NausicaCache;

  constructor(cache: NausicaCache = {}) {
    this.cache = cache;
  }

  get(path: string): NoteAnalysis | undefined {
    return this.cache[path];
  }

  set(path: string, analysis: NoteAnalysis): void {
    this.cache[path] = analysis;
  }

  delete(path: string): void {
    delete this.cache[path];
  }

  rename(oldPath: string, newPath: string): void {
    const existing = this.cache[oldPath];
    if (existing === undefined) return;
    delete this.cache[oldPath];
    this.cache[newPath] = existing;
  }

  /** All analyses, most rigid (highest CFI) first. */
  all(): Array<{ path: string; analysis: NoteAnalysis }> {
    return Object.entries(this.cache)
      .map(([path, analysis]) => ({ path, analysis }))
      .sort((a, b) => b.analysis.cfi - a.analysis.cfi);
  }

  size(): number {
    return Object.keys(this.cache).length;
  }

  toJSON(): NausicaCache {
    return this.cache;
  }

  /** Tolerant of null / malformed persisted data — falls back to empty. */
  static fromJSON(data: unknown): AnalysisStore {
    if (typeof data !== 'object' || data === null || Array.isArray(data)) {
      return new AnalysisStore();
    }
    const cache: NausicaCache = {};
    for (const [path, value] of Object.entries(data)) {
      if (isNoteAnalysis(value)) cache[path] = value;
    }
    return new AnalysisStore(cache);
  }
}
