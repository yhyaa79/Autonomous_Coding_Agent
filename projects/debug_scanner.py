"""اسکن خودکار صفحهٔ وب برای پنل دیباگ ACA (بدون مرورگر headless)."""

from __future__ import annotations

import re
import time
import uuid
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

MAX_BODY_BYTES = 1_500_000
FETCH_TIMEOUT = 30
MAX_LINK_CHECKS = 12

DEBUG_CATEGORIES: tuple[dict[str, str], ...] = (
    {
        "id": "ui",
        "label": "رابط کاربری (UI)",
        "hint": "viewport، عنوان، تصاویر، ساختار بصری",
    },
    {
        "id": "ux",
        "label": "تجربه کاربری (UX)",
        "hint": "زبان، لینک‌های خالی، فرم‌ها، خوانایی",
    },
    {
        "id": "backend",
        "label": "بک‌اند / شبکه",
        "hint": "کد HTTP، زمان پاسخ، هدرهای سرور",
    },
    {
        "id": "functional",
        "label": "عملکردی / خطا",
        "hint": "لینک‌های شکسته، منابع ناموفق",
    },
    {
        "id": "security",
        "label": "امنیت",
        "hint": "HTTPS، هدرهای حفاظتی، محتوای حساس",
    },
    {
        "id": "performance",
        "label": "کارایی",
        "hint": "حجم صفحه، تعداد اسکریپت و استایل",
    },
    {
        "id": "accessibility",
        "label": "دسترسی‌پذیری (a11y)",
        "hint": "lang، سرفصل‌ها، alt، label",
    },
    {
        "id": "seo",
        "label": "SEO",
        "hint": "meta، canonical، robots",
    },
)

DEFAULT_CATEGORY_IDS: tuple[str, ...] = tuple(c["id"] for c in DEBUG_CATEGORIES)


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.meta: dict[str, str] = {}
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []
        self.h1_count = 0
        self.forms: list[dict[str, Any]] = []
        self._current_form: dict[str, Any] | None = None
        self.inputs_without_label = 0
        self._input_ids: set[str] = set()
        self.labels_for: set[str] = set()
        self.html_lang = ""
        self.has_viewport = False
        self.inline_styles = 0
        self.http_in_src = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k.lower(): (v or "") for k, v in attrs}
        t = tag.lower()
        if t == "html":
            self.html_lang = attr.get("lang", "").strip()
        if t == "title":
            self._in_title = True
        if t == "meta":
            name = (attr.get("name") or attr.get("property") or "").lower()
            content = attr.get("content", "")
            if name:
                self.meta[name] = content
            if attr.get("name", "").lower() == "viewport" or "viewport" in attr.get("content", "").lower():
                self.has_viewport = True
        if t == "h1":
            self.h1_count += 1
        if t == "a":
            self.links.append({"href": attr.get("href", ""), "text": ""})
        if t == "img":
            self.images.append({"src": attr.get("src", ""), "alt": attr.get("alt", "")})
            src = attr.get("src", "")
            if src.startswith("http://"):
                self.http_in_src += 1
        if t == "script":
            src = attr.get("src", "")
            if src:
                self.scripts.append(src)
        if t == "link" and attr.get("rel", "").lower() == "stylesheet":
            self.stylesheets.append(attr.get("href", ""))
        if t == "form":
            self._current_form = {"inputs": 0, "has_action": bool(attr.get("action"))}
            self.forms.append(self._current_form)
        if t == "input" and self._current_form is not None:
            self._current_form["inputs"] += 1
            iid = attr.get("id", "").strip()
            if iid:
                self._input_ids.add(iid)
            itype = (attr.get("type") or "text").lower()
            if itype not in ("hidden", "submit", "button", "image"):
                if not attr.get("aria-label") and not attr.get("title"):
                    self.inputs_without_label += 1
        if t == "label":
            fr = attr.get("for", "").strip()
            if fr:
                self.labels_for.add(fr)
        if attr.get("style"):
            self.inline_styles += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
        if tag.lower() == "form":
            self._current_form = None

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self.links and not self.links[-1].get("_closed"):
            self.links[-1]["text"] = (self.links[-1].get("text") or "") + data

    def finalize_labels(self) -> int:
        missing = 0
        for iid in self._input_ids:
            if iid not in self.labels_for:
                missing += 1
        return missing + max(0, self.inputs_without_label - len(self.labels_for))


def _normalize_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        raise ValueError("آدرس صفحه خالی است")
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    parsed = urlparse(u)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("فقط http و https مجاز است")
    if not parsed.netloc:
        raise ValueError("آدرس نامعتبر است")
    return u


