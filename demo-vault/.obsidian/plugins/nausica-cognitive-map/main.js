/*
Nausica Cognitive Map — Obsidian plugin (research prototype, not a diagnosis).
This file is bundled from src/ by esbuild. See the Nausica repo for sources.
*/
"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/main.ts
var main_exports = {};
__export(main_exports, {
  default: () => NausicaPlugin
});
module.exports = __toCommonJS(main_exports);
var import_obsidian3 = require("obsidian");

// src/api.ts
function normalizeBaseUrl(baseUrl) {
  return baseUrl.trim().replace(/\/+$/, "");
}
async function sha256Hex(text) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  let hex = "";
  for (const byte of new Uint8Array(digest)) {
    hex += byte.toString(16).padStart(2, "0");
  }
  return hex;
}
async function analyzeText(baseUrl, text, authToken, fileHash) {
  const url = `${normalizeBaseUrl(baseUrl)}/analyze`;
  const headers = { "Content-Type": "application/json" };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  let res;
  try {
    res = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({ text, source: "obsidian", file_hash: fileHash })
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : String(err);
    throw new Error(`Could not reach Nausica backend at ${url}: ${reason}`);
  }
  if (res.status === 401) {
    throw new Error("Nausica: unauthorized \u2014 log in via Settings \u2192 Nausica Cognitive Map.");
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Nausica API ${res.status}: ${detail || res.statusText}`);
  }
  return await res.json();
}
async function loginForToken(baseUrl, email, password) {
  const url = `${normalizeBaseUrl(baseUrl)}/auth/login`;
  let res;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : String(err);
    throw new Error(`Could not reach Nausica backend at ${url}: ${reason}`);
  }
  const body = await res.text().catch(() => "");
  if (!res.ok) {
    let message = body || res.statusText;
    try {
      const parsed = JSON.parse(body);
      if (typeof parsed.detail === "string") message = parsed.detail;
    } catch {
    }
    throw new Error(`Nausica login failed: ${message}`);
  }
  return JSON.parse(body).access_token;
}

// src/types.ts
var DISTORTION_LABELS = [
  "all_or_nothing",
  "overgeneralization",
  "emotional_reasoning",
  "catastrophizing",
  "mind_reading"
];

// src/colors.ts
var CFI_RAMP_HEX = ["#379e8f", "#248579", "#1a6c64", "#16554f", "#123f3b"];
function cfiHex(cfi) {
  const idx = Math.min(
    CFI_RAMP_HEX.length - 1,
    Math.max(0, Math.floor(cfi * CFI_RAMP_HEX.length))
  );
  return CFI_RAMP_HEX[idx];
}
function cfiLabelText(cfi) {
  if (cfi < 0.35) return "flexible";
  if (cfi < 0.6) return "moderate";
  return "rigid";
}
var DISTORTION_DISPLAY = {
  all_or_nothing: { icon: "\u25D0", en: "All-or-nothing" },
  overgeneralization: { icon: "\u221E", en: "Overgeneralization" },
  emotional_reasoning: { icon: "\u2665", en: "Emotional reasoning" },
  catastrophizing: { icon: "\u2301", en: "Catastrophizing" },
  mind_reading: { icon: "\u25CE", en: "Mind reading" }
};
var DISTORTION_HEX = {
  all_or_nothing: "#4c77c9",
  overgeneralization: "#0a9187",
  emotional_reasoning: "#ae6e1f",
  catastrophizing: "#8e66cc",
  mind_reading: "#c25573"
};

// src/InlineCard.ts
var BAR_THRESHOLD = 0.2;
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== void 0) node.textContent = text;
  return node;
}
function renderInlineCard(container, analysis) {
  const card = el("div", "nausica-card");
  const header = el("div", "nausica-card-header");
  const dot = el("span", "nausica-dot");
  dot.style.backgroundColor = cfiHex(analysis.cfi);
  header.appendChild(dot);
  header.appendChild(el("span", "nausica-cfi-value", `CFI ${analysis.cfi.toFixed(2)}`));
  header.appendChild(el("span", "nausica-cfi-word", cfiLabelText(analysis.cfi)));
  card.appendChild(header);
  const bars = el("div", "nausica-bars");
  for (const label of DISTORTION_LABELS) {
    const p = analysis.distortions[label];
    if (typeof p !== "number" || p < BAR_THRESHOLD) continue;
    const row = el("div", "nausica-bar-row");
    const display = DISTORTION_DISPLAY[label];
    row.appendChild(el("span", "nausica-bar-icon", display.icon));
    row.appendChild(el("span", "nausica-bar-label", display.en));
    const track = el("div", "nausica-bar-track");
    const fill = el("div", "nausica-bar-fill");
    fill.style.width = `${Math.round(p * 100)}%`;
    fill.style.backgroundColor = DISTORTION_HEX[label];
    track.appendChild(fill);
    row.appendChild(track);
    row.appendChild(el("span", "nausica-bar-pct", `${Math.round(p * 100)}%`));
    bars.appendChild(row);
  }
  if (bars.childElementCount === 0) {
    bars.appendChild(
      el("div", "nausica-bar-none", "No distortion above the display threshold.")
    );
  }
  card.appendChild(bars);
  const footer = el("div", "nausica-card-footer");
  const when = new Date(analysis.analyzedAt);
  const whenText = isNaN(when.getTime()) ? analysis.analyzedAt : when.toLocaleString();
  footer.appendChild(el("span", "nausica-analyzed-at", `Analyzed ${whenText}`));
  footer.appendChild(
    el("span", "nausica-disclaimer", "Research prototype \u2014 not a diagnosis.")
  );
  card.appendChild(footer);
  container.appendChild(card);
}

// src/RigidityMapView.ts
var import_obsidian = require("obsidian");
var VIEW_TYPE_RIGIDITY_MAP = "nausica-rigidity-map";
function basename(path) {
  const file = path.split("/").pop() ?? path;
  return file.replace(/\.md$/i, "");
}
var RigidityMapView = class extends import_obsidian.ItemView {
  constructor(leaf, store) {
    super(leaf);
    this.store = store;
  }
  getViewType() {
    return VIEW_TYPE_RIGIDITY_MAP;
  }
  getDisplayText() {
    return "Cognitive Rigidity Map";
  }
  getIcon() {
    return "brain";
  }
  async onOpen() {
    this.render();
  }
  refresh(store) {
    this.store = store;
    this.render();
  }
  render() {
    const container = this.contentEl;
    container.empty();
    container.addClass("nausica-map");
    container.createEl("h4", { text: "Cognitive Rigidity Map", cls: "nausica-map-title" });
    container.createEl("div", {
      text: "Research prototype \u2014 not a diagnosis.",
      cls: "nausica-map-disclaimer"
    });
    const entries = this.store.all();
    if (entries.length === 0) {
      container.createEl("div", {
        cls: "nausica-map-empty",
        text: 'No notes analyzed yet. Run "Analyze current note" or "Analyze all Markdown notes" with the Nausica backend running. This is a research prototype, not a diagnosis.'
      });
      return;
    }
    const list = container.createEl("div", { cls: "nausica-map-list" });
    for (const { path, analysis } of entries) {
      const row = list.createEl("div", { cls: "nausica-map-row" });
      const dot = row.createEl("span", { cls: "nausica-dot" });
      dot.style.backgroundColor = cfiHex(analysis.cfi);
      row.createEl("span", { text: basename(path), cls: "nausica-map-name" });
      row.createEl("span", { text: analysis.cfi.toFixed(2), cls: "nausica-map-cfi" });
      row.setAttribute("title", path);
      row.addEventListener("click", () => {
        void this.app.workspace.openLinkText(path, "", false);
      });
    }
  }
  async onClose() {
    this.contentEl.empty();
  }
};

// src/SettingsTab.ts
var import_obsidian2 = require("obsidian");
var DEFAULT_SETTINGS = {
  backendUrl: "http://127.0.0.1:8000",
  autoAnalyzeOnOpen: true,
  authToken: ""
};
var NausicaSettingsTab = class extends import_obsidian2.PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    // Credentials live only while the tab is open — never persisted.
    this.email = "";
    this.password = "";
    this.plugin = plugin;
  }
  display() {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("p", {
      text: "Nausica is a research prototype for studying cognitive flexibility in text. It is not a diagnosis or a medical device.",
      cls: "nausica-settings-note"
    });
    new import_obsidian2.Setting(containerEl).setName("Backend URL").setDesc("Base URL of the Nausica FastAPI backend (uvicorn src.api.main:app).").addText(
      (text) => text.setPlaceholder(DEFAULT_SETTINGS.backendUrl).setValue(this.plugin.settings.backendUrl).onChange(async (value) => {
        this.plugin.settings.backendUrl = value.trim() || DEFAULT_SETTINGS.backendUrl;
        await this.plugin.persist();
      })
    );
    new import_obsidian2.Setting(containerEl).setName("Auto-analyze on open").setDesc("Analyze a note automatically when it is opened and has no cached analysis.").addToggle(
      (toggle) => toggle.setValue(this.plugin.settings.autoAnalyzeOnOpen).onChange(async (value) => {
        this.plugin.settings.autoAnalyzeOnOpen = value;
        await this.plugin.persist();
      })
    );
    new import_obsidian2.Setting(containerEl).setName("Account").setHeading();
    new import_obsidian2.Setting(containerEl).setName("Email").setDesc("Backend account email. Credentials are used once to get a token and never stored.").addText(
      (text) => text.setPlaceholder("you@example.com").onChange((value) => {
        this.email = value;
      })
    );
    new import_obsidian2.Setting(containerEl).setName("Password").addText((text) => {
      text.inputEl.type = "password";
      text.onChange((value) => {
        this.password = value;
      });
    });
    new import_obsidian2.Setting(containerEl).setName("Log in").setDesc("Exchange email + password for an access token (stored in plugin data).").addButton(
      (btn) => btn.setButtonText("Log in / Get token").setCta().onClick(async () => {
        try {
          const token = await loginForToken(
            this.plugin.settings.backendUrl,
            this.email.trim(),
            this.password
          );
          this.plugin.settings.authToken = token;
          await this.plugin.persist();
          new import_obsidian2.Notice("Nausica: logged in \u2014 token saved.");
          this.display();
        } catch (err) {
          new import_obsidian2.Notice(err instanceof Error ? err.message : String(err));
        }
      })
    );
    new import_obsidian2.Setting(containerEl).setName("Access token").setDesc("Or paste a token directly (from the web app or /auth/login).").addText(
      (text) => text.setPlaceholder("eyJ\u2026").setValue(this.plugin.settings.authToken).onChange(async (value) => {
        this.plugin.settings.authToken = value.trim();
        await this.plugin.persist();
      })
    );
  }
};

// src/store.ts
function isNoteAnalysis(value) {
  if (typeof value !== "object" || value === null) return false;
  const v = value;
  return typeof v.cfi === "number" && typeof v.analyzedAt === "string" && typeof v.distortions === "object" && v.distortions !== null;
}
var AnalysisStore = class _AnalysisStore {
  constructor(cache = {}) {
    this.cache = cache;
  }
  get(path) {
    return this.cache[path];
  }
  set(path, analysis) {
    this.cache[path] = analysis;
  }
  delete(path) {
    delete this.cache[path];
  }
  rename(oldPath, newPath) {
    const existing = this.cache[oldPath];
    if (existing === void 0) return;
    delete this.cache[oldPath];
    this.cache[newPath] = existing;
  }
  /** All analyses, most rigid (highest CFI) first. */
  all() {
    return Object.entries(this.cache).map(([path, analysis]) => ({ path, analysis })).sort((a, b) => b.analysis.cfi - a.analysis.cfi);
  }
  size() {
    return Object.keys(this.cache).length;
  }
  toJSON() {
    return this.cache;
  }
  /** Tolerant of null / malformed persisted data — falls back to empty. */
  static fromJSON(data) {
    if (typeof data !== "object" || data === null || Array.isArray(data)) {
      return new _AnalysisStore();
    }
    const cache = {};
    for (const [path, value] of Object.entries(data)) {
      if (isNoteAnalysis(value)) cache[path] = value;
    }
    return new _AnalysisStore(cache);
  }
};

// src/main.ts
var CARD_HOST_CLASS = "nausica-card-host";
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
var NausicaPlugin = class extends import_obsidian3.Plugin {
  constructor() {
    super(...arguments);
    this.settings = { ...DEFAULT_SETTINGS };
    this.store = new AnalysisStore();
  }
  async onload() {
    await this.loadPersisted();
    this.registerView(
      VIEW_TYPE_RIGIDITY_MAP,
      (leaf) => new RigidityMapView(leaf, this.store)
    );
    this.addRibbonIcon("brain", "Open Cognitive Rigidity Map", () => {
      void this.activateMapView();
    });
    this.addSettingTab(new NausicaSettingsTab(this.app, this));
    this.addCommand({
      id: "nausica-analyze-note",
      name: "Analyze current note",
      callback: () => {
        void this.analyzeActiveNote();
      }
    });
    this.addCommand({
      id: "nausica-analyze-all",
      name: "Analyze all Markdown notes",
      callback: () => {
        void this.analyzeAllNotes();
      }
    });
    this.registerEvent(
      this.app.workspace.on("file-open", (file) => {
        if (file instanceof import_obsidian3.TFile && file.extension === "md") {
          void this.handleFileOpen(file);
        }
      })
    );
    this.registerEvent(
      this.app.vault.on("rename", (file, oldPath) => {
        if (file instanceof import_obsidian3.TFile) {
          this.store.rename(oldPath, file.path);
          void this.persist();
        }
      })
    );
    this.registerEvent(
      this.app.vault.on("delete", (file) => {
        if (file instanceof import_obsidian3.TFile) {
          this.store.delete(file.path);
          void this.persist();
          this.refreshMapViews();
        }
      })
    );
  }
  onunload() {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE_RIGIDITY_MAP);
  }
  // --- persistence ---------------------------------------------------------
  async loadPersisted() {
    const raw = await this.loadData();
    this.settings = { ...DEFAULT_SETTINGS, ...raw?.settings ?? {} };
    this.store = AnalysisStore.fromJSON(raw?.cache ?? null);
  }
  async persist() {
    await this.saveData({ settings: this.settings, cache: this.store.toJSON() });
  }
  // --- analysis ------------------------------------------------------------
  async analyzeFile(file) {
    const text = await this.app.vault.cachedRead(file);
    const fileHash = await sha256Hex(text);
    const response = await analyzeText(this.settings.backendUrl, text, this.settings.authToken, fileHash);
    const analysis = {
      distortions: response.distortions,
      cfi: response.cfi,
      analyzedAt: (/* @__PURE__ */ new Date()).toISOString()
    };
    this.store.set(file.path, analysis);
    await this.persist();
    return analysis;
  }
  async analyzeActiveNote() {
    if (!this.settings.authToken) {
      new import_obsidian3.Notice("Nausica: log in first \u2014 Settings \u2192 Nausica Cognitive Map.");
      return;
    }
    const file = this.app.workspace.getActiveFile();
    if (!file || file.extension !== "md") {
      new import_obsidian3.Notice("Nausica: open a Markdown note first.");
      return;
    }
    try {
      const analysis = await this.analyzeFile(file);
      this.injectCard(file, analysis);
      this.refreshMapViews();
      new import_obsidian3.Notice(`Nausica: analyzed "${file.basename}" (CFI ${analysis.cfi.toFixed(2)}).`);
    } catch (err) {
      console.error("Nausica analyze failed", err);
      new import_obsidian3.Notice("Nausica backend unreachable \u2014 is uvicorn running?");
    }
  }
  async analyzeAllNotes() {
    if (!this.settings.authToken) {
      new import_obsidian3.Notice("Nausica: log in first \u2014 Settings \u2192 Nausica Cognitive Map.");
      return;
    }
    const files = this.app.vault.getMarkdownFiles();
    if (files.length === 0) {
      new import_obsidian3.Notice("Nausica: no Markdown notes in this vault.");
      return;
    }
    new import_obsidian3.Notice(`Nausica: analyzing ${files.length} notes\u2026`);
    let done = 0;
    let failed = 0;
    for (const file of files) {
      try {
        await this.analyzeFile(file);
      } catch (err) {
        console.error(`Nausica: failed to analyze ${file.path}`, err);
        failed += 1;
        if (failed === 1) {
          new import_obsidian3.Notice("Nausica backend unreachable \u2014 is uvicorn running?");
        }
      }
      done += 1;
      if (done % 5 === 0) {
        new import_obsidian3.Notice(`Nausica: ${done}/${files.length} notes analyzed.`);
      }
      await sleep(100);
    }
    this.refreshMapViews();
    const active = this.app.workspace.getActiveFile();
    if (active) {
      const analysis = this.store.get(active.path);
      if (analysis) this.injectCard(active, analysis);
    }
    new import_obsidian3.Notice(
      failed > 0 ? `Nausica: done \u2014 ${done - failed} analyzed, ${failed} failed.` : `Nausica: all ${done} notes analyzed.`
    );
  }
  async handleFileOpen(file) {
    const cached = this.store.get(file.path);
    if (cached) {
      this.injectCard(file, cached);
      return;
    }
    if (!this.settings.autoAnalyzeOnOpen) return;
    if (!this.settings.authToken) return;
    try {
      const analysis = await this.analyzeFile(file);
      if (this.app.workspace.getActiveFile()?.path === file.path) {
        this.injectCard(file, analysis);
      }
      this.refreshMapViews();
    } catch (err) {
      console.error("Nausica auto-analyze failed", err);
      new import_obsidian3.Notice("Nausica backend unreachable \u2014 is uvicorn running?");
    }
  }
  // --- rendering -----------------------------------------------------------
  injectCard(file, analysis) {
    const view = this.app.workspace.getActiveViewOfType(import_obsidian3.MarkdownView);
    if (!view || view.file?.path !== file.path) return;
    const content = view.contentEl;
    content.querySelectorAll(`.${CARD_HOST_CLASS}`).forEach((node) => node.remove());
    const host = document.createElement("div");
    host.className = CARD_HOST_CLASS;
    content.prepend(host);
    renderInlineCard(host, analysis);
  }
  refreshMapViews() {
    for (const leaf of this.app.workspace.getLeavesOfType(VIEW_TYPE_RIGIDITY_MAP)) {
      const view = leaf.view;
      if (view instanceof RigidityMapView) view.refresh(this.store);
    }
  }
  async activateMapView() {
    const { workspace } = this.app;
    let leaf = workspace.getLeavesOfType(VIEW_TYPE_RIGIDITY_MAP)[0] ?? null;
    if (!leaf) {
      leaf = workspace.getRightLeaf(false);
      if (!leaf) return;
      await leaf.setViewState({ type: VIEW_TYPE_RIGIDITY_MAP, active: true });
    }
    workspace.revealLeaf(leaf);
    if (leaf.view instanceof RigidityMapView) leaf.view.refresh(this.store);
  }
};
