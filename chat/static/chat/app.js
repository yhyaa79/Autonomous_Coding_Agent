(() => {
  const LS_PROJECT = "aca_project_id";
  const LS_CONV = "aca_conversation_id";
  const LS_TIMELINE_PANEL = "aca_timeline_panel_open";
  const LS_SIDE_PANEL_MODE = "aca_side_panel_mode";
  const LS_SHOW_ALL_PHASE_LOGS = "aca_show_all_phase_logs";
  const LS_COMPOSER_MODELS = "aca_composer_enabled_models";
  const COMPOSER_COLLAPSE_WORDS = 320;
  const COMPOSER_INPUT_MIN_LINES = 2;
  const COMPOSER_INPUT_MAX_LINES = 8;
  const COMPOSER_ATTACH_MAX_BYTES = 512 * 1024;

  const CHEVRON_SVG =
    '<svg class="chevron-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M9 6l6 6-6 6"/></path></svg>';

  const COPY_SVG =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';

  const INFO_SVG =
    '<svg class="conv-info-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>';

  const SEND_BTN_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M214.6 41.4c-12.5-12.5-32.8-12.5-45.3 0l-160 160c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L160 141.2V448c0 17.7 14.3 32 32 32s32-14.3 32-32V141.2L329.4 246.6c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3l-160-160z"></path></svg>';

  const STOP_BTN_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="1.5" fill="currentColor"/></svg>';

  const LS_TREE_EXPANDED = "aca_file_tree_expanded";
  const FA_DATE_TIME_OPTS = {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  };

  const RESOURCE_KIND_LABELS = {
    code: "کد",
    prompt: "متن",
    link: "لینک",
    image: "تصویر",
    video: "ویدیو",
    audio: "صوت",
    mixed: "ترکیبی",
  };

  const acaRender = () => window.AcaRender || {};

  function formatCredits2(value) {
    if (value == null || value === "") return "—";
    const n = typeof value === "number" ? value : parseFloat(String(value).replace(/,/g, ""));
    if (!Number.isFinite(n)) return String(value);
    return n.toFixed(2);
  }

  const FALLBACK_AGENTS = [
    {
      id: "coding",
      display_name: "کدنویسی",
      description: "git، تست، lint",
      default_allow_shell: true,
      default_allow_write: true,
    },
    {
      id: "autonomous",
      display_name: "همهٔ ابزارها",
      description: "کد + SEO + اجتماعی",
      default_allow_shell: true,
      default_allow_write: true,
    },
  ];

  const el = {
    projectList: document.getElementById("project-list"),
    log: document.getElementById("log"),
    form: document.getElementById("form"),
    input: document.getElementById("input"),
    send: document.getElementById("send"),
    contextRing: document.getElementById("context-ring"),
    contextRingProgress: document.getElementById("context-ring-progress"),
    statusBar: document.getElementById("status-bar"),
    statusMascot: document.getElementById("status-mascot"),
    status: document.getElementById("status-line"),
    chatTitle: document.getElementById("chat-title"),
    showAllPhaseLogs: document.getElementById("show-all-phase-logs"),
    phaseLogPanel: document.getElementById("phase-log-panel"),
    phaseLogTrace: document.getElementById("phase-log-trace"),
    phaseLogEmpty: document.getElementById("phase-log-empty"),
    fileTree: document.getElementById("file-tree"),
    filePreview: document.getElementById("file-preview"),
    focusPreviewCard: document.getElementById("focus-preview-card"),
    focusScopeCard: document.getElementById("focus-scope-card"),
    toolTrace: document.getElementById("tool-trace"),
    btnCopyToolTrace: document.getElementById("btn-copy-tool-trace"),
    toolLinkInput: document.getElementById("tool-link-input"),
    btnAttachTool: document.getElementById("btn-attach-tool"),
    conversationToolsList: document.getElementById("conversation-tools-list"),
    btnCloseCodeChanges: document.getElementById("btn-close-code-changes"),
    conversationToolsCount: document.getElementById("conversation-tools-count"),
    scopeChips: document.getElementById("scope-chips"),
    btnNewProject: document.getElementById("btn-new-project"),
    dialogProject: document.getElementById("dialog-project"),
    formProject: document.getElementById("form-project"),
    cancelProject: document.getElementById("cancel-project"),
    projectRootPath: document.getElementById("project-root-path"),
    pathPickerList: document.getElementById("path-picker-list"),
    pathPickerCurrent: document.getElementById("path-picker-current"),
    pathPickerUp: document.getElementById("path-picker-up"),
    chatHead: document.querySelector(".aca-chat__head"),
    btnNewScheduledJob: document.getElementById("btn-new-scheduled-job"),
    dialogPermission: document.getElementById("dialog-permission"),
    permissionDialogTitle: document.getElementById("permission-dialog-title"),
    permissionDialogMessage: document.getElementById("permission-dialog-message"),
    permissionDialogDetail: document.getElementById("permission-dialog-detail"),
    permissionAllow: document.getElementById("permission-allow"),
    permissionDeny: document.getElementById("permission-deny"),
    userInputPanel: document.getElementById("user-input-panel"),
    userInputPanelTitle: document.getElementById("user-input-panel-title"),
    userInputPanelMessage: document.getElementById("user-input-panel-message"),
    userInputPanelFields: document.getElementById("user-input-panel-fields"),
    userInputPanelNotes: document.getElementById("user-input-panel-notes"),
    userInputPanelSubmit: document.getElementById("user-input-panel-submit"),
    userInputPanelCancel: document.getElementById("user-input-panel-cancel"),
    userInputPanelDismiss: document.getElementById("user-input-panel-dismiss"),
    jobDialogTitle: document.getElementById("job-dialog-title"),
    allowShell: document.getElementById("allow-shell"),
    allowWrite: document.getElementById("allow-write"),
    useStream: document.getElementById("use-stream"),
    enableThinking: document.getElementById("enable-thinking"),
    thinkingDeep: document.getElementById("thinking-deep"),
    maxRounds: document.getElementById("max-rounds"),
    btnDeleteProject: document.getElementById("btn-delete-project"),
    btnDeleteConversation: document.getElementById("btn-delete-conversation"),
    jobTimeline: document.getElementById("job-timeline"),
    timelineScroll: document.getElementById("timeline-scroll"),
    timelineNowLabel: document.getElementById("timeline-now-label"),
    jobRunTrace: document.getElementById("job-run-trace"),
    btnRefreshJobs: document.getElementById("btn-refresh-jobs"),
    dialogJob: document.getElementById("dialog-job"),
    formJob: document.getElementById("form-job"),
    cancelJob: document.getElementById("cancel-job"),
    llmModel: document.getElementById("llm-model"),
    llmModelLabel: document.getElementById("llm-model-label"),
    llmModelTrigger: document.getElementById("llm-model-trigger"),
    llmModelPanel: document.getElementById("llm-model-panel"),
    llmModelPicker: document.getElementById("llm-model-picker"),
    settingsModelCatalog: document.getElementById("settings-model-catalog"),
    btnComposerOptions: document.getElementById("btn-composer-options"),
    composerOptionsPopover: document.getElementById("composer-options-popover"),
    walletBadge: document.getElementById("wallet-badge"),
    btnLogout: document.getElementById("btn-logout"),
    appGrid: document.getElementById("app-grid"),
    panelProjects: document.getElementById("panel-projects"),
    panelViewProjects: document.getElementById("panel-view-projects"),
    btnToggleProjectsPanel: document.getElementById("btn-toggle-projects-panel"),
    btnToggleTimelinePanel: document.getElementById("btn-toggle-timeline-panel"),
    btnToggleChangesPanel: document.getElementById("btn-toggle-changes-panel"),
    btnToggleGrowthPanel: document.getElementById("btn-toggle-growth-panel"),
    btnToggleDebugPanel: document.getElementById("btn-toggle-debug-panel"),
    btnToggleServerPanel: document.getElementById("btn-toggle-server-panel"),
    panelViewTimeline: document.getElementById("panel-view-timeline"),
    panelViewChanges: document.getElementById("panel-view-changes"),
    panelViewGrowth: document.getElementById("panel-view-growth"),
    panelViewDebug: document.getElementById("panel-view-debug"),
    panelViewServer: document.getElementById("panel-view-server"),
    growthHubRoot: document.getElementById("growth-hub-root"),
    btnRefreshGrowthHub: document.getElementById("btn-refresh-growth-hub"),
    debugHubRoot: document.getElementById("debug-hub-root"),
    btnRefreshDebugHub: document.getElementById("btn-refresh-debug-hub"),
    codeChangesSummary: document.getElementById("code-changes-summary"),
    codeChangesScroll: document.getElementById("code-changes-scroll"),
    codeChangesTimeline: document.getElementById("code-changes-timeline"),
    codeChangesDetail: document.getElementById("code-changes-detail"),
    btnRefreshChanges: document.getElementById("btn-refresh-changes"),
    btnOpenSettings: document.getElementById("btn-open-settings"),
    btnCloseSettings: document.getElementById("btn-close-settings"),
    btnPhaseLogMore: document.getElementById("btn-phase-log-more"),
    viewChat: document.getElementById("view-chat"),
    panelViewSettings: document.getElementById("panel-view-settings"),
    composerAgentBadge: document.getElementById("composer-agent-badge"),
    btnNewResource: document.getElementById("btn-new-resource"),
    dialogResourceDetail: document.getElementById("dialog-resource-detail"),
    resourceDetailTitle: document.getElementById("resource-detail-title"),
    resourceDetailSlug: document.getElementById("resource-detail-slug"),
    resourceDetailVersion: document.getElementById("resource-detail-version"),
    resourceDetailKind: document.getElementById("resource-detail-kind"),
    resourceDetailDescription: document.getElementById("resource-detail-description"),
    resourceDetailBlocks: document.getElementById("resource-detail-blocks"),
    resourceDetailBlocksWrap: document.getElementById("resource-detail-blocks-wrap"),
    resourceDetailTags: document.getElementById("resource-detail-tags"),
    resourceDetailCopyLink: document.getElementById("resource-detail-copy-link"),
    resourceDetailClose: document.getElementById("resource-detail-close"),
    liveExec: document.getElementById("live-exec"),
    btnCloseLiveExec: document.getElementById("btn-close-live-exec"),
    btnToggleLiveExec: document.getElementById("btn-toggle-live-exec"),
    chatPanel: document.querySelector(".aca-chat"),
    timelineTraceBlock: document.getElementById("timeline-trace-block"),
    btnExpandJobTrace: document.getElementById("btn-expand-job-trace"),
    codeChangesTraceBlock: document.getElementById("code-changes-trace-block"),
    btnExpandCodeDetail: document.getElementById("btn-expand-code-detail"),
    fileAccessAlwaysInput: document.getElementById("file-access-always-input"),
    fileAccessDeniedInput: document.getElementById("file-access-denied-input"),
    fileAccessAlwaysList: document.getElementById("file-access-always-list"),
    fileAccessDeniedList: document.getElementById("file-access-denied-list"),
    btnFileAccessAlwaysAdd: document.getElementById("btn-file-access-always-add"),
    btnFileAccessDeniedAdd: document.getElementById("btn-file-access-denied-add"),
    fileAccessSave: document.getElementById("file-access-save"),
    fileAccessStatus: document.getElementById("file-access-status"),
    composerAttachments: document.getElementById("composer-attachments"),
    composerPasteFold: document.getElementById("composer-paste-fold"),
    composerFileInput: document.getElementById("composer-file-input"),
    btnComposerAttach: document.getElementById("btn-composer-attach"),
    btnComposerMic: document.getElementById("btn-composer-mic"),
    dialogFilePreview: document.getElementById("dialog-file-preview"),
    filePreviewModalTitle: document.getElementById("file-preview-modal-title"),
    filePreviewModalMeta: document.getElementById("file-preview-modal-meta"),
    filePreviewModalBody: document.getElementById("file-preview-modal-body"),
    filePreviewModalClose: document.getElementById("file-preview-modal-close"),
    dialogComposerAttachment: document.getElementById("dialog-composer-attachment"),
    composerAttachmentModalTitle: document.getElementById("composer-attachment-modal-title"),
    composerAttachmentModalMeta: document.getElementById("composer-attachment-modal-meta"),
    composerAttachmentModalBody: document.getElementById("composer-attachment-modal-body"),
    composerAttachmentModalClose: document.getElementById("composer-attachment-modal-close"),
    userLlmBaseUrl: document.getElementById("user-llm-base-url"),
    userLlmModel: document.getElementById("user-llm-model"),
    userLlmApiKey: document.getElementById("user-llm-api-key"),
    userLlmEnabled: document.getElementById("user-llm-enabled"),
    btnUserLlmSave: document.getElementById("btn-user-llm-save"),
    btnUserLlmClear: document.getElementById("btn-user-llm-clear"),
    userLlmStatus: document.getElementById("user-llm-status"),
    userLlmKeyHint: document.getElementById("user-llm-key-hint"),
    remoteHost: document.getElementById("remote-host"),
    remotePort: document.getElementById("remote-port"),
    remoteUsername: document.getElementById("remote-username"),
    remoteAuthMethod: document.getElementById("remote-auth-method"),
    remotePassword: document.getElementById("remote-password"),
    remotePrivateKey: document.getElementById("remote-private-key"),
    remoteKeyPassphrase: document.getElementById("remote-key-passphrase"),
    remoteRootPath: document.getElementById("remote-root-path"),
    remoteRootLocalHint: document.getElementById("remote-root-local-hint"),
    remoteHostFingerprint: document.getElementById("remote-host-fingerprint"),
    remoteStrictHostKey: document.getElementById("remote-strict-host-key"),
    remoteAllowServerWide: document.getElementById("remote-allow-server-wide"),
    remoteEnabled: document.getElementById("remote-enabled"),
    remotePasswordWrap: document.getElementById("remote-password-wrap"),
    remoteKeyWrap: document.getElementById("remote-key-wrap"),
    btnRemoteTest: document.getElementById("btn-remote-test"),
    btnRemoteClear: document.getElementById("btn-remote-clear"),
    remoteServerStatus: document.getElementById("remote-server-status"),
    remoteServerProjectHint: document.getElementById("remote-server-project-hint"),
  };

  const SIDE_PANEL_MODES = ["projects", "changes", "settings"];

  let state = {
    projects: [],
    conversations: [],
    conversationsByProject: {},
    expandedProjects: new Set(),
    showAllPhaseLogs: false,
    pathPickerPath: null,
    jobs: [],
    agents: FALLBACK_AGENTS,
    projectId: null,
    conversationId: null,
    conversation: null,
    scopePaths: [],
    selectingProject: false,
    timelineTimer: null,
    schedulerPollTimer: null,
    sessionCreatedConvId: null,
    convInputDirty: false,
    convMessageSent: false,
    jobRuns: [],
    growthHub: null,
    growthHubTab: "maintenance",
    debugHub: null,
    debugScan: null,
    debugScanning: false,
    busy: false,
    models: [],
    userLlm: null,
    walletBalance: null,
    sidePanelMode: "projects",
    codeChangesData: null,
    codeChangesSelectedTurn: null,
    codeChangesFocusMessageId: null,
    activeRunId: null,
    stopRequested: false,
    pendingPermission: null,
    pendingUserInput: null,
    userInputByConversation: {},
    streamHadAskUser: false,
    userInputAwaitingServer: false,
    treeExpandedPaths: new Set(),
    jobDialogCreateMode: false,
    resourceModal: { tool: null, versions: [], viewingPublicId: null },
    fileAccessDraft: { always: [], denied: [] },
    liveExecDismissed: true,
    jobTraceMaxed: false,
    codeDetailMaxed: false,
    streamingAssistantEl: null,
    composerAttachments: [],
    composerPasteFull: null,
    lastPreviewPath: null,
    lastPreviewContent: null,
    lastPreviewLang: null,
  };

  const JOB_STATUS_FA = {
    active: "فعال",
    paused: "متوقف",
    cancelled: "لغو",
    completed: "تمام",
  };

  const AGENT_BADGE_CLASS = {
    autonomous: "",
    coding: "",
    maintenance: "agent-badge--maintain",
    marketing: "agent-badge--marketing",
    seo: "agent-badge--seo",
    social: "agent-badge--social",
    debug: "agent-badge--debug",
  };

  const DEBUG_SEVERITY_FA = {
    critical: "بحرانی",
    high: "بالا",
    medium: "متوسط",
    low: "پایین",
    info: "اطلاع",
  };

  const DEBUG_CATEGORY_FA = {
    ui: "UI",
    ux: "UX",
    backend: "بک‌اند",
    functional: "عملکردی",
    security: "امنیت",
    performance: "کارایی",
    accessibility: "دسترسی",
    seo: "SEO",
  };

  const GROWTH_CHANNEL_STATUS_FA = {
    planned: "برنامه",
    active: "فعال",
    paused: "متوقف",
    blocked: "مسدود",
  };


  let statusMascotCtl = null;
  let statusClearTimer = null;
  const CONTEXT_RING_CIRCUMFERENCE = 2 * Math.PI * 15.5;

  function setStatus(t, opts = {}) {
    if (!el.status) return;
    const text = t || "";
    el.status.textContent = text;
    if (statusClearTimer) {
      clearTimeout(statusClearTimer);
      statusClearTimer = null;
    }
    if (text.trim() && !opts.persistent) {
      statusClearTimer = setTimeout(() => {
        if (el.status && el.status.textContent === text) {
          setStatus("");
        }
      }, 5000);
    }
    if (statusMascotCtl) statusMascotCtl.sync();
    syncPhaseLogPanelVisibility();
  }

  function modelContextLimit(modelId) {
    const id = modelId || (el.llmModel && el.llmModel.value) || "";
    const entry = (state.models || []).find((m) => m.id === id);
    if (entry && entry.context_window_tokens) {
      return Number(entry.context_window_tokens);
    }
    return 128000;
  }

  function isContextFull(extraText = "") {
    const ctx = state.conversation && state.conversation.context;
    const limit = (ctx && ctx.limit_tokens) || modelContextLimit();
    let used = (ctx && ctx.used_tokens) || 0;
    const draft = (extraText || "").trim();
    if (draft) used += Math.ceil(draft.length / 4);
    return used >= limit;
  }

  function syncContextRing(extraText = "") {
    if (!el.contextRing || !el.contextRingProgress) return;
    const ctx = state.conversation && state.conversation.context;
    const limit = (ctx && ctx.limit_tokens) || modelContextLimit();
    let used = (ctx && ctx.used_tokens) || 0;
    const draft = (extraText || "").trim();
    if (draft) used += Math.ceil(draft.length / 4);
    const ratio = limit > 0 ? Math.min(1, used / limit) : 0;
    const full = used >= limit;
    const filled = CONTEXT_RING_CIRCUMFERENCE * ratio;
    el.contextRingProgress.style.strokeDasharray = `${filled} ${CONTEXT_RING_CIRCUMFERENCE}`;
    el.contextRing.classList.toggle("context-ring--full", full);
    el.contextRing.hidden = !state.conversationId;
    el.contextRing.title = `کانتکست: ${used.toLocaleString("fa-IR")} / ${limit.toLocaleString(
      "fa-IR"
    )} توکن`;
    if (!state.busy && el.send && !el.send.classList.contains("send-btn--stop")) {
      el.send.disabled = full || !state.conversationId;
    }
  }

  function initStatusMascot() {
    if (!window.AcaStatusMascot || !el.statusBar || !el.statusMascot || !el.status) return;
    statusMascotCtl = window.AcaStatusMascot.init({
      barEl: el.statusBar,
      mascotEl: el.statusMascot,
      statusEl: el.status,
    });
  }

  function syncPhaseLogPanelVisibility() {
    if (!el.phaseLogPanel) return;
    const show =
      state.busy ||
      phaseLogPanelHasContent() ||
      !!(el.status && el.status.textContent.trim());
    el.phaseLogPanel.classList.toggle("is-active", show);
  }

  function renderWalletBadge() {
    if (!el.walletBadge) return;
    if (state.walletBalance == null) {
      el.walletBadge.textContent = "";
      return;
    }
    el.walletBadge.textContent = `اعتبار: ${formatCredits2(state.walletBalance)}`;
  }

  function applyWalletFromPayload(wallet) {
    if (!wallet) return;
    state.walletBalance = wallet.balance_credits;
    renderWalletBadge();
  }

  function byokModelId() {
    const cfg = window.APP_CONFIG || {};
    return cfg.byokModelId || "__aca_user_api__";
  }

  function parseAppUserLlm(raw) {
    if (!raw) return null;
    if (typeof raw === "string") {
      try {
        return JSON.parse(raw);
      } catch {
        return null;
      }
    }
    return raw;
  }

  function isByokModelSelected() {
    return !!(el.llmModel && el.llmModel.value === byokModelId());
  }

  function catalogModelEntries() {
    const entries = (state.models || []).map((m) => ({
      id: m.id,
      label: m.label,
      input_per_1k_credits: m.input_per_1k_credits,
      output_per_1k_credits: m.output_per_1k_credits,
      isByok: false,
    }));
    if (state.userLlm && state.userLlm.configured) {
      entries.push({
        id: state.userLlm.byok_model_id || byokModelId(),
        label: state.userLlm.label || "API شخصی (بدون کسر اعتبار)",
        input_per_1k_credits: null,
        output_per_1k_credits: null,
        isByok: true,
      });
    }
    return entries;
  }

  function allCatalogModelIds() {
    return catalogModelEntries().map((m) => m.id);
  }

  function getEnabledComposerModelIds() {
    const all = allCatalogModelIds();
    if (!all.length) return [];
    try {
      const raw = localStorage.getItem(LS_COMPOSER_MODELS);
      if (!raw) return all;
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed) || !parsed.length) return all;
      const filtered = parsed.filter((id) => all.includes(id));
      return filtered.length ? filtered : all;
    } catch {
      return all;
    }
  }

  function saveEnabledComposerModelIds(ids) {
    try {
      localStorage.setItem(LS_COMPOSER_MODELS, JSON.stringify(ids));
    } catch (e) {}
  }

  function modelLabelById(id) {
    const hit = catalogModelEntries().find((m) => m.id === id);
    return hit ? hit.label : id;
  }

  function syncLlmModelTriggerLabel() {
    if (!el.llmModelLabel || !el.llmModel) return;
    const val = el.llmModel.value;
    el.llmModelLabel.textContent = val ? modelLabelById(val) : "—";
  }

  function renderLlmModelPanel() {
    if (!el.llmModelPanel || !el.llmModel) return;
    const enabled = getEnabledComposerModelIds();
    el.llmModelPanel.innerHTML = "";
    if (!enabled.length) {
      const empty = document.createElement("p");
      empty.className = "llm-model-picker__empty";
      empty.textContent = "مدلی انتخاب نشده — از تنظیمات تیک بزنید";
      el.llmModelPanel.appendChild(empty);
      return;
    }
    enabled.forEach((id) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "llm-model-picker__option";
      btn.setAttribute("role", "option");
      btn.dataset.modelId = id;
      btn.textContent = modelLabelById(id);
      if (el.llmModel.value === id) btn.classList.add("is-selected");
      btn.addEventListener("click", () => selectComposerModel(id));
      el.llmModelPanel.appendChild(btn);
    });
  }

  function setLlmModelPanelOpen(open) {
    if (!el.llmModelPanel || !el.llmModelTrigger) return;
    const on = !!open;
    el.llmModelPanel.hidden = !on;
    el.llmModelTrigger.setAttribute("aria-expanded", on ? "true" : "false");
    if (on) renderLlmModelPanel();
  }

  function ensureComposerModelOption(id) {
    if (!el.llmModel || !id) return;
    if ([...el.llmModel.options].some((o) => o.value === id)) return;
    const entry = catalogModelEntries().find((m) => m.id === id);
    if (!entry) return;
    const opt = document.createElement("option");
    opt.value = entry.id;
    opt.textContent = entry.label;
    el.llmModel.appendChild(opt);
  }

  function selectComposerModel(id, opts = {}) {
    if (!el.llmModel || !id) return;
    const enabled = getEnabledComposerModelIds();
    if (!enabled.includes(id) && !opts.allowDisabled) return;
    ensureComposerModelOption(id);
    const prev = el.llmModel.value;
    el.llmModel.value = id;
    syncLlmModelTriggerLabel();
    renderLlmModelPanel();
    if (!opts.silent) setLlmModelPanelOpen(false);
    if (!opts.skipApi && prev !== id && state.conversationId) {
      api(`/api/conversations/${state.conversationId}/update/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ llm_model: id }),
      }).catch((e) => setStatus(e.message));
    }
    if (state.conversation && state.conversation.context) {
      state.conversation.context.model_id = id;
      state.conversation.context.limit_tokens = modelContextLimit(id);
      const used = state.conversation.context.used_tokens || 0;
      state.conversation.context.remaining_tokens = Math.max(
        0,
        state.conversation.context.limit_tokens - used
      );
      state.conversation.context.full = used >= state.conversation.context.limit_tokens;
    }
    syncContextRing(el.input?.value || "");
  }

  function renderSettingsModelCatalog() {
    if (!el.settingsModelCatalog) return;
    const enabled = new Set(getEnabledComposerModelIds());
    el.settingsModelCatalog.innerHTML = "";
    catalogModelEntries().forEach((m) => {
      const row = document.createElement("label");
      row.className = "settings-model-row";
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = enabled.has(m.id);
      cb.dataset.modelId = m.id;
      const name = document.createElement("span");
      name.className = "settings-model-row__name";
      name.textContent = m.label;
      const price = document.createElement("span");
      price.className = "settings-model-row__price muted";
      if (m.isByok) {
        price.textContent = "بدون کسر اعتبار ACA";
      } else {
        price.textContent = `in ${formatCredits2(m.input_per_1k_credits)} / out ${formatCredits2(m.output_per_1k_credits)} per 1k`;
      }
      row.appendChild(cb);
      row.appendChild(name);
      row.appendChild(price);
      cb.addEventListener("change", () => {
        const ids = [...el.settingsModelCatalog.querySelectorAll("input[type=checkbox]")]
          .filter((input) => input.checked)
          .map((input) => input.dataset.modelId);
        const all = allCatalogModelIds();
        const next = ids.length ? ids.filter((id) => all.includes(id)) : all;
        saveEnabledComposerModelIds(next);
        initModelSelect({ preserveValue: true });
      });
      el.settingsModelCatalog.appendChild(row);
    });
  }

  function initModelSelect(opts = {}) {
    if (!el.llmModel) return;
    const cfg = window.APP_CONFIG || {};
    state.models = cfg.models || [];
    if (typeof state.models === "string") {
      try {
        state.models = JSON.parse(state.models);
      } catch {
        state.models = [];
      }
    }
    if (!state.userLlm) state.userLlm = parseAppUserLlm(cfg.userLlm);
    const prev = opts.preserveValue ? el.llmModel.value : "";
    const enabled = getEnabledComposerModelIds();
    el.llmModel.innerHTML = "";
    catalogModelEntries()
      .filter((m) => enabled.includes(m.id))
      .forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = m.label;
        el.llmModel.appendChild(opt);
      });
    const def = cfg.defaultModel || cfg.model || "gpt-4o-mini";
    if (prev && [...el.llmModel.options].some((o) => o.value === prev)) {
      el.llmModel.value = prev;
    } else if (el.llmModel.querySelector(`option[value="${def}"]`)) {
      el.llmModel.value = def;
    } else if (el.llmModel.options.length) {
      el.llmModel.selectedIndex = 0;
    }
    syncLlmModelTriggerLabel();
    renderLlmModelPanel();
    renderSettingsModelCatalog();
  }

  function setComposerOptionsOpen(open) {
    if (!el.composerOptionsPopover || !el.btnComposerOptions) return;
    const on = !!open;
    el.composerOptionsPopover.hidden = !on;
    el.btnComposerOptions.setAttribute("aria-expanded", on ? "true" : "false");
  }

  function initComposerOptionsUi() {
    if (el.btnComposerOptions && el.composerOptionsPopover) {
      el.btnComposerOptions.addEventListener("click", (ev) => {
        ev.stopPropagation();
        const open = el.composerOptionsPopover.hidden;
        setComposerOptionsOpen(open);
        if (open) setLlmModelPanelOpen(false);
      });
    }
    if (el.llmModelTrigger) {
      el.llmModelTrigger.addEventListener("click", (ev) => {
        ev.stopPropagation();
        if (el.llmModelTrigger.disabled) return;
        const open = el.llmModelPanel && el.llmModelPanel.hidden;
        setLlmModelPanelOpen(open);
        if (open) setComposerOptionsOpen(false);
      });
    }
    document.addEventListener("click", (ev) => {
      const t = ev.target;
      if (el.composerOptionsPopover && !el.composerOptionsPopover.hidden) {
        if (!el.composerOptionsPopover.contains(t) && t !== el.btnComposerOptions && !el.btnComposerOptions?.contains(t)) {
          setComposerOptionsOpen(false);
        }
      }
      if (el.llmModelPanel && !el.llmModelPanel.hidden) {
        if (!el.llmModelPicker?.contains(t)) setLlmModelPanelOpen(false);
      }
    });
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") {
        setComposerOptionsOpen(false);
        setLlmModelPanelOpen(false);
      }
    });
  }

  function syncSidePanelModeUi(mode) {
    const m = SIDE_PANEL_MODES.includes(mode) ? mode : "projects";
    state.sidePanelMode = m;
    if (m !== "projects") {
      localStorage.setItem(LS_SIDE_PANEL_MODE, m);
    }
    if (el.btnToggleProjectsPanel) {
      el.btnToggleProjectsPanel.classList.toggle("is-active", m === "projects");
    }
    if (el.btnOpenSettings) {
      el.btnOpenSettings.classList.toggle("is-active", m === "settings");
    }
    if (el.panelViewProjects) {
      el.panelViewProjects.classList.toggle("panel-side-view-hidden", m !== "projects");
      el.panelViewProjects.hidden = m !== "projects";
    }
    if (el.panelViewChanges) {
      el.panelViewChanges.classList.toggle("panel-side-view-hidden", m !== "changes");
      el.panelViewChanges.hidden = m !== "changes";
    }
    if (el.panelViewSettings) {
      el.panelViewSettings.classList.toggle("panel-side-view-hidden", m !== "settings");
      el.panelViewSettings.hidden = m !== "settings";
    }
    if (el.panelProjects) {
      el.panelProjects.classList.toggle("mode-changes", m === "changes");
      el.panelProjects.classList.toggle("mode-settings", m === "settings");
      el.panelProjects.classList.toggle("is-dock-wide", m === "changes" || m === "settings");
    }
    if (m === "changes" && state.conversationId) {
      loadConversationCodeChanges().catch((e) => setStatus(e.message));
    }
  }

  function syncSidePanelUi(open, mode) {
    const isOpen = !!open;
    const nextMode = isOpen
      ? SIDE_PANEL_MODES.includes(mode) && mode !== "projects"
        ? mode
        : state.sidePanelMode !== "projects"
          ? state.sidePanelMode
          : "projects"
      : "projects";
    syncSidePanelModeUi(nextMode);
    localStorage.setItem(LS_TIMELINE_PANEL, isOpen ? "1" : "0");
  }

  function isSidePanelCollapsed() {
    return state.sidePanelMode === "projects";
  }

  function toggleSidePanelMode(mode) {
    if (mode === "projects") {
      syncSidePanelUi(false);
      return;
    }
    const onProjects = isSidePanelCollapsed();
    if (onProjects || state.sidePanelMode !== mode) {
      syncSidePanelUi(true, mode);
    } else {
      syncSidePanelUi(false);
    }
  }

  let themeMode = "dark";

  function themeIsDark(mode) {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    return mode === "dark" || (mode === "system" && prefersDark);
  }

  function syncHljsTheme(dark) {
    const lightCss = document.getElementById("hljs-theme-light");
    const darkCss = document.getElementById("hljs-theme-dark");
    if (lightCss) lightCss.disabled = !!dark;
    if (darkCss) darkCss.disabled = !dark;
  }

  function applyThemeChoice(mode) {
    themeMode = mode || "dark";
    const dark = themeIsDark(themeMode);
    document.body.classList.toggle("dark-mode", dark);
    syncHljsTheme(dark);
    try {
      localStorage.setItem("aca_theme", themeMode);
    } catch (e) {}
    document.querySelectorAll(".theme-pill").forEach((btn) => {
      btn.classList.toggle("is-selected", btn.getAttribute("data-theme") === themeMode);
    });
  }

  function syncPhaseLogMoreButton() {
    if (!el.btnPhaseLogMore) return;
    el.btnPhaseLogMore.classList.toggle("is-active", state.showAllPhaseLogs);
    el.btnPhaseLogMore.setAttribute(
      "aria-pressed",
      state.showAllPhaseLogs ? "true" : "false"
    );
  }

  function toggleShowAllPhaseLogs() {
    state.showAllPhaseLogs = !state.showAllPhaseLogs;
    if (el.showAllPhaseLogs) el.showAllPhaseLogs.checked = state.showAllPhaseLogs;
    localStorage.setItem(LS_SHOW_ALL_PHASE_LOGS, state.showAllPhaseLogs ? "1" : "0");
    refreshPhaseLogVisibility();
    syncPhaseLogMoreButton();
  }

  function updateComposerOptionsEnabled(enabled) {
    const on = !!enabled;
    if (el.llmModel) el.llmModel.disabled = !on;
    if (el.llmModelTrigger) el.llmModelTrigger.disabled = !on;
    if (el.btnComposerOptions) el.btnComposerOptions.disabled = !on;
    if (el.maxRounds) el.maxRounds.disabled = !on;
    if (el.allowWrite) el.allowWrite.disabled = !on;
    if (el.allowShell) el.allowShell.disabled = !on;
    if (el.enableThinking) el.enableThinking.disabled = !on;
    if (el.thinkingDeep) el.thinkingDeep.disabled = !on;
  }

  function updateComposerAgentBadge(agentType) {
    if (!el.composerAgentBadge) return;
    if (!agentType) {
      el.composerAgentBadge.hidden = true;
      el.composerAgentBadge.textContent = "—";
      return;
    }
    el.composerAgentBadge.hidden = false;
    el.composerAgentBadge.textContent = `ایجنت: ${agentLabel(agentType)}`;
  }

  function setUserLlmStatus(text, isError) {
    if (!el.userLlmStatus) return;
    if (!text) {
      el.userLlmStatus.hidden = true;
      el.userLlmStatus.textContent = "";
      return;
    }
    el.userLlmStatus.hidden = false;
    el.userLlmStatus.textContent = text;
    el.userLlmStatus.style.color = isError ? "var(--color-danger, #f87171)" : "";
  }

  function applyUserLlmForm(status) {
    state.userLlm = status;
    if (el.userLlmBaseUrl && status && status.base_url) el.userLlmBaseUrl.value = status.base_url;
    if (el.userLlmModel && status && status.remote_model) el.userLlmModel.value = status.remote_model;
    if (el.userLlmEnabled) el.userLlmEnabled.checked = status ? status.configured !== false : true;
    if (el.userLlmKeyHint) {
      el.userLlmKeyHint.textContent = status && status.has_key
        ? "کلید ذخیره شده است. برای تعویض، کلید جدید وارد کنید."
        : "کلید ذخیره‌شده روی سرور رمزنگاری می‌شود و در UI نمایش داده نمی‌شود.";
    }
    if (el.userLlmApiKey) el.userLlmApiKey.value = "";
    initModelSelect({ preserveValue: true });
  }

  async function loadUserLlmSettings() {
    try {
      const data = await api("/api/user/llm-settings/");
      applyUserLlmForm(data);
    } catch (e) {
      setUserLlmStatus(e.message, true);
    }
  }

  function initUserLlmSettingsUi() {
    const cfg = window.APP_CONFIG || {};
    if (cfg.userLlm) applyUserLlmForm(parseAppUserLlm(cfg.userLlm));
    if (el.btnUserLlmSave) {
      el.btnUserLlmSave.addEventListener("click", async () => {
        setUserLlmStatus("در حال اعتبارسنجی…", false);
        try {
          const data = await api("/api/user/llm-settings/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              api_key: el.userLlmApiKey ? el.userLlmApiKey.value : "",
              base_url: el.userLlmBaseUrl ? el.userLlmBaseUrl.value : "",
              remote_model: el.userLlmModel ? el.userLlmModel.value : "",
              is_enabled: el.userLlmEnabled ? el.userLlmEnabled.checked : true,
            }),
          });
          applyUserLlmForm(data);
          setUserLlmStatus("ذخیره شد. مدل «API شخصی» در composer فعال است.", false);
        } catch (e) {
          setUserLlmStatus(e.message, true);
        }
      });
    }
    if (el.btnUserLlmClear) {
      el.btnUserLlmClear.addEventListener("click", async () => {
        if (!window.confirm("کلید API شخصی حذف شود؟")) return;
        try {
          const data = await api("/api/user/llm-settings/", { method: "DELETE" });
          applyUserLlmForm(data);
          setUserLlmStatus("کلید حذف شد.", false);
        } catch (e) {
          setUserLlmStatus(e.message, true);
        }
      });
    }
    loadUserLlmSettings().catch(() => {});
  }

  function setRemoteServerStatus(text, isError) {
    if (!el.remoteServerStatus) return;
    if (!text) {
      el.remoteServerStatus.hidden = true;
      el.remoteServerStatus.textContent = "";
      return;
    }
    el.remoteServerStatus.hidden = false;
    el.remoteServerStatus.textContent = text;
    el.remoteServerStatus.style.color = isError ? "var(--color-danger, #f87171)" : "";
  }

  function remoteFormEnabled(on) {
    const ids = [
      "remoteHost",
      "remotePort",
      "remoteUsername",
      "remoteAuthMethod",
      "remotePassword",
      "remotePrivateKey",
      "remoteKeyPassphrase",
      "remoteRootPath",
      "remoteHostFingerprint",
      "remoteStrictHostKey",
      "remoteAllowServerWide",
      "remoteEnabled",
      "btnRemoteTest",
      "btnRemoteClear",
    ];
    ids.forEach((key) => {
      const node = el[key];
      if (node) node.disabled = !on;
    });
  }

  function syncRemoteAuthMethodUi() {
    const method = el.remoteAuthMethod ? el.remoteAuthMethod.value : "password";
    if (el.remotePasswordWrap) el.remotePasswordWrap.hidden = method !== "password";
    if (el.remoteKeyWrap) el.remoteKeyWrap.hidden = method !== "private_key";
  }

  function applyRemoteServerForm(status, opts = {}) {
    const preserveSecrets = opts.preserveSecrets !== false;
    if (!status) return;
    if (el.remoteHost) el.remoteHost.value = status.host || "";
    if (el.remotePort) el.remotePort.value = String(status.port || 22);
    if (el.remoteUsername) el.remoteUsername.value = status.username || "";
    if (el.remoteAuthMethod) el.remoteAuthMethod.value = status.auth_method || "password";
    if (el.remoteRootPath) el.remoteRootPath.value = status.remote_root_path || "";
    if (el.remoteRootLocalHint) {
      const local = (status.local_root_path || "").trim();
      if (local) {
        el.remoteRootLocalHint.hidden = false;
        el.remoteRootLocalHint.textContent =
          `مسیر لوکال این پروژه (روی همین ماشین، برای SSH استفاده نکنید): ${local}`;
      } else {
        el.remoteRootLocalHint.hidden = true;
        el.remoteRootLocalHint.textContent = "";
      }
    }
    if (el.remoteHostFingerprint) el.remoteHostFingerprint.value = status.host_key_fingerprint || "";
    if (el.remoteStrictHostKey) el.remoteStrictHostKey.checked = status.strict_host_key !== false;
    if (el.remoteAllowServerWide) {
      el.remoteAllowServerWide.checked = !!status.allow_server_wide_paths;
    }
    if (el.remoteEnabled) el.remoteEnabled.checked = !!status.enabled;
    if (!preserveSecrets) {
      if (el.remotePassword) el.remotePassword.value = "";
      if (el.remotePrivateKey) el.remotePrivateKey.value = "";
      if (el.remoteKeyPassphrase) el.remoteKeyPassphrase.value = "";
    }
    syncRemoteAuthMethodUi();
  }

  function remoteServerPayload() {
    const auth = el.remoteAuthMethod ? el.remoteAuthMethod.value : "password";
    const body = {
      host: el.remoteHost ? el.remoteHost.value.trim() : "",
      port: el.remotePort ? parseInt(el.remotePort.value, 10) || 22 : 22,
      username: el.remoteUsername ? el.remoteUsername.value.trim() : "",
      auth_method: auth,
      remote_root_path: el.remoteRootPath ? el.remoteRootPath.value.trim() : "",
      host_key_fingerprint: el.remoteHostFingerprint ? el.remoteHostFingerprint.value.trim() : "",
      strict_host_key: el.remoteStrictHostKey ? el.remoteStrictHostKey.checked : true,
      allow_server_wide_paths: el.remoteAllowServerWide ? el.remoteAllowServerWide.checked : false,
      is_enabled: el.remoteEnabled ? el.remoteEnabled.checked : false,
    };
    if (auth === "private_key") {
      body.private_key = el.remotePrivateKey ? el.remotePrivateKey.value.trim() : "";
      body.key_passphrase = el.remoteKeyPassphrase ? el.remoteKeyPassphrase.value : "";
    } else {
      body.password = el.remotePassword ? el.remotePassword.value : "";
    }
    return body;
  }

  let remoteServerSaveTimer = null;
  let remoteServerSaving = false;

  async function persistRemoteServerSettings(silent) {
    if (!state.projectId || remoteServerSaving) return;
    remoteServerSaving = true;
    if (!silent) setRemoteServerStatus("در حال ذخیره…", false);
    try {
      const data = await api(`/api/projects/${state.projectId}/remote-server/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(remoteServerPayload()),
      });
      applyRemoteServerForm(data, { preserveSecrets: true });
      await loadProjects();
      if (!silent) setRemoteServerStatus("ذخیره شد.", false);
    } catch (e) {
      setRemoteServerStatus(e.message, true);
    } finally {
      remoteServerSaving = false;
    }
  }

  function scheduleRemoteServerSave() {
    if (!state.projectId) return;
    clearTimeout(remoteServerSaveTimer);
    remoteServerSaveTimer = setTimeout(() => {
      persistRemoteServerSettings(true).catch(() => {});
    }, 650);
  }

  function bindRemoteServerAutoSave() {
    const nodes = [
      el.remoteHost,
      el.remotePort,
      el.remoteUsername,
      el.remoteAuthMethod,
      el.remotePassword,
      el.remotePrivateKey,
      el.remoteKeyPassphrase,
      el.remoteRootPath,
      el.remoteHostFingerprint,
      el.remoteStrictHostKey,
      el.remoteAllowServerWide,
      el.remoteEnabled,
    ];
    nodes.forEach((node) => {
      if (!node) return;
      const ev = node.type === "checkbox" || node.tagName === "SELECT" ? "change" : "input";
      node.addEventListener(ev, () => scheduleRemoteServerSave());
    });
  }

  async function loadRemoteServerSettings(projectId) {
    const pid = Number(projectId);
    if (!pid) {
      remoteFormEnabled(false);
      if (el.remoteServerProjectHint) {
        el.remoteServerProjectHint.textContent =
          "پروژه‌ای را از لیست انتخاب کنید تا اتصال SSH آن را تنظیم کنید.";
      }
      return;
    }
    remoteFormEnabled(true);
    const p = state.projects.find((x) => x.id === pid);
    if (el.remoteServerProjectHint && p) {
      el.remoteServerProjectHint.textContent = `پروژه: ${p.name} — دستورات ایجنت روی سرور زیر اجرا می‌شوند.`;
    }
    try {
      const data = await api(`/api/projects/${pid}/remote-server/`);
      applyRemoteServerForm(data, { preserveSecrets: false });
      setRemoteServerStatus("", false);
    } catch (e) {
      setRemoteServerStatus(e.message, true);
    }
  }

  function initRemoteServerSettingsUi() {
    if (!el.remoteHost && !el.btnRemoteTest) return;
    if (el.remoteAuthMethod) {
      el.remoteAuthMethod.addEventListener("change", syncRemoteAuthMethodUi);
    }
    bindRemoteServerAutoSave();
    if (el.btnRemoteTest) {
      el.btnRemoteTest.addEventListener("click", async () => {
        if (!state.projectId) return;
        setRemoteServerStatus("در حال تست اتصال…", false);
        try {
          const data = await api(`/api/projects/${state.projectId}/remote-server/test/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(remoteServerPayload()),
          });
          let msg = data.remote_root_check || "اتصال موفق بود.";
          if (data.fingerprint) {
            msg += ` Fingerprint: ${data.fingerprint}`;
            if (el.remoteHostFingerprint && !el.remoteHostFingerprint.value.trim()) {
              el.remoteHostFingerprint.value = data.fingerprint;
              scheduleRemoteServerSave();
            }
          }
          setRemoteServerStatus(msg, !data.remote_root_ok);
        } catch (e) {
          setRemoteServerStatus(e.message, true);
        }
      });
    }
    if (el.btnRemoteClear) {
      el.btnRemoteClear.addEventListener("click", async () => {
        if (!state.projectId || !window.confirm("اتصال SSH این پروژه حذف شود؟")) return;
        try {
          await api(`/api/projects/${state.projectId}/remote-server/`, { method: "DELETE" });
          await loadRemoteServerSettings(state.projectId);
          await loadProjects();
          setRemoteServerStatus("تنظیمات SSH حذف شد.", false);
        } catch (e) {
          setRemoteServerStatus(e.message, true);
        }
      });
    }
    syncRemoteAuthMethodUi();
    loadRemoteServerSettings(state.projectId).catch(() => {});
  }

  function initSettingsUi() {
    if (el.btnOpenSettings) {
      el.btnOpenSettings.addEventListener("click", () => toggleSidePanelMode("settings"));
    }
    if (el.btnCloseSettings) {
      el.btnCloseSettings.addEventListener("click", () => syncSidePanelUi(false));
    }
    if (el.btnPhaseLogMore) {
      el.btnPhaseLogMore.addEventListener("click", () => toggleShowAllPhaseLogs());
    }
    initUserLlmSettingsUi();
    let savedTheme = "dark";
    try {
      savedTheme = localStorage.getItem("aca_theme") || "dark";
    } catch (e) {}
    applyThemeChoice(savedTheme);
    document.querySelectorAll(".theme-pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        applyThemeChoice(btn.getAttribute("data-theme") || "dark");
      });
    });
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      if (themeMode === "system") applyThemeChoice("system");
    });
  }

  function setComposerEntryEnabled(on) {
    const enabled = !!on;
    if (el.btnComposerAttach) el.btnComposerAttach.disabled = !enabled;
    if (el.btnComposerMic) el.btnComposerMic.disabled = !enabled;
    if (!enabled) stopSpeechToText();
  }

  function openCodeChangesPanel(assistantMessageId) {
    state.codeChangesFocusMessageId = assistantMessageId || null;
    syncSidePanelUi(true, "changes");
  }

  async function patchGrowthHub(body) {
    if (!state.projectId) return null;
    const data = await api(`/api/projects/${state.projectId}/growth-hub/`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    state.growthHub = data.growth_hub;
    renderGrowthHub();
    return data;
  }

  async function loadGrowthHub() {
    if (!state.projectId || !el.growthHubRoot) return;
    el.growthHubRoot.innerHTML = '<p class="timeline-empty muted">در حال بارگذاری…</p>';
    const data = await api(`/api/projects/${state.projectId}/growth-hub/`);
    state.growthHub = data.growth_hub;
    renderGrowthHub();
  }

  function renderGrowthHub() {
    if (!el.growthHubRoot) return;
    const hub = state.growthHub;
    if (!state.projectId || !hub) {
      el.growthHubRoot.innerHTML = '<p class="timeline-empty muted">پروژه انتخاب نشده</p>';
      return;
    }
    const tab = state.growthHubTab === "marketing" ? "marketing" : "maintenance";
    const stages = hub.stages || [];
    const stageHtml = stages
      .map((s) => {
        const active = s.id === hub.lifecycle_stage ? " is-active" : "";
        return `<button type="button" class="growth-stage-btn${active}" data-growth-stage="${escapeHtml(s.id)}">${escapeHtml(s.label)}<span>${escapeHtml(s.hint || "")}</span></button>`;
      })
      .join("");

    const tasks = tab === "marketing" ? hub.marketing_tasks || [] : hub.maintenance_tasks || [];
    const checklist = tasks
      .map((t) => {
        const checked = t.done ? " checked" : "";
        return `<li><input type="checkbox" data-growth-task="${escapeHtml(t.id)}" data-growth-list="${tab}"${checked}><span>${escapeHtml(t.title)}</span></li>`;
      })
      .join("");

    const catalog = hub.channel_catalog || [];
    const channels = hub.channels || {};
    const channelRows = catalog
      .map((ch) => {
        const st = channels[ch.id] || {};
        const enabled = st.enabled ? " checked" : "";
        const status = st.status || "planned";
        const opts = Object.keys(GROWTH_CHANNEL_STATUS_FA)
          .map(
            (k) =>
              `<option value="${k}"${k === status ? " selected" : ""}>${escapeHtml(GROWTH_CHANNEL_STATUS_FA[k])}</option>`
          )
          .join("");
        return `<div class="growth-channel-row" data-channel-id="${escapeHtml(ch.id)}">
          <label><input type="checkbox" data-growth-channel-enable="${escapeHtml(ch.id)}"${enabled}> ${escapeHtml(ch.label)}</label>
          <select data-growth-channel-status="${escapeHtml(ch.id)}">${opts}</select>
          <span class="muted" title="${escapeHtml(ch.notes || "")}">؟</span>
        </div>`;
      })
      .join("");

    const jobs = (hub.suggested_jobs || [])
      .map(
        (j) => `<div class="growth-job-card">
          <strong>${escapeHtml(j.title)}</strong>
          <div class="muted">${escapeHtml(j.cron_expression || j.schedule_kind || "")} · ${escapeHtml(j.target_agent_type || "")}</div>
          <button type="button" class="btn btn-tiny primary" data-growth-job="${escapeHtml(j.id)}">افزودن به تایم‌لاین</button>
        </div>`
      )
      .join("");

    const report =
      tab === "marketing"
        ? hub.last_marketing_plan || "—"
        : hub.last_maintenance_report || "—";

    el.growthHubRoot.innerHTML = `
      <section>
        <h4 class="muted" style="margin:0 0 8px;font-size:11px">چرخهٔ عمر محصول</h4>
        <div class="growth-lifecycle">${stageHtml}</div>
      </section>
      <div class="growth-field-row">
        <label for="growth-production-url">آدرس production</label>
        <input type="url" id="growth-production-url" placeholder="https://example.ir" value="${escapeHtml(hub.production_url || "")}">
        <button type="button" class="btn btn-tiny" id="btn-save-growth-url">ذخیره آدرس</button>
      </div>
      <div class="growth-tabs">
        <button type="button" class="growth-tab${tab === "maintenance" ? " is-active" : ""}" data-growth-tab="maintenance">نگهداری</button>
        <button type="button" class="growth-tab${tab === "marketing" ? " is-active" : ""}" data-growth-tab="marketing">مارکتینگ</button>
      </div>
      <ul class="growth-checklist">${checklist || "<li class='muted'>—</li>"}</ul>
      <div class="growth-actions">
        <button type="button" class="btn btn-tiny primary" data-growth-agent="maintenance">ایجنت نگهداری</button>
        <button type="button" class="btn btn-tiny primary" data-growth-agent="marketing">ایجنت مارکتینگ</button>
        <button type="button" class="btn btn-tiny" data-growth-open-timeline>تایم‌لاین jobها</button>
      </div>
      <section>
        <h4 class="muted" style="margin:12px 0 6px;font-size:11px">کانال‌ها (ایران)</h4>
        <div class="growth-channels">${channelRows}</div>
      </section>
      <section>
        <h4 class="muted" style="margin:12px 0 6px;font-size:11px">پیشنهاد زمان‌بندی</h4>
        <div class="growth-job-templates">${jobs}</div>
      </section>
      <section>
        <h4 class="muted" style="margin:12px 0 6px;font-size:11px">آخرین گزارش</h4>
        <div class="growth-report">${escapeHtml(report)}</div>
      </section>`;

    el.growthHubRoot.querySelectorAll("[data-growth-stage]").forEach((btn) => {
      btn.onclick = () =>
        patchGrowthHub({ lifecycle_stage: btn.dataset.growthStage }).catch((e) => setStatus(e.message));
    });
    el.growthHubRoot.querySelectorAll("[data-growth-tab]").forEach((btn) => {
      btn.onclick = () => {
        state.growthHubTab = btn.dataset.growthTab;
        renderGrowthHub();
      };
    });
    el.growthHubRoot.querySelectorAll("[data-growth-task]").forEach((inp) => {
      inp.onchange = () =>
        patchGrowthHub({
          toggle_task: {
            list: inp.dataset.growthList,
            task_id: inp.dataset.growthTask,
            done: inp.checked,
          },
        }).catch((e) => setStatus(e.message));
    });
    el.growthHubRoot.querySelectorAll("[data-growth-channel-enable]").forEach((inp) => {
      inp.onchange = () =>
        patchGrowthHub({
          channel: { id: inp.dataset.growthChannelEnable, enabled: inp.checked },
        }).catch((e) => setStatus(e.message));
    });
    el.growthHubRoot.querySelectorAll("[data-growth-channel-status]").forEach((sel) => {
      sel.onchange = () =>
        patchGrowthHub({
          channel: { id: sel.dataset.growthChannelStatus, status: sel.value },
        }).catch((e) => setStatus(e.message));
    });
    const saveUrl = el.growthHubRoot.querySelector("#btn-save-growth-url");
    const urlInput = el.growthHubRoot.querySelector("#growth-production-url");
    if (saveUrl && urlInput) {
      saveUrl.onclick = () =>
        patchGrowthHub({ production_url: urlInput.value.trim() }).catch((e) => setStatus(e.message));
    }
    el.growthHubRoot.querySelectorAll("[data-growth-agent]").forEach((btn) => {
      btn.onclick = () => startGrowthAgentChat(btn.dataset.growthAgent).catch((e) => setStatus(e.message));
    });
    const openTl = el.growthHubRoot.querySelector("[data-growth-open-timeline]");
    if (openTl) {
      openTl.onclick = () => syncSidePanelUi(true, "timeline");
    }
    el.growthHubRoot.querySelectorAll("[data-growth-job]").forEach((btn) => {
      btn.onclick = () => applySuggestedGrowthJob(btn.dataset.growthJob).catch((e) => setStatus(e.message));
    });
  }

  async function startGrowthAgentChat(agentType) {
    const prompts = {
      maintenance:
        "پروژه روی سرور استقرار یافته. یک دور کامل نگهداری انجام بده: health، لاگ، بکاپ، SSL و در صورت نیاز schedule_job برای پایش. نتیجه را در growth hub ثبت کن.",
      marketing:
        "برای بازار ایران یک طرح جذب کاربر ۲ هفته‌ای بده: کانال اصلی + جایگزین، متن فارسی آمادهٔ انتشار، SEO اولیه و KPI. محدودیت API شبکه‌های اجتماعی را در نظر بگیر.",
    };
    await createConversation(agentType);
    if (prompts[agentType]) {
      setComposerInputValue(prompts[agentType]);
      el.input.focus();
      setStatus("مکالمهٔ ایجنت آماده است — Enter برای ارسال");
    }
  }

  function debugSelectedCategories() {
    if (!el.debugHubRoot) return [];
    return [...el.debugHubRoot.querySelectorAll("[data-debug-cat]:checked")].map(
      (inp) => inp.dataset.debugCat
    );
  }

  function formatDebugScanReport(scan) {
    if (!scan) return "";
    const lines = [
      `URL: ${scan.url}`,
      `وضعیت: ${scan.status}`,
      `خلاصه: ${JSON.stringify(scan.summary || {})}`,
      "",
      "یافته‌ها:",
    ];
    (scan.findings || []).forEach((f, i) => {
      lines.push(
        `${i + 1}. [${f.severity}] ${f.title} (${f.category})`,
        `   ${f.description || ""}`,
        f.evidence ? `   شواهد: ${f.evidence}` : "",
        f.suggestion ? `   پیشنهاد: ${f.suggestion}` : ""
      );
    });
    return lines.filter(Boolean).join("\n");
  }

  async function patchDebugHub(body) {
    if (!state.projectId) return null;
    const data = await api(`/api/projects/${state.projectId}/debug-hub/`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    state.debugHub = data.debug_hub;
    if (data.scan) state.debugScan = data.scan;
    renderDebugHub();
    return data;
  }

  async function loadDebugHub() {
    if (!state.projectId || !el.debugHubRoot) return;
    el.debugHubRoot.innerHTML = '<p class="timeline-empty muted">در حال بارگذاری…</p>';
    const data = await api(`/api/projects/${state.projectId}/debug-hub/`);
    state.debugHub = data.debug_hub;
    if (!state.debugScan && data.debug_hub?.latest_scan) {
      state.debugScan = data.debug_hub.latest_scan;
    }
    renderDebugHub();
  }

  async function runDebugScan() {
    if (!state.projectId || state.debugScanning) return;
    const urlInput = el.debugHubRoot?.querySelector("#debug-page-url");
    const url = urlInput ? urlInput.value.trim() : "";
    const categories = debugSelectedCategories();
    state.debugScanning = true;
    renderDebugHub();
    try {
      const data = await api(`/api/projects/${state.projectId}/debug-hub/scan/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, categories }),
      });
      state.debugHub = data.debug_hub;
      state.debugScan = data.scan;
      setStatus("اسکن دیباگ تمام شد");
    } catch (e) {
      setStatus(e.message || "خطا در اسکن");
    } finally {
      state.debugScanning = false;
      renderDebugHub();
    }
  }

  function renderDebugFindings(scan) {
    const findings = scan?.findings || [];
    if (!findings.length) {
      return `<p class="muted">یافته‌ای ثبت نشد — یا صفحه سالم است یا اسکن محدود بود.</p>`;
    }
    return findings
      .map((f) => {
        const sev = f.severity || "info";
        const cat = DEBUG_CATEGORY_FA[f.category] || f.category;
        return `<article class="debug-finding" data-finding-id="${escapeHtml(f.id || "")}">
          <div class="debug-finding__head">
            <strong>${escapeHtml(f.title || "")}</strong>
            <span class="debug-sev debug-sev--${escapeHtml(sev)}">${escapeHtml(DEBUG_SEVERITY_FA[sev] || sev)} · ${escapeHtml(cat)}</span>
          </div>
          <p>${escapeHtml(f.description || "")}</p>
          ${f.evidence ? `<p class="debug-metrics">${escapeHtml(f.evidence)}</p>` : ""}
          ${f.suggestion ? `<p class="muted">${escapeHtml(f.suggestion)}</p>` : ""}
          <button type="button" class="btn btn-tiny" data-debug-fix-one="${escapeHtml(f.id || "")}">رفع با ایجنت</button>
        </article>`;
      })
      .join("");
  }

  function renderDebugHub() {
    if (!el.debugHubRoot) return;
    const hub = state.debugHub;
    if (!state.projectId || !hub) {
      el.debugHubRoot.innerHTML = '<p class="timeline-empty muted">پروژه انتخاب نشده</p>';
      return;
    }
    const preferred = new Set(hub.preferred_categories || []);
    const cats = hub.categories || [];
    const catHtml = cats
      .map((c) => {
        const on = preferred.has(c.id) ? " checked" : "";
        return `<label class="debug-cat-card${on ? " is-on" : ""}">
          <input type="checkbox" data-debug-cat="${escapeHtml(c.id)}"${on}>
          <div>${escapeHtml(c.label)}<span>${escapeHtml(c.hint || "")}</span></div>
        </label>`;
      })
      .join("");

    const scan = state.debugScan || hub.latest_scan;
    const summary = scan?.summary || {};
    const metrics = scan?.metrics || {};
    const summaryHtml = scan
      ? `<div class="debug-summary-strip">
          <span class="debug-pill">مجموع ${summary.total || 0}</span>
          ${summary.critical ? `<span class="debug-pill debug-pill--critical">بحرانی ${summary.critical}</span>` : ""}
          ${summary.high ? `<span class="debug-pill debug-pill--high">بالا ${summary.high}</span>` : ""}
          ${summary.medium ? `<span class="debug-pill">متوسط ${summary.medium}</span>` : ""}
        </div>
        <p class="debug-metrics">HTTP ${escapeHtml(String(metrics.status_code || "—"))} · ${escapeHtml(String(metrics.response_time_ms || "—"))}ms · ${escapeHtml(String(Math.round((metrics.size_bytes || 0) / 1024)))}KB</p>`
      : "";

    const history = (hub.recent_scans || [])
      .map((s) => {
        const active = scan && s.id === scan.id ? " is-active" : "";
        const tot = (s.summary && s.summary.total) || 0;
        return `<li><button type="button" class="${active}" data-debug-history="${s.id}">${escapeHtml(s.url || "")} · ${tot} مورد</button></li>`;
      })
      .join("");

    const scanning = state.debugScanning
      ? '<p class="muted">در حال اسکن صفحه…</p>'
      : renderDebugFindings(scan);

    el.debugHubRoot.innerHTML = `
      <p class="debug-intro">آدرس صفحه را وارد کنید، دسته‌های مورد نظر را انتخاب کنید و اسکن را شروع کنید. سپس با ایجنت دیباگ، رفع خودکار در کد پروژه انجام دهید.</p>
      <div class="debug-field-row">
        <label for="debug-page-url">آدرس صفحه</label>
        <input type="url" id="debug-page-url" placeholder="https://example.com/page" value="${escapeHtml(hub.last_url || "")}">
      </div>
      <div class="debug-cat-grid">${catHtml}</div>
      <div class="debug-scan-actions">
        <button type="button" class="btn btn-tiny primary" id="btn-run-debug-scan" ${state.debugScanning ? "disabled" : ""}>شروع اسکن</button>
        <button type="button" class="btn btn-tiny" id="btn-save-debug-prefs">ذخیره انتخاب‌ها</button>
        <button type="button" class="btn btn-tiny primary" id="btn-debug-agent-all" ${scan ? "" : "disabled"}>رفع همه با ایجنت</button>
      </div>
      ${summaryHtml}
      <section class="debug-findings">${scanning}</section>
      <section>
        <h4 class="muted" style="margin:8px 0 4px;font-size:11px">تاریخچه اسکن</h4>
        <ul class="debug-history">${history || "<li class='muted'>—</li>"}</ul>
      </section>`;

    el.debugHubRoot.querySelectorAll("[data-debug-cat]").forEach((inp) => {
      inp.onchange = () => {
        inp.closest(".debug-cat-card")?.classList.toggle("is-on", inp.checked);
      };
    });
    const runBtn = el.debugHubRoot.querySelector("#btn-run-debug-scan");
    if (runBtn) runBtn.onclick = () => runDebugScan().catch((e) => setStatus(e.message));
    const saveBtn = el.debugHubRoot.querySelector("#btn-save-debug-prefs");
    if (saveBtn) {
      saveBtn.onclick = () =>
        patchDebugHub({
          last_url: el.debugHubRoot.querySelector("#debug-page-url")?.value.trim(),
          preferred_categories: debugSelectedCategories(),
        }).catch((e) => setStatus(e.message));
    }
    const fixAll = el.debugHubRoot.querySelector("#btn-debug-agent-all");
    if (fixAll) {
      fixAll.onclick = () => startDebugAgentChat(scan, null).catch((e) => setStatus(e.message));
    }
    el.debugHubRoot.querySelectorAll("[data-debug-fix-one]").forEach((btn) => {
      btn.onclick = () => {
        const fid = btn.dataset.debugFixOne;
        const finding = (scan?.findings || []).find((f) => f.id === fid);
        startDebugAgentChat(scan, finding).catch((e) => setStatus(e.message));
      };
    });
    el.debugHubRoot.querySelectorAll("[data-debug-history]").forEach((btn) => {
      btn.onclick = () =>
        patchDebugHub({ load_scan_id: parseInt(btn.dataset.debugHistory, 10) }).catch((e) =>
          setStatus(e.message)
        );
    });
  }

  async function startDebugAgentChat(scan, singleFinding) {
    if (!scan) return;
    const report = singleFinding
      ? formatDebugScanReport({
          ...scan,
          findings: [singleFinding],
          summary: { total: 1 },
        })
      : formatDebugScanReport(scan);
    const intro = singleFinding
      ? "این یک یافتهٔ تکی از اسکن دیباگ است. در کد پروژه رفعش کن و در صورت امکان دوباره web_fetch بزن:"
      : "گزارش کامل اسکن دیباگ صفحه. هر مورد را در کد پروژه رفع کن (حداقل موارد بحرانی و بالا اولویت):";
    await createConversation("debug");
    setComposerInputValue(`${intro}\n\n${report}`);
    el.input.focus();
    setStatus("مکالمهٔ ایجنت دیباگ آماده است — Enter برای ارسال");
  }

  async function applySuggestedGrowthJob(jobId) {
    const hub = state.growthHub;
    if (!hub || !state.projectId) return;
    const tpl = (hub.suggested_jobs || []).find((j) => j.id === jobId);
    if (!tpl) return;
    await api(`/api/projects/${state.projectId}/jobs/create/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: tpl.title,
        target_agent_type: tpl.target_agent_type,
        schedule_kind: tpl.schedule_kind,
        cron_expression: tpl.cron_expression,
        timezone_name: "Asia/Tehran",
        message: tpl.message,
        status: "active",
      }),
    });
    setStatus("زمان‌بندی از طریق ایجنت (schedule_job / منبع time) ثبت شد");
    await loadJobsForProject(state.projectId);
  }

  function initSidePanelToggle() {
    const savedOpen = localStorage.getItem(LS_TIMELINE_PANEL);
    const open = savedOpen === "1";
    const savedMode = localStorage.getItem(LS_SIDE_PANEL_MODE);
    const allowedSaved =
      savedMode &&
      SIDE_PANEL_MODES.includes(savedMode) &&
      savedMode !== "projects" &&
      savedMode !== "tools"
        ? savedMode
        : null;
    if (open && allowedSaved && allowedSaved !== "changes") {
      syncSidePanelUi(true, allowedSaved);
    } else {
      syncSidePanelUi(false);
    }
    if (el.btnToggleProjectsPanel) {
      el.btnToggleProjectsPanel.onclick = () => syncSidePanelUi(false);
    }
    if (el.btnCloseCodeChanges) {
      el.btnCloseCodeChanges.onclick = () => syncSidePanelUi(false);
    }
    if (el.btnRefreshChanges) {
      el.btnRefreshChanges.onclick = () =>
        loadConversationCodeChanges().catch((e) => setStatus(e.message));
    }
  }

  function statusLabelFa(status) {
    if (status === "added") return "افزوده";
    if (status === "removed") return "حذف";
    return "ویرایش";
  }

  function renderCodeDiffLines(lines, marks, lang, lineNumbers) {
    const wrap = document.createElement("div");
    wrap.className = "cc-diff-lines";
    const language = lang || "plaintext";
    (lines || []).forEach((line, idx) => {
      const row = document.createElement("div");
      const mark = (marks && marks[idx]) || " ";
      const lineNo =
        lineNumbers && lineNumbers.length > idx ? lineNumbers[idx] : idx + 1;
      const isGap = lineNo == null;
      row.className =
        "cc-line" +
        (isGap ? " cc-line-gap" : "") +
        (!isGap && mark === "-" ? " mark-del" : !isGap && mark === "+" ? " mark-add" : "");
      const text = document.createElement("span");
      if (isGap) {
        text.textContent =
          line || "▼ خطوط میانی برای خوانایی نمایش داده نشده ▼";
        row.appendChild(text);
      } else {
        const num = document.createElement("span");
        num.className = "cc-line-num";
        num.textContent = String(lineNo);
        if (acaRender().highlightCode) {
          text.innerHTML = acaRender().highlightCode(line || "", language);
        } else {
          text.textContent = line || "";
        }
        row.appendChild(num);
        row.appendChild(text);
      }
      wrap.appendChild(row);
    });
    if (!lines || !lines.length) {
      wrap.innerHTML = '<div class="code-changes-detail-empty">—</div>';
    }
    return wrap;
  }

  function resetCodeDiffPaneScroll() {
    if (!el.codeChangesDetail) return;
    el.codeChangesDetail.querySelectorAll(".cc-diff-pane").forEach((pane) => {
      pane.scrollLeft = 0;
      pane.scrollTop = 0;
    });
  }

  function renderCodeChangesFileCard(file, turn) {
    const card = document.createElement("article");
    card.className = "cc-file-card";
    const head = document.createElement("div");
    head.className = "cc-file-head";
    const path = document.createElement("div");
    path.className = "cc-file-path";
    path.textContent = file.path || "";
    const meta = document.createElement("div");
    meta.className = "cc-file-head-meta";
    const badge = document.createElement("span");
    badge.className = `cc-file-badge ${file.status || "modified"}`;
    badge.textContent = statusLabelFa(file.status);
    meta.appendChild(badge);
    if (turn && turn.can_undo && turn.assistant_message_id && file.path) {
      const restoreBtn = document.createElement("button");
      restoreBtn.type = "button";
      restoreBtn.className = "btn btn-tiny btn-undo cc-file-restore";
      restoreBtn.textContent = "بازگردانی";
      restoreBtn.title = "برگرداندن فقط این فایل به محتوای قبل از این تغییر";
      restoreBtn.disabled = state.busy;
      restoreBtn.onclick = () =>
        restoreTurnFile(Number(turn.assistant_message_id), file.path);
      meta.appendChild(restoreBtn);
    }
    head.appendChild(path);
    head.appendChild(meta);
    card.appendChild(head);
    if (file.binary) {
      const note = document.createElement("div");
      note.className = "cc-binary-note";
      note.textContent = "فایل باینری یا بزرگ — نمایش متنی در دسترس نیست";
      card.appendChild(note);
      return card;
    }
    const split = document.createElement("div");
    split.className = "cc-diff-split";
    const beforePane = document.createElement("div");
    beforePane.className = "cc-diff-pane before";
    beforePane.innerHTML = '<div class="cc-diff-pane-label">قبل</div>';
    const lang = acaRender().langFromPath ? acaRender().langFromPath(file.path) : "plaintext";
    beforePane.appendChild(
      renderCodeDiffLines(
        file.before_lines,
        file.before_marks,
        lang,
        file.before_line_numbers
      )
    );
    const afterPane = document.createElement("div");
    afterPane.className = "cc-diff-pane after";
    afterPane.innerHTML = '<div class="cc-diff-pane-label">بعد</div>';
    afterPane.appendChild(
      renderCodeDiffLines(
        file.after_lines,
        file.after_marks,
        lang,
        file.after_line_numbers
      )
    );
    split.appendChild(beforePane);
    split.appendChild(afterPane);
    card.appendChild(split);
    return card;
  }

  function renderCodeChangesPanel(data) {
    if (!el.codeChangesDetail) return;
    el.codeChangesDetail.innerHTML = "";
    const turns = (data && data.turns) || [];
    if (!state.conversationId) {
      el.codeChangesDetail.innerHTML =
        '<div class="code-changes-detail-empty">ابتدا یک مکالمه انتخاب کنید</div>';
      return;
    }
    if (!turns.length) {
      el.codeChangesDetail.innerHTML =
        '<div class="code-changes-detail-empty">هنوز تغییری در فایل‌های این مکالمه ثبت نشده</div>';
      return;
    }
    const focusId = state.codeChangesFocusMessageId;
    turns.forEach((turn) => {
      const section = document.createElement("section");
      section.className = "cc-turn-block";
      if (focusId && turn.assistant_message_id === focusId) {
        section.classList.add("cc-turn-focus");
      }
      const filesWrap = document.createElement("div");
      filesWrap.className = "cc-turn-files";
      if (!turn.files || !turn.files.length) {
        filesWrap.innerHTML =
          '<div class="code-changes-detail-empty">فایلی برای این نوبت تغییر نکرده</div>';
      } else {
        turn.files.forEach((f) => filesWrap.appendChild(renderCodeChangesFileCard(f, turn)));
      }
      section.appendChild(filesWrap);
      el.codeChangesDetail.appendChild(section);
    });
    state.codeChangesFocusMessageId = null;
    resetCodeDiffPaneScroll();
    requestAnimationFrame(() => resetCodeDiffPaneScroll());
    const foc = el.codeChangesDetail.querySelector(".cc-turn-focus");
    if (foc) foc.scrollIntoView({ block: "start", behavior: "smooth" });
  }

  async function loadConversationCodeChanges() {
    if (!el.codeChangesDetail) return;
    if (!state.conversationId) {
      state.codeChangesData = null;
      renderCodeChangesPanel(null);
      if (el.btnRefreshChanges) el.btnRefreshChanges.disabled = true;
      return;
    }
    if (el.btnRefreshChanges) el.btnRefreshChanges.disabled = false;
    el.codeChangesDetail.innerHTML =
      '<div class="code-changes-detail-empty">در حال بارگذاری…</div>';
    const data = await api(`/api/conversations/${state.conversationId}/code-changes/`);
    state.codeChangesData = data;
    renderCodeChangesPanel(data);
  }

  function openMessageCodeChanges(assistantMessageId) {
    if (!assistantMessageId) return;
    state.codeChangesFocusMessageId = assistantMessageId;
    openCodeChangesPanel(assistantMessageId);
  }

  function showPhase(event) {
    if (!event || event.type !== "phase") return;
  }

  const PHASE_TRAIL_SKIP = new Set(["receive", "done"]);

  function phaseLogPanelHasContent() {
    if (!el.phaseLogTrace) return false;
    return !!el.phaseLogTrace.querySelector(
      ".phase-log-sync-bundle, .assistant-phase-log-bundle, .msg.phase-log"
    );
  }

  function phaseLogEntries() {
    if (!el.phaseLogTrace) return [];
    return [...el.phaseLogTrace.querySelectorAll(".msg.phase-log, .phase-log-sync-bundle")];
  }

  function syncPhaseLogEmptyState() {
    if (!el.phaseLogEmpty) return;
    el.phaseLogEmpty.hidden = phaseLogPanelHasContent();
  }

  function clearPhaseLogPanel() {
    if (!el.phaseLogTrace) return;
    el.phaseLogTrace.querySelectorAll(".msg.phase-log, .phase-log-sync-bundle").forEach((n) => n.remove());
    syncPhaseLogEmptyState();
  }

  function refreshPhaseLogVisibility() {
    const entries = phaseLogEntries();
    entries.forEach((node, idx) => {
      const show = state.showAllPhaseLogs || idx === entries.length - 1;
      node.hidden = !show;
    });
    syncPhaseLogEmptyState();
  }

  function syncPhaseLogPanelBundle() {
    if (!el.phaseLogTrace) return;
    el.phaseLogTrace.querySelectorAll(".phase-log-sync-bundle").forEach((n) => n.remove());
    const host = resolvePhaseLogHostAssistant();
    const src = host ? host.querySelector(".assistant-phase-log-bundle") : null;
    if (!src || !src.children.length) {
      syncPhaseLogEmptyState();
      return;
    }
    const clone = src.cloneNode(true);
    clone.classList.add("phase-log-sync-bundle");
    el.phaseLogTrace.appendChild(clone);
    refreshPhaseLogVisibility();
    el.phaseLogTrace.scrollTop = el.phaseLogTrace.scrollHeight;
  }

  function phaseLogLabel(event) {
    const payload = event.payload || event;
    const detail = payload.detail ? ` — ${payload.detail}` : event.detail ? ` — ${event.detail}` : "";
    const label = payload.label || payload.phase || event.label || event.phase || "log";
    return `${label}${detail}`;
  }

  function createPhaseLogChatNode(event) {
    const div = document.createElement("div");
    div.className = "msg phase-log phase-log-inline";
    div.textContent = phaseLogLabel(event);
    return div;
  }

  function resetPhaseBundleController(bundle) {
    if (!bundle) return;
    bundle._phaseCtrl = { groups: [], bundle };
    bundle.innerHTML = "";
  }

  function getPhaseBundleController(bundle) {
    if (!bundle._phaseCtrl) resetPhaseBundleController(bundle);
    return bundle._phaseCtrl;
  }

  function phaseEventMeta(event) {
    const payload = event.payload || event;
    const phase = payload.phase || event.phase || "";
    const label = phaseLogLabel(event);
    return { phase, label };
  }

  function isRoundMainPhaseEvent(event) {
    const { phase, label } = phaseEventMeta(event);
    if (phase === "model_plan") return true;
    return /(?:—\s*)?دور\s*\d+\s*$/.test(label);
  }

  function deactivatePhaseGroups(ctrl) {
    ctrl.groups.forEach((g) => {
      g.active = false;
    });
  }

  function ensurePreamblePhaseGroup(ctrl) {
    const last = ctrl.groups[ctrl.groups.length - 1];
    if (last && last.kind === "preamble") return last;
    deactivatePhaseGroups(ctrl);
    const group = {
      kind: "preamble",
      mainLabel: "آماده‌سازی",
      children: [],
      expanded: false,
      active: true,
    };
    ctrl.groups.push(group);
    return group;
  }

  function pushPhaseSubLog(ctrl, label) {
    let group = ctrl.groups[ctrl.groups.length - 1];
    if (!group || (group.kind === "milestone" && !group.active)) {
      group = ensurePreamblePhaseGroup(ctrl);
    }
    const lastChild = group.children[group.children.length - 1];
    if (lastChild !== label) group.children.push(label);
    group.active = true;
  }

  function ingestPhaseEvent(ctrl, event) {
    const { phase, label } = phaseEventMeta(event);
    if (PHASE_TRAIL_SKIP.has(phase)) return;

    if (isRoundMainPhaseEvent(event)) {
      deactivatePhaseGroups(ctrl);
      ctrl.groups.push({
        kind: "round",
        mainLabel: label,
        children: [],
        expanded: false,
        active: true,
      });
      return;
    }

    if (phase === "compose") {
      deactivatePhaseGroups(ctrl);
      ctrl.groups.push({
        kind: "milestone",
        mainLabel: label,
        children: [],
        expanded: false,
        active: true,
      });
      return;
    }

    pushPhaseSubLog(ctrl, label);
  }

  function resolvePhaseBundleFromClickTarget(node) {
    const host = node?.closest?.(".assistant-phase-log-bundle, .phase-log-sync-bundle");
    if (!host) return null;
    if (host.classList.contains("phase-log-sync-bundle")) {
      const assistant = resolvePhaseLogHostAssistant();
      return assistant?.querySelector(".assistant-phase-log-bundle") || null;
    }
    return host;
  }

  function handlePhaseLogMainClick(e) {
    const main = e.target.closest("[data-phase-main]");
    if (!main || main.disabled) return;
    const bundle = resolvePhaseBundleFromClickTarget(main);
    if (!bundle) return;
    const idx = Number(main.dataset.phaseIdx);
    const ctrl = getPhaseBundleController(bundle);
    const group = ctrl.groups[idx];
    if (!group || !group.children.length) return;
    group.expanded = !group.expanded;
    renderPhaseBundle(bundle);
    syncPhaseLogPanelBundle();
  }

  function renderPhaseBundle(bundle) {
    const ctrl = getPhaseBundleController(bundle);
    bundle.innerHTML = "";
    if (!ctrl.groups.length) return;

    const inProgress = !!bundle.closest(".assistant-in-progress");
    const stack = document.createElement("div");
    stack.className = "phase-log-stack";

    ctrl.groups.forEach((group, idx) => {
      const isLast = idx === ctrl.groups.length - 1;
      const isActive = inProgress && isLast && group.active;
      const hasChildren = group.children.length > 0;
      const wrap = document.createElement("div");
      wrap.className = "phase-log-group";
      if (group.expanded) wrap.classList.add("is-expanded");
      if (isActive) wrap.classList.add("is-active");
      if (!isActive) wrap.classList.add("is-settled");

      const mainBtn = document.createElement("button");
      mainBtn.type = "button";
      mainBtn.className = "phase-log-group__main";
      mainBtn.dataset.phaseMain = "1";
      mainBtn.dataset.phaseIdx = String(idx);
      mainBtn.setAttribute(
        "aria-expanded",
        group.expanded && hasChildren ? "true" : "false"
      );
      if (!hasChildren) mainBtn.disabled = true;

      const chev = document.createElement("span");
      chev.className = "phase-log-group__chev";
      chev.setAttribute("aria-hidden", "true");

      const mainText = document.createElement("span");
      mainText.className = "phase-log-group__main-text";
      mainText.textContent = group.mainLabel;

      mainBtn.appendChild(chev);
      mainBtn.appendChild(mainText);

      if (hasChildren) {
        const count = document.createElement("span");
        count.className = "phase-log-group__badge";
        count.textContent = String(group.children.length);
        mainBtn.appendChild(count);
      }

      wrap.appendChild(mainBtn);

      if (isActive && hasChildren && !group.expanded) {
        const live = document.createElement("div");
        live.className = "phase-log-group__live";
        live.setAttribute("aria-live", "polite");
        const liveText = document.createElement("span");
        liveText.className = "phase-log-group__live-text";
        liveText.textContent = group.children[group.children.length - 1];
        live.appendChild(liveText);
        wrap.appendChild(live);
      }

      if (hasChildren) {
        const subs = document.createElement("div");
        subs.className = "phase-log-group__subs";
        group.children.forEach((childLabel) => {
          const sub = document.createElement("div");
          sub.className = "phase-log-group__sub";
          sub.textContent = childLabel;
          subs.appendChild(sub);
        });
        wrap.appendChild(subs);
      }

      stack.appendChild(wrap);
    });

    bundle.appendChild(stack);
    syncPhaseLogPanelVisibility();
  }

  function appendPhaseEventToBundle(bundle, event) {
    const ctrl = getPhaseBundleController(bundle);
    ingestPhaseEvent(ctrl, event);
    renderPhaseBundle(bundle);
  }

  function renderPhaseBundleFromEvents(bundle, events) {
    resetPhaseBundleController(bundle);
    (events || []).forEach((ev) => appendPhaseEventToBundle(bundle, ev));
    renderPhaseBundle(bundle);
  }

  function pinAgentActivityIndicatorLast() {
    if (!el.log) return;
    const row = el.log.querySelector(".agent-activity-indicator");
    if (row) el.log.appendChild(row);
  }

  function ensureAssistantPhaseLogBundle(assistantEl) {
    if (!assistantEl) return null;
    let bundle = assistantEl.querySelector(".assistant-phase-log-bundle");
    if (!bundle) {
      bundle = document.createElement("div");
      bundle.className = "assistant-phase-log-bundle";
      resetPhaseBundleController(bundle);
      const body = assistantEl.querySelector(".msg-body");
      if (body) assistantEl.insertBefore(bundle, body);
      else assistantEl.prepend(bundle);
    }
    return bundle;
  }

  function createStreamingAssistantShell() {
    const div = document.createElement("div");
    div.className = "msg assistant assistant-in-progress";
    const bundle = document.createElement("div");
    bundle.className = "assistant-phase-log-bundle";
    resetPhaseBundleController(bundle);
    div.appendChild(bundle);
    const body = document.createElement("div");
    body.className = "msg-body";
    div.appendChild(body);
    const actions = document.createElement("div");
    actions.className = "msg-actions";
    div.appendChild(actions);
    el.log.appendChild(div);
    pinAgentActivityIndicatorLast();
    el.log.scrollTop = el.log.scrollHeight;
    syncChatHeadVisibility();
    return div;
  }

  function resolvePhaseLogHostAssistant() {
    if (state.streamingAssistantEl && state.streamingAssistantEl.isConnected) {
      return state.streamingAssistantEl;
    }
    const assistants = el.log ? [...el.log.querySelectorAll(".msg.assistant")] : [];
    for (let i = assistants.length - 1; i >= 0; i -= 1) {
      const node = assistants[i];
      if (node.classList.contains("assistant-in-progress")) return node;
    }
    return null;
  }

  function appendPhaseLogToChat(event) {
    if (!el.log || !event) return;
    let host = resolvePhaseLogHostAssistant();
    if (!host) {
      host = createStreamingAssistantShell();
      state.streamingAssistantEl = host;
    }
    const bundle = ensureAssistantPhaseLogBundle(host);
    appendPhaseEventToBundle(bundle, event);
    pinAgentActivityIndicatorLast();
    el.log.scrollTop = el.log.scrollHeight;
  }

  function addPhaseLogEntry(event) {
    appendPhaseLogToChat(event);
    syncPhaseLogPanelBundle();
  }

  function initPhaseLogPanel() {
    const saved = localStorage.getItem(LS_SHOW_ALL_PHASE_LOGS);
    if (saved === "1") {
      state.showAllPhaseLogs = true;
      if (el.showAllPhaseLogs) el.showAllPhaseLogs.checked = true;
    }
    if (el.log) el.log.addEventListener("click", handlePhaseLogMainClick);
    if (el.phaseLogTrace) el.phaseLogTrace.addEventListener("click", handlePhaseLogMainClick);
    syncPhaseLogEmptyState();
    syncPhaseLogMoreButton();
  }

  const TREE_ICON_FOLDER =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"></path></svg>';
  const TREE_ICON_FILE =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"></path><path d="M14 2v6h6"></path></svg>';

  const FILE_ICO_SVG = {
    text:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/><path d="M14 2v6h6"/><path d="M8 13h8M8 17h5"/></svg>',
    pdf:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/><path d="M14 2v6h6"/><path d="M8 16v-4h2.2a1.8 1.8 0 0 1 0 3.6H8"/></svg>',
    word:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/><path d="M14 2v6h6"/><path d="M8 12l1.5 6 2-4.5L14 18l1.5-6"/></svg>',
    sheet:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/><path d="M14 2v6h6"/><path d="M8 12h8M8 16h8M12 12v8"/></svg>',
    slides:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M12 16v4M8 20h8"/></svg>',
    image:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="1.5"/><path d="M21 17l-5-5-4 4-2-2-5 5"/></svg>',
    audio:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M9 18V6l10-2v14"/><path d="M6 15a3 3 0 1 0 0-6"/></svg>',
    video:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="6" width="14" height="12" rx="2"/><path d="M17 10l4-2v8l-4-2"/></svg>',
    archive:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 7h16v3H4z"/><path d="M6 10v9a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-9"/><path d="M10 13h4"/></svg>',
    file:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/><path d="M14 2v6h6"/></svg>',
  };

  const PASTE_FOLD_ICON =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/><path d="M14 2v6h6"/><path d="M8 12h8M8 16h6"/></svg>';

  function fileKindFromName(name, mime) {
    const n = (name || "").toLowerCase();
    const m = (mime || "").toLowerCase();
    if (m.startsWith("image/") || /\.(png|jpe?g|gif|webp|svg|bmp|ico|avif)$/i.test(n)) return "image";
    if (m.startsWith("audio/") || /\.(mp3|wav|ogg|m4a|flac|aac)$/i.test(n)) return "audio";
    if (m.startsWith("video/") || /\.(mp4|webm|mov|mkv|avi)$/i.test(n)) return "video";
    if (m === "application/pdf" || /\.pdf$/i.test(n)) return "pdf";
    if (/\.(doc|docx|odt|rtf)$/i.test(n) || m.includes("word")) return "word";
    if (/\.(xls|xlsx|ods|csv)$/i.test(n) || m.includes("sheet") || m.includes("excel")) return "sheet";
    if (/\.(ppt|pptx|odp)$/i.test(n) || m.includes("presentation")) return "slides";
    if (/\.(zip|rar|7z|tar|gz|bz2|xz)$/i.test(n) || m.includes("zip") || m.includes("compressed"))
      return "archive";
    if (
      m.startsWith("text/") ||
      /\.(txt|md|py|js|mjs|ts|tsx|jsx|json|html|css|xml|yml|yaml|sh|sql|log|ini|toml|env|rs|go|java|kt|rb|php|c|cpp|h)$/i.test(
        n
      )
    )
      return "text";
    return "file";
  }

  function fileIconHtml(kind) {
    const k = FILE_ICO_SVG[kind] ? kind : "file";
    return `<span class="file-ico file-ico--${k}" aria-hidden="true">${FILE_ICO_SVG[k]}</span>`;
  }

  function formatFileSize(bytes) {
    if (bytes == null || !Number.isFinite(bytes)) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function revokeComposerAttachment(att) {
    if (att && att.objectUrl) {
      try {
        URL.revokeObjectURL(att.objectUrl);
      } catch (e) {}
      att.objectUrl = null;
    }
  }

  /** تبدیل گفتار به متن — Chrome با continuous=true زود قطع می‌شود؛ استریم میکروفون + ری‌استارت کنترل‌شده. */
  const speechSession = {
    active: false,
    recognizer: null,
    micStream: null,
    restartTimer: null,
    watchdogTimer: null,
    generation: 0,
    lastHeardAt: 0,
    lang: "fa-IR",
  };
  let speechFinalBuffer = "";

  function getSpeechRecognitionCtor() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
  }

  function commitSpeechInputToBuffer() {
    if (!el.input) return;
    speechFinalBuffer = el.input.value || "";
    if (speechFinalBuffer && !speechFinalBuffer.endsWith(" ")) speechFinalBuffer += " ";
    setComposerInputValue(speechFinalBuffer);
  }

  function clearSpeechTimers() {
    if (speechSession.restartTimer) {
      window.clearTimeout(speechSession.restartTimer);
      speechSession.restartTimer = null;
    }
    if (speechSession.watchdogTimer) {
      window.clearInterval(speechSession.watchdogTimer);
      speechSession.watchdogTimer = null;
    }
  }

  function releaseSpeechMicStream() {
    if (!speechSession.micStream) return;
    try {
      speechSession.micStream.getTracks().forEach((t) => t.stop());
    } catch (e) {}
    speechSession.micStream = null;
  }

  function detachSpeechRecognizer() {
    const rec = speechSession.recognizer;
    speechSession.recognizer = null;
    if (!rec) return;
    rec.onstart = null;
    rec.onend = null;
    rec.onresult = null;
    rec.onerror = null;
    try {
      rec.abort();
    } catch (e) {
      try {
        rec.stop();
      } catch (e2) {}
    }
  }

  function scheduleSpeechRestart(delayMs) {
    if (!speechSession.active) return;
    if (speechSession.restartTimer) return;
    speechSession.restartTimer = window.setTimeout(() => {
      speechSession.restartTimer = null;
      if (speechSession.active) startSpeechRecognizerPass();
    }, Math.max(0, delayMs || 0));
  }

  function applySpeechResult(ev, generation) {
    if (generation !== speechSession.generation || !speechSession.active || !el.input) return;
    speechSession.lastHeardAt = Date.now();
    let interim = "";
    for (let i = ev.resultIndex; i < ev.results.length; i++) {
      const alt = ev.results[i][0];
      const piece = alt ? alt.transcript : "";
      if (!piece) continue;
      if (ev.results[i].isFinal) speechFinalBuffer += piece;
      else interim += piece;
    }
    setComposerInputValue(speechFinalBuffer + interim);
  }

  function startSpeechRecognizerPass() {
    const SpeechRecognition = getSpeechRecognitionCtor();
    if (!SpeechRecognition || !speechSession.active || !el.input || el.input.disabled) return;

    detachSpeechRecognizer();
    commitSpeechInputToBuffer();

    const generation = ++speechSession.generation;
    const rec = new SpeechRecognition();
    speechSession.recognizer = rec;

    // در Chrome پایدارتر از continuous=true برای ضبط طولانی
    rec.continuous = false;
    rec.interimResults = true;
    rec.maxAlternatives = 1;
    rec.lang = speechSession.lang;

    rec.onstart = () => {
      if (generation !== speechSession.generation) return;
      speechSession.lastHeardAt = Date.now();
    };

    rec.onresult = (ev) => applySpeechResult(ev, generation);

    rec.onerror = (ev) => {
      if (generation !== speechSession.generation) return;
      const code = ev.error || "";
      if (code === "not-allowed" || code === "service-not-allowed") {
        setStatus("دسترسی میکروفون رد شد.");
        stopSpeechToText();
        return;
      }
      commitSpeechInputToBuffer();
      scheduleSpeechRestart(code === "network" ? 800 : 120);
    };

    rec.onend = () => {
      if (generation !== speechSession.generation) return;
      speechSession.recognizer = null;
      commitSpeechInputToBuffer();
      if (speechSession.active) scheduleSpeechRestart(80);
    };

    try {
      rec.start();
    } catch (e) {
      speechSession.recognizer = null;
      scheduleSpeechRestart(450);
    }
  }

  function startSpeechWatchdog() {
    if (speechSession.watchdogTimer) return;
    speechSession.watchdogTimer = window.setInterval(() => {
      if (!speechSession.active) return;
      const hasRecognizer = !!speechSession.recognizer;
      const pendingRestart = !!speechSession.restartTimer;
      if (!hasRecognizer && !pendingRestart) {
        scheduleSpeechRestart(0);
        return;
      }
      const idleMs = Date.now() - (speechSession.lastHeardAt || 0);
      if (hasRecognizer && idleMs > 25000) {
        detachSpeechRecognizer();
        scheduleSpeechRestart(100);
      }
    }, 1500);
  }

  async function acquireSpeechMicStream() {
    if (speechSession.micStream) return true;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return true;
    try {
      speechSession.micStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
      return true;
    } catch (e) {
      setStatus("دسترسی میکروفون رد شد.");
      return false;
    }
  }

  function stopSpeechToText() {
    speechSession.active = false;
    clearSpeechTimers();
    detachSpeechRecognizer();
    releaseSpeechMicStream();
    if (el.btnComposerMic) {
      el.btnComposerMic.classList.remove("is-listening");
      el.btnComposerMic.setAttribute("aria-pressed", "false");
    }
    commitSpeechInputToBuffer();
  }

  async function toggleSpeechToText() {
    if (!getSpeechRecognitionCtor()) {
      setStatus("مرورگر شما تبدیل گفتار به متن را پشتیبانی نمی‌کند (Chrome/Edge).");
      return;
    }
    if (speechSession.active) {
      stopSpeechToText();
      return;
    }
    if (!el.input || el.input.disabled) return;

    const micOk = await acquireSpeechMicStream();
    if (!micOk) return;

    speechFinalBuffer = el.input.value || "";
    if (speechFinalBuffer && !speechFinalBuffer.endsWith(" ")) speechFinalBuffer += " ";

    speechSession.active = true;
    speechSession.lang = "fa-IR";
    speechSession.lastHeardAt = Date.now();
    speechSession.generation = 0;

    if (el.btnComposerMic) {
      el.btnComposerMic.classList.add("is-listening");
      el.btnComposerMic.setAttribute("aria-pressed", "true");
    }

    startSpeechWatchdog();
    startSpeechRecognizerPass();
  }

  function apiHeaders(extra = {}) {
    const h = { ...extra };
    const token = localStorage.getItem("aca_api_token") || "";
    if (token) h["X-ACA-Token"] = token;
    return h;
  }

  async function api(url, opts = {}) {
    const headers = apiHeaders(opts.headers || {});
    const res = await fetch(url, { ...opts, headers });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText || String(res.status));
    return data;
  }

  function agentLabel(id) {
    const a = state.agents.find((x) => x.id === id);
    return a ? a.display_name : id || "autonomous";
  }

  function applyAgentOptionDefaults(agentId) {
    const a = state.agents.find((x) => x.id === agentId);
    if (!a) return;
    el.allowShell.checked = !!a.default_allow_shell;
    el.allowWrite.checked = !!a.default_allow_write;
  }


  function setChevronButton(btn, open) {
    if (!btn) return;
    btn.innerHTML = CHEVRON_SVG;
    btn.classList.toggle("open", !!open);
    btn.classList.toggle("collapsed", !open);
  }

  function createSummaryWithChevron(text) {
    const summary = document.createElement("summary");
    const chev = document.createElement("span");
    chev.className = "summary-chevron btn-chevron collapsed";
    chev.innerHTML = CHEVRON_SVG;
    const label = document.createElement("span");
    label.className = "summary-label";
    label.textContent = text;
    summary.appendChild(chev);
    summary.appendChild(label);
    return summary;
  }

  function extractToolCardCopyText(card) {
    if (!card) return "";
    const sections = [...card.querySelectorAll(".tool-card-section")];
    if (sections.length) {
      return sections
        .map((sec) => {
          const label = sec.querySelector(".tool-card-section__label");
          const pre = sec.querySelector("pre");
          const title = label ? label.textContent.trim() : "";
          const body = pre ? pre.textContent : "";
          return title ? `${title}\n${body}` : body;
        })
        .filter(Boolean)
        .join("\n\n");
    }
    const pre = card.querySelector("pre");
    return pre ? pre.textContent : "";
  }

  function attachToolCardCopyButton(summary, card) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tool-card-copy-btn";
    btn.title = "کپی";
    btn.setAttribute("aria-label", "کپی");
    btn.innerHTML = COPY_SVG;
    btn.addEventListener("mousedown", (ev) => ev.stopPropagation());
    btn.addEventListener("click", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      const text = extractToolCardCopyText(card);
      if (!text.trim()) {
        setStatus("متنی برای کپی نیست");
        return;
      }
      copyText(text, "کپی شد");
    });
    summary.appendChild(btn);
  }

  function syncChatHeadVisibility() {
    if (!el.chatHead || !el.log) return;
    const hasChat = el.log.querySelector(".msg");
    el.chatHead.classList.toggle("is-hidden", !!hasChat);
  }

  function setAgentActivityIndicator(on) {
    if (!el.log) return;
    let row = el.log.querySelector(".agent-activity-indicator");
    if (!on) {
      row?.remove();
      return;
    }
    if (!row) {
      row = document.createElement("div");
      row.className = "agent-activity-indicator";
      row.setAttribute("aria-live", "polite");
      row.innerHTML =
        '<span class="agent-pulse-dot"></span><span class="agent-pulse-dot"></span><span class="agent-pulse-dot"></span><span>ایجنت در حال کار…</span>';
      el.log.appendChild(row);
    }
    pinAgentActivityIndicatorLast();
    el.log.scrollTop = el.log.scrollHeight;
  }

  function setComposerBusyMode(running) {
    if (!el.send) return;
    const canStop = running && el.useStream && el.useStream.checked;
    if (canStop) {
      el.send.type = "button";
      el.send.classList.add("send-btn--stop");
      el.send.setAttribute("aria-label", "توقف");
      el.send.innerHTML = STOP_BTN_SVG;
      el.send.disabled = false;
    } else {
      el.send.type = "submit";
      el.send.classList.remove("send-btn--stop");
      el.send.setAttribute("aria-label", "ارسال");
      el.send.innerHTML = SEND_BTN_SVG;
      el.send.disabled =
        running || !state.conversationId || isContextFull(el.input?.value || "");
    }
    syncContextRing(el.input?.value || "");
    syncLiveExecPanel();
  }

  function treeExpandedStorageKey() {
    const id = state.conversationId || state.projectId;
    return id ? `${LS_TREE_EXPANDED}_${id}` : null;
  }

  function loadTreeExpandedPaths() {
    const key = treeExpandedStorageKey();
    if (!key) {
      state.treeExpandedPaths = new Set();
      return;
    }
    try {
      const raw = localStorage.getItem(key);
      state.treeExpandedPaths = new Set(JSON.parse(raw || "[]"));
    } catch {
      state.treeExpandedPaths = new Set();
    }
  }

  function persistTreeExpandedPaths() {
    const key = treeExpandedStorageKey();
    if (!key) return;
    localStorage.setItem(key, JSON.stringify([...state.treeExpandedPaths]));
  }

  function syncProjectRootPathInput(path) {
    if (el.projectRootPath && path) {
      el.projectRootPath.value = path;
    }
  }

  async function respondPermission(approved) {
    const pending = state.pendingPermission;
    if (!pending || !pending.request_id) return;
    state.pendingPermission = null;
    if (el.dialogPermission?.open) el.dialogPermission.close();
    try {
      await api("/api/chat/permission/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request_id: pending.request_id,
          approved: !!approved,
        }),
      });
      if (approved) {
        if (pending.kind === "allow_write" && el.allowWrite) {
          el.allowWrite.checked = true;
        }
        if (pending.kind === "allow_shell" && el.allowShell) {
          el.allowShell.checked = true;
        }
      }
    } catch (err) {
      setStatus("خطا در ثبت اجازه: " + err.message);
    }
  }

  function hideUserInputPanel() {
    if (el.userInputPanel) el.userInputPanel.hidden = true;
    if (el.userInputPanelFields) el.userInputPanelFields.innerHTML = "";
    if (el.userInputPanelNotes) el.userInputPanelNotes.value = "";
    clearInlineUserInputForm();
  }

  function clearUserInputForConversation(conversationId) {
    if (!conversationId) return;
    delete state.userInputByConversation[conversationId];
    if (state.pendingUserInput?.conversationId === conversationId) {
      state.pendingUserInput = null;
      hideUserInputPanel();
    }
  }

  function mountUserInputPanelUi(event) {
    if (!el.userInputPanel) return;
    const fields = Array.isArray(event.fields) ? event.fields : defaultSshUserInputEvent().fields;
    event.fields = fields;
    el.userInputPanel.hidden = false;
    if (el.userInputPanelTitle) {
      el.userInputPanelTitle.textContent = event.title || "ورود اطلاعات";
    }
    if (el.userInputPanelMessage) {
      el.userInputPanelMessage.textContent =
        event.message || "ایجنت برای ادامه به اطلاعات زیر نیاز دارد.";
    }
    if (el.userInputPanelNotes) el.userInputPanelNotes.value = "";
    event._collectValues = buildUserInputFieldNodes(fields, el.userInputPanelFields);
    el.userInputPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    const focusTarget =
      el.userInputPanelFields &&
      el.userInputPanelFields.querySelector("input, textarea");
    if (focusTarget) focusTarget.focus();
  }

  function refreshUserInputPanel() {
    const cid = state.conversationId;
    if (!cid) {
      hideUserInputPanel();
      state.pendingUserInput = null;
      return;
    }
    const stored = state.userInputByConversation[cid];
    if (stored) {
      state.pendingUserInput = stored;
      mountUserInputPanelUi(stored);
      return;
    }
    hideUserInputPanel();
    state.pendingUserInput = null;
    maybeOfferUserInputFromConversation(state.conversation);
  }

  function buildUserInputFieldNodes(fields, container) {
    const valueMap = {};
    if (!container) return () => ({});
    container.innerHTML = "";
    (fields || []).forEach((f) => {
      const id = String(f.id || "").trim();
      if (!id) return;
      const label = document.createElement("label");
      label.className = "field";
      const title = document.createElement("span");
      title.textContent = f.label || id;
      label.appendChild(title);
      const ftype = String(f.type || "text").toLowerCase();
      let input;
      if (ftype === "multiline") {
        input = document.createElement("textarea");
        input.rows = 3;
      } else {
        input = document.createElement("input");
        input.type = ftype === "password" ? "password" : "text";
        if (ftype === "password") {
          input.autocomplete = "new-password";
          input.setAttribute("autocapitalize", "off");
          input.setAttribute("autocorrect", "off");
          input.spellcheck = false;
        }
      }
      input.name = id;
      input.required = !!f.required;
      if (f.placeholder) input.placeholder = f.placeholder;
      label.appendChild(input);
      container.appendChild(label);
      valueMap[id] = input;
    });
    return () => {
      const values = {};
      Object.keys(valueMap).forEach((key) => {
        const node = valueMap[key];
        values[key] = node && typeof node.value === "string" ? node.value : "";
      });
      return values;
    };
  }

  async function submitUserInput(cancelled) {
    const pending = state.pendingUserInput;
    if (!pending) return;
    if (
      pending.conversationId &&
      state.conversationId &&
      pending.conversationId !== state.conversationId
    ) {
      setStatus("این فرم مربوط به مکالمهٔ دیگری است — همان مکالمه را باز کنید.");
      return;
    }
    if (!cancelled && el.userInputPanelFields) {
      const inputs = el.userInputPanelFields.querySelectorAll("input, textarea");
      for (const inp of inputs) {
        if (!inp.checkValidity()) {
          inp.reportValidity();
          return;
        }
      }
    }
    const requestId = pending.request_id;
    const collect = pending._collectValues ? pending._collectValues() : {};
    const notes = (el.userInputPanelNotes && el.userInputPanelNotes.value.trim()) || "";
    const convId = pending.conversationId || state.conversationId;
    state.pendingUserInput = null;
    if (convId) delete state.userInputByConversation[convId];
    hideUserInputPanel();
    if (cancelled) {
      if (requestId) {
        try {
          await api("/api/chat/user-input/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ request_id: requestId, cancelled: true }),
          });
        } catch (err) {
          setStatus("خطا در ثبت انصراف: " + err.message);
        }
      }
      return;
    }
    if (!requestId) {
      if (!state.conversationId || state.busy) {
        setStatus("لطفاً صبر کنید تا اجرای قبلی تمام شود.");
        return;
      }
      const payload = { type: "ssh_connection", values: collect, notes };
      const followUp =
        "[فرم اتصال سرور — اطلاعات کاربر]\n```json\n" +
        JSON.stringify(payload, null, 2) +
        "\n```\nبا این اطلاعات به سرور وصل شو و درخواست قبلی را ادامه بده.";
      addMessage("user", "اطلاعات اتصال سرور (از فرم) ارسال شد.");
      state.busy = true;
      syncPhaseLogPanelVisibility();
      setUndoButtonsDisabled(true);
      setComposerBusyMode(true);
      el.toolTrace.innerHTML = "";
      syncLiveExecPanel();
      const convId = state.conversationId;
      try {
        await sendStream(followUp, convId);
        await refreshConversationAfterTurn();
        setStatus("ذخیره شد");
      } catch (err) {
        handleTurnFailure(err, { message: followUp, conversationId: convId, assistantEl: null });
      } finally {
        state.busy = false;
        syncPhaseLogPanelVisibility();
        setUndoButtonsDisabled(false);
        setComposerBusyMode(false);
        syncLiveExecPanel();
        loadTree();
      }
      return;
    }
    state.userInputAwaitingServer = true;
    try {
      await api("/api/chat/user-input/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request_id: requestId,
          cancelled: false,
          values: collect,
          notes,
        }),
      });
      setStatus("اطلاعات ثبت شد — ایجنت ادامه می‌دهد…");
    } catch (err) {
      setStatus("خطا در ثبت اطلاعات: " + err.message);
    } finally {
      state.userInputAwaitingServer = false;
    }
  }

  function replyPromisedUserForm(text) {
    if (!text || String(text).trim().length < 24) return false;
    const raw = String(text);
    const lower = raw.toLowerCase();
    const credHints = [
      "گذرواژه",
      "رمز",
      "password",
      "نام کاربری",
      "username",
      "آدرس ip",
      " ip ",
      "ssh",
      "سرور",
      "nginx",
      "دامنه",
    ];
    const hits = credHints.filter((h) => raw.includes(h) || lower.includes(h)).length;
    const formHints = [
      "فرم زیر",
      "در فرم",
      "لطفاً این اطلاعات",
      "لطفا این اطلاعات",
      "اطلاعات زیر",
      "وارد کنید",
      "نیاز دارم",
      "form below",
    ];
    if (formHints.some((h) => raw.includes(h) || lower.includes(h)) && hits >= 2) return true;
    if (raw.includes("1.") && raw.includes("2.") && hits >= 2) return true;
    return false;
  }

  function defaultSshUserInputEvent(message) {
    return {
      title: "اتصال به سرور",
      message:
        message ||
        "برای اتصال SSH و ادامهٔ کار، این فیلدها را پر کنید.",
      fields: [
        {
          id: "host",
          label: "آدرس IP یا نام دامنه",
          type: "text",
          required: true,
          placeholder: "مثلاً 203.0.113.10",
        },
        {
          id: "username",
          label: "نام کاربری SSH",
          type: "text",
          required: true,
          placeholder: "مثلاً root",
        },
        {
          id: "password",
          label: "گذرواژه (در صورت نیاز)",
          type: "password",
          required: false,
        },
      ],
    };
  }

  function clearInlineUserInputForm() {
    document.querySelectorAll(".chat-user-input-card").forEach((n) => n.remove());
  }

  function conversationHadAskUserTool(conv) {
    const trace = conv?.tool_trace || [];
    return trace.some((e) => e.type === "tool" && e.step && e.step.tool === "ask_user");
  }

  function maybeOfferUserInputFromConversation(conv) {
    if (!conv || state.busy) return;
    if (Number(conv.id) !== Number(state.conversationId)) return;
    if (state.userInputByConversation[conv.id]) return;
    const messages = conv.messages || [];
    const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
    if (!lastAssistant || !replyPromisedUserForm(lastAssistant.content)) return;
    if (conversationHadAskUserTool(conv)) return;
    showUserInputSurface(
      defaultSshUserInputEvent(
        "برای ادامهٔ کار روی سرور، اطلاعات اتصال را در فرم زیر وارد کنید."
      ),
      conv.id
    );
  }

  function showUserInputSurface(event, conversationId) {
    const cid = Number(conversationId || state.conversationId);
    if (!cid) return;
    const fields = Array.isArray(event.fields) ? event.fields : defaultSshUserInputEvent().fields;
    event.fields = fields;
    event.conversationId = cid;
    state.userInputByConversation[cid] = event;

    if (cid === Number(state.conversationId)) {
      state.pendingUserInput = event;
      mountUserInputPanelUi(event);
      setStatus("فرم ورود اطلاعات آماده است — فیلدها را پر کنید.");
    }
  }

  function showUserInputDialog(event) {
    showUserInputSurface(event, event.conversationId || state.conversationId);
  }

  function showPermissionDialog(event) {
    state.pendingPermission = event;
    if (!el.dialogPermission) return;
    if (el.permissionDialogTitle) {
      el.permissionDialogTitle.textContent =
        event.kind === "allow_shell" ? "اجازهٔ shell" : "اجازهٔ نوشتن فایل";
    }
    if (el.permissionDialogMessage) {
      el.permissionDialogMessage.textContent = event.message || "ایجنت نیاز به اجازه دارد.";
    }
    if (el.permissionDialogDetail) {
      const lines = [`ابزار: ${event.tool || "—"}`];
      if (event.args) lines.push(JSON.stringify(event.args, null, 2));
      el.permissionDialogDetail.textContent = lines.join("\n\n");
    }
    el.dialogPermission.showModal();
  }

  async function requestAgentStop() {
    if (!state.activeRunId || !state.conversationId) return;
    state.stopRequested = true;
    setStatus("در حال توقف…");
    if (el.dialogPermission?.open) el.dialogPermission.close();
    try {
      await api("/api/chat/cancel/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: state.conversationId,
          run_id: state.activeRunId,
        }),
      });
    } catch (err) {
      setStatus("توقف: " + err.message);
    }
  }

  function sortAgentsForUi(agents) {
    const list = [...(agents || [])];
    list.sort((a, b) =>
      (a.display_name || "").localeCompare(b.display_name || "", "fa")
    );
    return list;
  }

  function defaultChatAgentId() {
    const agents = state.agents || [];
    const coding = agents.find((a) => a.id === "coding");
    if (coding) return coding.id;
    const autonomous = agents.find((a) => a.id === "autonomous");
    if (autonomous) return autonomous.id;
    return agents[0]?.id || "coding";
  }

  function renderAgentNewButtonsInto(container, projectId) {
    if (!container) return;
    container.innerHTML = "";
    const agentId = defaultChatAgentId();
    const agent = (state.agents || []).find((a) => a.id === agentId);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-tiny btn-primary-agent primary btn-new-chat";
    btn.title = agent?.description || "شروع گفتگو با ایجنت";
    btn.textContent = "+ چت با ایجنت";
    btn.onclick = () => {
      const run = () => createConversation(agentId, { title: "مکالمه جدید" });
      if (state.projectId !== projectId) selectProject(projectId).then(run);
      else run();
    };
    container.appendChild(btn);
  }

  function renderAgentNewButtons() {
    renderProjectList();
  }

  function isProjectExpanded(projectId) {
    return state.expandedProjects.has(Number(projectId));
  }

  function toggleProjectExpanded(projectId) {
    const id = Number(projectId);
    if (state.expandedProjects.has(id)) state.expandedProjects.delete(id);
    else {
      state.expandedProjects.add(id);
      if (!state.conversationsByProject[id]) {
        loadConversationsForProject(id).catch((e) => setStatus(e.message));
      }
    }
    renderProjectList();
  }

  function buildConversationLi(c) {
    const li = document.createElement("li");
    li.dataset.id = String(c.id);
    li.classList.toggle("active", c.id === state.conversationId);
    const badgeCls = AGENT_BADGE_CLASS[c.agent_type] || "";
    const agentName = agentLabel(c.agent_type);
    let dateStr = "";
    try {
      dateStr = new Date(c.updated_at).toLocaleString("fa-IR");
    } catch {
      dateStr = c.updated_at || "";
    }
    const topic = c.topic_summary || c.title || "مکالمه";
    const credits =
      c.total_credits_used && parseFloat(c.total_credits_used) > 0
        ? `${formatCredits2(c.total_credits_used)} اعتبار`
        : "—";
    const msgCount = c.message_count || 0;
    li.innerHTML = `<div class="list-row"><div class="list-body"><div class="conv-topic-row"><div class="conv-topic" title="${escapeHtml(topic)}">${escapeHtml(topic)}</div><button type="button" class="btn-conv-info" title="اطلاعات بیشتر" aria-label="اطلاعات">${INFO_SVG}</button></div><div class="conv-meta"></div><div class="conv-details"><div class="conv-details-inner"><div class="conv-date">${escapeHtml(dateStr)}</div><div>${msgCount} پیام · ${credits}</div></div></div></div><button type="button" class="btn-icon" data-delete-conversation="${c.id}" title="حذف">×</button></div>`;
    return li;
  }

  async function loadAgents() {
    try {
      const data = await api("/api/agents/");
      if (data.agents && data.agents.length) {
        state.agents = sortAgentsForUi(data.agents);
      }
    } catch (e) {
      console.warn("agents API:", e);
      state.agents = sortAgentsForUi(FALLBACK_AGENTS);
    }
    renderAgentNewButtons();
  }

  function renderProjectList() {
    if (!el.projectList) return;
    el.projectList.innerHTML = "";
    if (!state.projects.length) {
      el.projectList.innerHTML = '<p class="list-empty muted">+ پروژه</p>';
      return;
    }
    state.projects.forEach((p) => {
      const block = document.createElement("div");
      block.className = "project-block";
      if (p.id === state.projectId) block.classList.add("active-project");
      block.dataset.projectId = String(p.id);

      const head = document.createElement("div");
      head.className = "project-block-head";

      const chevron = document.createElement("button");
      chevron.type = "button";
      chevron.className = "btn-chevron";
      setChevronButton(chevron, isProjectExpanded(p.id));
      chevron.onclick = (ev) => {
        ev.stopPropagation();
        toggleProjectExpanded(p.id);
      };

      const titleBtn = document.createElement("button");
      titleBtn.type = "button";
      titleBtn.className = "project-title-btn";
      const remoteTag =
        p.remote_server && p.remote_server.enabled
          ? '<span class="item-meta-tag" title="اجرای ایجنت روی SSH">SSH</span>'
          : "";
      const stage = p.growth_hub && p.growth_hub.lifecycle_stage;
      const stageTag =
        stage && stage !== "build"
          ? `<span class="item-meta-tag" title="مرحلهٔ عمر محصول">${escapeHtml(stage)}</span>`
          : "";
      titleBtn.innerHTML = `<span class="item-title">${escapeHtml(p.name)}</span><span class="item-meta muted">${remoteTag}${stageTag}</span>`;
      titleBtn.onclick = () => selectProject(p.id);

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "btn-icon";
      delBtn.dataset.deleteProject = String(p.id);
      delBtn.title = "حذف";
      delBtn.textContent = "×";

      head.appendChild(chevron);
      head.appendChild(titleBtn);
      head.appendChild(delBtn);

      const body = document.createElement("div");
      body.className = "project-block-body";
      if (!isProjectExpanded(p.id)) body.classList.add("collapsed");

      if (isProjectExpanded(p.id)) {
        const agentRow = document.createElement("div");
        agentRow.className = "agent-new-row";
        renderAgentNewButtonsInto(agentRow, p.id);
        body.appendChild(agentRow);

        const ul = document.createElement("ul");
        ul.className = "list list-conversations-nested";
        const convs = state.conversationsByProject[p.id];
        if (convs === undefined) {
          ul.innerHTML = '<li class="list-empty muted">…</li>';
        } else if (!convs.length) {
          ul.innerHTML = '<li class="list-empty muted">—</li>';
        } else {
          convs.forEach((c) => ul.appendChild(buildConversationLi(c)));
        }
        body.appendChild(ul);
      }

      block.appendChild(head);
      block.appendChild(body);
      el.projectList.appendChild(block);
    });
    if (el.btnDeleteProject) {
      el.btnDeleteProject.disabled = !state.projectId;
    }
  }

  function renderConversationList() {
    renderProjectList();
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  async function fetchProjects() {
    const data = await api("/api/projects/");
    state.projects = data.projects || [];
    renderProjectList();
  }

  function setDeleteConversationButtonDisabled(disabled) {
    if (el.btnDeleteConversation) el.btnDeleteConversation.disabled = disabled;
  }

  function conversationMessageCount(conversationId) {
    const id = Number(conversationId);
    if (!id) return null;
    if (state.conversation && state.conversation.id === id) {
      if (state.conversation.message_count != null) {
        return Number(state.conversation.message_count) || 0;
      }
      if (Array.isArray(state.conversation.messages)) {
        return state.conversation.messages.length;
      }
    }
    const pid = state.projectId;
    const lists = [
      ...(pid ? state.conversationsByProject[pid] || [] : []),
      ...(state.conversations || []),
    ];
    const row = lists.find((c) => c.id === id);
    if (row && row.message_count != null) return Number(row.message_count) || 0;
    return null;
  }

  function conversationHasNoMessages(conversationId) {
    const count = conversationMessageCount(conversationId);
    return count === 0;
  }

  async function deleteConversationSilent(conversationId) {
    await api(`/api/conversations/${conversationId}/delete/`, { method: "DELETE" });
    if (state.conversationId === Number(conversationId)) {
      state.conversationId = null;
      state.conversation = null;
      localStorage.removeItem(LS_CONV);
      el.log.innerHTML = "";
      clearPhaseLogPanel();
      setComposerInputValue("");
      el.input.disabled = true;
      el.send.disabled = true;
      setComposerEntryEnabled(false);
      setDeleteConversationButtonDisabled(true);
      el.chatTitle.textContent = "مکالمه‌ای انتخاب نشده";
      updateComposerAgentBadge(null);
      updateComposerOptionsEnabled(false);
    }
    if (state.projectId) await loadConversationsForProject(state.projectId);
  }

  async function maybeDiscardEmptyConversationOnLeave(leavingId) {
    const id = Number(leavingId ?? state.conversationId);
    if (!id || id !== state.conversationId) return;
    if (!conversationHasNoMessages(id)) {
      if (state.sessionCreatedConvId === id) state.sessionCreatedConvId = null;
      return;
    }
    try {
      await deleteConversationSilent(id);
    } catch (e) {
      console.warn("discard empty conv:", e);
    }
    if (state.sessionCreatedConvId === id) state.sessionCreatedConvId = null;
  }

  async function createConversation(agentType, opts = {}) {
    if (!state.projectId) return;
    try {
      await maybeDiscardEmptyConversationOnLeave();
      state.expandedProjects.add(state.projectId);
      const title =
        opts.title || `مکالمه ${agentLabel(agentType)}`;
      const data = await api(`/api/projects/${state.projectId}/conversations/create/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scope_paths: state.scopePaths,
          agent_type: agentType,
          title,
        }),
      });
      state.sessionCreatedConvId = data.conversation.id;
      state.convInputDirty = false;
      state.convMessageSent = false;
      await loadConversationsForProject(state.projectId);
      await selectConversation(data.conversation.id, { skipDiscard: true });
    } catch (e) {
      setStatus("خطا در ایجاد مکالمه: " + e.message);
    }
  }

  function optionsPayload() {
    const rounds = parseInt(el.maxRounds.value, 10);
    const payload = {
      allow_shell: el.allowShell.checked,
      allow_write: el.allowWrite.checked,
      max_tool_rounds: Number.isFinite(rounds) ? rounds : undefined,
      enable_thinking: el.enableThinking && el.enableThinking.checked,
      thinking_depth: el.thinkingDeep && el.thinkingDeep.checked ? "deep" : "standard",
      scope_paths: [...state.scopePaths],
    };
    if (el.llmModel && el.llmModel.value) {
      payload.model = el.llmModel.value;
    }
    return payload;
  }

  let scopePersistTimer = null;

  async function persistScopeToServer() {
    if (!state.conversationId) return;
    try {
      await api(`/api/conversations/${state.conversationId}/update/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scope_paths: state.scopePaths,
        }),
      });
      if (state.conversation) {
        state.conversation.scope_paths = [...state.scopePaths];
      }
      loadTree();
    } catch (e) {
      setStatus(e.message);
    }
  }

  function schedulePersistScope(delayMs = 300) {
    if (scopePersistTimer) clearTimeout(scopePersistTimer);
    scopePersistTimer = setTimeout(() => {
      scopePersistTimer = null;
      persistScopeToServer();
    }, delayMs);
  }

  function renderScopeChips() {
    if (!el.scopeChips) return;
    el.scopeChips.innerHTML = "";
    const hasScope = state.scopePaths.length > 0;
    if (el.focusScopeCard) el.focusScopeCard.hidden = !hasScope;
    if (!hasScope) return;
    state.scopePaths.forEach((p) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.innerHTML = `${p} <button type="button" title="حذف">×</button>`;
      chip.querySelector("button").onclick = () => {
        state.scopePaths = state.scopePaths.filter((x) => x !== p);
        renderScopeChips();
        renderTreeHighlight();
        schedulePersistScope(0);
      };
      el.scopeChips.appendChild(chip);
    });
  }

  function addScopePath(path) {
    if (!path || path === ".") return;
    if (!state.scopePaths.includes(path)) {
      state.scopePaths.push(path);
      state.scopePaths.sort();
      renderScopeChips();
      renderTreeHighlight();
    }
  }

  function toggleScopePath(path, enabled) {
    if (!path || path === ".") return;
    if (enabled) addScopePath(path);
    else {
      state.scopePaths = state.scopePaths.filter((x) => x !== path);
      renderScopeChips();
      syncTreeFocusUi();
    }
    schedulePersistScope(0);
  }

  function syncTreeFocusUi() {
    document.querySelectorAll(".tree-item[data-path]").forEach((node) => {
      const p = node.dataset.path;
      node.classList.toggle("in-focus", state.scopePaths.includes(p));
      const cb = node.querySelector('input[type="checkbox"].tree-focus-cb');
      if (cb) cb.checked = state.scopePaths.includes(p);
    });
  }

  function renderTreeHighlight() {
    syncTreeFocusUi();
  }

  function fillMessageBody(body, role, text) {
    body.innerHTML = "";
    const content = text != null ? String(text) : "";
    if (role === "assistant" && acaRender().renderMarkdown) {
      body.appendChild(acaRender().renderMarkdown(content));
    } else {
      body.textContent = content;
    }
  }

  function ensureMessageShell(div, text, role) {
    const msgRole = role || (div.classList.contains("user") ? "user" : "assistant");
    let body = div.querySelector(".msg-body");
    if (!body) {
      const plain = (div.textContent || "").trim();
      div.textContent = "";
      body = document.createElement("div");
      body.className = "msg-body";
      fillMessageBody(body, msgRole, text != null ? text : plain);
      div.appendChild(body);
      let actions = div.querySelector(".msg-actions");
      if (!actions) {
        actions = document.createElement("div");
        actions.className = "msg-actions";
        div.appendChild(actions);
      }
    } else if (text != null) {
      fillMessageBody(body, msgRole, text);
    }
    if (!div.querySelector(".msg-actions")) {
      const actions = document.createElement("div");
      actions.className = "msg-actions";
      div.appendChild(actions);
    }
    return body;
  }

  function addMessage(role, text, meta) {
    const div = document.createElement("div");
    div.className = "msg " + role;
    if (meta && meta.id) div.dataset.messageId = String(meta.id);
    ensureMessageShell(div, text, role);
    if (meta) applyMessageActions(div, meta);
    el.log.appendChild(div);
    pinAgentActivityIndicatorLast();
    el.log.scrollTop = el.log.scrollHeight;
    syncChatHeadVisibility();
    return div;
  }

  function setMessageText(div, text) {
    const role = div.classList.contains("user") ? "user" : "assistant";
    ensureMessageShell(div, text, role);
  }

  function createCreditsChatNode(payload) {
    const div = document.createElement("div");
    div.className = "msg credits-log";
    const total = payload && (payload.total_credits || payload.total);
    div.textContent = total
      ? `اعتبار این نوبت: ${formatCredits2(total)}`
      : "اعتبار مصرف شد";
    return div;
  }

  function renderTimeline(timeline, messages) {
    if (!el.log) return;
    el.log.innerHTML = "";
    state.streamingAssistantEl = null;
    const metaById = {};
    (messages || []).forEach((m) => {
      metaById[m.id] = m;
    });
    let pendingPhaseEvents = [];
    (timeline || []).forEach((item) => {
      if (item.type === "phase_log" || item.type === "thinking") {
        pendingPhaseEvents.push({
          payload: item.payload,
          label: item.payload?.label || (item.type === "thinking" ? "فاز thinking" : undefined),
          phase: item.payload?.phase || (item.type === "thinking" ? "thinking" : undefined),
          detail:
            item.payload?.detail ||
            (item.type === "thinking" ? "تحلیل انجام شد" : undefined),
        });
        return;
      }
      if (item.type === "message") {
        const meta = metaById[item.id] || item;
        const role = meta.role || item.role;
        const div = addMessage(role, item.content, meta);
        if (role === "assistant" && pendingPhaseEvents.length) {
          const bundle = ensureAssistantPhaseLogBundle(div);
          renderPhaseBundleFromEvents(bundle, pendingPhaseEvents);
          pendingPhaseEvents = [];
        }
        return;
      }
      if (item.type === "credits") {
        el.log.appendChild(createCreditsChatNode(item.payload || {}));
        pinAgentActivityIndicatorLast();
      }
    });
    el.log.scrollTop = el.log.scrollHeight;
    syncChatHeadVisibility();
  }

  function renderConversationView(conv) {
    state.streamingAssistantEl = null;
    if (!conv) {
      el.log.innerHTML = "";
      syncChatHeadVisibility();
      return;
    }
    if (conv.timeline && conv.timeline.length) {
      renderTimeline(conv.timeline, conv.messages || []);
    } else {
      renderMessages(conv.messages || []);
    }
    renderToolTraceSnapshot(conv.tool_trace || []);
    refreshUserInputPanel();
    syncContextRing(el.input?.value || "");
  }

  function applyMessageActions(div, meta) {
    if (!div || !meta) return;
    const role =
      meta.role ||
      (div.classList.contains("user") ? "user" : "assistant");
    if (role !== "assistant") return;
    ensureMessageShell(div);
    const actions = div.querySelector(".msg-actions");
    if (!actions) return;
    actions.innerHTML = "";
    const changesId = meta.changes_for_message_id || (meta.has_code_changes ? meta.id : null);
    if (meta.has_code_changes && changesId) {
      const btnChanges = document.createElement("button");
      btnChanges.type = "button";
      btnChanges.className = "btn btn-tiny btn-code-changes";
      btnChanges.textContent = "تغییرات کد";
      btnChanges.title = "نمایش تغییرات فایل در این نوبت";
      btnChanges.disabled = state.busy;
      btnChanges.onclick = () => openMessageCodeChanges(Number(changesId));
      actions.appendChild(btnChanges);
    }
  }


  function attachRetryButton(div, message, conversationId) {
    if (!div || !message) return;
    ensureMessageShell(div);
    const actions = div.querySelector(".msg-actions");
    if (!actions || actions.querySelector(".btn-retry")) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-tiny btn-retry";
    btn.textContent = "تلاش مجدد";
    btn.title = "ارسال دوبارهٔ همان پیام";
    btn.disabled = state.busy;
    btn.onclick = () => retryFailedChatTurn(message, conversationId, div);
    actions.appendChild(btn);
  }

  function handleTurnFailure(err, { message, conversationId, assistantEl }) {
    const shell =
      assistantEl ||
      state.streamingAssistantEl ||
      (el.log && el.log.querySelector(".msg.assistant:last-child"));
    const msg = err && err.message ? err.message : String(err || "خطا");
    if (shell && shell.isConnected) {
      const body = shell.querySelector(".msg-body");
      const existing = body && body.textContent && body.textContent.trim();
      if (!existing || shell.classList.contains("assistant-in-progress")) {
        setMessageText(shell, "خطا: " + msg);
      }
      shell.classList.remove("assistant-in-progress");
      attachRetryButton(shell, message, conversationId);
      state.streamingAssistantEl = null;
    } else {
      const div = addMessage("assistant", "خطا: " + msg);
      attachRetryButton(div, message, conversationId);
    }
    setStatus(msg);
  }

  async function refreshConversationAfterTurn() {
    if (!state.conversationId) return;
    const refreshed = await api(`/api/conversations/${state.conversationId}/`);
    state.conversation = refreshed.conversation;
    el.chatTitle.textContent = state.conversation.title;
    renderConversationView(state.conversation);
    if (state.sidePanelMode === "changes") {
      loadConversationCodeChanges().catch(() => {});
    }
    if (state.projectId) {
      await loadJobsForProject(state.projectId);
      await loadJobRunsForProject(state.projectId);
    }
    await loadConversationTools();
  }

  async function retryFailedChatTurn(message, conversationId, failedEl) {
    const convId = Number(conversationId || state.conversationId);
    if (!convId || !message || state.busy) return;
    if (Number(state.conversationId) !== convId) {
      setStatus("این تلاش مجدد مربوط به مکالمهٔ دیگری است.");
      return;
    }
    if (isContextFull()) {
      setStatus("کانتکست پر است — مکالمهٔ جدید بسازید.");
      return;
    }
    failedEl?.remove();
    state.busy = true;
    syncPhaseLogPanelVisibility();
    setUndoButtonsDisabled(true);
    setComposerBusyMode(true);
    el.toolTrace.innerHTML = "";
    syncLiveExecPanel();
    try {
      await sendStream(message, convId);
      await refreshConversationAfterTurn();
      setStatus("ذخیره شد");
    } catch (err) {
      handleTurnFailure(err, { message, conversationId: convId, assistantEl: null });
    } finally {
      state.busy = false;
      syncPhaseLogPanelVisibility();
      state.stopRequested = false;
      state.activeRunId = null;
      setAgentActivityIndicator(false);
      setUndoButtonsDisabled(false);
      setComposerBusyMode(false);
      if (el.dialogPermission?.open) el.dialogPermission.close();
      refreshUserInputPanel();
      syncLiveExecPanel();
      loadTree();
    }
  }

  function attachCodeChangesButton(div, messageId) {
    if (!div || !messageId) return;
    div.dataset.messageId = String(messageId);
    api(`/api/messages/${messageId}/code-changes/`)
      .then((data) => {
        if (data.summary && data.summary.files_changed) {
          applyMessageActions(div, {
            role: "assistant",
            id: messageId,
            has_code_changes: true,
            changes_for_message_id: messageId,
          });
        }
      })
      .catch(() => {});
  }

  function setUndoButtonsDisabled(disabled) {
    document
      .querySelectorAll(".btn-undo, .btn-code-changes, .cc-file-restore")
      .forEach((btn) => {
        btn.disabled = disabled;
      });
  }

  function buildFileRestoreConfirmMessage(filePath, preview) {
    let msg =
      `فایل «${filePath}» به محتوای قبل از این تغییر برمی‌گردد.\n` +
      "مکالمه و پیام‌ها حفظ می‌شوند.";
    if (preview && preview.legacy_full_backup) {
      return "بازگردانی تک‌فایلی برای این نوبت پشتیبانی نمی‌شود.";
    }
    if (preview && (preview.modified_after_turn || preview.later_turns_touching)) {
      const extra =
        preview.later_turns_touching > 0
          ? ` (${preview.later_turns_touching} نوبت بعدی هم این فایل را تغییر داده‌اند)`
          : "";
      msg +=
        "\n\nاین فایل بعد از این نوبت دوباره تغییر کرده است" +
        extra +
        ".\nبا تأیید، فقط به نسخهٔ قبل از این تغییر برمی‌گردد.";
    }
    return msg;
  }

  async function restoreTurnFile(messageId, filePath) {
    if (!messageId || !filePath || state.busy) {
      if (state.busy) setStatus("صبر کنید تا پاسخ فعلی تمام شود");
      return;
    }
    const pathQuery = encodeURIComponent(filePath);
    let preview = null;
    try {
      preview = await api(
        `/api/messages/${messageId}/restore-file-preview/?path=${pathQuery}`
      );
    } catch (err) {
      setStatus("امکان بازگردانی نیست: " + err.message);
      return;
    }
    if (preview && preview.legacy_full_backup) {
      setStatus(buildFileRestoreConfirmMessage(filePath, preview));
      return;
    }
    if (!window.confirm(buildFileRestoreConfirmMessage(filePath, preview))) return;
    state.busy = true;
    syncPhaseLogPanelVisibility();
    setUndoButtonsDisabled(true);
    el.send.disabled = true;
    setStatus("در حال بازگردانی فایل…");
    try {
      await api(`/api/messages/${messageId}/restore-file/`, {
        method: "POST",
        body: JSON.stringify({ path: filePath, confirm: true }),
      });
      if (state.sidePanelMode === "changes") {
        await loadConversationCodeChanges();
      }
      clearFilePreview();
      await loadTree();
      setStatus(`فایل «${filePath}» بازگردانی شد`);
    } catch (err) {
      setStatus("بازگردانی ناموفق بود: " + err.message);
    } finally {
      state.busy = false;
      syncPhaseLogPanelVisibility();
      setUndoButtonsDisabled(false);
      if (state.conversationId) el.send.disabled = false;
    }
  }

  function renderMessages(messages) {
    el.log.innerHTML = "";
    (messages || []).forEach((m) => addMessage(m.role, m.content, m));
    syncChatHeadVisibility();
  }

  function addThinkingBlock(text) {
    const details = document.createElement("details");
    details.className = "tool-card tool-card--ltr thinking-card";
    details.open = false;
    const summary = createSummaryWithChevron("فاز thinking (تحلیل قبل از ابزار)");
    attachToolCardCopyButton(summary, details);
    details.appendChild(summary);
    const pre = document.createElement("pre");
    pre.textContent = text;
    details.appendChild(pre);
    el.toolTrace.prepend(details);
    syncLiveExecPanel();
  }

  function liveExecTraceCount() {
    if (!el.toolTrace) return 0;
    return el.toolTrace.querySelectorAll(".tool-card, .thinking-card").length;
  }

  function syncLiveExecPanel() {
    const hasTrace = liveExecTraceCount() > 0;
    const hasLiveExec = hasTrace || !!state.busy;
    const open = hasLiveExec && !state.liveExecDismissed;
    if (el.btnToggleLiveExec) {
      el.btnToggleLiveExec.disabled = !hasLiveExec;
      el.btnToggleLiveExec.classList.toggle("is-active", open);
      el.btnToggleLiveExec.classList.toggle("is-busy", hasLiveExec && !!state.busy && !open);
    }
    if (el.liveExec) {
      if (!hasLiveExec) {
        el.liveExec.hidden = true;
        el.liveExec.classList.remove("is-open");
      } else {
        el.liveExec.hidden = false;
        el.liveExec.classList.toggle("is-open", open);
      }
    }
    el.chatPanel?.classList.remove("is-live-exec-maxed");
  }

  function openLiveExecPanel() {
    state.liveExecDismissed = false;
    syncLiveExecPanel();
  }

  function dismissLiveExecPanel() {
    state.liveExecDismissed = true;
    syncLiveExecPanel();
  }

  function updateToolsPanelEnabled(enabled) {
    const on = !!enabled;
    if (el.toolLinkInput) el.toolLinkInput.disabled = !on;
    if (el.btnAttachTool) el.btnAttachTool.disabled = !on;
  }

  async function copyText(text, statusMessage = "لینک کپی شد") {
    try {
      await navigator.clipboard.writeText(text);
      setStatus(statusMessage);
      return true;
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        setStatus(statusMessage);
        return true;
      } catch {
        setStatus("کپی ناموفق — متن را دستی بردارید");
        return false;
      } finally {
        ta.remove();
      }
    }
  }

  function buildToolTraceExportText() {
    if (!el.toolTrace) return "";
    const cards = [...el.toolTrace.querySelectorAll(".tool-card")];
    if (!cards.length) return "";
    const blocks = [...cards].reverse().map((card, index) => {
      const summary = card.querySelector("summary");
      const pre = card.querySelector("pre");
      const title = (summary && summary.textContent.trim()) || `ورودی ${index + 1}`;
      const body = (pre && pre.textContent) || "";
      return `=== ${title} ===\n${body}`;
    });
    return blocks.join("\n\n");
  }

  async function copyToolTraceOutputs() {
    const text = buildToolTraceExportText();
    if (!text.trim()) {
      setStatus("خروجی برای کپی نیست — ابتدا agent را اجرا کنید");
      return;
    }
    await copyText(text, "خروجی‌های اجرای زنده کپی شد");
  }

  function resourceKindLabel(kind) {
    return RESOURCE_KIND_LABELS[kind] || kind || "—";
  }

  function buildVersionSelect(selectEl, versions, activePublicId) {
    if (!selectEl) return;
    selectEl.innerHTML = "";
    const latestOpt = document.createElement("option");
    latestOpt.value = "";
    latestOpt.textContent = "آخرین ورژن (پیش‌فرض)";
    selectEl.appendChild(latestOpt);
    (versions || []).forEach((v) => {
      const opt = document.createElement("option");
      opt.value = v.public_id;
      opt.textContent = `v${v.version_number} · ${resourceKindLabel(v.content_kind)}`;
      if (v.public_id === activePublicId) opt.selected = true;
      selectEl.appendChild(opt);
    });
    if (!activePublicId) latestOpt.selected = true;
  }

  async function loadResourceDetail(publicId) {
    const data = await api(`/api/shared-tools/${encodeURIComponent(publicId)}/`);
    state.resourceModal.tool = data.tool;
    state.resourceModal.versions = data.versions || data.tool?.versions_brief || [];
    state.resourceModal.viewingPublicId = data.tool?.public_id || publicId;
    fillResourceModal(data.tool, state.resourceModal.versions);
    if (el.dialogResourceDetail && !el.dialogResourceDetail.open) {
      el.dialogResourceDetail.showModal();
    }
  }

  function fillResourceModal(tool, versions) {
    if (!tool) return;
    if (el.resourceDetailTitle) el.resourceDetailTitle.textContent = tool.display_name || tool.tool_id;
    if (el.resourceDetailSlug) {
      el.resourceDetailSlug.textContent = `${tool.tool_id} · ${tool.version_count || 1} ورژن`;
    }
    renderResourceTagChips(el.resourceDetailTags, tool.tags, null);
    buildVersionSelect(el.resourceDetailVersion, versions, tool.public_id);
    if (el.resourceDetailKind) {
      el.resourceDetailKind.textContent = `نوع: ${resourceKindLabel(tool.content_kind)} · ورژن ${tool.version_number}`;
    }
    if (el.resourceDetailDescription) {
      el.resourceDetailDescription.textContent = (tool.description || "—").trim();
    }
    const preview = formatResourceBlocksPreview(tool.content_blocks);
    if (el.resourceDetailBlocksWrap && el.resourceDetailBlocks) {
      if (preview) {
        el.resourceDetailBlocksWrap.hidden = false;
        el.resourceDetailBlocks.textContent = preview;
      } else {
        el.resourceDetailBlocksWrap.hidden = true;
        el.resourceDetailBlocks.textContent = "";
      }
    }
    state.resourceModal.shareLink = tool.share_link || "";
  }

  async function onResourceVersionSelectChange() {
    const pid = el.resourceDetailVersion?.value;
    if (!pid) {
      const latest = (state.resourceModal.versions || [])[0];
      if (latest) await loadResourceDetail(latest.public_id);
      return;
    }
    await loadResourceDetail(pid);
  }

  async function pinConversationResourceVersion(toolId, versionPublicId) {
    if (!state.conversationId) return;
    await api(
      `/api/conversations/${state.conversationId}/tools/by-id/${encodeURIComponent(toolId)}/version/`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ public_id: versionPublicId || null }),
      }
    );
    await loadConversationTools();
    setStatus(versionPublicId ? "ورژن پین‌شده برای این مکالمه تنظیم شد" : "از آخرین ورژن استفاده می‌شود");
  }

  function resourceTagLabel(tagId, catalog) {
    const cat = catalog || {};
    const entry = cat[tagId];
    if (entry && entry.label) return entry.label;
    const fallbacks = {
      time: "زمان",
      connection: "اتصال",
      workflow: "گردش‌کار",
      ai: "هوش مصنوعی",
      debug: "دیباگ",
      ops: "عملیات",
      knowledge: "دانش",
    };
    return fallbacks[tagId] || tagId;
  }

  function renderResourceTagChips(container, tags, catalog) {
    if (!container) return;
    container.innerHTML = "";
    (tags || []).forEach((tag) => {
      const chip = document.createElement("span");
      chip.className = `resource-tag-chip resource-tag-chip--${tag}`;
      chip.textContent = resourceTagLabel(tag, catalog);
      container.appendChild(chip);
    });
  }

  function formatResourceBlocksPreview(blocks) {
    const lines = [];
    (blocks || []).forEach((b) => {
      if (!b || typeof b !== "object") return;
      if (b.type === "text" || b.type === "prompt") lines.push(String(b.text || "").trim());
      else if (b.type === "link") lines.push(`${b.label || "لینک"}: ${b.url || ""}`);
      else if (b.url) lines.push(`${b.type}: ${b.url}`);
    });
    return lines.filter(Boolean).join("\n\n");
  }

  function renderToolCards(container, tools, { mode }) {
    if (!container) return;
    container.innerHTML = "";
    if (!tools || !tools.length) {
      const empty = document.createElement("p");
      empty.className = "muted tools-empty";
      empty.textContent =
        "هنوز منبعی به این مکالمه وصل نشده — با لینک اضافه کنید یا از ایجنت بسازید.";
      container.appendChild(empty);
      return;
    }
    tools.forEach((t) => {
      if (!t?.tool_id) return;
      if (!t.public_id && !t.latest_public_id) {
        return;
      }
      const cardPublicId = t.public_id || t.latest_public_id;
      const card = document.createElement("article");
      card.className = "tool-lib-card";
      card.dataset.publicId = cardPublicId;
      card.dataset.toolId = t.tool_id;
      const head = document.createElement("div");
      head.className = "tool-lib-head";
      const title = document.createElement("div");
      title.className = "tool-lib-title";
      title.textContent = t.display_name || t.tool_id;
      const badge = document.createElement("span");
      badge.className = "resource-kind-badge";
      badge.textContent = resourceKindLabel(t.content_kind);
      head.appendChild(title);
      head.appendChild(badge);
      const tagRow = document.createElement("div");
      tagRow.className = "tool-lib-tags";
      renderResourceTagChips(tagRow, t.tags, null);
      const meta = document.createElement("div");
      meta.className = "tool-lib-meta";
      const verLabel =
        t.version_count > 1
          ? `v${t.version_number} از ${t.version_count}`
          : `v${t.version_number || 1}`;
      meta.textContent = `${t.tool_id} · ${verLabel}`;
      const desc = document.createElement("p");
      desc.className = "tool-lib-desc";
      desc.textContent = (t.description || "بدون توضیح").slice(0, 220);
      const actions = document.createElement("div");
      actions.className = "tool-lib-actions";
      const btnInfo = document.createElement("button");
      btnInfo.type = "button";
      btnInfo.className = "btn btn-tiny";
      btnInfo.textContent = "مشاهده";
      btnInfo.onclick = () => loadResourceDetail(cardPublicId).catch((e) => setStatus(e.message));
      actions.appendChild(btnInfo);
      const btnCopy = document.createElement("button");
      btnCopy.type = "button";
      btnCopy.className = "btn btn-tiny";
      btnCopy.textContent = "کپی لینک";
      btnCopy.title = t.share_link || "";
      btnCopy.onclick = () => copyText(t.share_link || "");
      actions.appendChild(btnCopy);
      if (mode === "conversation") {
        card.appendChild(head);
        if (tagRow.childNodes.length) card.appendChild(tagRow);
        card.appendChild(meta);
        card.appendChild(desc);
        const pinRow = document.createElement("label");
        pinRow.className = "resource-pin-row";
        pinRow.title = "ورژنی که ایجنت باید استفاده کند";
        const pinLabel = document.createElement("span");
        pinLabel.textContent = "ورژن:";
        const pinSelect = document.createElement("select");
        pinSelect.className = "resource-pin-select";
        buildVersionSelect(pinSelect, t.versions_brief || [], t.pinned_public_id || "");
        pinSelect.onchange = () =>
          pinConversationResourceVersion(t.tool_id, pinSelect.value || null).catch((e) =>
            setStatus(e.message)
          );
        pinRow.appendChild(pinLabel);
        pinRow.appendChild(pinSelect);
        card.appendChild(pinRow);
        const btnRemove = document.createElement("button");
        btnRemove.type = "button";
        btnRemove.className = "btn btn-tiny btn-danger-soft";
        btnRemove.textContent = "حذف";
        btnRemove.onclick = () =>
          detachConversationTool(cardPublicId).catch((e) => setStatus(e.message));
        actions.appendChild(btnRemove);
      }
      card.appendChild(actions);
      container.appendChild(card);
    });
  }

  async function loadConversationTools() {
    if (!state.conversationId) {
      renderToolCards(el.conversationToolsList, [], { mode: "conversation" });
      if (el.conversationToolsCount) el.conversationToolsCount.textContent = "0";
      updateToolsPanelEnabled(false);
      return;
    }
    updateToolsPanelEnabled(true);
    const data = await api(`/api/conversations/${state.conversationId}/tools/`);
    const tools = data.tools || [];
    renderToolCards(el.conversationToolsList, tools, { mode: "conversation" });
    if (el.conversationToolsCount) {
      el.conversationToolsCount.textContent = String(tools.length);
    }
  }

  const RESOURCE_MUTATING_TOOLS = new Set([
    "upsert_knowledge_resource",
    "create_project_tool",
  ]);

  async function refreshResourcePanelsQuiet() {
    if (!state.conversationId) return;
    try {
      await loadConversationTools();
    } catch (_) {
      /* ignore refresh errors during stream */
    }
  }

  async function attachConversationTool(ref) {
    if (!state.conversationId) {
      setStatus("ابتدا یک مکالمه انتخاب کنید");
      return;
    }
    const rawRef =
      typeof ref === "string" && ref.trim()
        ? ref.trim()
        : (el.toolLinkInput && el.toolLinkInput.value.trim()) || "";
    if (!rawRef) {
      setStatus("لینک یا شناسهٔ ابزار را وارد کنید");
      return;
    }
    const payload = { ref: rawRef };
    const data = await api(`/api/conversations/${state.conversationId}/tools/attach/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (el.toolLinkInput) el.toolLinkInput.value = "";
    renderToolCards(el.conversationToolsList, data.tools || [], { mode: "conversation" });
    if (el.conversationToolsCount) {
      el.conversationToolsCount.textContent = String((data.tools || []).length);
    }
    setStatus(`منبع «${data.tool?.display_name || data.tool?.tool_id || ""}» اضافه شد`);
  }

  async function detachConversationTool(publicId) {
    if (!state.conversationId) return;
    const data = await api(
      `/api/conversations/${state.conversationId}/tools/${encodeURIComponent(publicId)}/`,
      { method: "DELETE" }
    );
    renderToolCards(el.conversationToolsList, data.tools || [], { mode: "conversation" });
    if (el.conversationToolsCount) {
      el.conversationToolsCount.textContent = String((data.tools || []).length);
    }
    setStatus("منبع از این مکالمه حذف شد");
  }

  function renderToolTraceSnapshot(trace) {
    if (!el.toolTrace) return;
    el.toolTrace.innerHTML = "";
    (trace || []).forEach((entry) => {
      if (entry.type === "thinking" && entry.content) {
        addThinkingBlock(entry.content);
      } else if (entry.type === "tool" && entry.step) {
        addToolCard(entry.step);
      }
    });
    syncLiveExecPanel();
  }

  function addToolCard(step) {
    const card = document.createElement("details");
    card.className = "tool-card tool-card--ltr";
    card.open = false;
    const summary = createSummaryWithChevron(`${step.tool} · round ${step.round || "?"}`);
    attachToolCardCopyButton(summary, card);
    card.appendChild(summary);
    const bodyWrap = document.createElement("div");
    bodyWrap.className = "tool-card-body ltr-block";

    const argsSection = document.createElement("div");
    argsSection.className = "tool-card-section";
    const argsLabel = document.createElement("div");
    argsLabel.className = "tool-card-section__label";
    argsLabel.textContent = "Arguments";
    const argsPre = document.createElement("pre");
    const argsText = JSON.stringify(step.args, null, 2);
    if (acaRender().highlightCode) {
      const code = document.createElement("code");
      code.className = "language-json hljs";
      code.innerHTML = acaRender().highlightCode(argsText, "json");
      argsPre.appendChild(code);
    } else {
      argsPre.textContent = argsText;
    }
    argsSection.appendChild(argsLabel);
    argsSection.appendChild(argsPre);
    bodyWrap.appendChild(argsSection);

    if (step.result != null && String(step.result).trim()) {
      const resSection = document.createElement("div");
      resSection.className = "tool-card-section";
      const resLabel = document.createElement("div");
      resLabel.className = "tool-card-section__label";
      resLabel.textContent = "Result";
      const resPre = document.createElement("pre");
      const resultText = String(step.result);
      const resultLang = resultText.trim().startsWith("{") || resultText.trim().startsWith("[") ? "json" : "plaintext";
      if (acaRender().highlightCode && resultLang === "json") {
        const code = document.createElement("code");
        code.className = "language-json hljs";
        code.innerHTML = acaRender().highlightCode(resultText, "json");
        resPre.appendChild(code);
      } else {
        resPre.textContent = resultText;
      }
      resSection.appendChild(resLabel);
      resSection.appendChild(resPre);
      bodyWrap.appendChild(resSection);
    }

    card.appendChild(bodyWrap);
    el.toolTrace.prepend(card);
    syncLiveExecPanel();
  }

  function formatDt(iso) {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString("fa-IR");
    } catch {
      return iso;
    }
  }

  function jobEventTime(j) {
    const iso =
      j.status === "active" || j.status === "paused"
        ? j.next_run_at || j.run_at
        : j.last_run_at || j.next_run_at || j.run_at;
    if (!iso) return null;
    const t = new Date(iso).getTime();
    return Number.isFinite(t) ? t : null;
  }

  function scheduleKindLabel(j) {
    let sched = j.schedule_kind || "";
    if (j.schedule_kind === "cron" && j.cron_expression) sched += ` · ${j.cron_expression}`;
    else if (j.schedule_kind === "once" && j.run_at) sched += ` · ${formatDt(j.run_at)}`;
    else if (j.schedule_kind === "interval" && j.interval_seconds)
      sched += ` · هر ${j.interval_seconds}ث`;
    return sched;
  }

  function relativeTimeLabel(targetMs, nowMs) {
    const diffSec = Math.round((targetMs - nowMs) / 1000);
    const abs = Math.abs(diffSec);
    if (abs < 60) return diffSec >= 0 ? "همین الان" : "لحظاتی پیش";
    const min = Math.round(abs / 60);
    if (min < 120) return diffSec >= 0 ? `تا ${min} دقیقه` : `${min} دقیقه پیش`;
    const hr = Math.round(min / 60);
    return diffSec >= 0 ? `تا ${hr} ساعت` : `${hr} ساعت پیش`;
  }

  function stopTimelineClock() {
    if (state.timelineTimer) {
      clearInterval(state.timelineTimer);
      state.timelineTimer = null;
    }
  }

  function stopSchedulerPoll() {
    if (state.schedulerPollTimer) {
      clearInterval(state.schedulerPollTimer);
      state.schedulerPollTimer = null;
    }
  }

  function startTimelineClock() {
    stopTimelineClock();
    if (!state.projectId) return;
    state.timelineTimer = setInterval(() => {
      renderJobTimeline();
    }, 1000);
  }

  function startSchedulerPoll() {
    stopSchedulerPoll();
    if (!state.projectId) return;
    const tick = () => {
      api(`/api/projects/${state.projectId}/scheduler/tick/`, { method: "POST" })
        .then((data) => {
          const ran = (data.results || []).filter((r) => r.ok);
          if (ran.length) {
            loadJobRunsForProject(state.projectId);
            loadJobsForProject(state.projectId);
            setStatus(`${ran.length} job زمان‌بندی اجرا شد`);
          }
        })
        .catch(() => {});
    };
    tick();
    state.schedulerPollTimer = setInterval(tick, 12000);
  }

  function renderJobTimeline() {
    if (!el.jobTimeline) return;
    const now = Date.now();
    if (el.timelineNowLabel) {
      el.timelineNowLabel.textContent = new Date(now).toLocaleString("fa-IR", FA_DATE_TIME_OPTS);
    }
    if (!state.projectId) {
      el.jobTimeline.innerHTML = '<div class="timeline-empty">پروژه انتخاب نشده</div>';
      return;
    }

    const events = state.jobs
      .map((j) => ({ j, t: jobEventTime(j) }))
      .filter((x) => x.t !== null)
      .sort((a, b) => a.t - b.t);

    el.jobTimeline.innerHTML = "";
    if (!state.jobs.length) {
      el.jobTimeline.innerHTML =
        '<div class="timeline-empty">زمان‌بندی نیست — از agent زمان‌بند schedule_job بزنید</div>';
      return;
    }

    const future = events.filter((e) => e.t >= now);
    const past = events.filter((e) => e.t < now).reverse();

    past.slice(0, 8).forEach(({ j, t }) => appendTimelineItem(j, t, now, true));
    const nowRow = document.createElement("div");
    nowRow.className = "tl-now-row";
    nowRow.innerHTML =
      '<span class="tl-now-badge">الان</span><span class="tl-now-line"></span>';
    el.jobTimeline.appendChild(nowRow);
    future.slice(0, 12).forEach(({ j, t }) => appendTimelineItem(j, t, now, false));
  }

  function appendTimelineItem(j, t, now, isPast) {
    const due = j.status === "active" && t <= now;
    const row = document.createElement("div");
    row.className = "tl-item" + (due ? " due" : "") + (isPast ? " past" : "");
    row.dataset.jobId = String(j.id);
    const st = JOB_STATUS_FA[j.status] || j.status;
    const timeStr = new Date(t).toLocaleString("fa-IR", FA_DATE_TIME_OPTS);
    const nextRun = j.next_run_at
      ? new Date(j.next_run_at).toLocaleString("fa-IR", FA_DATE_TIME_OPTS)
      : "—";
    const maxRuns =
      j.max_runs != null && j.max_runs !== ""
        ? `${j.run_count || 0} / ${j.max_runs}`
        : `${j.run_count || 0} / ∞`;
    row.innerHTML = `
      <div class="tl-time">${escapeHtml(timeStr)}<br><span class="muted">${relativeTimeLabel(t, now)}</span></div>
      <div class="tl-card">
        <div class="tl-title">${escapeHtml(j.title)} <span class="muted">(${st})</span></div>
        <div class="tl-meta">${escapeHtml(j.schedule_kind || "")} · agent: ${escapeHtml(j.target_agent_type || "—")}</div>
        <div class="tl-meta">اجرای بعدی: ${escapeHtml(nextRun)} · تعداد: ${escapeHtml(maxRuns)}</div>
        <div class="tl-meta tl-message">${escapeHtml(j.message_preview || "")}</div>
      </div>`;
    el.jobTimeline.appendChild(row);
  }

  function renderJobRunTrace() {
    if (!el.jobRunTrace) return;
    el.jobRunTrace.innerHTML = "";
    if (!state.jobRuns.length) {
      el.jobRunTrace.innerHTML = '<p class="muted" style="margin:4px 8px">هنوز اجرایی ثبت نشده</p>';
      return;
    }
    state.jobRuns.slice(0, 12).forEach((run) => {
      const card = document.createElement("details");
      card.className = "tool-card";
      const ok = run.status === "success";
      card.open = !ok && state.jobRuns.indexOf(run) === 0;
      const summary = createSummaryWithChevron(
        `${run.job_title || "job"} · ${run.status} · ${formatDt(run.started_at)}`
      );
      card.appendChild(summary);
      const pre = document.createElement("pre");
      let body = run.reply || "";
      if (run.error_code) body = `[${run.error_code}]\n` + body;
      if (run.tool_steps && run.tool_steps.length) {
        body += "\n\n--- tools ---\n" + JSON.stringify(run.tool_steps, null, 2);
      }
      pre.textContent = body || "—";
      card.appendChild(pre);
      el.jobRunTrace.appendChild(card);
    });
  }

  async function loadJobRunsForProject(projectId) {
    if (!projectId || !el.jobRunTrace) return;
    try {
      const data = await api(`/api/projects/${projectId}/jobs/runs/`);
      state.jobRuns = data.runs || [];
      renderJobRunTrace();
    } catch (e) {
      el.jobRunTrace.innerHTML = `<p class="muted">${escapeHtml(e.message)}</p>`;
    }
  }

  function syncJobScheduleFieldsVisibility() {
    const kind = document.getElementById("job-edit-kind")?.value || "once";
    if (!el.dialogJob) return;
    el.dialogJob.classList.remove(
      "schedule-kind-once",
      "schedule-kind-cron",
      "schedule-kind-interval"
    );
    el.dialogJob.classList.add(`schedule-kind-${kind}`);
  }

  function isoFromDateTimeInputs() {
    const d = document.getElementById("job-edit-date")?.value;
    const t = document.getElementById("job-edit-time")?.value;
    if (!d || !t) return null;
    const local = new Date(`${d}T${t}:00`);
    if (Number.isNaN(local.getTime())) return null;
    const pad = (n) => String(n).padStart(2, "0");
    return (
      `${local.getFullYear()}-${pad(local.getMonth() + 1)}-${pad(local.getDate())}` +
      `T${pad(local.getHours())}:${pad(local.getMinutes())}:00`
    );
  }

  function fillDateTimeInputsFromIso(iso) {
    const dateEl = document.getElementById("job-edit-date");
    const timeEl = document.getElementById("job-edit-time");
    if (!iso || !dateEl || !timeEl) return;
    const dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return;
    const pad = (n) => String(n).padStart(2, "0");
    dateEl.value = `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}`;
    timeEl.value = `${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
  }

  async function loadJobsForProject(projectId) {
    if (!projectId || !el.jobTimeline) return;
    try {
      const data = await api(`/api/projects/${projectId}/jobs/`);
      state.jobs = data.jobs || [];
      renderJobTimeline();
    } catch (e) {
      if (el.jobTimeline) {
        el.jobTimeline.innerHTML = `<div class="timeline-empty">${escapeHtml(e.message)}</div>`;
      }
    }
  }

  function openJobCreator() {
    if (!state.projectId) return;
    state.jobDialogCreateMode = true;
    if (el.jobDialogTitle) el.jobDialogTitle.textContent = "زمان‌بندی جدید";
    document.getElementById("job-edit-id").value = "";
    document.getElementById("job-edit-title").value = "";
    document.getElementById("job-edit-kind").value = "once";
    fillDateTimeInputsFromIso(new Date().toISOString());
    document.getElementById("job-edit-cron").value = "";
    document.getElementById("job-edit-interval").value = "";
    document.getElementById("job-edit-tz").value = "Asia/Tehran";
    document.getElementById("job-edit-message").value = "";
    document.getElementById("job-edit-max-runs").value = "";
    document.getElementById("job-edit-status").value = "active";
    syncJobScheduleFieldsVisibility();
    el.dialogJob.showModal();
  }

  async function openJobEditor(jobId) {
    state.jobDialogCreateMode = false;
    if (el.jobDialogTitle) el.jobDialogTitle.textContent = "ویرایش زمان‌بندی";
    const data = await api(`/api/jobs/${jobId}/detail/`);
    const j = data.job;
    document.getElementById("job-edit-id").value = j.id;
    document.getElementById("job-edit-title").value = j.title || "";
    document.getElementById("job-edit-kind").value = j.schedule_kind || "once";
    fillDateTimeInputsFromIso(j.run_at || j.next_run_at);
    document.getElementById("job-edit-cron").value = j.cron_expression || "";
    document.getElementById("job-edit-interval").value = j.interval_seconds || "";
    document.getElementById("job-edit-tz").value = j.timezone_name || "Asia/Tehran";
    document.getElementById("job-edit-message").value = j.message || "";
    document.getElementById("job-edit-max-runs").value =
      j.max_runs != null && j.max_runs !== "" ? String(j.max_runs) : "";
    document.getElementById("job-edit-status").value = j.status || "active";
    syncJobScheduleFieldsVisibility();
    el.dialogJob.showModal();
  }

  async function patchJob(jobId, body) {
    await api(`/api/jobs/${jobId}/`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    await loadJobsForProject(state.projectId);
  }

  async function deleteJob(jobId) {
    if (!confirm("این زمان‌بندی از دیتابیس حذف شود؟")) return;
    await api(`/api/jobs/${jobId}/delete/`, { method: "DELETE" });
    await loadJobsForProject(state.projectId);
    setStatus("زمان‌بندی حذف شد");
  }

  async function deleteProject(projectId) {
    const p = state.projects.find((x) => x.id === Number(projectId));
    const name = p ? p.name : projectId;
    if (!confirm(`پروژه «${name}» و همه مکالمات و زمان‌بندی‌هایش حذف شوند؟`)) return;
    await api(`/api/projects/${projectId}/delete/`, { method: "DELETE" });
    if (state.projectId === Number(projectId)) {
      state.projectId = null;
      state.conversationId = null;
      localStorage.removeItem(LS_PROJECT);
      localStorage.removeItem(LS_CONV);
    }
    await fetchProjects();
    state.conversations = [];
    state.jobs = [];
    renderConversationList();
    renderJobTimeline();
    stopTimelineClock();
    stopSchedulerPoll();
    if (state.projects.length) {
      await selectProject(state.projects[0].id);
    } else {
      renderAgentNewButtons();
      el.btnDeleteProject.disabled = true;
      el.btnRefreshJobs.disabled = true;
      if (el.btnNewScheduledJob) el.btnNewScheduledJob.disabled = true;
    }
    setStatus("پروژه حذف شد");
  }

  async function deleteConversation(conversationId) {
    if (!confirm("این مکالمه و تمام پیام‌هایش حذف شوند؟")) return;
    await api(`/api/conversations/${conversationId}/delete/`, { method: "DELETE" });
    if (state.conversationId === Number(conversationId)) {
      state.conversationId = null;
      state.conversation = null;
      localStorage.removeItem(LS_CONV);
      el.log.innerHTML = "";
      clearPhaseLogPanel();
      el.input.disabled = true;
      el.send.disabled = true;
      setComposerEntryEnabled(false);
      setDeleteConversationButtonDisabled(true);
      el.chatTitle.textContent = "مکالمه‌ای انتخاب نشده";
      state.codeChangesData = null;
      renderCodeChangesTimeline(null);
      if (el.btnRefreshChanges) el.btnRefreshChanges.disabled = true;
      updateComposerAgentBadge(null);
      updateComposerOptionsEnabled(false);
    }
    await loadConversationsForProject(state.projectId);
    await loadJobsForProject(state.projectId);
    setStatus("مکالمه حذف شد");
  }

  async function loadConversationsForProject(projectId) {
    const pid = Number(projectId);
    const data = await api(`/api/projects/${pid}/conversations/`);
    state.conversationsByProject[pid] = data.conversations || [];
    if (data.project) {
      const idx = state.projects.findIndex((p) => p.id === pid);
      if (idx >= 0) state.projects[idx] = { ...state.projects[idx], ...data.project };
      else state.projects.push(data.project);
    }
    if (pid === state.projectId) {
      state.conversations = state.conversationsByProject[pid];
    }
    renderProjectList();
  }

  function currentProjectRecord() {
    return state.projects.find((p) => p.id === state.projectId) || null;
  }

  function normalizePathInput(raw) {
    return (raw || "").trim().replace(/\\/g, "/").replace(/^\/+/, "").replace(/\/+$/, "");
  }

  function renderFileAccessLists() {
    const render = (ul, paths, kind) => {
      if (!ul) return;
      ul.innerHTML = "";
      if (!paths.length) {
        const li = document.createElement("li");
        li.className = "muted";
        li.textContent = "—";
        ul.appendChild(li);
        return;
      }
      paths.forEach((path) => {
        const li = document.createElement("li");
        const span = document.createElement("span");
        span.className = "path";
        span.textContent = path;
        const rm = document.createElement("button");
        rm.type = "button";
        rm.className = "btn btn-tiny";
        rm.textContent = "حذف";
        rm.onclick = () => {
          state.fileAccessDraft[kind] = state.fileAccessDraft[kind].filter((p) => p !== path);
          renderFileAccessLists();
        };
        li.appendChild(span);
        li.appendChild(rm);
        ul.appendChild(li);
      });
    };
    render(el.fileAccessAlwaysList, state.fileAccessDraft.always, "always");
    render(el.fileAccessDeniedList, state.fileAccessDraft.denied, "denied");
  }

  function setFileAccessStatus(text, isError) {
    if (!el.fileAccessStatus) return;
    if (!text) {
      el.fileAccessStatus.hidden = true;
      el.fileAccessStatus.textContent = "";
      return;
    }
    el.fileAccessStatus.hidden = false;
    el.fileAccessStatus.textContent = text;
    el.fileAccessStatus.classList.toggle("is-error", Boolean(isError));
  }

  function applyUserFileAccessDraft(data) {
    state.fileAccessDraft = {
      always: [...(data?.always_context_paths || [])],
      denied: [...(data?.denied_content_paths || [])],
    };
    renderFileAccessLists();
  }

  async function loadUserFileAccessSettings() {
    try {
      const data = await api("/api/user/file-access/");
      applyUserFileAccessDraft(data);
    } catch (e) {
      setFileAccessStatus(e.message, true);
    }
  }

  async function saveUserFileAccessSettings() {
    setFileAccessStatus("در حال ذخیره…", false);
    try {
      const data = await api("/api/user/file-access/", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          always_context_paths: state.fileAccessDraft.always,
          denied_content_paths: state.fileAccessDraft.denied,
        }),
      });
      applyUserFileAccessDraft(data);
      setFileAccessStatus("ذخیره شد.", false);
    } catch (e) {
      setFileAccessStatus(e.message, true);
    }
  }

  function addFileAccessPath(kind) {
    const input = kind === "always" ? el.fileAccessAlwaysInput : el.fileAccessDeniedInput;
    const path = normalizePathInput(input?.value);
    if (!path) return;
    const list = state.fileAccessDraft[kind];
    if (!list.includes(path)) list.push(path);
    if (input) input.value = "";
    renderFileAccessLists();
  }

  function setJobTraceMaxed(maxed) {
    if (state.jobTraceMaxed === maxed) return;
    state.jobTraceMaxed = maxed;
    const section = el.timelineTraceBlock?.closest(".timeline-section");
    el.timelineTraceBlock?.classList.toggle("is-panel-maxed", maxed);
    section?.classList.toggle("is-trace-maxed", maxed);
    if (el.btnExpandJobTrace) {
      el.btnExpandJobTrace.setAttribute("aria-expanded", maxed ? "true" : "false");
    }
  }

  function setCodeDetailMaxed(maxed) {
    if (state.codeDetailMaxed === maxed) return;
    state.codeDetailMaxed = maxed;
    const section = el.codeChangesTraceBlock?.closest(".timeline-section");
    el.codeChangesTraceBlock?.classList.toggle("is-panel-maxed", maxed);
    section?.classList.toggle("is-trace-maxed", maxed);
    if (el.btnExpandCodeDetail) {
      el.btnExpandCodeDetail.setAttribute("aria-expanded", maxed ? "true" : "false");
    }
  }

  function initPanelExpandControls() {
    if (el.btnCloseLiveExec) {
      el.btnCloseLiveExec.onclick = () => dismissLiveExecPanel();
    }
    if (el.btnToggleLiveExec) {
      el.btnToggleLiveExec.onclick = () => openLiveExecPanel();
    }
    syncLiveExecPanel();
    if (el.btnExpandJobTrace) {
      el.btnExpandJobTrace.onclick = (ev) => {
        ev.stopPropagation();
        setJobTraceMaxed(!state.jobTraceMaxed);
      };
    }
    if (el.btnExpandCodeDetail) {
      el.btnExpandCodeDetail.onclick = (ev) => {
        ev.stopPropagation();
        setCodeDetailMaxed(!state.codeDetailMaxed);
      };
    }
  }

  function initUserFileAccessSettings() {
    if (el.btnFileAccessAlwaysAdd) {
      el.btnFileAccessAlwaysAdd.onclick = () => addFileAccessPath("always");
    }
    if (el.btnFileAccessDeniedAdd) {
      el.btnFileAccessDeniedAdd.onclick = () => addFileAccessPath("denied");
    }
    if (el.fileAccessAlwaysInput) {
      el.fileAccessAlwaysInput.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter") {
          ev.preventDefault();
          addFileAccessPath("always");
        }
      });
    }
    if (el.fileAccessDeniedInput) {
      el.fileAccessDeniedInput.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter") {
          ev.preventDefault();
          addFileAccessPath("denied");
        }
      });
    }
    if (el.fileAccessSave) {
      el.fileAccessSave.onclick = () => saveUserFileAccessSettings();
    }
    loadUserFileAccessSettings().catch(() => {});
  }

  function setFocusPreviewVisible(visible) {
    if (el.focusPreviewCard) el.focusPreviewCard.hidden = !visible;
  }

  function clearFilePreview() {
    if (el.filePreview) el.filePreview.innerHTML = "";
    state.lastPreviewPath = null;
    state.lastPreviewContent = null;
    setFocusPreviewVisible(false);
  }

  async function selectProject(id) {
    const pid = Number(id);
    if (!pid || state.selectingProject) return;
    state.selectingProject = true;
    try {
      await maybeDiscardEmptyConversationOnLeave();
      stopTimelineClock();
      stopSchedulerPoll();
      state.projectId = pid;
      state.conversationId = null;
      state.conversation = null;
      state.sessionCreatedConvId = null;
      state.scopePaths = [];
      localStorage.setItem(LS_PROJECT, String(pid));
      renderProjectList();
      renderAgentNewButtons();

      el.input.disabled = true;
      el.send.disabled = true;
      setComposerEntryEnabled(false);
      el.chatTitle.textContent = "مکالمه‌ای انتخاب نشده";
      el.log.innerHTML = "";
      clearPhaseLogPanel();
      el.toolTrace.innerHTML = "";
      state.liveExecDismissed = true;
      syncLiveExecPanel();
      clearFilePreview();
      renderScopeChips();
      updateToolsPanelEnabled(false);
      updateComposerAgentBadge(null);
      updateComposerOptionsEnabled(false);
      await loadConversationsForProject(pid);
      loadRemoteServerSettings(pid).catch(() => {});
      await Promise.all([loadJobsForProject(pid), loadJobRunsForProject(pid)]);
      startTimelineClock();
      startSchedulerPoll();
      if (el.btnRefreshJobs) el.btnRefreshJobs.disabled = false;
      if (el.btnNewScheduledJob) el.btnNewScheduledJob.disabled = false;
      if (el.btnDeleteProject) el.btnDeleteProject.disabled = false;
      if (el.btnRefreshGrowthHub) el.btnRefreshGrowthHub.disabled = false;
      if (el.btnRefreshDebugHub) el.btnRefreshDebugHub.disabled = false;
      if (state.sidePanelMode === "growth") {
        loadGrowthHub().catch(() => {});
      }
      if (state.sidePanelMode === "debug") {
        loadDebugHub().catch(() => {});
      }

      const pendingConvId =
        window.APP_CONFIG && window.APP_CONFIG.pendingToolConversationId
          ? Number(window.APP_CONFIG.pendingToolConversationId)
          : null;
      const savedConv = parseInt(localStorage.getItem(LS_CONV), 10);
      const convId =
        pendingConvId && state.conversations.some((c) => c.id === pendingConvId)
          ? pendingConvId
          : savedConv;
      const pick = state.conversations.find((c) => c.id === convId);
      if (pick) {
        if (pendingConvId) window.APP_CONFIG.pendingToolConversationId = null;
        await selectConversation(pick.id);
      } else {
        loadTree();
      }
    } catch (e) {
      setStatus("خطا در بارگذاری پروژه: " + e.message);
    } finally {
      state.selectingProject = false;
    }
  }

  async function selectConversation(id, opts = {}) {
    const cid = Number(id);
    if (!cid) return;
    try {
      if (
        state.busy &&
        state.conversationId &&
        Number(state.conversationId) !== cid &&
        !opts.skipDiscard
      ) {
        setStatus("صبر کنید تا اجرای فعلی تمام شود.");
        return;
      }
      if (!opts.skipDiscard && state.conversationId && state.conversationId !== cid) {
        await maybeDiscardEmptyConversationOnLeave(state.conversationId);
      }
      if (cid !== state.sessionCreatedConvId) {
        state.sessionCreatedConvId = null;
      }
      if (state.conversationId !== cid) {
        state.convInputDirty = false;
        state.convMessageSent = false;
        setComposerInputValue("");
        clearPhaseLogPanel();
      }
      state.conversationId = cid;
      localStorage.setItem(LS_CONV, String(cid));
      const data = await api(`/api/conversations/${cid}/`);
      state.conversation = data.conversation;
      if (state.conversation.project_id) {
        state.expandedProjects.add(Number(state.conversation.project_id));
      }
      state.scopePaths = [...(state.conversation.effective_scope_paths || [])];
      state.liveExecDismissed = true;
      renderScopeChips();
      el.chatTitle.textContent = state.conversation.title;
      const at = state.conversation.agent_type || "coding";
      applyAgentOptionDefaults(at);
      updateComposerAgentBadge(at);
      updateComposerOptionsEnabled(true);
      if (el.llmModel && state.conversation.llm_model) {
        selectComposerModel(state.conversation.llm_model, {
          skipApi: true,
          silent: true,
          allowDisabled: true,
        });
      }
      renderConversationView(state.conversation);
      if (el.btnRefreshChanges) el.btnRefreshChanges.disabled = false;
      if (state.sidePanelMode === "changes") {
        loadConversationCodeChanges().catch(() => {});
      }
      el.input.disabled = false;
      el.send.disabled = false;
      setComposerEntryEnabled(true);
      setDeleteConversationButtonDisabled(false);
      renderConversationList();
      await Promise.all([loadTree(), loadConversationTools()]);
      const pending = window.APP_CONFIG && window.APP_CONFIG.pendingToolRef;
      if (pending && el.toolLinkInput) {
        el.toolLinkInput.value = pending;
        window.APP_CONFIG.pendingToolRef = null;
        attachConversationTool(pending).catch((err) =>
          setStatus("افزودن ابزار از لینک: " + err.message)
        );
      }
    } catch (e) {
      localStorage.removeItem(LS_CONV);
      setStatus("خطا در باز کردن مکالمه: " + e.message);
    }
  }

  function workspaceContextQuery() {
    if (state.conversationId) return `conversation_id=${state.conversationId}`;
    if (state.projectId) return `project_id=${state.projectId}`;
    return "";
  }

  async function loadTree() {
    const ctx = workspaceContextQuery();
    if (!ctx) return;
    loadTreeExpandedPaths();
    el.fileTree.textContent = "…";
    const q = ctx;
    try {
      const data = await api(`/api/workspace/tree/?depth=32&${q}`);
      el.fileTree.innerHTML = "";
      renderTreeNode(data.tree, el.fileTree, 0);
      renderTreeHighlight();
    } catch (e) {
      el.fileTree.textContent = e.message;
    }
  }

  function createTreeRow(node, depth) {
    const row = document.createElement("div");
    row.className =
      "tree-item " +
      (node.type === "dir" ? "dir" : "file") +
      (node.in_scope === false ? " out-scope" : "");
    row.dataset.path = node.path;

    if (node.type === "dir") {
      const expand = document.createElement("button");
      expand.type = "button";
      expand.className = "btn-chevron collapsed tree-expand";
      setChevronButton(expand, false);
      expand.setAttribute("aria-label", "باز/بسته");
      expand.onclick = (ev) => {
        ev.stopPropagation();
        const wrap = row.nextElementSibling;
        if (!wrap || !wrap.classList.contains("tree-children")) return;
        const nowCollapsed = wrap.classList.toggle("collapsed");
        setChevronButton(expand, !nowCollapsed);
        if (nowCollapsed) state.treeExpandedPaths.delete(node.path);
        else state.treeExpandedPaths.add(node.path);
        persistTreeExpandedPaths();
      };
      row.appendChild(expand);
    } else {
      const spacer = document.createElement("span");
      spacer.className = "tree-expand-spacer";
      row.appendChild(spacer);
    }

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.className = "tree-focus-cb";
    cb.checked = state.scopePaths.includes(node.path);
    cb.title = "محدودهٔ focus";
    cb.onclick = (ev) => ev.stopPropagation();
    cb.onchange = () => toggleScopePath(node.path, cb.checked);

    const icon = document.createElement("span");
    icon.className = "tree-icon";
    icon.innerHTML = node.type === "dir" ? TREE_ICON_FOLDER : TREE_ICON_FILE;

    const label = document.createElement("span");
    label.className = "tree-label";
    label.textContent = node.name;

    // ترتیب جدید: icon → label → cb  (cb آخر خط و چسبیده به چپ)
    row.appendChild(icon);
    row.appendChild(label);
    row.appendChild(cb);

    row.onclick = (ev) => {
      if (ev.target.closest(".tree-focus-cb") || ev.target.closest(".tree-expand")) return;
      if (node.type === "file") previewFile(node.path);
    };
    return row;
  }

  function renderTreeNode(node, container, depth) {
    if (node.type === "dir") {
      const row = createTreeRow(node, depth);
      container.appendChild(row);
      const childrenWrap = document.createElement("div");
      const expanded = state.treeExpandedPaths.has(node.path);
      childrenWrap.className = "tree-children" + (expanded ? "" : " collapsed");
      const expandBtn = row.querySelector(".tree-expand");
      if (expandBtn) setChevronButton(expandBtn, expanded);
      (node.children || []).forEach((ch) => renderTreeNode(ch, childrenWrap, depth + 1));
      container.appendChild(childrenWrap);
    } else {
      container.appendChild(createTreeRow(node, depth));
    }
  }

  function renderFilePreview(path, content) {
    if (!el.filePreview) return;
    setFocusPreviewVisible(true);
    const lines = (content || "").split("\n");
    const lang = acaRender().langFromPath ? acaRender().langFromPath(path) : "plaintext";
    state.lastPreviewPath = path;
    state.lastPreviewContent = content || "";
    state.lastPreviewLang = lang;
    el.filePreview.innerHTML = "";
    const head = document.createElement("div");
    head.className = "preview-header";
    const main = document.createElement("div");
    main.className = "preview-header__main";
    const pathEl = document.createElement("div");
    pathEl.className = "preview-path";
    pathEl.textContent = path;
    const meta = document.createElement("div");
    meta.className = "preview-meta muted";
    meta.textContent = `${lines.length} lines · ${lang}`;
    main.appendChild(pathEl);
    main.appendChild(meta);
    const expandBtn = document.createElement("button");
    expandBtn.type = "button";
    expandBtn.className = "btn btn-tiny";
    expandBtn.textContent = "بزرگ‌نمایی";
    expandBtn.title = "نمایش کامل فایل";
    expandBtn.onclick = () => openFilePreviewModal(path, content || "", lang);
    head.appendChild(main);
    head.appendChild(expandBtn);

    const body = document.createElement("div");
    body.className = "preview-body ltr-block";
    if (acaRender().renderHighlightedLines) {
      body.appendChild(acaRender().renderHighlightedLines(content || "", lang));
    } else {
      lines.forEach((line) => {
        const row = document.createElement("div");
        row.className = "preview-line";
        const code = document.createElement("span");
        code.className = "preview-code";
        code.textContent = line;
        row.appendChild(code);
        body.appendChild(row);
      });
    }
    el.filePreview.appendChild(head);
    el.filePreview.appendChild(body);
  }

  function openFilePreviewModal(path, content, lang) {
    if (!el.dialogFilePreview) return;
    if (el.filePreviewModalTitle) el.filePreviewModalTitle.textContent = path;
    if (el.filePreviewModalMeta) {
      const lineCount = (content || "").split("\n").length;
      el.filePreviewModalMeta.textContent = `${lineCount} lines · ${lang}`;
    }
    if (el.filePreviewModalBody) {
      el.filePreviewModalBody.innerHTML = "";
      if (acaRender().renderHighlightedLines) {
        el.filePreviewModalBody.appendChild(
          acaRender().renderHighlightedLines(content || "", lang)
        );
      } else {
        el.filePreviewModalBody.textContent = content || "";
      }
    }
    el.dialogFilePreview.showModal();
  }

  function wordCount(text) {
    return (text || "").trim().split(/\s+/).filter(Boolean).length;
  }

  function resizeComposerInput() {
    if (!el.input) return;
    el.input.style.height = "auto";
    const style = window.getComputedStyle(el.input);
    const lineHeight = parseFloat(style.lineHeight) || 22;
    const pad = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
    const minH = lineHeight * COMPOSER_INPUT_MIN_LINES + pad;
    const maxH = lineHeight * COMPOSER_INPUT_MAX_LINES + pad;
    const next = Math.min(maxH, Math.max(minH, el.input.scrollHeight));
    el.input.style.height = `${next}px`;
    el.input.style.overflowY = el.input.scrollHeight > maxH ? "auto" : "hidden";
  }

  function setComposerInputValue(text) {
    if (!el.input) return;
    el.input.value = text ?? "";
    el.input.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function clearComposerPasteFold() {
    state.composerPasteFull = null;
    if (el.composerPasteFold) {
      el.composerPasteFold.hidden = true;
      el.composerPasteFold.innerHTML = "";
    }
  }

  function showComposerPasteFold(fullText) {
    if (!el.composerPasteFold || !el.input) return;
    state.composerPasteFull = fullText;
    const words = wordCount(fullText);
    el.composerPasteFold.hidden = false;
    el.composerPasteFold.innerHTML = "";
    const icon = document.createElement("span");
    icon.className = "file-ico file-ico--text";
    icon.innerHTML = PASTE_FOLD_ICON;
    const label = document.createElement("span");
    label.className = "composer-paste-fold__label";
    label.textContent = `متن پیست‌شده · ${words} کلمه`;
    label.title = `متن پیست‌شده · ${words} کلمه`;
    const expand = document.createElement("button");
    expand.type = "button";
    expand.className = "btn btn-tiny";
    expand.textContent = "نمایش کامل";
    expand.onclick = () => {
      setComposerInputValue(fullText);
      clearComposerPasteFold();
    };
    const clear = document.createElement("button");
    clear.type = "button";
    clear.className = "composer-paste-fold__remove";
    clear.setAttribute("aria-label", "حذف");
    clear.textContent = "×";
    clear.onclick = () => {
      clearComposerPasteFold();
      resizeComposerInput();
    };
    el.composerPasteFold.appendChild(icon);
    el.composerPasteFold.appendChild(label);
    el.composerPasteFold.appendChild(expand);
    el.composerPasteFold.appendChild(clear);
    setComposerInputValue("");
  }

  function openComposerAttachmentPreview(att) {
    if (!el.dialogComposerAttachment || !att) return;
    const kind = att.kind || fileKindFromName(att.name, att.mime);
    if (el.composerAttachmentModalTitle) el.composerAttachmentModalTitle.textContent = att.name || "—";
    if (el.composerAttachmentModalMeta) {
      el.composerAttachmentModalMeta.textContent = `${formatFileSize(att.size)} · ${att.mime || kind}`;
    }
    if (!el.composerAttachmentModalBody) return;
    el.composerAttachmentModalBody.innerHTML = "";
    const url = att.objectUrl;

    if (kind === "image" && url) {
      const img = document.createElement("img");
      img.className = "attachment-preview-media";
      img.src = url;
      img.alt = att.name || "";
      el.composerAttachmentModalBody.appendChild(img);
    } else if (kind === "audio" && url) {
      const audio = document.createElement("audio");
      audio.className = "attachment-preview-player";
      audio.controls = true;
      audio.src = url;
      el.composerAttachmentModalBody.appendChild(audio);
    } else if (kind === "video" && url) {
      const video = document.createElement("video");
      video.className = "attachment-preview-media attachment-preview-player";
      video.controls = true;
      video.src = url;
      el.composerAttachmentModalBody.appendChild(video);
    } else if (kind === "pdf" && url) {
      const frame = document.createElement("iframe");
      frame.className = "attachment-preview-frame";
      frame.src = url;
      frame.title = att.name || "PDF";
      el.composerAttachmentModalBody.appendChild(frame);
    } else if (kind === "text" && att.text != null) {
      const pre = document.createElement("pre");
      pre.className = "attachment-preview-text scroller";
      pre.textContent = att.text;
      el.composerAttachmentModalBody.appendChild(pre);
    } else if (kind === "archive") {
      const note = document.createElement("p");
      note.className = "attachment-preview-note muted";
      note.textContent =
        "پیش‌نمایش محتوای آرشیو در مرورگر پشتیبانی نمی‌شود. فایل هنگام ارسال پیام ضمیمه می‌شود.";
      el.composerAttachmentModalBody.appendChild(note);
      if (url) {
        const link = document.createElement("a");
        link.className = "btn btn-tiny";
        link.href = url;
        link.download = att.name || "archive";
        link.textContent = "دانلود";
        link.style.margin = "0 auto";
        link.style.display = "inline-block";
        el.composerAttachmentModalBody.appendChild(link);
      }
    } else {
      const note = document.createElement("p");
      note.className = "attachment-preview-note muted";
      note.textContent = att.isBinary
        ? "پیش‌نمایش این نوع فایل در مرورگر محدود است. محتوا هنگام ارسال به ایجنت فرستاده می‌شود."
        : "محتوایی برای نمایش نیست.";
      el.composerAttachmentModalBody.appendChild(note);
      if (url) {
        const link = document.createElement("a");
        link.className = "btn btn-tiny";
        link.href = url;
        link.download = att.name || "file";
        link.textContent = "دانلود";
        link.style.margin = "12px auto 0";
        link.style.display = "inline-block";
        el.composerAttachmentModalBody.appendChild(link);
      }
    }
    el.dialogComposerAttachment.showModal();
  }

  function renderComposerAttachments() {
    if (!el.composerAttachments) return;
    el.composerAttachments.innerHTML = "";
    if (!state.composerAttachments.length) {
      el.composerAttachments.hidden = true;
      return;
    }
    el.composerAttachments.hidden = false;
    state.composerAttachments.forEach((att, idx) => {
      const chip = document.createElement("div");
      chip.className = "composer-attachment-chip";
      chip.title = att.name;
      chip.setAttribute("role", "button");
      chip.tabIndex = 0;
      const iconWrap = document.createElement("div");
      iconWrap.innerHTML = fileIconHtml(att.kind || fileKindFromName(att.name, att.mime));
      const name = document.createElement("span");
      name.className = "composer-attachment-chip__name";
      name.textContent = att.name;
      const rm = document.createElement("button");
      rm.type = "button";
      rm.setAttribute("aria-label", "حذف");
      rm.textContent = "×";
      rm.onclick = (ev) => {
        ev.stopPropagation();
        revokeComposerAttachment(state.composerAttachments[idx]);
        state.composerAttachments.splice(idx, 1);
        renderComposerAttachments();
      };
      chip.onclick = () => openComposerAttachmentPreview(att);
      chip.onkeydown = (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          openComposerAttachmentPreview(att);
        }
      };
      if (iconWrap.firstElementChild) chip.appendChild(iconWrap.firstElementChild);
      chip.appendChild(name);
      chip.appendChild(rm);
      el.composerAttachments.appendChild(chip);
    });
  }

  async function readComposerFile(file) {
    if (file.size > COMPOSER_ATTACH_MAX_BYTES) {
      throw new Error(
        `فایل ${file.name} بزرگ‌تر از ${Math.round(COMPOSER_ATTACH_MAX_BYTES / 1024)}KB است`
      );
    }
    const isText =
      file.type.startsWith("text/") ||
      /\.(txt|md|py|js|mjs|ts|tsx|jsx|json|html|css|xml|yml|yaml|sh|sql|csv|log|ini|toml|env|rs|go|java|kt|rb|php|c|cpp|h)$/i.test(
        file.name
      );
    const kind = fileKindFromName(file.name, file.type);
    const objectUrl = URL.createObjectURL(file);
    if (isText) {
      const text = await file.text();
      return {
        name: file.name,
        size: file.size,
        mime: file.type || "text/plain",
        text,
        kind,
        objectUrl,
        isBinary: false,
      };
    }
    const buf = await file.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let binary = "";
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
    }
    const b64 = btoa(binary);
    const preview =
      b64.length > 12000
        ? `${b64.slice(0, 12000)}\n...(base64 truncated for UI; full payload sent on submit)`
        : b64;
    return {
      name: file.name,
      size: file.size,
      mime: file.type || "application/octet-stream",
      text: `[Attached binary: ${file.name}]\n\`\`\`base64\n${preview}\n\`\`\``,
      isBinary: true,
      kind,
      objectUrl,
    };
  }

  function buildOutboundMessage(userText) {
    const parts = [];
    let base = (userText || "").trim();
    if (state.composerPasteFull) {
      parts.push(state.composerPasteFull.trim());
    } else if (base) {
      parts.push(base);
    }
    state.composerAttachments.forEach((att) => {
      parts.push(
        `---\nAttached file: ${att.name} (${att.mime || "file"}, ${att.size} bytes)\n${att.text || ""}`
      );
    });
    return parts.join("\n\n").trim();
  }

  function resetComposerAfterSend() {
    if (el.input) setComposerInputValue("");
    state.composerAttachments.forEach(revokeComposerAttachment);
    state.composerAttachments = [];
    clearComposerPasteFold();
    renderComposerAttachments();
    resizeComposerInput();
    stopSpeechToText();
  }

  async function previewFile(path) {
    if (!el.filePreview) return;
    const ctx = workspaceContextQuery();
    if (!ctx) {
      clearFilePreview();
      return;
    }
    el.filePreview.innerHTML = '<div class="preview-empty muted">…</div>';
    const q = `path=${encodeURIComponent(path)}&${ctx}`;
    try {
      const data = await api(`/api/workspace/file/?${q}`);
      renderFilePreview(path, data.content || "");
    } catch (e) {
      clearFilePreview();
      setStatus(e.message);
    }
  }

  async function loadPathPicker(path) {
    const q = path ? `?path=${encodeURIComponent(path)}` : "";
    const data = await api(`/api/projects/browse-dirs/${q}`);
    state.pathPickerPath = data.path;
    syncProjectRootPathInput(data.path);
    if (el.pathPickerCurrent) el.pathPickerCurrent.textContent = data.path;
    if (el.pathPickerUp) {
      el.pathPickerUp.disabled = !data.parent;
      el.pathPickerUp.dataset.parent = data.parent || "";
    }
    if (!el.pathPickerList) return;
    el.pathPickerList.innerHTML = "";
    if (!data.entries || !data.entries.length) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = "زیرپوشه‌ای نیست";
      el.pathPickerList.appendChild(li);
      return;
    }
    data.entries.forEach((entry) => {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "path-picker-dir";
      btn.textContent = `📁 ${entry.name}`;
      btn.onclick = () => loadPathPicker(entry.path);
      li.appendChild(btn);
      el.pathPickerList.appendChild(li);
    });
  }

  el.projectList.addEventListener("click", (ev) => {
    const del = ev.target.closest("[data-delete-project]");
    if (del) {
      ev.stopPropagation();
      deleteProject(del.dataset.deleteProject).catch((e) => setStatus(e.message));
      return;
    }
    const delConv = ev.target.closest("[data-delete-conversation]");
    if (delConv) {
      ev.stopPropagation();
      deleteConversation(delConv.dataset.deleteConversation).catch((e) => setStatus(e.message));
      return;
    }
    const infoBtn = ev.target.closest(".btn-conv-info");
    if (infoBtn) {
      ev.stopPropagation();
      const li = infoBtn.closest("li[data-id]");
      if (li) li.classList.toggle("is-info-open");
      return;
    }
    const convLi = ev.target.closest("li[data-id]");
    if (convLi) {
      const block = convLi.closest(".project-block");
      const pid = block && block.dataset.projectId;
      if (pid && Number(pid) !== state.projectId) {
        selectProject(pid).then(() => selectConversation(convLi.dataset.id));
      } else {
        selectConversation(convLi.dataset.id);
      }
      return;
    }
  });

  if (el.jobTimeline) {
    el.jobTimeline.addEventListener("click", (ev) => {
      const card = ev.target.closest(".tl-item");
      if (!card || !card.dataset.jobId) return;
      openJobEditor(card.dataset.jobId).catch((e) => setStatus(e.message));
    });
  }

  if (el.showAllPhaseLogs) {
    el.showAllPhaseLogs.addEventListener("change", () => {
      state.showAllPhaseLogs = el.showAllPhaseLogs.checked;
      localStorage.setItem(LS_SHOW_ALL_PHASE_LOGS, state.showAllPhaseLogs ? "1" : "0");
      refreshPhaseLogVisibility();
      syncPhaseLogMoreButton();
    });
  }
  initPhaseLogPanel();

  if (el.btnRefreshJobs) {
    el.btnRefreshJobs.onclick = (ev) => {
      ev.stopPropagation();
      if (state.projectId) {
        Promise.all([
          loadJobsForProject(state.projectId),
          loadJobRunsForProject(state.projectId),
        ]).catch((e) => setStatus(e.message));
      }
    };
  }

  el.input.addEventListener("input", () => {
    resizeComposerInput();
    syncContextRing(el.input.value || "");
    if (
      state.sessionCreatedConvId &&
      state.conversationId === state.sessionCreatedConvId &&
      el.input.value.trim()
    ) {
      state.convInputDirty = true;
    }
  });

  if (el.input) {
    el.input.addEventListener("keydown", (ev) => {
      if (ev.key !== "Enter" || ev.shiftKey || ev.isComposing) return;
      ev.preventDefault();
      if (state.busy && el.send && el.send.classList.contains("send-btn--stop")) {
        requestAgentStop();
        return;
      }
      if (el.send && !el.send.disabled && el.form) {
        el.form.requestSubmit();
      }
    });
  }

  el.input.addEventListener("paste", (ev) => {
    const text = ev.clipboardData?.getData("text/plain") || "";
    if (wordCount(text) <= COMPOSER_COLLAPSE_WORDS) return;
    ev.preventDefault();
    state.composerPasteFull = text;
    showComposerPasteFold(text);
  });

  if (el.btnComposerAttach && el.composerFileInput) {
    el.btnComposerAttach.addEventListener("click", () => {
      if (!state.conversationId || el.btnComposerAttach.disabled) return;
      el.composerFileInput.click();
    });
    el.composerFileInput.addEventListener("change", async () => {
      const files = [...(el.composerFileInput.files || [])];
      el.composerFileInput.value = "";
      for (const file of files) {
        try {
          const att = await readComposerFile(file);
          state.composerAttachments.push(att);
        } catch (err) {
          setStatus(err.message || String(err));
        }
      }
      renderComposerAttachments();
    });
  }

  if (el.filePreviewModalClose && el.dialogFilePreview) {
    el.filePreviewModalClose.onclick = () => el.dialogFilePreview.close();
  }

  if (el.composerAttachmentModalClose && el.dialogComposerAttachment) {
    el.composerAttachmentModalClose.onclick = () => el.dialogComposerAttachment.close();
  }

  if (el.btnComposerMic) {
    el.btnComposerMic.addEventListener("click", () => {
      if (el.btnComposerMic.disabled) return;
      toggleSpeechToText();
    });
  }

  resizeComposerInput();

  const jobKindEl = document.getElementById("job-edit-kind");
  if (jobKindEl) jobKindEl.addEventListener("change", syncJobScheduleFieldsVisibility);

  if (el.btnDeleteProject) {
    el.btnDeleteProject.onclick = () => {
      if (state.projectId) {
        deleteProject(state.projectId).catch((e) => setStatus(e.message));
      }
    };
  }

  if (el.btnDeleteConversation) {
    el.btnDeleteConversation.onclick = () => {
      if (state.conversationId) {
        deleteConversation(state.conversationId).catch((e) => setStatus(e.message));
      }
    };
  }

  if (el.cancelJob) el.cancelJob.onclick = () => el.dialogJob.close();
  if (el.formJob) {
    el.formJob.onsubmit = async (e) => {
      e.preventDefault();
      const jobId = document.getElementById("job-edit-id").value;
      const kind = document.getElementById("job-edit-kind").value;
      const body = {
        title: document.getElementById("job-edit-title").value,
        schedule_kind: kind,
        cron_expression: document.getElementById("job-edit-cron").value,
        interval_seconds: document.getElementById("job-edit-interval").value
          ? parseInt(document.getElementById("job-edit-interval").value, 10)
          : null,
        timezone: document.getElementById("job-edit-tz").value,
        message: document.getElementById("job-edit-message").value,
        status: document.getElementById("job-edit-status").value,
      };
      const maxRunsRaw = document.getElementById("job-edit-max-runs").value;
      body.max_runs = maxRunsRaw ? parseInt(maxRunsRaw, 10) : null;
      if (kind === "once") {
        const runAt = isoFromDateTimeInputs();
        if (!runAt) {
          setStatus("تاریخ و ساعت را برای اجرای یک‌بار پر کنید");
          return;
        }
        body.run_at = runAt;
      }
      try {
        if (state.jobDialogCreateMode || !jobId) {
          if (!state.projectId) return;
          await api(`/api/projects/${state.projectId}/jobs/create/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          });
          state.jobDialogCreateMode = false;
        } else {
          await patchJob(jobId, body);
        }
        el.dialogJob.close();
        await loadJobsForProject(state.projectId);
        setStatus("زمان‌بندی ذخیره شد");
      } catch (err) {
        setStatus(err.message);
      }
    };
  }

  el.btnNewProject.onclick = () => {
    if (el.formProject) el.formProject.reset();
    if (el.projectRootPath) el.projectRootPath.value = "";
    loadPathPicker("").catch((e) => setStatus(e.message));
    el.dialogProject.showModal();
  };
  el.cancelProject.onclick = () => el.dialogProject.close();
  if (el.pathPickerUp) {
    el.pathPickerUp.onclick = () => {
      const parent = el.pathPickerUp.dataset.parent;
      if (parent) loadPathPicker(parent).catch((e) => setStatus(e.message));
    };
  }
  if (el.btnNewScheduledJob) {
    el.btnNewScheduledJob.onclick = () => openJobCreator();
  }
  if (el.permissionAllow) {
    el.permissionAllow.onclick = () => respondPermission(true);
  }
  if (el.permissionDeny) {
    el.permissionDeny.onclick = () => respondPermission(false);
  }
  if (el.userInputPanelSubmit) {
    el.userInputPanelSubmit.onclick = () => submitUserInput(false);
  }
  if (el.userInputPanelCancel) {
    el.userInputPanelCancel.onclick = () => submitUserInput(true);
  }
  if (el.userInputPanelDismiss) {
    el.userInputPanelDismiss.onclick = () => clearUserInputForConversation(state.conversationId);
  }
  if (el.send) {
    el.send.addEventListener("click", (ev) => {
      if (state.busy && el.send.classList.contains("send-btn--stop")) {
        ev.preventDefault();
        requestAgentStop();
      }
    });
  }
  el.formProject.onsubmit = async (e) => {
    e.preventDefault();
    try {
      const fd = new FormData(el.formProject);
      const created = await api("/api/projects/create/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: fd.get("name"),
          root_path: fd.get("root_path"),
        }),
      });
      el.dialogProject.close();
      el.formProject.reset();
      await fetchProjects();
      if (created.project && created.project.id) {
        await selectProject(created.project.id);
      }
    } catch (err) {
      setStatus("خطا در ایجاد پروژه: " + err.message);
    }
  };

  function handleStreamChatEvent(event, assistantElRef, streamConversationId, streamOutcome) {
    const streamConvId = Number(streamConversationId);
    if (
      streamConvId &&
      state.conversationId &&
      Number(state.conversationId) !== streamConvId
    ) {
      return assistantElRef.el;
    }
    let assistantEl = assistantElRef.el;
    if (event.type === "run_started" && event.run_id) {
      state.activeRunId = event.run_id;
      return assistantEl;
    }
    if (event.type === "phase") {
      showPhase(event);
      addPhaseLogEntry(event);
    }
    if (event.type === "focus_inferred" && event.paths && event.paths.length) {
      addPhaseLogEntry({
        type: "phase",
        phase: "focus_auto",
        label: "محدودهٔ focus (خودکار)",
        detail: event.detail || event.paths.join("، "),
      });
    }
    if (event.type === "thinking" && event.content) {
      addThinkingBlock(event.content);
      const thinkingPhase = {
        type: "phase",
        phase: "thinking",
        label: "فاز thinking",
        detail: "تحلیل انجام شد",
      };
      showPhase(thinkingPhase);
      addPhaseLogEntry(thinkingPhase);
    }
    if (event.type === "permission_request") {
      showPermissionDialog(event);
    }
    if (event.type === "permission_resolved") {
      if (event.approved && el.dialogPermission?.open) {
        el.dialogPermission.close();
      } else if (!event.approved || event.timed_out) {
        if (el.dialogPermission?.open) el.dialogPermission.close();
      }
    }
    if (event.type === "user_input_request") {
      showUserInputSurface(event, streamConversationId);
    }
    if (event.type === "user_input_resolved") {
      if (event.timed_out) {
        setStatus("زمان فرم تمام شد — دوباره فیلدها را پر کنید.");
        if (streamConversationId) clearUserInputForConversation(streamConversationId);
      } else if (event.cancelled) {
        if (streamConversationId) clearUserInputForConversation(streamConversationId);
        if (state.stopRequested) setStatus("متوقف شد");
      } else if (state.userInputAwaitingServer) {
        if (streamConversationId) clearUserInputForConversation(streamConversationId);
      }
    }
    if (event.type === "tool_end") {
      if (event.tool === "ask_user") state.streamHadAskUser = true;
      addToolCard(event);
      if (event.tool && RESOURCE_MUTATING_TOOLS.has(event.tool)) {
        refreshResourcePanelsQuiet();
      }
    }
    if (event.type === "error") throw new Error(event.reply || event.error);
    if (event.type === "done" && streamOutcome) {
      streamOutcome.gotDone = true;
    }
    if (event.type === "done") {
      if (!assistantEl) {
        assistantEl = state.streamingAssistantEl || addMessage("assistant", event.reply || "");
      } else {
        setMessageText(assistantEl, event.reply || "");
      }
      if (replyPromisedUserForm(event.reply) && !state.streamHadAskUser) {
        showUserInputSurface(
          defaultSshUserInputEvent(
            "ایجنت فرم را فراخوانی نکرد؛ لطفاً اطلاعات سرور را در باکس بالای ورودی چت پر کنید."
          ),
          streamConversationId
        );
      }
      assistantEl.classList.remove("assistant-in-progress");
      state.streamingAssistantEl = null;
      if (event.stopped_by_user) {
        setStatus("متوقف شد");
      }
    }
    if (event.type === "saved") {
      if (streamOutcome) streamOutcome.saved = true;
      if (event.assistant_message_id && assistantEl) {
        attachCodeChangesButton(assistantEl, event.assistant_message_id);
      }
      if (event.usage && event.usage.total_credits && !isByokModelSelected()) {
        el.log.appendChild(createCreditsChatNode(event.usage));
        pinAgentActivityIndicatorLast();
        syncChatHeadVisibility();
      }
      if (event.wallet) applyWalletFromPayload(event.wallet);
      if (event.usage && event.usage.total_credits && !isByokModelSelected()) {
        setStatus(`ذخیره شد`);
      } else if (!state.stopRequested) {
        setStatus("ذخیره شد");
      }
    }
    assistantElRef.el = assistantEl;
    return assistantEl;
  }

  const STREAM_IDLE_TIMEOUT_MS = 15 * 60 * 1000;

  async function sendStream(message, streamConversationId) {
    const streamConvId = Number(streamConversationId || state.conversationId);
    if (!streamConvId) throw new Error("مکالمه انتخاب نشده است");
    state.activeRunId = null;
    state.stopRequested = false;
    state.streamHadAskUser = false;
    state.streamingAssistantEl = createStreamingAssistantShell();
    setAgentActivityIndicator(true);
    setStatus("در حال اجرا…", { persistent: true });
    const streamOutcome = { saved: false, gotDone: false };
    const res = await fetch("/api/chat/stream/", {
      method: "POST",
      headers: apiHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        conversation_id: streamConvId,
        message,
        options: optionsPayload(),
      }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const msg =
        res.status === 409
          ? data.reply || "یک پاسخ دیگر در حال اجراست."
          : data.reply || data.error || "خطا";
      throw new Error(msg);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    const assistantRef = { el: state.streamingAssistantEl };
    let lastStreamActivityAt = Date.now();
    const idleWatch = window.setInterval(() => {
      if (Date.now() - lastStreamActivityAt < STREAM_IDLE_TIMEOUT_MS) return;
      reader.cancel().catch(() => {});
    }, 5000);
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        lastStreamActivityAt = Date.now();
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data:")) continue;
          lastStreamActivityAt = Date.now();
          const event = JSON.parse(line.slice(5).trim());
          handleStreamChatEvent(event, assistantRef, streamConvId, streamOutcome);
        }
      }
      if (!streamOutcome.saved) {
        throw new Error(
          streamOutcome.gotDone
            ? "پاسخ ذخیره نشد"
            : "اتصال قطع شد یا پاسخ کامل نشد"
        );
      }
    } finally {
      window.clearInterval(idleWatch);
      if (state.streamingAssistantEl) {
        state.streamingAssistantEl.classList.remove("assistant-in-progress");
      }
      if (streamOutcome.saved) {
        state.streamingAssistantEl = null;
      }
      setAgentActivityIndicator(false);
      state.activeRunId = null;
    }
  }

  async function sendClassic(message) {
    setStatus("در حال اجرا…");
    state.streamingAssistantEl = createStreamingAssistantShell();
    setAgentActivityIndicator(true);
    try {
      const data = await api("/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: state.conversationId,
          message,
          options: optionsPayload(),
        }),
      });
      (data.phase_log || []).forEach((p) => {
        if (p.type === "phase") addPhaseLogEntry(p);
      });
      if (data.inferred_scope_paths && data.inferred_scope_paths.length) {
        addPhaseLogEntry({
          type: "phase",
          phase: "focus_auto",
          label: "محدودهٔ focus (خودکار)",
          detail: data.inferred_scope_paths.join("، "),
        });
      }
      if (data.thinking) addThinkingBlock(data.thinking);
      const bubble = state.streamingAssistantEl || addMessage("assistant", data.reply || "");
      setMessageText(bubble, data.reply || "");
      if (data.assistant_message_id) {
        attachCodeChangesButton(bubble, data.assistant_message_id);
      }
      (data.tool_steps || []).forEach(addToolCard);
      if (data.wallet) applyWalletFromPayload(data.wallet);
      if (data.usage && data.usage.total_credits && !isByokModelSelected()) {
        el.log.appendChild(createCreditsChatNode(data.usage));
        pinAgentActivityIndicatorLast();
        syncChatHeadVisibility();
      }
      setStatus("ذخیره شد");
    } finally {
      if (state.streamingAssistantEl) {
        state.streamingAssistantEl.classList.remove("assistant-in-progress");
      }
      state.streamingAssistantEl = null;
      setAgentActivityIndicator(false);
    }
  }

  el.form.onsubmit = async (e) => {
    e.preventDefault();
    if (!state.conversationId) return;
    if (state.busy) {
      setStatus("صبر کنید تا پاسخ فعلی تمام شود.");
      return;
    }
    const message = buildOutboundMessage(el.input.value);
    if (!message) return;
    if (isContextFull(message)) {
      setStatus("کانتکست پر است — مکالمهٔ جدید بسازید.");
      return;
    }
    const convId = state.conversationId;
    addMessage("user", message);
    state.convMessageSent = true;
    state.sessionCreatedConvId = null;
    clearUserInputForConversation(state.conversationId);
    state.busy = true;
    syncPhaseLogPanelVisibility();
    setUndoButtonsDisabled(true);
    resetComposerAfterSend();
    setComposerBusyMode(true);
    el.toolTrace.innerHTML = "";
    syncLiveExecPanel();
    try {
      await sendStream(message);
      const refreshed = await api(`/api/conversations/${state.conversationId}/`);
      state.conversation = refreshed.conversation;
      el.chatTitle.textContent = state.conversation.title;
      renderConversationView(state.conversation);
      if (state.sidePanelMode === "changes") {
        loadConversationCodeChanges().catch(() => {});
      }
      if (state.projectId) {
        await loadJobsForProject(state.projectId);
        await loadJobRunsForProject(state.projectId);
      }
      await loadConversationTools();
    } catch (err) {
      addMessage("assistant", "خطا: " + err.message);
      setStatus("");
    } finally {
      state.busy = false;
      syncPhaseLogPanelVisibility();
      state.stopRequested = false;
      state.activeRunId = null;
      setAgentActivityIndicator(false);
      setUndoButtonsDisabled(false);
      setComposerBusyMode(false);
      if (el.dialogPermission?.open) el.dialogPermission.close();
      refreshUserInputPanel();
      syncLiveExecPanel();
      loadTree();
    }
  };

  if (el.btnCopyToolTrace) {
    el.btnCopyToolTrace.onclick = () =>
      copyToolTraceOutputs().catch((e) => setStatus(e.message));
  }
  if (el.btnAttachTool) {
    el.btnAttachTool.onclick = () =>
      attachConversationTool().catch((e) => setStatus(e.message));
  }
  if (el.resourceDetailVersion) {
    el.resourceDetailVersion.onchange = () =>
      onResourceVersionSelectChange().catch((e) => setStatus(e.message));
  }
  if (el.resourceDetailClose) {
    el.resourceDetailClose.onclick = () => el.dialogResourceDetail?.close();
  }
  if (el.resourceDetailCopyLink) {
    el.resourceDetailCopyLink.onclick = () => {
      const link = state.resourceModal.shareLink || state.resourceModal.tool?.share_link || "";
      if (link) copyText(link);
      else setStatus("لینک منبع موجود نیست");
    };
  }
  if (el.toolLinkInput) {
    el.toolLinkInput.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        attachConversationTool().catch((e) => setStatus(e.message));
      }
    });
  }

  async function bootstrap() {
    initStatusMascot();
    initModelSelect();
    initComposerOptionsUi();
    initSidePanelToggle();
    initPanelExpandControls();
    initUserFileAccessSettings();
    initSettingsUi();
    initRemoteServerSettingsUi();
    updateComposerOptionsEnabled(false);
    const cfg = window.APP_CONFIG || {};
    if (cfg.wallet) {
      let w = cfg.wallet;
      if (typeof w === "string") {
        try {
          w = JSON.parse(w);
        } catch {
          w = null;
        }
      }
      applyWalletFromPayload(w);
    }
    if (el.btnLogout) {
      el.btnLogout.onclick = () => {
        fetch("/api/auth/logout/", { method: "POST" }).finally(() => {
          window.location.href = "/login/";
        });
      };
    }
    setStatus("در حال بارگذاری…");
    if (window.APP_CONFIG && window.APP_CONFIG.apiTokenRequired) {
      if (!localStorage.getItem("aca_api_token")) {
        const t = prompt("توکن API (X-ACA-Token) را وارد کنید:");
        if (t) localStorage.setItem("aca_api_token", t.trim());
      }
    }
    await Promise.all([loadAgents(), fetchProjects()]);
    if (state.projects.length) {
      const pendingProjId =
        window.APP_CONFIG && window.APP_CONFIG.pendingToolProjectId
          ? Number(window.APP_CONFIG.pendingToolProjectId)
          : null;
      const saved = parseInt(localStorage.getItem(LS_PROJECT), 10);
      const exists = state.projects.some((p) => p.id === saved);
      const pendingOk =
        pendingProjId && state.projects.some((p) => p.id === pendingProjId);
      const initialId = pendingOk ? pendingProjId : exists ? saved : state.projects[0].id;
      if (pendingOk) window.APP_CONFIG.pendingToolProjectId = null;
      await selectProject(initialId);
    } else {
      renderAgentNewButtons();
    }
    setStatus("");
  }

  bootstrap().catch((e) => setStatus("خطا در بارگذاری: " + e.message));
})();
