/* global hljs */
(() => {
  const LANG_BY_EXT = {
    py: "python",
    js: "javascript",
    mjs: "javascript",
    ts: "typescript",
    tsx: "typescript",
    jsx: "javascript",
    json: "json",
    html: "html",
    htm: "html",
    css: "css",
    scss: "scss",
    md: "markdown",
    sh: "bash",
    bash: "bash",
    zsh: "bash",
    yml: "yaml",
    yaml: "yaml",
    xml: "xml",
    sql: "sql",
    go: "go",
    rs: "rust",
    java: "java",
    kt: "kotlin",
    rb: "ruby",
    php: "php",
    c: "c",
    h: "c",
    cpp: "cpp",
    cc: "cpp",
    cs: "csharp",
    swift: "swift",
    dockerfile: "dockerfile",
    toml: "ini",
    ini: "ini",
  };

  const LANG_LABELS = {
    python: "Python",
    javascript: "JavaScript",
    typescript: "TypeScript",
    json: "JSON",
    bash: "Bash",
    yaml: "YAML",
    markdown: "Markdown",
    plaintext: "Plain text",
  };

  function langFromPath(path) {
    if (!path) return "plaintext";
    const base = String(path).split("/").pop() || "";
    const dot = base.lastIndexOf(".");
    if (dot < 0) return "plaintext";
    const ext = base.slice(dot + 1).toLowerCase();
    if (ext === "dockerfile" || base.toLowerCase() === "dockerfile") return "dockerfile";
    return LANG_BY_EXT[ext] || "plaintext";
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function highlightCode(code, lang) {
    const text = code || "";
    if (typeof hljs === "undefined") return escapeHtml(text);
    const language = lang && hljs.getLanguage(lang) ? lang : "plaintext";
    try {
      return hljs.highlight(text, { language, ignoreIllegals: true }).value;
    } catch {
      return escapeHtml(text);
    }
  }

  function langDisplayName(lang) {
    const key = (lang || "plaintext").toLowerCase();
    return LANG_LABELS[key] || key.charAt(0).toUpperCase() + key.slice(1);
  }

  function attachCodeBlockCopy(btn, rawCode) {
    btn.addEventListener("click", async () => {
      const text = rawCode || "";
      try {
        await navigator.clipboard.writeText(text);
        const prev = btn.textContent;
        btn.textContent = "کپی شد";
        setTimeout(() => {
          btn.textContent = prev;
        }, 1600);
      } catch {
        btn.textContent = "خطا";
      }
    });
  }

  function createCodeBlock(rawCode, lang) {
    const language = lang && lang !== "plaintext" ? lang : "plaintext";
    const wrap = document.createElement("div");
    wrap.className = "md-code-block ltr-block";
    const head = document.createElement("div");
    head.className = "md-code-block__head";
    const langEl = document.createElement("span");
    langEl.className = "md-code-block__lang";
    langEl.textContent = langDisplayName(language);
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "btn btn-tiny md-code-block__copy";
    copyBtn.textContent = "کپی";
    attachCodeBlockCopy(copyBtn, rawCode);
    head.appendChild(langEl);
    head.appendChild(copyBtn);
    const pre = document.createElement("pre");
    const code = document.createElement("code");
    code.className = `hljs language-${language}`;
    code.innerHTML = highlightCode(rawCode, language);
    pre.appendChild(code);
    wrap.appendChild(head);
    wrap.appendChild(pre);
    return wrap;
  }

  function renderMarkdown(text) {
    const src = text || "";
    const parts = [];
    const re = /```(\w*)\n?([\s\S]*?)```/g;
    let last = 0;
    let m;
    while ((m = re.exec(src)) !== null) {
      if (m.index > last) {
        parts.push({ kind: "text", body: src.slice(last, m.index) });
      }
      parts.push({ kind: "code", lang: m[1] || "", body: m[2].replace(/\n$/, "") });
      last = m.index + m[0].length;
    }
    if (last < src.length) parts.push({ kind: "text", body: src.slice(last) });

    const out = document.createElement("div");
    out.className = "md-root";

    parts.forEach((part) => {
      if (part.kind === "code") {
        out.appendChild(createCodeBlock(part.body, part.lang || "plaintext"));
        return;
      }
      const lines = part.body.split("\n");
      let paraBuf = [];
      const flushPara = () => {
        if (!paraBuf.length) return;
        const p = document.createElement("p");
        p.className = "md-p";
        p.innerHTML = inlineMarkdown(paraBuf.join("\n"));
        out.appendChild(p);
        paraBuf = [];
      };
      lines.forEach((line) => {
        const h = line.match(/^(#{1,6})\s+(.+)$/);
        if (h) {
          flushPara();
          const level = h[1].length;
          const el = document.createElement(`h${Math.min(level, 6)}`);
          el.className = `md-h md-h${level}`;
          el.innerHTML = inlineMarkdown(h[2]);
          out.appendChild(el);
          return;
        }
        if (/^[-*]\s+/.test(line.trim())) {
          flushPara();
          const li = document.createElement("div");
          li.className = "md-li";
          li.innerHTML = "• " + inlineMarkdown(line.replace(/^[-*]\s+/, ""));
          out.appendChild(li);
          return;
        }
        if (!line.trim()) {
          flushPara();
          return;
        }
        paraBuf.push(line);
      });
      flushPara();
    });
    return out;
  }

  function inlineMarkdown(line) {
    let s = escapeHtml(line);
    s = s.replace(/`([^`]+)`/g, (_, c) => `<code class="md-inline-code">${escapeHtml(c)}</code>`);
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    return s;
  }

  function renderHighlightedLines(content, lang) {
    const wrap = document.createElement("div");
    wrap.className = "code-lines hljs-root ltr-block";
    const lines = (content || "").split("\n");
    lines.forEach((line) => {
      const row = document.createElement("div");
      row.className = "preview-line";
      const code = document.createElement("code");
      code.className = `preview-code language-${lang}`;
      code.innerHTML = highlightCode(line, lang);
      row.appendChild(code);
      wrap.appendChild(row);
    });
    return wrap;
  }

  window.AcaRender = {
    langFromPath,
    langDisplayName,
    highlightCode,
    renderMarkdown,
    renderHighlightedLines,
    createCodeBlock,
    escapeHtml,
  };
})();
