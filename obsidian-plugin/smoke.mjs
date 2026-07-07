// Node smoke test for the pure (obsidian-free) modules.
// Bundles src/testable.ts to ESM with esbuild, then asserts store + color logic.
// Run: node smoke.mjs — prints "SMOKE OK" and exits 0 on success.

import esbuild from 'esbuild';
import assert from 'node:assert/strict';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const outfile = path.join(here, 'testable.mjs');

await esbuild.build({
  entryPoints: [path.join(here, 'src/testable.ts')],
  bundle: true,
  format: 'esm',
  target: 'es2021',
  outfile,
  logLevel: 'silent',
});

const { AnalysisStore, cfiHex, cfiLabelText, CFI_RAMP_HEX } = await import(
  pathToFileURL(outfile).href
);

const mkAnalysis = (cfi) => ({
  distortions: {
    all_or_nothing: 0.5,
    overgeneralization: 0.1,
    emotional_reasoning: 0.3,
    catastrophizing: 0.2,
    mind_reading: 0.4,
  },
  cfi,
  analyzedAt: '2026-07-06T12:00:00.000Z',
});

// --- store set/get/rename/delete round-trip via toJSON/fromJSON -------------
{
  const store = new AnalysisStore();
  store.set('Journal/a.md', mkAnalysis(0.7));
  store.set('Journal/b.md', mkAnalysis(0.2));
  assert.equal(store.get('Journal/a.md').cfi, 0.7);

  store.rename('Journal/a.md', 'Journal/renamed.md');
  assert.equal(store.get('Journal/a.md'), undefined);
  assert.equal(store.get('Journal/renamed.md').cfi, 0.7);

  const revived = AnalysisStore.fromJSON(JSON.parse(JSON.stringify(store.toJSON())));
  assert.equal(revived.get('Journal/renamed.md').cfi, 0.7);
  assert.equal(revived.get('Journal/b.md').cfi, 0.2);
  assert.equal(revived.size(), 2);

  revived.delete('Journal/b.md');
  assert.equal(revived.get('Journal/b.md'), undefined);
  assert.equal(revived.size(), 1);
}

// --- fromJSON tolerance ------------------------------------------------------
{
  assert.equal(AnalysisStore.fromJSON(null).size(), 0);
  assert.equal(AnalysisStore.fromJSON(undefined).size(), 0);
  assert.equal(AnalysisStore.fromJSON('garbage').size(), 0);
  assert.equal(AnalysisStore.fromJSON(42).size(), 0);
  assert.equal(AnalysisStore.fromJSON([1, 2, 3]).size(), 0);
  // Malformed entries are dropped; valid ones survive.
  const mixed = AnalysisStore.fromJSON({
    'ok.md': mkAnalysis(0.5),
    'bad.md': { cfi: 'not-a-number' },
    'worse.md': null,
  });
  assert.equal(mixed.size(), 1);
  assert.equal(mixed.get('ok.md').cfi, 0.5);
}

// --- all() sorted by cfi descending ------------------------------------------
{
  const store = new AnalysisStore();
  store.set('low.md', mkAnalysis(0.1));
  store.set('high.md', mkAnalysis(0.9));
  store.set('mid.md', mkAnalysis(0.5));
  const paths = store.all().map((e) => e.path);
  assert.deepEqual(paths, ['high.md', 'mid.md', 'low.md']);
}

// --- cfiHex bucketing (ported CFI_RAMP_HEX, index 0 = most flexible) ----------
{
  assert.deepEqual(CFI_RAMP_HEX, ['#379e8f', '#248579', '#1a6c64', '#16554f', '#123f3b']);
  assert.equal(cfiHex(0.1), '#379e8f'); // lightest — flexible
  assert.equal(cfiHex(0.9), '#123f3b'); // darkest — rigid
  assert.notEqual(cfiHex(0.1), cfiHex(0.9));
  assert.equal(cfiHex(0), '#379e8f');
  assert.equal(cfiHex(1), '#123f3b'); // clamped: floor(1*5)=5 -> index 4
  assert.equal(cfiHex(0.5), '#1a6c64'); // middle bucket
}

// --- cfiLabelText boundaries ---------------------------------------------------
{
  assert.equal(cfiLabelText(0.2), 'flexible');
  assert.equal(cfiLabelText(0.5), 'moderate');
  assert.equal(cfiLabelText(0.8), 'rigid');
  assert.equal(cfiLabelText(0.35), 'moderate'); // boundary: <0.35 is flexible
  assert.equal(cfiLabelText(0.6), 'rigid'); // boundary: <0.6 is moderate
}

console.log('SMOKE OK');