def _finding(
    category: str,
    severity: str,
    title: str,
    description: str,
    *,
    evidence: str = "",
    suggestion: str = "",
) -> dict[str, Any]:
    return {
        "id": uuid.uuid4().hex[:12],
        "category": category,
        "severity": severity,
        "title": title,
        "description": description,
        "evidence": evidence,
        "suggestion": suggestion,
    }


def _fetch_page(url: str) -> tuple[bytes, dict[str, str], float, int]:
    req = Request(
        url,
        headers={
            "User-Agent": "ACA-DebugScanner/1.0",
            "Accept": "text/html,application/xhtml+xml,application/json,*/*",
        },
    )
    start = time.perf_counter()
    try:
        with urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            code = int(getattr(resp, "status", None) or resp.getcode() or 0)
            raw = resp.read(MAX_BODY_BYTES + 1)
    except HTTPError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        headers = {k.lower(): v for k, v in (e.headers.items() if e.headers else [])}
        body = e.read(MAX_BODY_BYTES) if hasattr(e, "read") else b""
        return body, headers, elapsed_ms, int(e.code)
    except URLError as e:
        raise ValueError(f"دریافت صفحه ناموفق: {e}") from e
    elapsed_ms = (time.perf_counter() - start) * 1000
    return raw, headers, elapsed_ms, code


def _head_check(full_url: str) -> int | None:
    req = Request(full_url, method="HEAD", headers={"User-Agent": "ACA-DebugScanner/1.0"})
    try:
        with urlopen(req, timeout=12) as resp:
            return int(getattr(resp, "status", None) or resp.getcode() or 0)
    except HTTPError as e:
        return int(e.code)
    except URLError:
        return None


