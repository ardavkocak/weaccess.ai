"""
Ofis Gorev Takibi (ofis-gorev-takibi) SQLite semasinin Django karsiligi.

TUMU `managed = False`: bu tablolari orijinal proje (database/schema.js)
olusturur/gocurur. Django yalnizca okur/yazar, hicbir migration uretmez
(bkz. router.py). Sutun adlari ve tipler kaynak semayla birebir eslesir.
"""
from django.db import models


class Employee(models.Model):
    full_name = models.CharField(max_length=100, db_column="full_name")
    discord_user_id = models.CharField(max_length=32, null=True, blank=True, db_column="discord_user_id")
    is_active = models.IntegerField(default=1, db_column="is_active")
    position = models.IntegerField(db_column="position")
    created_at = models.CharField(max_length=32, db_column="created_at", blank=True)
    # Elle girilen sirket adi — Yemek Sistemi katilim listelerini buna gore
    # gruplar (bkz. meal_vote_service.py). Sabit bir secenek listesi YOK,
    # serbest metin: yeni bir sirket eklemek icin kod degismesi gerekmez.
    company = models.CharField(max_length=100, null=True, blank=True, db_column="company")

    class Meta:
        managed = False
        db_table = "employees"
        app_label = "office_bot"
        ordering = ["position"]

    def __str__(self):
        return self.full_name

    @property
    def is_active_bool(self):
        return self.is_active == 1


class DutyType(models.Model):
    key = models.CharField(max_length=50, unique=True, db_column="key")
    name = models.CharField(max_length=100, db_column="name")
    emoji = models.CharField(max_length=10, blank=True, db_column="emoji")
    is_enabled = models.IntegerField(default=1, db_column="is_enabled")
    created_at = models.CharField(max_length=32, db_column="created_at", blank=True)

    class Meta:
        managed = False
        db_table = "duty_types"
        app_label = "office_bot"

    def __str__(self):
        return self.name


class RotationState(models.Model):
    duty_type = models.OneToOneField(
        DutyType, primary_key=True, on_delete=models.DO_NOTHING,
        db_column="duty_type_id", db_constraint=False, related_name="rotation_state",
    )
    current_employee = models.ForeignKey(
        Employee, null=True, on_delete=models.DO_NOTHING,
        db_column="current_employee_id", db_constraint=False,
    )
    updated_at = models.CharField(max_length=32, db_column="updated_at", blank=True)

    class Meta:
        managed = False
        db_table = "rotation_state"
        app_label = "office_bot"


class DutyCycleServed(models.Model):
    duty_type = models.ForeignKey(DutyType, on_delete=models.DO_NOTHING, db_column="duty_type_id", db_constraint=False)
    employee = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, db_column="employee_id", db_constraint=False)
    served_at = models.CharField(max_length=32, db_column="served_at", blank=True)

    class Meta:
        managed = False
        db_table = "duty_cycle_served"
        app_label = "office_bot"


class ScheduledMessage(models.Model):
    key = models.CharField(max_length=100, unique=True, db_column="key")
    name = models.CharField(max_length=150, db_column="name")
    send_time = models.CharField(max_length=5, db_column="send_time")
    message_template = models.TextField(db_column="message_template")
    kind = models.CharField(max_length=20, db_column="kind")
    duty_type = models.ForeignKey(
        DutyType, null=True, on_delete=models.DO_NOTHING, db_column="duty_type_id", db_constraint=False,
    )
    is_enabled = models.IntegerField(default=1, db_column="is_enabled")
    sort_order = models.IntegerField(default=0, db_column="sort_order")
    created_at = models.CharField(max_length=32, db_column="created_at", blank=True)

    class Meta:
        managed = False
        db_table = "scheduled_messages"
        app_label = "office_bot"
        ordering = ["sort_order", "send_time"]

    def __str__(self):
        return self.name


