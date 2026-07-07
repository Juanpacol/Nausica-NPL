import { ItemView, WorkspaceLeaf } from 'obsidian';
import type { AnalysisStore } from './store';
import { cfiHex } from './colors';

export const VIEW_TYPE_RIGIDITY_MAP = 'nausica-rigidity-map';

function basename(path: string): string {
  const file = path.split('/').pop() ?? path;
  return file.replace(/\.md$/i, '');
}

export class RigidityMapView extends ItemView {
  private store: AnalysisStore;

  constructor(leaf: WorkspaceLeaf, store: AnalysisStore) {
    super(leaf);
    this.store = store;
  }

  getViewType(): string {
    return VIEW_TYPE_RIGIDITY_MAP;
  }

  getDisplayText(): string {
    return 'Cognitive Rigidity Map';
  }

  getIcon(): string {
    return 'brain';
  }

  async onOpen(): Promise<void> {
    this.render();
  }

  refresh(store: AnalysisStore): void {
    this.store = store;
    this.render();
  }

  private render(): void {
    const container = this.contentEl;
    container.empty();
    container.addClass('nausica-map');

    container.createEl('h4', { text: 'Cognitive Rigidity Map', cls: 'nausica-map-title' });
    container.createEl('div', {
      text: 'Research prototype — not a diagnosis.',
      cls: 'nausica-map-disclaimer',
    });

    const entries = this.store.all(); // sorted most-rigid first
    if (entries.length === 0) {
      container.createEl('div', {
        cls: 'nausica-map-empty',
        text:
          'No notes analyzed yet. Run "Analyze current note" or "Analyze all Markdown notes" ' +
          'with the Nausica backend running. This is a research prototype, not a diagnosis.',
      });
      return;
    }

    const list = container.createEl('div', { cls: 'nausica-map-list' });
    for (const { path, analysis } of entries) {
      const row = list.createEl('div', { cls: 'nausica-map-row' });
      const dot = row.createEl('span', { cls: 'nausica-dot' });
      dot.style.backgroundColor = cfiHex(analysis.cfi);
      row.createEl('span', { text: basename(path), cls: 'nausica-map-name' });
      row.createEl('span', { text: analysis.cfi.toFixed(2), cls: 'nausica-map-cfi' });
      row.setAttribute('title', path);
      row.addEventListener('click', () => {
        void this.app.workspace.openLinkText(path, '', false);
      });
    }
  }

  async onClose(): Promise<void> {
    this.contentEl.empty();
  }
}
