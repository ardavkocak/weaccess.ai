"""
office_bot URL yapisi.

config/urls.py icinde dogrudan "operasyonlar/" onekiyle mount edilir; boylece
"Görev Takibi" ve "Yemek Sistemi" Sidebar ogeleri ayni uygulamanin farkli
path'lerine (gorev-takibi/, yemek/) duser.
"""
from django.urls import path

from . import views

app_name = "office_bot"

urlpatterns = [
    path("gorev-takibi/", views.DutyDashboardView.as_view(), name="duty_dashboard"),
    path("gorev-takibi/personeller/", views.EmployeeListView.as_view(), name="employee_list"),
    path("gorev-takibi/personeller/<int:pk>/duzenle/", views.EmployeeEditView.as_view(), name="employee_edit"),
    path("gorev-takibi/personeller/<int:pk>/durum/", views.EmployeeToggleView.as_view(), name="employee_toggle"),
    path("gorev-takibi/personeller/<int:pk>/sil/", views.EmployeeDeleteView.as_view(), name="employee_delete"),
    path("gorev-takibi/personeller/<int:pk>/tasi/", views.EmployeeMoveView.as_view(), name="employee_move"),
    path("gorev-takibi/sira/", views.QueueView.as_view(), name="queue"),
    path("gorev-takibi/gecmis/", views.HistoryView.as_view(), name="history"),
    path("gorev-takibi/ayarlar/discord/", views.DiscordSettingsView.as_view(), name="settings_discord"),
    path("gorev-takibi/ayarlar/bildirimler/", views.ScheduleSettingsView.as_view(), name="settings_schedule"),
    path("yemek/", views.MealDashboardView.as_view(), name="meal_dashboard"),
    path("yemek/yukle/", views.MealUploadView.as_view(), name="meal_upload"),
    path("yemek/sil/", views.MealRemoveAllView.as_view(), name="meal_remove_all"),
    path("yemek/test/", views.MealTestActionsView.as_view(), name="meal_test_actions"),
    path("yemek/test/katilim.json", views.MealTestParticipationApiView.as_view(), name="meal_test_participation_api"),
]
