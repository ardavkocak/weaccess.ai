"""Yemek katilim oylari servisi (salt okunur kisim) — mealVote.service.js portu."""
from __future__ import annotations

from ..models import Employee, MealVote
from .date_utils import today_iso

# Employee.company alani bos birakilmis (henuz elle doldurulmamis) ya da
# Employee kaydi hic bulunamayan (bilinmeyen Discord ID'den gelen dis oy)
# katilimcilar icin.
UNASSIGNED_COMPANY = "Diğer"


def group_by_company(entries: list[dict]) -> list[dict]:
    """
    Bir katilim listesini (yes/no/pending) 'company' alanina gore gruplar.
    Sirket adi ALFABETIK sirada gelir (Diger her zaman en sonda); yeni bir
    sirket Employee.company alanina elle girildiginde kod degismeden
    otomatik ortaya cikar (bkz. apps/office_bot/employees.html formu).
    """
    buckets: dict[str, list[dict]] = {}
    for entry in entries:
        buckets.setdefault(entry.get("company", UNASSIGNED_COMPANY), []).append(entry)

    ordered_companies = sorted(buckets, key=lambda c: (c == UNASSIGNED_COMPANY, c))
    return [
        {"company": company, "count": len(buckets[company]), "people": buckets[company]}
        for company in ordered_companies
    ]


# Yemek sonuc bildirimi (DM) icin ayar anahtarlari — apps/office_bot/views.py
# (Ayarlar formu) ve apps/office_bot/scheduler.py (otomatik gonderim) ikisi de
# BU anahtarlari kullanir; string'in tek yerde tanimli olmasi icin burada.
MEAL_RESULT_ENABLED_KEY = "meal_result_enabled"
MEAL_RESULT_TIME_KEY = "meal_result_notify_time"
MEAL_RESULT_USER_ID_KEY = "meal_result_discord_user_id"
MEAL_RESULT_LAST_SENT_KEY = "meal_result_last_sent_date"
MEAL_RESULT_DEFAULT_TIME = "15:30"

# Discord'un tek bir embed alani (field.value) icin izin verdigi karakter
# sinirini asmamak icin uzun kisi listeleri parcalara bolunur.
_FIELD_VALUE_LIMIT = 1024
_MAX_FIELDS = 25
_RESULT_EMBED_COLOR = 0x2ECC71


def _split_field_value(text):
    """Bir alan degerini satir satir, 1024 karakteri asmayacak parcalara boler."""
    if len(text) <= _FIELD_VALUE_LIMIT:
        return [text]

    chunks = []
    current, current_len = [], 0
    for line in text.split("\n"):
        added_len = len(line) + 1
        if current and current_len + added_len > _FIELD_VALUE_LIMIT:
            chunks.append("\n".join(current))
            current, current_len = [], 0
        current.append(line)
        current_len += added_len
    if current:
        chunks.append("\n".join(current))
    return chunks


