from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from agent.constants import DEFAULT_AGENT_ID, normalize_agent_id
from agent.scope import normalize_scope_paths


class Project(models.Model):
    name = models.CharField(max_length=200)
    root_path = models.TextField(help_text="Absolute path on disk")
    default_scope_paths = models.JSONField(default=list, blank=True)
    always_context_paths = models.JSONField(
        default=list,
        blank=True,
        help_text="فایل‌هایی که محتوایشان در هر نوبت مکالمه به ایجنت تزریق می‌شود",
    )
    denied_content_paths = models.JSONField(
        default=list,
        blank=True,
        help_text="فایل‌هایی که ایجنت هرگز محتوایشان را نمی‌بیند",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="aca_projects",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.name

    def effective_default_scope(self) -> list[str]:
        return normalize_scope_paths(self.default_scope_paths)


class Conversation(models.Model):
    AGENT_CODING = "coding"
    AGENT_AUTONOMOUS = "autonomous"
    AGENT_SEO = "seo"
    AGENT_SOCIAL = "social"
    AGENT_MAINTENANCE = "maintenance"
    AGENT_MARKETING = "marketing"
    AGENT_DEBUG = "debug"
    AGENT_CHOICES = [
        (AGENT_CODING, "coding"),
        (AGENT_AUTONOMOUS, "autonomous"),
        (AGENT_SEO, "seo"),
        (AGENT_SOCIAL, "social"),
        (AGENT_MAINTENANCE, "maintenance"),
        (AGENT_MARKETING, "marketing"),
        (AGENT_DEBUG, "debug"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="conversations"
    )
    agent_type = models.CharField(
        max_length=32,
        choices=AGENT_CHOICES,
        default=AGENT_CODING,
    )
    title = models.CharField(max_length=300, default="مکالمه جدید")
    scope_paths = models.JSONField(default=list, blank=True)
    scope_note = models.TextField(blank=True, default="")
    llm_model = models.CharField(max_length=64, blank=True, default="")
    topic_summary = models.CharField(max_length=120, blank=True, default="")
    total_credits_used = models.DecimalField(
        max_digits=18, decimal_places=6, default=Decimal("0")
    )
    tool_trace = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def user_configured_scope(self) -> list[str]:
        """فقط scope تنظیم‌شده توسط کاربر — نه auto."""
        own = normalize_scope_paths(self.scope_paths)
        if own:
            return own
        return self.project.effective_default_scope()

    def has_user_defined_scope(self) -> bool:
        return bool(self.user_configured_scope())

    def effective_scope(self) -> list[str]:
        """برای UI: scope ذخیره‌شده (کاربر/پروژه)."""
        return self.user_configured_scope()

    def to_history(self) -> list[dict[str, str]]:
        from agent.history import conversation_messages_to_model_history

        return conversation_messages_to_model_history(
            self.messages.filter(conversation_id=self.pk).order_by("created_at", "id")
        )


class ConversationFeedItem(models.Model):
    KIND_PHASE = "phase_log"
    KIND_TOOL = "tool_step"
    KIND_CREDITS = "credits"
    KIND_THINKING = "thinking"
    KIND_CHOICES = [
        (KIND_PHASE, "phase_log"),
        (KIND_TOOL, "tool_step"),
        (KIND_CREDITS, "credits"),
        (KIND_THINKING, "thinking"),
    ]

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="feed_items"
    )
    turn_index = models.PositiveIntegerField(db_index=True)
    sub_order = models.PositiveIntegerField(default=0)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["turn_index", "sub_order", "id"]


class ChatMessage(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = [(ROLE_USER, "user"), (ROLE_ASSISTANT, "assistant")]

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    tool_steps = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class MessageBackup(models.Model):
    """نسخهٔ فایل‌های تغییر یافته در یک نوبت ایجنت (قبل از اولین ویرایش هر فایل)."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="message_backups"
    )
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="message_backups"
    )
    message = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="backup",
        null=True,
        blank=True,
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ScheduledJob(models.Model):
    KIND_ONCE = "once"
    KIND_CRON = "cron"
    KIND_INTERVAL = "interval"
    KIND_CHOICES = [
        (KIND_ONCE, "once"),
        (KIND_CRON, "cron"),
        (KIND_INTERVAL, "interval"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "active"),
        (STATUS_PAUSED, "paused"),
        (STATUS_COMPLETED, "completed"),
        (STATUS_CANCELLED, "cancelled"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="scheduled_jobs"
    )
    source_conversation = models.ForeignKey(
        Conversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_jobs",
    )
    created_by_agent_type = models.CharField(max_length=32, default=DEFAULT_AGENT_ID)
    target_agent_type = models.CharField(max_length=32, default=DEFAULT_AGENT_ID)
    title = models.CharField(max_length=200)
    payload = models.JSONField(default=dict, blank=True)
    schedule_kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    run_at = models.DateTimeField(null=True, blank=True)
    cron_expression = models.CharField(max_length=120, blank=True, default="")
    interval_seconds = models.PositiveIntegerField(null=True, blank=True)
    timezone_name = models.CharField(max_length=64, blank=True, default="Asia/Tehran")
    next_run_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    max_runs = models.PositiveIntegerField(null=True, blank=True)
    run_count = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.schedule_kind == self.KIND_ONCE and not self.run_at:
            raise ValidationError({"run_at": "برای once الزامی است"})
        if self.schedule_kind == self.KIND_CRON and not self.cron_expression.strip():
            raise ValidationError({"cron_expression": "برای cron الزامی است"})
        if self.schedule_kind == self.KIND_INTERVAL and not self.interval_seconds:
            raise ValidationError({"interval_seconds": "برای interval الزامی است"})


class JobRun(models.Model):
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_RUNNING, "running"),
        (STATUS_SUCCESS, "success"),
        (STATUS_FAILED, "failed"),
    ]

    job = models.ForeignKey(ScheduledJob, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    reply = models.TextField(blank=True, default="")
    tool_steps = models.JSONField(default=list, blank=True)
    error_code = models.CharField(max_length=64, blank=True, default="")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]


class SharedTool(models.Model):
    """خانوادهٔ منبع در کتابخانه — نام ثابت؛ محتوا در ورژن‌ها."""

    display_name = models.CharField(max_length=200)
    tool_id = models.CharField(max_length=64, unique=True, db_index=True)
    source_project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shared_tools_created",
    )
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.tool_id})"


class SharedToolVersion(models.Model):
    """یک ورژن از منبع — متن، کد، لینk، رسانه و…"""

    KIND_CODE = "code"
    KIND_PROMPT = "prompt"
    KIND_LINK = "link"
    KIND_IMAGE = "image"
    KIND_VIDEO = "video"
    KIND_AUDIO = "audio"
    KIND_MIXED = "mixed"
    KIND_CHOICES = [
        (KIND_CODE, "code"),
        (KIND_PROMPT, "prompt"),
        (KIND_LINK, "link"),
        (KIND_IMAGE, "image"),
        (KIND_VIDEO, "video"),
        (KIND_AUDIO, "audio"),
        (KIND_MIXED, "mixed"),
    ]

    shared_tool = models.ForeignKey(
        SharedTool,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()
    public_id = models.CharField(max_length=36, unique=True, db_index=True)
    content_kind = models.CharField(
        max_length=16, choices=KIND_CHOICES, default=KIND_CODE
    )
    description = models.TextField(blank=True, default="")
    parameters = models.JSONField(default=dict, blank=True)
    source_body = models.TextField(blank=True, default="")
    content_blocks = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["shared_tool", "version_number"],
                name="uniq_shared_tool_version_number",
            )
        ]


class ConversationSharedTool(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="shared_tool_links",
    )
    shared_tool = models.ForeignKey(
        SharedTool,
        on_delete=models.CASCADE,
        related_name="conversation_links",
    )
    pinned_version = models.ForeignKey(
        SharedToolVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversation_pins",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "shared_tool"],
                name="uniq_conversation_shared_tool",
            )
        ]


class ProjectMemory(models.Model):
    """یادداشت پایدار پروژه — جایگزین فایل .agent/PROJECT_MEMORY.md."""

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="memory"
    )
    content = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)


class ProjectDebugState(models.Model):
    """لاگ سبک دیباگ و آخرین راه‌حل بازیابی."""

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="debug_state"
    )
    attempts = models.JSONField(default=list, blank=True)
    last_recovery = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)


class ProjectSession(models.Model):
    """متادیتای سبک نشست (مثل اینستاگرام). فایل سنگین تلگرام داخل .aca می‌ماند."""

    KIND_INSTAGRAM = "instagram"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="agent_sessions"
    )
    kind = models.CharField(max_length=32)
    account_key = models.CharField(max_length=200)
    payload = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "kind", "account_key"],
                name="uniq_project_agent_session",
            )
        ]


class ProjectTool(models.Model):
    """سورس ابزار سفارشی پروژه. فایل اجرایی فقط داخل .aca ساخته می‌شود."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="project_tools"
    )
    tool_id = models.CharField(max_length=64)
    description = models.TextField(blank=True, default="")
    parameters = models.JSONField(default=dict, blank=True)
    source_body = models.TextField(blank=True, default="")
    module_source = models.TextField(blank=True, default="")
    shared_public_id = models.CharField(max_length=36, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "tool_id"],
                name="uniq_project_tool",
            )
        ]
        ordering = ["tool_id"]


