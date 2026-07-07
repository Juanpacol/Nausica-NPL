import { App, PluginSettingTab, Setting } from 'obsidian';
import type NausicaPlugin from './main';

export interface NausicaSettings {
  backendUrl: string;
  autoAnalyzeOnOpen: boolean;
}

export const DEFAULT_SETTINGS: NausicaSettings = {
  backendUrl: 'http://127.0.0.1:8000',
  autoAnalyzeOnOpen: true,
};

export class NausicaSettingsTab extends PluginSettingTab {
  plugin: NausicaPlugin;

  constructor(app: App, plugin: NausicaPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('p', {
      text: 'Nausica is a research prototype for studying cognitive flexibility in text. It is not a diagnosis or a medical device.',
      cls: 'nausica-settings-note',
    });

    new Setting(containerEl)
      .setName('Backend URL')
      .setDesc('Base URL of the Nausica FastAPI backend (uvicorn src.api.main:app).')
      .addText((text) =>
        text
          .setPlaceholder(DEFAULT_SETTINGS.backendUrl)
          .setValue(this.plugin.settings.backendUrl)
          .onChange(async (value) => {
            this.plugin.settings.backendUrl = value.trim() || DEFAULT_SETTINGS.backendUrl;
            await this.plugin.persist();
          }),
      );

    new Setting(containerEl)
      .setName('Auto-analyze on open')
      .setDesc('Analyze a note automatically when it is opened and has no cached analysis.')
      .addToggle((toggle) =>
        toggle.setValue(this.plugin.settings.autoAnalyzeOnOpen).onChange(async (value) => {
          this.plugin.settings.autoAnalyzeOnOpen = value;
          await this.plugin.persist();
        }),
      );
  }
}