def build_result_embed(menu_date):
    """
    Bir gunun yemek katilim sonuclarini sirkete gore gruplanmis, DM olarak
    gonderilmeye hazir bir Discord embed'i (dict) olarak uretir.

    Ayni get_participation()/group_by_company() mantigini kullanir — admin
    panelindeki "Katilim" gorunumuyle (bkz. views.py _context) BIREBIR ayni
    kaynaktan besleniyor, ayrica bir sorgu/gruplama yazilmadi.
    """
    participation = get_participation(menu_date)
    counts = participation["counts"]
    yes_by_company = {g["company"]: g["people"] for g in group_by_company(participation["yes"])}
    no_by_company = {g["company"]: g["people"] for g in group_by_company(participation["no"])}

    companies = sorted(
        set(yes_by_company) | set(no_by_company),
        key=lambda c: (c == UNASSIGNED_COMPANY, c),
    )

    fields = []
    for company in companies:
        yes_people = yes_by_company.get(company, [])
        no_people = no_by_company.get(company, [])
        lines = [f"✅ Yiyecekler ({len(yes_people)})"]
        lines += [f"• {p['name']}" for p in yes_people]
        lines.append(f"❌ Yemeyecekler ({len(no_people)})")
        lines += [f"• {p['name']}" for p in no_people]

        for idx, chunk in enumerate(_split_field_value("\n".join(lines))):
            name = f"🏢 {company}" if idx == 0 else f"🏢 {company} (devam)"
            fields.append({"name": name, "value": chunk, "inline": False})

    # Ozet alani icin her zaman yer birakilsin diye sirket alanlari, toplam
    # 25 alan sinirinin bir eksigine kadar tutulur; asarsa kesilip belirtilir.
    if len(fields) > _MAX_FIELDS - 1:
        fields = fields[: _MAX_FIELDS - 2] + [{
            "name": "⚠️ Not",
            "value": "Alan sınırı nedeniyle bazı şirketler burada gösterilemedi. Tüm sonuçlar için Portal'daki Yemek Sistemi ekranına bakın.",
            "inline": False,
        }]

    fields.append({
        "name": "📊 Özet",
        "value": (
            f"Toplam Personel: {counts['total']}\n"
            f"Yiyecek: {counts['yes']}\n"
            f"Yemeyecek: {counts['no']}\n"
            f"Cevap Vermeyen: {counts['pending']}"
        ),
        "inline": False,
    })

    return {
        "title": "🍽️ Bugünkü Yemek Katılım Sonuçları",
        "color": _RESULT_EMBED_COLOR,
        "fields": fields,
    }


def is_open(menu_date: str) -> bool:
    """
    Anket açık mı? KURAL: menünün ait olduğu günün SONUNDA otomatik kapanır —
    yani menu_date bugünden eskiyse anket kapalıdır. Gerçek oylar Discord
    butonları üzerinden Node botuna gelir; bu fonksiyon aynı kuralın Portal
    tarafındaki karşılığıdır (bkz. ofis-gorev-takibi mealVote.service.js
    isOpen), yalnızca GÖSTERİM amaçlı (açık/kapalı rozeti) kullanılır.
    """
    return menu_date >= today_iso()


def get_counts(menu_date):
    votes = MealVote.objects.filter(menu_date=menu_date)
    yes = votes.filter(choice="yes").count()
    no = votes.filter(choice="no").count()
    return {"yes": yes, "no": no, "total": yes + no}


def get_participation(menu_date):
    votes = list(MealVote.objects.filter(menu_date=menu_date).order_by("updated_at"))
    employees_by_discord_id = {
        e.discord_user_id: e for e in Employee.objects.exclude(discord_user_id__isnull=True).exclude(discord_user_id="")
    }

    def to_entry(vote):
        employee = employees_by_discord_id.get(vote.discord_user_id)
        return {
            "employee_id": employee.id if employee else None,
            "name": employee.full_name if employee else (vote.discord_user_name or vote.discord_user_id),
            "discord_user_id": vote.discord_user_id,
            "is_external": employee is None,
            "updated_at": vote.updated_at,
            "company": (employee.company if employee else None) or UNASSIGNED_COMPANY,
        }

    yes = [to_entry(v) for v in votes if v.choice == "yes"]
    no = [to_entry(v) for v in votes if v.choice == "no"]

    voted_ids = {v.discord_user_id for v in votes}
    pending = []
    for employee in Employee.objects.filter(is_active=1).order_by("position"):
        if not employee.discord_user_id or employee.discord_user_id not in voted_ids:
            pending.append({
                "employee_id": employee.id,
                "name": employee.full_name,
                "discord_user_id": employee.discord_user_id,
                "has_no_discord_id": not employee.discord_user_id,
                "company": employee.company or UNASSIGNED_COMPANY,
            })

    return {
        "yes": yes, "no": no, "pending": pending,
        "counts": {
            "yes": len(yes), "no": len(no), "pending": len(pending),
            "responded": len(yes) + len(no),
            "total": len(pending) + len(yes) + len(no),
        },
    }