class ProjectServerConnection(models.Model):
    AUTH_PASSWORD = "password"
    AUTH_PRIVATE_KEY = "private_key"
    AUTH_CHOICES = [
        (AUTH_PASSWORD, "password"),
        (AUTH_PRIVATE_KEY, "private_key"),
    ]

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="server_connection",
    )
    is_enabled = models.BooleanField(default=False)
    host = models.CharField(max_length=255, blank=True, default="")
    port = models.PositiveIntegerField(default=22)
    username = models.CharField(max_length=128, blank=True, default="")
    auth_method = models.CharField(
        max_length=16,
        choices=AUTH_CHOICES,
        default=AUTH_PASSWORD,
    )
    secret_encrypted = models.TextField(blank=True, default="")
    key_passphrase_encrypted = models.TextField(blank=True, default="")
    remote_root_path = models.TextField(blank=True, default="")
    strict_host_key = models.BooleanField(default=True)
    host_key_fingerprint = models.CharField(max_length=128, blank=True, default="")
    allow_server_wide_paths = models.BooleanField(
        default=False,
        help_text="اجازهٔ read/write با مسیر مطلق خارج از remote_root (مثلاً nginx)",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "اتصال SSH پروژه"
        verbose_name_plural = "اتصال SSH پروژه"

    def __str__(self) -> str:
        return f"SSH · {self.project_id} · {self.host or '—'}"


class ProjectDebugProfile(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="debug_profile",
    )
    last_url = models.CharField(max_length=500, blank=True, default="")
    preferred_categories = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پروفایل دیباگ"
        verbose_name_plural = "پروفایل‌های دیباگ"

    def __str__(self) -> str:
        return f"DebugProfile · {self.project_id}"


class DebugScan(models.Model):
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_RUNNING, "running"),
        (STATUS_COMPLETED, "completed"),
        (STATUS_FAILED, "failed"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="debug_scans",
    )
    url = models.CharField(max_length=500)
    categories = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_RUNNING,
    )
    findings = models.JSONField(default=list, blank=True)
    metrics = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "اسکن دیباگ"
        verbose_name_plural = "اسکن‌های دیباگ"

    def __str__(self) -> str:
        return f"DebugScan · {self.project_id} · {self.url[:40]}"


