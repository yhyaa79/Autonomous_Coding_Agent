from decimal import Decimal

from django import forms
from django.contrib import admin

from .billing import ChatTokenUsage, UserWallet, WalletTransaction, admin_charge_wallet
from .models import (
    AgentMessage,
    ChatMessage,
    Conversation,
    ConversationSharedTool,
    JobRun,
    Project,
    ScheduledJob,
    SharedTool,
    SharedToolVersion,
)


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    fields = ("role", "content", "tool_steps", "created_at")
    can_delete = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "root_path", "conversation_count", "updated_at")
    list_filter = ("owner",)
    search_fields = ("name", "root_path")
    ordering = ("-updated_at",)

    @admin.display(description="مکالمات")
    def conversation_count(self, obj: Project) -> int:
        return obj.conversations.count()


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "project", "agent_type", "message_count", "updated_at")
    list_filter = ("agent_type", "project")
    search_fields = ("title",)
    inlines = [ChatMessageInline]

    @admin.display(description="پیام‌ها")
    def message_count(self, obj: Conversation) -> int:
        return obj.messages.count()


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "short_content", "created_at")
    list_filter = ("role",)
    search_fields = ("content",)

    @admin.display(description="متن")
    def short_content(self, obj: ChatMessage) -> str:
        return (obj.content or "")[:80]


@admin.register(ScheduledJob)
class ScheduledJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "project",
        "target_agent_type",
        "schedule_kind",
        "status",
        "next_run_at",
    )
    list_filter = ("status", "schedule_kind", "target_agent_type")


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "status", "started_at", "finished_at")
    list_filter = ("status",)


@admin.register(AgentMessage)
class AgentMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "from_agent_type", "to_agent_type", "status", "created_at")
    list_filter = ("status", "to_agent_type")


@admin.register(SharedTool)
class SharedToolAdmin(admin.ModelAdmin):
    list_display = ("display_name", "tool_id", "source_project", "updated_at")
    search_fields = ("display_name", "tool_id")


class SharedToolVersionInline(admin.TabularInline):
    model = SharedToolVersion
    extra = 0
    readonly_fields = ("public_id", "version_number", "content_kind", "created_at")
    fields = (
        "version_number",
        "public_id",
        "content_kind",
        "description",
        "created_at",
    )


SharedToolAdmin.inlines = [SharedToolVersionInline]


@admin.register(SharedToolVersion)
class SharedToolVersionAdmin(admin.ModelAdmin):
    list_display = ("shared_tool", "version_number", "content_kind", "public_id", "created_at")
    search_fields = ("public_id", "shared_tool__tool_id", "description")


@admin.register(ConversationSharedTool)
class ConversationSharedToolAdmin(admin.ModelAdmin):
    list_display = ("conversation", "shared_tool", "pinned_version", "added_at")
    list_filter = ("conversation__project",)


@admin.register(ChatTokenUsage)
class ChatTokenUsageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "conversation",
        "primary_model",
        "prompt_tokens",
        "completion_tokens",
        "total_credits",
        "estimated",
        "created_at",
    )
    list_filter = ("primary_model", "estimated")
    readonly_fields = ("breakdown", "created_at")


# ---------------------------------------------------------------------------
# کیف پول کاربر — با امکان شارژ از پنل ادمین
# ---------------------------------------------------------------------------

class UserWalletAdminForm(forms.ModelForm):
    """فرم ادمین کیف پول با فیلد موقت «مبلغ شارژ»."""

    charge_amount = forms.DecimalField(
        label="مبلغ شارژ (اعتبار ACA)",
        required=False,
        min_value=Decimal("0.000001"),
        max_digits=18,
        decimal_places=6,
        help_text=(
            "برای افزایش موجودی، مبلغ مثبت وارد کنید و ذخیره بزنید. "
            "اگر خالی بماند فقط اطلاعات کیف پول ذخیره می‌شود."
        ),
    )

    class Meta:
        model = UserWallet
        fields = ("user",)

    def clean_charge_amount(self):
        amount = self.cleaned_data.get("charge_amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("مبلغ شارژ باید مثبت باشد.")
        return amount


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    form = UserWalletAdminForm
    list_display = ("user", "balance", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("balance", "updated_at")
    actions = ["charge_selected_wallets"]

    fieldsets = (
        (None, {"fields": ("user", "balance", "updated_at")}),
        ("شارژ کیف پول", {"fields": ("charge_amount",)}),
    )

    def save_model(self, request, obj, form, change):
        """اگر ادمین مبلغ شارژ وارد کرده باشد، تراکنش شارژ ثبت می‌شود."""
        amount = form.cleaned_data.get("charge_amount")

        # ساخت کیف پول جدید در صورت نیاز
        if not change and not obj.pk:
            obj.save()
            change = True

        if amount and amount > 0:
            admin_charge_wallet(
                obj.user,
                amount,
                actor=request.user,
                note="شارژ از پنل ادمین",
            )
            # بروزرسانی نمونه برای نمایش موجودی جدید
            obj.refresh_from_db(fields=["balance", "updated_at"])
        else:
            super().save_model(request, obj, form, change)

    @admin.action(description="شارژ ۱۰۰۰۰ اعتبار")
    def charge_selected_wallets(self, request, queryset):
        for wallet in queryset:
            admin_charge_wallet(
                wallet.user,
                Decimal("10000"),
                actor=request.user,
                note="شارژ دسته‌ای ادمین",
            )


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "kind", "amount", "balance_after", "description", "created_at")
    list_filter = ("kind",)
    readonly_fields = (
        "user",
        "kind",
        "amount",
        "balance_after",
        "description",
        "created_by",
        "created_at",
    )

    def has_add_permission(self, request):
        return False