class DutyHistory(models.Model):
    duty_type = models.ForeignKey(DutyType, on_delete=models.DO_NOTHING, db_column="duty_type_id", db_constraint=False)
    employee = models.ForeignKey(
        Employee, null=True, on_delete=models.DO_NOTHING, db_column="employee_id", db_constraint=False,
    )
    employee_name = models.CharField(max_length=100, db_column="employee_name")
    duty_date = models.CharField(max_length=10, db_column="duty_date")
    source = models.CharField(max_length=10, default="cron", db_column="source")
    notified = models.IntegerField(default=0, db_column="notified")
    consumed_turn = models.IntegerField(default=0, db_column="consumed_turn")
    created_at = models.CharField(max_length=32, db_column="created_at", blank=True)

    class Meta:
        managed = False
        db_table = "duty_history"
        app_label = "office_bot"
        ordering = ["-duty_date", "-id"]


class DutyConfirmation(models.Model):
    duty_type = models.ForeignKey(DutyType, on_delete=models.DO_NOTHING, db_column="duty_type_id", db_constraint=False)
    duty_date = models.CharField(max_length=10, db_column="duty_date")
    status = models.CharField(max_length=20, default="pending", db_column="status")
    step = models.IntegerField(default=0, db_column="step")
    source = models.CharField(max_length=10, default="cron", db_column="source")
    start_employee = models.ForeignKey(
        Employee, null=True, on_delete=models.DO_NOTHING, db_column="start_employee_id",
        db_constraint=False, related_name="+",
    )
    candidate_employee = models.ForeignKey(
        Employee, null=True, on_delete=models.DO_NOTHING, db_column="candidate_employee_id",
        db_constraint=False, related_name="+",
    )
    candidate_name = models.CharField(max_length=100, null=True, db_column="candidate_name")
    previous_name = models.CharField(max_length=100, null=True, db_column="previous_name")
    confirmed_employee = models.ForeignKey(
        Employee, null=True, on_delete=models.DO_NOTHING, db_column="confirmed_employee_id",
        db_constraint=False, related_name="+",
    )
    confirmed_name = models.CharField(max_length=100, null=True, db_column="confirmed_name")
    channel_id = models.CharField(max_length=32, null=True, db_column="channel_id")
    message_id = models.CharField(max_length=32, null=True, db_column="message_id")
    reset_count = models.IntegerField(default=0, db_column="reset_count")
    created_at = models.CharField(max_length=32, db_column="created_at", blank=True)
    updated_at = models.CharField(max_length=32, db_column="updated_at", blank=True)

    class Meta:
        managed = False
        db_table = "duty_confirmations"
        app_label = "office_bot"


class Settings(models.Model):
    key = models.CharField(max_length=100, primary_key=True, db_column="key")
    value = models.TextField(blank=True, db_column="value")
    updated_at = models.CharField(max_length=32, db_column="updated_at", blank=True)

    class Meta:
        managed = False
        db_table = "settings"
        app_label = "office_bot"


class MealMenu(models.Model):
    menu_date = models.CharField(max_length=10, unique=True, db_column="menu_date")
    day_name = models.CharField(max_length=20, blank=True, db_column="day_name")
    items = models.TextField(db_column="items")  # JSON dizisi (metin olarak saklanir)
    source_file = models.CharField(max_length=255, null=True, db_column="source_file")
    announced_at = models.CharField(max_length=32, null=True, db_column="announced_at")
    created_at = models.CharField(max_length=32, db_column="created_at", blank=True)
    updated_at = models.CharField(max_length=32, db_column="updated_at", blank=True)

    class Meta:
        managed = False
        db_table = "meal_menus"
        app_label = "office_bot"
        ordering = ["menu_date"]


class MealVote(models.Model):
    menu_date = models.CharField(max_length=10, db_column="menu_date")
    discord_user_id = models.CharField(max_length=32, db_column="discord_user_id")
    discord_user_name = models.CharField(max_length=100, null=True, db_column="discord_user_name")
    choice = models.CharField(max_length=5, db_column="choice")
    created_at = models.CharField(max_length=32, db_column="created_at", blank=True)
    updated_at = models.CharField(max_length=32, db_column="updated_at", blank=True)

    class Meta:
        managed = False
        db_table = "meal_votes"
        app_label = "office_bot"
