import { MarkdownView, Notice, Plugin, TFile, WorkspaceLeaf } from 'obsidian';
import { analyzeText, sha256Hex } from './api';
import { renderInlineCard } from './InlineCard';
import { RigidityMapView, VIEW_TYPE_RIGIDITY_MAP } from './RigidityMapView';
import { DEFAULT_SETTINGS, NausicaSettings, NausicaSettingsTab } from './SettingsTab';
import { AnalysisStore } from './store';
import type { NoteAnalysis } from './types';

interface PersistedData {
  settings?: Partial<NausicaSettings>;
  cache?: unknown;
}

const CARD_HOST_CLASS = 'nausica-card-host';

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default class NausicaPlugin extends Plugin {
  settings: NausicaSettings = { ...DEFAULT_SETTINGS };
  store: AnalysisStore = new AnalysisStore();

  async onload(): Promise<void> {
    await this.loadPersisted();

    this.registerView(
      VIEW_TYPE_RIGIDITY_MAP,
      (leaf: WorkspaceLeaf) => new RigidityMapView(leaf, this.store),
    );

    this.addRibbonIcon('brain', 'Open Cognitive Rigidity Map', () => {
      void this.activateMapView();
    });

    this.addSettingTab(new NausicaSettingsTab(this.app, this));

    this.addCommand({
      id: 'nausica-analyze-note',
      name: 'Analyze current note',
      callback: () => {
        void this.analyzeActiveNote();
      },
    });

    this.addCommand({
      id: 'nausica-analyze-all',
      name: 'Analyze all Markdown notes',
      callback: () => {
        void this.analyzeAllNotes();
      },
    });

    this.registerEvent(
      this.app.workspace.on('file-open', (file) => {
        if (file instanceof TFile && file.extension === 'md') {
          void this.handleFileOpen(file);
        }
      }),
    );

    this.registerEvent(
      this.app.vault.on('rename', (file, oldPath) => {
        if (file instanceof TFile) {
          this.store.rename(oldPath, file.path);
          void this.persist();
        }
      }),
    );

    this.registerEvent(
      this.app.vault.on('delete', (file) => {
        if (file instanceof TFile) {
          this.store.delete(file.path);
          void this.persist();
          this.refreshMapViews();
        }
      }),
    );
  }

  onunload(): void {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE_RIGIDITY_MAP);
  }

  // --- persistence ---------------------------------------------------------

  private async loadPersisted(): Promise<void> {
    const raw = (await this.loadData()) as PersistedData | null;
    this.settings = { ...DEFAULT_SETTINGS, ...(raw?.settings ?? {}) };
    this.store = AnalysisStore.fromJSON(raw?.cache ?? null);
  }

  async persist(): Promise<void> {
    await this.saveData({ settings: this.settings, cache: this.store.toJSON() });
  }

  // --- analysis ------------------------------------------------------------

  private async analyzeFile(file: TFile): Promise<NoteAnalysis> {
    const text = await this.app.vault.cachedRead(file);
    const fileHash = await sha256Hex(text);
    const response = await analyzeText(this.settings.backendUrl, text, this.settings.authToken, fileHash);
    const analysis: NoteAnalysis = {
      distortions: response.distortions,
      cfi: response.cfi,
      analyzedAt: new Date().toISOString(),
    };
    this.store.set(file.path, analysis);
    await this.persist();
    return analysis;
  }

  private async analyzeActiveNote(): Promise<void> {
    if (!this.settings.authToken) {
      new Notice('Nausica: log in first — Settings → Nausica Cognitive Map.');
      return;
    }
    const file = this.app.workspace.getActiveFile();
    if (!file || file.extension !== 'md') {
      new Notice('Nausica: open a Markdown note first.');
      return;
    }
    try {
      const analysis = await this.analyzeFile(file);
      this.injectCard(file, analysis);
      this.refreshMapViews();
      new Notice(`Nausica: analyzed "${file.basename}" (CFI ${analysis.cfi.toFixed(2)}).`);
    } catch (err) {
      console.error('Nausica analyze failed', err);
      new Notice('Nausica backend unreachable — is uvicorn running?');
    }
  }

  private async analyzeAllNotes(): Promise<void> {
    if (!this.settings.authToken) {
      new Notice('Nausica: log in first — Settings → Nausica Cognitive Map.');
      return;
    }
    const files = this.app.vault.getMarkdownFiles();
    if (files.length === 0) {
      new Notice('Nausica: no Markdown notes in this vault.');
      return;
    }
    new Notice(`Nausica: analyzing ${files.length} notes…`);
    let done = 0;
    let failed = 0;
    for (const file of files) {
      try {
        await this.analyzeFile(file);
      } catch (err) {
        console.error(`Nausica: failed to analyze ${file.path}`, err);
        failed += 1;
        if (failed === 1) {
          new Notice('Nausica backend unreachable — is uvicorn running?');
        }
      }
      done += 1;
      if (done % 5 === 0) {
        new Notice(`Nausica: ${done}/${files.length} notes analyzed.`);
      }
      await sleep(100);
    }
    this.refreshMapViews();
    const active = this.app.workspace.getActiveFile();
    if (active) {
      const analysis = this.store.get(active.path);
      if (analysis) this.injectCard(active, analysis);
    }
    new Notice(
      failed > 0
        ? `Nausica: done — ${done - failed} analyzed, ${failed} failed.`
        : `Nausica: all ${done} notes analyzed.`,
    );
  }

  private async handleFileOpen(file: TFile): Promise<void> {
    const cached = this.store.get(file.path);
    if (cached) {
      this.injectCard(file, cached);
      return;
    }
    if (!this.settings.autoAnalyzeOnOpen) return;
    if (!this.settings.authToken) return; // quiet skip — cached cards above still render
    try {
      const analysis = await this.analyzeFile(file);
      // Only inject if the same file is still active.
      if (this.app.workspace.getActiveFile()?.path === file.path) {
        this.injectCard(file, analysis);
      }
      this.refreshMapViews();
    } catch (err) {
      console.error('Nausica auto-analyze failed', err);
      new Notice('Nausica backend unreachable — is uvicorn running?');
    }
  }

  // --- rendering -----------------------------------------------------------

  private injectCard(file: TFile, analysis: NoteAnalysis): void {
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (!view || view.file?.path !== file.path) return;
    const content = view.contentEl;
    content.querySelectorAll(`.${CARD_HOST_CLASS}`).forEach((node) => node.remove());
    const host = document.createElement('div');
    host.className = CARD_HOST_CLASS;
    content.prepend(host);
    renderInlineCard(host, analysis);
  }

  private refreshMapViews(): void {
    for (const leaf of this.app.workspace.getLeavesOfType(VIEW_TYPE_RIGIDITY_MAP)) {
      const view = leaf.view;
      if (view instanceof RigidityMapView) view.refresh(this.store);
    }
  }

  private async activateMapView(): Promise<void> {
    const { workspace } = this.app;
    let leaf: WorkspaceLeaf | null = workspace.getLeavesOfType(VIEW_TYPE_RIGIDITY_MAP)[0] ?? null;
    if (!leaf) {
      leaf = workspace.getRightLeaf(false);
      if (!leaf) return;
      await leaf.setViewState({ type: VIEW_TYPE_RIGIDITY_MAP, active: true });
    }
    workspace.revealLeaf(leaf);
    if (leaf.view instanceof RigidityMapView) leaf.view.refresh(this.store);
  }
}
