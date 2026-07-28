"""Tum sablonlarda kullanilabilecek ortak baglam degiskenleri."""
from django.utils import timezone


def sidebar_context(request):
    """Sidebar/navbar icin ozet bilgileri (bekleyen iadeler, bildirimler) saglar."""
    context = {
        "current_year": timezone.now().year,
    }
    if not request.user.is_authenticated:
        return context

    from apps.inventory.models import Assignment, Notification

    if getattr(request.user, "role", None) == "admin":
        context["pending_return_count"] = Assignment.objects.filter(returned=False).count()
    else:
        context["pending_return_count"] = 0

    context["unread_notification_count"] = Notification.objects.filter(
        user=request.user, is_read=False
    ).count()
    context["navbar_notifications"] = Notification.objects.filter(user=request.user).order_by("-created_at")[:6]
    return context
