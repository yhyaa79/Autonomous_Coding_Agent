"""منطق مشترک SEO — توسط فایل‌های ابزار import می‌شود."""

import json
import re
from html.parser import HTMLParser
from typing import Any

from agent.options import AgentOptions
from agent.tool_impl import read_file, tool_result, write_file
from agent.workspace import WorkspaceError, resolve_in_workspace


class SeoHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.in_title = False
        self.meta: list[dict[str, str]] = []
        self.h1: list[str] = []
        self.h2: list[str] = []
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.canonical = ""
        self.lang = ""
        self._heading: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = {k: (v or "") for k, v in attrs}
        if tag == "html" and ad.get("lang"):
            self.lang = ad["lang"]
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            self.meta.append(
                {
                    "name": ad.get("name", ""),
                    "property": ad.get("property", ""),
                    "content": ad.get("content", ""),
                }
            )
        if tag == "link" and ad.get("rel", "").lower() == "canonical":
            self.canonical = ad.get("href", "")
        if tag in ("h1", "h2"):
            self._heading = tag
        if tag == "a" and ad.get("href"):
            self.links.append({"href": ad["href"], "text": ""})
        if tag == "img":
            self.images.append({"src": ad.get("src", ""), "alt": ad.get("alt", "")})

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag in ("h1", "h2"):
            self._heading = None

    def handle_data(self, data: str) -> None:
        t = data.strip()
        if not t:
            return
        if self.in_title:
            self.title += t
        if self._heading == "h1":
            self.h1.append(t)
        elif self._heading == "h2":
            self.h2.append(t)


def parse_html_seo(html: str) -> dict[str, Any]:
    p = SeoHtmlParser()
    try:
        p.feed(html)
    except Exception as exc:
        return {"parse_error": str(exc)}
    desc = ""
    robots = ""
    og: dict[str, str] = {}
    for m in p.meta:
        name = (m.get("name") or "").lower()
        prop = (m.get("property") or "").lower()
        content = m.get("content") or ""
        if name == "description":
            desc = content
        if name == "robots":
            robots = content
        if prop.startswith("og:"):
            og[prop] = content
    imgs_no_alt = [i for i in p.images if i.get("src") and not (i.get("alt") or "").strip()]
    issues: list[str] = []
    if not p.title.strip():
        issues.append("missing_title")
    elif len(p.title) > 60:
        issues.append("title_too_long")
    if not desc:
        issues.append("missing_meta_description")
    elif len(desc) > 160:
        issues.append("meta_description_too_long")
    if not p.h1:
        issues.append("missing_h1")
    elif len(p.h1) > 1:
        issues.append("multiple_h1")
    if imgs_no_alt:
        issues.append("images_missing_alt")
    if not p.canonical:
        issues.append("missing_canonical")
    return {
        "title": p.title.strip(),
        "meta_description": desc,
        "meta_robots": robots,
        "lang": p.lang,
        "canonical": p.canonical,
        "h1": p.h1[:5],
        "h2_count": len(p.h2),
        "og_tags": og,
        "internal_links_sample": p.links[:15],
        "images_total": len(p.images),
        "images_missing_alt": len(imgs_no_alt),
        "issues": issues,
    }


def analyze_html_file(path: str, options: AgentOptions) -> str:
    root = options.workspace_path()
    try:
        resolve_in_workspace(root, path)
    except WorkspaceError as e:
        return tool_result(False, str(e))
    raw = read_file(path, 1, None, 800, options)
    if raw.startswith("Error:"):
        return tool_result(False, raw)
    lines = []
    for line in raw.splitlines():
        if "|" in line[:8]:
            parts = line.split("|", 1)
            if len(parts) == 2 and parts[0].strip().isdigit():
                lines.append(parts[1])
            else:
                lines.append(line)
        else:
            lines.append(line)
    html = "\n".join(lines)
    report = parse_html_seo(html)
    report["path"] = path
    return tool_result(True, json.dumps(report, ensure_ascii=False, indent=2))


def audit_site_basics(options: AgentOptions) -> str:
    root = options.workspace_path()
    findings: dict[str, Any] = {"root": str(root), "checks": []}

    def check_file(rel: str, label: str) -> None:
        p = root / rel
        findings["checks"].append(
            {
                "label": label,
                "path": rel,
                "exists": p.is_file(),
                "size": p.stat().st_size if p.is_file() else 0,
            }
        )

    for rel, label in [
        ("robots.txt", "robots.txt"),
        ("sitemap.xml", "sitemap.xml"),
        ("sitemap_index.xml", "sitemap index"),
    ]:
        check_file(rel, label)

    template_globs = list(root.glob("**/*.html"))[:40]
    findings["html_files_sample"] = [str(p.relative_to(root)) for p in template_globs]
    return tool_result(True, json.dumps(findings, ensure_ascii=False, indent=2))


def keyword_density(text: str, keywords: list[str]) -> dict[str, Any]:
    lowered = text.lower()
    words = re.findall(r"[\w\u0600-\u06ff]+", lowered, flags=re.UNICODE)
    total = len(words) or 1
    out: dict[str, Any] = {"word_count": len(words), "keywords": {}}
    for kw in keywords:
        k = kw.strip().lower()
        if not k:
            continue
        count = lowered.count(k)
        out["keywords"][kw] = {
            "occurrences": count,
            "density_percent": round(100.0 * count / total, 3),
        }
    return out


def analyze_content_seo(path: str, keywords: list[str], options: AgentOptions) -> str:
    root = options.workspace_path()
    try:
        resolve_in_workspace(root, path)
    except WorkspaceError as e:
        return tool_result(False, str(e))
    raw = read_file(path, 1, None, 600, options)
    text = re.sub(r"^\s*\d+\|", "", raw, flags=re.MULTILINE)
    text_plain = re.sub(r"<[^>]+>", " ", text)
    density = keyword_density(text_plain, keywords)
    headings = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", text, flags=re.I | re.S)
    headings_clean = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip() for h in headings[:12]]
    payload = {
        "path": path,
        "keyword_density": density,
        "headings_sample": headings_clean,
        "tip": "هدف: یک H1، توضیح متا ۱۵۰–۱۶۰ کاراکتر، تراکم کلیدواژه طبیعی (بدون stuffing).",
    }
    return tool_result(True, json.dumps(payload, ensure_ascii=False, indent=2))


def save_seo_report(title: str, markdown_body: str, options: AgentOptions) -> str:
    safe = re.sub(r"[^\w\u0600-\u06ff\-]+", "-", title.strip())[:60] or "seo-report"
    rel = f"seo-reports/{safe}.md"
    content = f"# {title}\n\n{markdown_body.strip()}\n"
    return write_file(rel, content, options)
