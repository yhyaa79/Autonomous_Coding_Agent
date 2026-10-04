"""ذخیره و بازسازی timeline مکالمه (لاگ، ابزار، اعتبار) بین پیام‌ها."""

import re
from decimal import Decimal
from typing import Any

from .models import ChatMessage, Conversation, ConversationFeedItem


def make_topic_summary(text: str, max_words: int = 6) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    if not t:
        return ""
    words = t.split()[:max_words]
    summary = " ".join(words)
    if len(t.split()) > max_words:
        summary += "…"
    return summary[:120]


def _next_turn_index(conv: Conversation) -> int:
    return conv.messages.filter(role=ChatMessage.ROLE_USER).count()


def persist_turn_feed(
    conv: Conversation,
    *,
    turn_index: int,
    phase_log: list[dict[str, Any]] | None,
    tool_steps: list[dict[str, Any]] | None,
    thinking: str | None,
    usage: dict[str, Any] | None,
) -> None:
    order = 0
    for ev in phase_log or []:
        if ev.get("type") != "phase":
            continue
        ConversationFeedItem.objects.create(
            conversation=conv,
            turn_index=turn_index,
            sub_order=order,
            kind=ConversationFeedItem.KIND_PHASE,
            payload=ev,
        )
        order += 1
    if thinking and str(thinking).strip():
        ConversationFeedItem.objects.create(
            conversation=conv,
            turn_index=turn_index,
            sub_order=order,
            kind=ConversationFeedItem.KIND_THINKING,
            payload={"content": str(thinking)},
        )
        order += 1
    for step in tool_steps or []:
        ConversationFeedItem.objects.create(
            conversation=conv,
            turn_index=turn_index,
            sub_order=order,
            kind=ConversationFeedItem.KIND_TOOL,
            payload=step,
        )
        order += 1
    if usage:
        ConversationFeedItem.objects.create(
            conversation=conv,
            turn_index=turn_index,
            sub_order=order,
            kind=ConversationFeedItem.KIND_CREDITS,
            payload=usage,
        )


def append_tool_trace(
    conv: Conversation,
    *,
    thinking: str | None,
    tool_steps: list[dict[str, Any]] | None,
) -> None:
    """همان ترتیب UI: جدیدترین ابزار بالای پنل اجرای زنده."""
    trace: list[dict[str, Any]] = list(conv.tool_trace or [])
    if thinking and str(thinking).strip():
        trace.insert(
            0,
            {
                "type": "thinking",
                "content": str(thinking),
            },
        )
    for step in reversed(tool_steps or []):
        trace.insert(0, {"type": "tool", "step": step})
    conv.tool_trace = trace[:500]
    conv.save(update_fields=["tool_trace", "updated_at"])


def add_conversation_credits(conv: Conversation, usage: dict[str, Any] | None) -> None:
    if not usage:
        return
    total = Decimal(str(usage.get("total_credits") or "0"))
    if total <= 0:
        return
    conv.total_credits_used = (conv.total_credits_used or Decimal("0")) + total
    conv.save(update_fields=["total_credits_used", "updated_at"])


def feed_items_by_turn(conv: Conversation) -> dict[int, list[ConversationFeedItem]]:
    grouped: dict[int, list[ConversationFeedItem]] = {}
    for item in conv.feed_items.all():
        grouped.setdefault(item.turn_index, []).append(item)
    return grouped


def build_conversation_timeline(conv: Conversation) -> list[dict[str, Any]]:
    """آیتم‌های timeline برای UI: پیام کاربر، لاگ/ابزار، پاسخ ایجنت، اعتبار."""
    messages = list(conv.messages.order_by("created_at", "id"))
    feed_map = feed_items_by_turn(conv)
    timeline: list[dict[str, Any]] = []
    turn_idx = 0
    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg.role != ChatMessage.ROLE_USER:
            i += 1
            continue
        timeline.append(_message_timeline_item(msg))
        for feed in feed_map.get(turn_idx, []):
            if feed.kind in (
                ConversationFeedItem.KIND_PHASE,
                ConversationFeedItem.KIND_THINKING,
            ):
                timeline.append(_feed_timeline_item(feed))
        i += 1
        if i < len(messages) and messages[i].role == ChatMessage.ROLE_ASSISTANT:
            timeline.append(_message_timeline_item(messages[i]))
            for feed in feed_map.get(turn_idx, []):
                if feed.kind == ConversationFeedItem.KIND_CREDITS:
                    timeline.append(_feed_timeline_item(feed))
            i += 1
        turn_idx += 1
    return timeline


def _message_timeline_item(m: ChatMessage) -> dict[str, Any]:
    return {
        "type": "message",
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "tool_steps": m.tool_steps,
        "created_at": m.created_at.isoformat(),
    }


def _feed_timeline_item(item: ConversationFeedItem) -> dict[str, Any]:
    return {
        "type": item.kind,
        "id": item.id,
        "turn_index": item.turn_index,
        "payload": item.payload,
        "created_at": item.created_at.isoformat(),
    }


def rebuild_conversation_ui_state(conv: Conversation) -> None:
    """بعد از undo یا حذف پیام، trace و اعتبار تجمیعی را از feed بازسازی کن."""
    trace: list[dict[str, Any]] = []
    assistants = conv.messages.filter(role=ChatMessage.ROLE_ASSISTANT).order_by(
        "created_at", "id"
    )
    for msg in assistants:
        for step in reversed(msg.tool_steps or []):
            trace.insert(0, {"type": "tool", "step": step})
    conv.tool_trace = trace[:500]
    total = Decimal("0")
    for item in conv.feed_items.filter(kind=ConversationFeedItem.KIND_CREDITS):
        total += Decimal(str(item.payload.get("total_credits") or "0"))
    conv.total_credits_used = total
    conv.save(update_fields=["tool_trace", "total_credits_used", "updated_at"])
