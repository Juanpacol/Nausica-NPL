# Nausica Demo Vault

A fixture Obsidian vault for demoing the **Nausica Cognitive Map** plugin.

> **Research prototype — not a diagnosis.** Nausica detects patterns of
> cognitive distortion in text and summarizes them as a continuous Cognitive
> Flexibility Index (CFI, higher = more rigid). It is a research tool, not a
> medical device, and its output must never be treated as diagnosis or
> treatment advice.

## What's in here

- `Journal/` — **9 synthetic journal entries** (2026-06-22 → 2026-07-05).
  They are entirely fictional, written to show a deliberate arc: the earliest
  notes are highly rigid (absolutist language, catastrophizing, mind reading),
  the middle ones mixed, and the latest noticeably more flexible. No real
  personal data.
- `.obsidian/plugins/nausica-cognitive-map/` — a pre-built copy of the plugin
  (`main.js`, `manifest.json`, `styles.css`), already listed in
  `community-plugins.json`.

## How to run the demo

1. **Start the backend** from the Nausica repo root:

   ```bash
   ./venv/bin/uvicorn src.api.main:app
   ```

   It listens on `http://127.0.0.1:8000` by default (the plugin's default too).

2. **Open this folder as a vault** in Obsidian: *Open another vault → Open
   folder as vault* → select `demo-vault`.

3. **Enable community plugins**: Settings → Community plugins → turn off
   Restricted mode, then make sure **Nausica Cognitive Map** is enabled
   (it should already appear in the installed list).

4. **Analyze the notes**: open the command palette (`Cmd/Ctrl+P`) and run
   **"Analyze all Markdown notes"**.

5. **Open the map**: click the brain icon in the left ribbon to open the
   **Cognitive Rigidity Map** in the right sidebar. Notes are sorted
   most-rigid first; click a row to open the note and see its inline analysis
   card (CFI, rigidity level, per-distortion bars).

If analysis fails with "Nausica backend unreachable", check that uvicorn is
running and that the backend URL in the plugin settings matches it.
