"""کیف پول کاربر، شارژ از ادمین، و کسر هزینهٔ مکالمه."""

from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class UserWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "کیف پول"
        verbose_name_plural = "کیف پول‌ها"

    def __str__(self) -> str:
        return f"{self.user} · {self.balance}"


class WalletTransaction(models.Model):
    KIND_CHARGE = "charge"
    KIND_USAGE = "usage"
    KIND_ADJUST = "adjust"
    KIND_CHOICES = [
        (KIND_CHARGE, "شارژ"),
        (KIND_USAGE, "مصرف"),
        (KIND_ADJUST, "تعدیل"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wallet_transactions")
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        help_text="مثبت برای شارژ، منفی برای مصرف",
    )
    balance_after = models.DecimalField(max_digits=18, decimal_places=6)
    description = models.CharField(max_length=500, blank=True, default="")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallet_transactions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "تراکنش کیف پول"
        verbose_name_plural = "تراکنش‌های کیف پول"


class ChatTokenUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_usages")
    conversation = models.ForeignKey(
        "projects.Conversation",
        on_delete=models.CASCADE,
        related_name="token_usages",
    )
    assistant_message = models.OneToOneField(
        "projects.ChatMessage",
        on_delete=models.CASCADE,
        related_name="token_usage",
        null=True,
        blank=True,
    )
    primary_model = models.CharField(max_length=64)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_credits = models.DecimalField(max_digits=18, decimal_places=6)
    breakdown = models.JSONField(default=list, blank=True)
    estimated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class InsufficientBalance(Exception):
    def __init__(self, balance: Decimal, required: Decimal):
        self.balance = balance
        self.required = required
        super().__init__(f"اعتبار کافی نیست: موجود {balance} · لازم {required}")


def get_or_create_wallet(user) -> UserWallet:
    wallet, _ = UserWallet.objects.get_or_create(user=user)
    return wallet


def wallet_summary(user) -> dict[str, Any]:
    w = get_or_create_wallet(user)
    return {
        "balance_credits": str(w.balance),
        "currency_label": "اعتبار ACA",
    }


@transaction.atomic
def admin_charge_wallet(
    user,
    amount: Decimal,
    *,
    actor=None,
    note: str = "",
) -> UserWallet:
    if amount <= 0:
        raise ValueError("مبلغ شارژ باید مثبت باشد")
    wallet = UserWallet.objects.select_for_update().get(user=user)
    wallet.balance += amount
    wallet.save(update_fields=["balance", "updated_at"])
    WalletTransaction.objects.create(
        user=user,
        kind=WalletTransaction.KIND_CHARGE,
        amount=amount,
        balance_after=wallet.balance,
        description=note or "شارژ از پنل ادمین",
        created_by=actor,
    )
    return wallet


@transaction.atomic
def charge_for_usage(
    user,
    conversation,
    assistant_message,
    usage_payload: dict[str, Any],
    *,
    primary_model: str,
) -> ChatTokenUsage:
    total = Decimal(str(usage_payload.get("total_credits") or "0"))
    if total <= 0:
        total = Decimal("0.000001")
    wallet = UserWallet.objects.select_for_update().get(user=user)
    if wallet.balance < total:
        raise InsufficientBalance(wallet.balance, total)
    wallet.balance -= total
    wallet.save(update_fields=["balance", "updated_at"])
    record = ChatTokenUsage.objects.create(
        user=user,
        conversation=conversation,
        assistant_message=assistant_message,
        primary_model=primary_model,
        prompt_tokens=int(usage_payload.get("prompt_tokens") or 0),
        completion_tokens=int(usage_payload.get("completion_tokens") or 0),
        total_credits=total,
        breakdown=usage_payload.get("slices") or [],
        estimated=bool(
            usage_payload.get("slices")
            and any(s.get("estimated") for s in usage_payload.get("slices") or [])
        ),
    )
    WalletTransaction.objects.create(
        user=user,
        kind=WalletTransaction.KIND_USAGE,
        amount=-total,
        balance_after=wallet.balance,
        description=f"مکالمه #{conversation.id} · {primary_model}",
    )
    return record


def assert_can_afford(user, minimum: Decimal | None = None) -> None:
    floor = minimum if minimum is not None else Decimal("0.000001")
    wallet = get_or_create_wallet(user)
    if wallet.balance < floor:
        raise InsufficientBalance(wallet.balance, floor)


@receiver(post_save, sender=User)
def _create_wallet_for_user(sender, instance, created, **kwargs):
    if created:
        UserWallet.objects.get_or_create(user=instance)
