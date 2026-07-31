"""Envanter uygulamasi URL yapilandirmasi."""
from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    # Sirketler
    path("sirketler/", views.CompanyListView.as_view(), name="company-list"),
    path("sirketler/yeni/", views.CompanyCreateView.as_view(), name="company-create"),
    path("sirketler/<int:pk>/duzenle/", views.CompanyUpdateView.as_view(), name="company-update"),
    path("sirketler/<int:pk>/sil/", views.CompanyDeleteView.as_view(), name="company-delete"),
    # Calisanlar
    path("calisanlar/", views.EmployeeListView.as_view(), name="employee-list"),
    path("calisanlar/yeni/", views.EmployeeCreateView.as_view(), name="employee-create"),
    path("calisanlar/<int:pk>/", views.EmployeeDetailView.as_view(), name="employee-detail"),
    path("calisanlar/<int:pk>/duzenle/", views.EmployeeUpdateView.as_view(), name="employee-update"),
    path("calisanlar/<int:pk>/sil/", views.EmployeeDeleteView.as_view(), name="employee-delete"),
    # Cihazlar (stok)
    path("cihazlar/", views.DeviceListView.as_view(), name="device-list"),
    path("cihazlar/yeni/", views.DeviceCreateView.as_view(), name="device-create"),
    path("cihazlar/<int:pk>/", views.DeviceDetailView.as_view(), name="device-detail"),
    path("cihazlar/<int:pk>/duzenle/", views.DeviceUpdateView.as_view(), name="device-update"),
    path("cihazlar/<int:pk>/sil/", views.DeviceDeleteView.as_view(), name="device-delete"),
    # Zimmetler
    path("zimmetler/", views.AssignmentListView.as_view(), name="assignment-list"),
    path("zimmetler/yeni/", views.AssignmentCreateView.as_view(), name="assignment-create"),
    path("zimmetler/<int:pk>/", views.AssignmentDetailView.as_view(), name="assignment-detail"),
    path("zimmetler/<int:pk>/iade-al/", views.AssignmentReturnView.as_view(), name="assignment-return"),
    path("zimmetler/<int:pk>/sil/", views.AssignmentDeleteView.as_view(), name="assignment-delete"),
    # Bildirimler
    path("bildirimler/", views.notification_list_view, name="notification-list"),
    path("bildirimler/<int:pk>/okundu/", views.mark_notification_read, name="notification-mark-read"),
    path("bildirimler/tumunu-okundu/", views.mark_all_notifications_read, name="notification-mark-all-read"),
    # Global Arama
    path("arama/", views.global_search_api, name="global-search"),
    # Disa/Ice Aktarma
    path("cihazlar/disa-aktar/", views.device_export_excel, name="device-export"),
    path("cihazlar/ice-aktar/", views.device_import_excel, name="device-import"),
    # PDF Tutanaklar: teslim ve iade icin ayri belgeler uretilir.
    path(
        "zimmetler/<int:pk>/teslim-tutanagi/",
        views.assignment_delivery_pdf_view,
        name="assignment-delivery-pdf",
    ),
    path(
        "zimmetler/<int:pk>/iade-tutanagi/",
        views.assignment_return_pdf_view,
        name="assignment-return-pdf",
    ),
]
