import { App, Notice, PluginSettingTab, Setting } from 'obsidian';
import { loginForToken } from './api';
import type NausicaPlugin from './main';

export interface NausicaSettings {
  backendUrl: string;
  autoAnalyzeOnOpen: boolean;
  authToken: string;
}

export const DEFAULT_SETTINGS: NausicaSettings = {
  backendUrl: 'http://127.0.0.1:8000',
  autoAnalyzeOnOpen: true,
  authToken: '',
};

export class NausicaSettingsTab extends PluginSettingTab {
  plugin: NausicaPlugin;
  // Credentials live only while the tab is open — never persisted.
  private email = '';
  private password = '';

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

    new Setting(containerEl).setName('Account').setHeading();

    new Setting(containerEl)
      .setName('Email')
      .setDesc('Backend account email. Credentials are used once to get a token and never stored.')
      .addText((text) =>
        text.setPlaceholder('you@example.com').onChange((value) => {
          this.email = value;
        }),
      );

    new Setting(containerEl).setName('Password').addText((text) => {
      text.inputEl.type = 'password';
      text.onChange((value) => {
        this.password = value;
      });
    });

    new Setting(containerEl)
      .setName('Log in')
      .setDesc('Exchange email + password for an access token (stored in plugin data).')
      .addButton((btn) =>
        btn
          .setButtonText('Log in / Get token')
          .setCta()
          .onClick(async () => {
            try {
              const token = await loginForToken(
                this.plugin.settings.backendUrl,
                this.email.trim(),
                this.password,
              );
              this.plugin.settings.authToken = token;
              await this.plugin.persist();
              new Notice('Nausica: logged in — token saved.');
              this.display();
            } catch (err) {
              new Notice(err instanceof Error ? err.message : String(err));
            }
          }),
      );

    new Setting(containerEl)
      .setName('Access token')
      .setDesc('Or paste a token directly (from the web app or /auth/login).')
      .addText((text) =>
        text
          .setPlaceholder('eyJ…')
          .setValue(this.plugin.settings.authToken)
          .onChange(async (value) => {
            this.plugin.settings.authToken = value.trim();
            await this.plugin.persist();
          }),
      );
  }
}