def run_page_debug_scan(
    url: str,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    """اسکن همگام؛ خروجی آمادهٔ ذخیره در DebugScan."""
    try:
        target = _normalize_url(url)
    except ValueError as e:
        return {
            "ok": False,
            "url": (url or "").strip(),
            "categories": categories or list(DEFAULT_CATEGORY_IDS),
            "findings": [],
            "metrics": {"url": (url or "").strip()},
            "summary": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
            },
            "error": str(e),
        }
    selected = [c for c in (categories or list(DEFAULT_CATEGORY_IDS)) if c in DEFAULT_CATEGORY_IDS]
    if not selected:
        selected = list(DEFAULT_CATEGORY_IDS)

    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {"url": target, "categories": selected}

    try:
        raw, headers, elapsed_ms, status_code = _fetch_page(target)
    except ValueError as e:
        return {
            "ok": False,
            "url": target,
            "categories": selected,
            "findings": [],
            "metrics": metrics,
            "summary": {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "error": str(e),
        }

    size_bytes = len(raw)
    metrics.update(
        {
            "status_code": status_code,
            "response_time_ms": round(elapsed_ms, 1),
            "size_bytes": size_bytes,
            "content_type": headers.get("content-type", ""),
        }
    )

    text = raw.decode("utf-8", errors="replace")
    parsed = urlparse(target)
    is_https = parsed.scheme == "https"

    if "backend" in selected:
        if status_code >= 500:
            findings.append(
                _finding(
                    "backend",
                    "critical",
                    "خطای سرور (۵xx)",
                    f"سرور با کد {status_code} پاسخ داد.",
                    evidence=f"HTTP {status_code}",
                    suggestion="لاگ سرور و traceback را بررسی کنید.",
                )
            )
        elif status_code >= 400:
            findings.append(
                _finding(
                    "backend",
                    "high",
                    "پاسخ خطای HTTP",
                    f"کد وضعیت {status_code} برای URL درخواست‌شده.",
                    evidence=f"HTTP {status_code}",
                    suggestion="مسیر، احراز هویت و ریدایرکت‌ها را چک کنید.",
                )
            )
        elif status_code >= 300:
            findings.append(
                _finding(
                    "backend",
                    "info",
                    "ریدایرکت",
                    f"پاسخ {status_code} — ممکن است عمدی باشد.",
                    evidence=f"HTTP {status_code}",
                )
            )
        if elapsed_ms > 3000:
            findings.append(
                _finding(
                    "backend",
                    "medium",
                    "زمان پاسخ بالا",
                    f"بارگذاری اولیه حدود {elapsed_ms:.0f}ms طول کشید.",
                    suggestion="کش CDN، فشرده‌سازی و بهینه‌سازی بک‌اند را بررسی کنید.",
                )
            )
        server = headers.get("server", "")
        if server:
            findings.append(
                _finding(
                    "backend",
                    "info",
                    "هدر Server",
                    "نسخهٔ سرور در پاسخ قابل مشاهده است.",
                    evidence=server[:120],
                    suggestion="در production نمایش جزئیات سرور را محدود کنید.",
                )
            )

    if "security" in selected:
        if not is_https:
            findings.append(
                _finding(
                    "security",
                    "high",
                    "اتصال غیر HTTPS",
                    "صفحه روی HTTP بارگذاری می‌شود.",
                    suggestion="گواهی SSL و ریدایرکت ۳۰۱ به HTTPS فعال کنید.",
                )
            )
        for hdr, label in (
            ("content-security-policy", "CSP"),
            ("x-frame-options", "X-Frame-Options"),
            ("x-content-type-options", "X-Content-Type-Options"),
            ("strict-transport-security", "HSTS"),
        ):
            if is_https and hdr == "strict-transport-security" and hdr not in headers:
                findings.append(
                    _finding(
                        "security",
                        "medium",
                        "HSTS تنظیم نشده",
                        "هدر Strict-Transport-Security در پاسخ HTTPS نیست.",
                        suggestion="HSTS را روی reverse proxy تنظیم کنید.",
                    )
                )
            elif hdr not in ("strict-transport-security",) and hdr not in headers:
                sev = "medium" if hdr == "content-security-policy" else "low"
                findings.append(
                    _finding(
                        "security",
                        sev,
                        f"هدر {label} موجود نیست",
                        f"هدر {hdr} در پاسخ HTTP دیده نشد.",
                        suggestion=f"هدر {label} را در وب‌سرور یا فریم‌ورک اضافه کنید.",
                    )
                )
        if re.search(r"(api[_-]?key|password|secret)\s*[:=]\s*['\"][^'\"]+['\"]", text, re.I):
            findings.append(
                _finding(
                    "security",
                    "critical",
                    "احتمال افشای secret در HTML",
                    "الگوی شبیه کلید/رمز در متن صفحه پیدا شد.",
                    suggestion="secrets را از فرانت‌اند حذف و فقط در سرور نگه دارید.",
                )
            )

    if "performance" in selected:
        if size_bytes > 800_000:
            findings.append(
                _finding(
                    "performance",
                    "medium",
                    "حجم پاسخ زیاد",
                    f"حدود {size_bytes // 1024}KB برای یک درخواست.",
                    suggestion="فشرده‌سازی Brotli/Gzip و تقسیم bundleها.",
                )
            )
        script_count = len(re.findall(r"<script\b", text, re.I))
        if script_count > 25:
            findings.append(
                _finding(
                    "performance",
                    "medium",
                    "اسکریپت‌های زیاد",
                    f"حدود {script_count} تگ script در HTML.",
                    suggestion="code splitting و defer/async.",
                )
            )

    parser = _PageParser()
    try:
        parser.feed(text[: min(len(text), 600_000)])
    except Exception:
        pass
    parser.title = parser.title.strip()

    if any(c in selected for c in ("ui", "ux", "accessibility", "seo")):
        if not parser.title:
            findings.append(
                _finding(
                    "ui",
                    "medium",
                    "عنوان صفحه (title) خالی",
                    "تگ title در HTML یافت نشد یا خالی است.",
                    suggestion="یک title کوتاه و توصیفی اضافه کنید.",
                )
            )
        elif len(parser.title) > 70 and "seo" in selected:
            findings.append(
                _finding(
                    "seo",
                    "low",
                    "title طولانی",
                    f"طول title حدود {len(parser.title)} کاراکتر است.",
                    evidence=parser.title[:80],
                    suggestion="title را زیر ~۶۰ کاراکتر نگه دارید.",
                )
            )

    if "ui" in selected and not parser.has_viewport:
        findings.append(
            _finding(
                "ui",
                "high",
                "meta viewport نیست",
                "برای موبایل meta viewport تعریف نشده.",
                suggestion='<meta name="viewport" content="width=device-width, initial-scale=1">',
            )
        )

    if "ux" in selected:
        if not parser.html_lang:
            findings.append(
                _finding(
                    "ux",
                    "medium",
                    "ویژگی lang روی html",
                    "زبان صفحه مشخص نیست — برای فارسی lang='fa' توصیه می‌شود.",
                )
            )
        empty_links = sum(
            1
            for lnk in parser.links
            if not (lnk.get("href") or "").strip() or (lnk.get("href") or "").strip() == "#"
        )
        if empty_links >= 3:
            findings.append(
                _finding(
                    "ux",
                    "low",
                    "لینک‌های بدون مقصد",
                    f"حدود {empty_links} لینک با href خالی یا #.",
                    suggestion="از button برای اقدامات بدون ناوبری استفاده کنید.",
                )
            )

    if "accessibility" in selected:
        imgs_no_alt = sum(1 for im in parser.images if not (im.get("alt") or "").strip())
        if imgs_no_alt:
            findings.append(
                _finding(
                    "accessibility",
                    "medium",
                    "تصاویر بدون alt",
                    f"{imgs_no_alt} تصویر بدون متن alt.",
                    suggestion="برای تصاویر معنادار alt توصیفی بنویسید.",
                )
            )
        if parser.h1_count == 0:
            findings.append(
                _finding(
                    "accessibility",
                    "medium",
                    "بدون h1",
                    "هیچ سرفصل h1 در صفحه نیست.",
                )
            )
        elif parser.h1_count > 1:
            findings.append(
                _finding(
                    "accessibility",
                    "low",
                    "چند h1",
                    f"{parser.h1_count} تگ h1 — معمولاً یک h1 کافی است.",
                )
            )
        label_gap = parser.finalize_labels()
        if label_gap > 2:
            findings.append(
                _finding(
                    "accessibility",
                    "medium",
                    "فرم بدون label کافی",
                    "برخی inputها label یا aria-label ندارند.",
                    suggestion="label مرتبط با for/id یا aria-label اضافه کنید.",
                )
            )

    if "seo" in selected:
        desc = parser.meta.get("description", "").strip()
        if not desc:
            findings.append(
                _finding(
                    "seo",
                    "medium",
                    "meta description نیست",
                    "توضیح متا برای موتور جستجو تعریف نشده.",
                )
            )
        elif len(desc) < 50:
            findings.append(
                _finding(
                    "seo",
                    "low",
                    "description کوتاه",
                    f"طول description حدود {len(desc)} کاراکتر.",
                )
            )
        robots = parser.meta.get("robots", "").lower()
        if "noindex" in robots:
            findings.append(
                _finding(
                    "seo",
                    "info",
                    "noindex فعال",
                    "صفحه از index موتور جستجو منع شده (شاید عمدی).",
                    evidence=robots,
                )
            )

    if "functional" in selected and status_code < 400:
        checked = 0
        broken: list[str] = []
        base_host = parsed.netloc
        for lnk in parser.links:
            href = (lnk.get("href") or "").strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            full = urljoin(target, href)
            p2 = urlparse(full)
            if p2.scheme not in ("http", "https"):
                continue
            if p2.netloc != base_host:
                continue
            if checked >= MAX_LINK_CHECKS:
                break
            checked += 1
            code = _head_check(full)
            if code is not None and code >= 400:
                broken.append(f"{full} → {code}")
        if broken:
            findings.append(
                _finding(
                    "functional",
                    "high",
                    "لینک‌های داخلی شکسته",
                    f"{len(broken)} لینک از {checked} نمونه با خطای HTTP.",
                    evidence="; ".join(broken[:5]),
                    suggestion="مسیرها و routing را اصلاح کنید.",
                )
            )
        if is_https and parser.http_in_src > 0:
            findings.append(
                _finding(
                    "functional",
                    "medium",
                    "محتوای mixed HTTP",
                    f"{parser.http_in_src} منبع img با http:// در صفحه HTTPS.",
                    suggestion="همه URLها را https کنید.",
                )
            )

    if "ui" in selected and parser.inline_styles > 40:
        findings.append(
            _finding(
                "ui",
                "low",
                "استایل inline زیاد",
                f"حدود {parser.inline_styles} attribute style.",
                suggestion="کلاس CSS متمرکز در فایل استایل.",
            )
        )

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: (severity_rank.get(f["severity"], 9), f["category"]))

    summary = {s: 0 for s in ("critical", "high", "medium", "low", "info")}
    for f in findings:
        sev = f.get("severity", "info")
        if sev in summary:
            summary[sev] += 1
    summary["total"] = len(findings)

    return {
        "ok": True,
        "url": target,
        "categories": selected,
        "findings": findings,
        "metrics": metrics,
        "summary": summary,
        "error": "",
    }


def categories_public() -> list[dict[str, str]]:
    return [{"id": c["id"], "label": c["label"], "hint": c["hint"]} for c in DEBUG_CATEGORIES]
