#!/usr/bin/env python3
"""One-off patcher for chat app.js retry/stream/context fixes."""
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "chat/static/chat/app.js"


def main() -> None:
    text = APP.read_text(encoding="utf-8")

    retry_block = """
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

"""

    if "function attachRetryButton" not in text:
        marker = "  function attachUndoButton(div, messageId) {"
        if marker not in text:
            raise SystemExit("attachUndo marker missing")
        text = text.replace(marker, retry_block + marker, 1)

    if 'syncContextRing(el.input?.value || "");' not in text.split("function renderConversationView")[1].split("function applyMessageActions")[0]:
        text = text.replace(
            "    refreshUserInputPanel();\n  }\n\n  function applyMessageActions(div, meta) {",
            '    refreshUserInputPanel();\n    syncContextRing(el.input?.value || "");\n  }\n\n  function applyMessageActions(div, meta) {',
            1,
        )

    if "صبر کنید تا اجرای فعلی تمام شود" not in text:
        text = text.replace(
            "  async function selectConversation(id, opts = {}) {\n    const cid = Number(id);\n    if (!cid) return;\n    try {\n      if (!opts.skipDiscard && state.conversationId && state.conversationId !== cid) {",
            "  async function selectConversation(id, opts = {}) {\n    const cid = Number(id);\n    if (!cid) return;\n    try {\n      if (\n        state.busy &&\n        state.conversationId &&\n        Number(state.conversationId) !== cid &&\n        !opts.skipDiscard\n      ) {\n        setStatus(\"صبر کنید تا اجرای فعلی تمام شود.\");\n        return;\n      }\n      if (!opts.skipDiscard && state.conversationId && state.conversationId !== cid) {",
            1,
        )

    if "streamOutcome" not in text:
        text = text.replace(
            "  function handleStreamChatEvent(event, assistantElRef, streamConversationId) {\n    let assistantEl = assistantElRef.el;",
            "  function handleStreamChatEvent(event, assistantElRef, streamConversationId, streamOutcome) {\n    const streamConvId = Number(streamConversationId);\n    if (\n      streamConvId &&\n      state.conversationId &&\n      Number(state.conversationId) !== streamConvId\n    ) {\n      return assistantElRef.el;\n    }\n    let assistantEl = assistantElRef.el;",
            1,
        )
        text = text.replace(
            '    if (event.type === "error") throw new Error(event.reply || event.error);\n    if (event.type === "done") {',
            '    if (event.type === "error") throw new Error(event.reply || event.error);\n    if (event.type === "done" && streamOutcome) {\n      streamOutcome.gotDone = true;\n    }\n    if (event.type === "done") {',
            1,
        )
        text = text.replace(
            '    if (event.type === "saved") {\n      if (event.can_undo && event.assistant_message_id && assistantEl) {',
            '    if (event.type === "saved") {\n      if (streamOutcome) streamOutcome.saved = true;\n      if (event.can_undo && event.assistant_message_id && assistantEl) {',
            1,
        )

        start = text.find("  async function sendStream(message, streamConversationId) {")
        end = text.find("  async function sendClassic(message) {")
        if start < 0 or end < 0:
            raise SystemExit("sendStream bounds missing")
        new_send = '''  async function sendStream(message, streamConversationId) {
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
      throw new Error(data.reply || data.error || "خطا");
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    const assistantRef = { el: state.streamingAssistantEl };
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data:")) continue;
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

'''
        text = text[:start] + new_send + text[end:]

    if "const convId = state.conversationId;" not in text.split("el.form.onsubmit")[1][:900]:
        text = text.replace(
            "    if (!message) return;\n    addMessage(\"user\", message);",
            '    if (!message) return;\n    if (isContextFull(message)) {\n      setStatus("کانتکست پر است — مکالمهٔ جدید بسازید.");\n      return;\n    }\n    const convId = state.conversationId;\n    addMessage("user", message);',
            1,
        )

    if "handleTurnFailure(err, { message, conversationId: convId" not in text:
        text = text.replace(
            """    try {
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
""",
            """    try {
      await sendStream(message, convId);
      await refreshConversationAfterTurn();
      setStatus("ذخیره شد");
    } catch (err) {
      handleTurnFailure(err, { message, conversationId: convId, assistantEl: null });
    } finally {
""",
            1,
        )

    if 'el.input.addEventListener("keydown"' not in text:
        text = text.replace(
            '  el.input.addEventListener("paste", (ev) => {',
            '''  if (el.input) {
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

  el.input.addEventListener("paste", (ev) => {''',
            1,
        )

    inp_marker = '  el.input.addEventListener("input", () => {\n    resizeComposerInput();\n    if ('
    if "syncContextRing(el.input.value" not in text.split(inp_marker)[1][:80] if inp_marker in text else True:
        text = text.replace(
            inp_marker,
            '  el.input.addEventListener("input", () => {\n    resizeComposerInput();\n    syncContextRing(el.input.value || "");\n    if (',
            1,
        )

    if "handleTurnFailure(err, { message: followUp" not in text:
        text = text.replace(
            """      try {
        await sendStream(followUp);
        const refreshed = await api(`/api/conversations/${state.conversationId}/`);
        state.conversation = refreshed.conversation;
        el.chatTitle.textContent = state.conversation.title;
        renderConversationView(state.conversation);
      } catch (err) {
        addMessage("assistant", "خطا: " + err.message);
      } finally {
""",
            """      const convId = state.conversationId;
      try {
        await sendStream(followUp, convId);
        await refreshConversationAfterTurn();
        setStatus("ذخیره شد");
      } catch (err) {
        handleTurnFailure(err, { message: followUp, conversationId: convId, assistantEl: null });
      } finally {
""",
            1,
        )

    APP.write_text(text, encoding="utf-8")
    print("patched", APP)


if __name__ == "__main__":
    main()