class ProjectGrowthHub(models.Model):
    STAGE_BUILD = "build"
    STAGE_DEPLOYED = "deployed"
    STAGE_MAINTAIN = "maintain"
    STAGE_GROW = "grow"
    STAGE_CHOICES = [
        (STAGE_BUILD, "build"),
        (STAGE_DEPLOYED, "deployed"),
        (STAGE_MAINTAIN, "maintain"),
        (STAGE_GROW, "grow"),
    ]

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="growth_hub",
    )
    lifecycle_stage = models.CharField(
        max_length=16,
        choices=STAGE_CHOICES,
        default=STAGE_BUILD,
    )
    production_url = models.CharField(max_length=500, blank=True, default="")
    launched_at = models.DateTimeField(null=True, blank=True)
    maintenance_tasks = models.JSONField(default=list, blank=True)
    marketing_tasks = models.JSONField(default=list, blank=True)
    channels = models.JSONField(default=dict, blank=True)
    metrics = models.JSONField(default=dict, blank=True)
    last_maintenance_report = models.TextField(blank=True, default="")
    last_marketing_plan = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "هاب نگهداری و رشد"
        verbose_name_plural = "هاب نگهداری و رشد"

    def __str__(self) -> str:
        return f"GrowthHub · {self.project_id} · {self.lifecycle_stage}"


class UserLlmSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="llm_settings",
    )
    api_key_encrypted = models.TextField(blank=True, default="")
    base_url = models.CharField(max_length=500, blank=True, default="")
    remote_model = models.CharField(max_length=128, blank=True, default="")
    is_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیمات API شخصی"
        verbose_name_plural = "تنظیمات API شخصی"

    def display_label(self) -> str:
        model = (self.remote_model or "").strip() or "مدل شخصی"
        return f"API شخصی · {model} (بدون کسر اعتبار)"

    def __str__(self) -> str:
        return f"LLM settings · {self.user}"


class UserFileAccess(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="file_access",
    )
    always_context_paths = models.JSONField(
        default=list,
        blank=True,
        help_text="فایل‌هایی که محتوایشان در هر نوبت به ایجنت تزریق می‌شود (همهٔ پروژه‌ها)",
    )
    denied_content_paths = models.JSONField(
        default=list,
        blank=True,
        help_text="فایل‌هایی که ایجنت محتوایشان را نمی‌بیند (همهٔ پروژه‌ها)",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "دسترسی فایل کاربر"
        verbose_name_plural = "دسترسی فایل کاربران"

    def __str__(self) -> str:
        return f"File access · {self.user}"


class AgentMessage(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONSUMED = "consumed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "pending"),
        (STATUS_CONSUMED, "consumed"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="agent_messages"
    )
    from_agent_type = models.CharField(max_length=32)
    to_agent_type = models.CharField(max_length=32)
    source_conversation = models.ForeignKey(
        Conversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_messages",
    )
    subject = models.CharField(max_length=300, blank=True, default="")
    body = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
