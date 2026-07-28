"""Zimmet teslim ve iade tutanaklarinin PDF ciktilarini uretir.

Iki ayri belge uretilir ve bunlar birbirinden tamamen bagimsiz tasarimlara
sahiptir:

* :func:`build_delivery_pdf` -> cihaz personele teslim edilirken kullanilan
  "Zimmet Tutanagi Formu".
* :func:`build_return_pdf`   -> cihaz geri alinirken kullanilan
  "Iade Teslim Tutanagi Formu" (hasar/eksik kutucuklari icerir).

Ortak yapi taslari (font kaydi, baslik bloku, bolum tablolari, imza bloklari,
sayfa alt bilgisi) modul icinde tek bir yerde tanimlanir; boylece iki belge de
ayni kurumsal gorunumu paylasir ama icerikleri ayrisir.

Ciktilar A4 boyutunda, baskiya uygun ve tek sayfaya sigacak sekilde
olceklendirilmistir.
"""
import os

import reportlab
from django.conf import settings
from django.db.models import Count, Min
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Assignment

# ---------------------------------------------------------------------------
# Fontlar
# ---------------------------------------------------------------------------
# reportlab ile birlikte gelen Bitstream Vera fontlari Turkce karakterleri
# (s, g, i, c, o, u ve buyuk harfleri) tam olarak destekler. Helvetica gibi
# standart Type1 fontlari bu karakterleri bozdugu icin TTF kaydi yapilir.
FONT_REGULAR = "ZimmetSans"
FONT_BOLD = "ZimmetSans-Bold"

_FONT_FILES = {
    FONT_REGULAR: "Vera.ttf",
    FONT_BOLD: "VeraBd.ttf",
}


def _register_fonts():
    """Turkce destekli fontlari (bir kez) reportlab'e kaydeder."""
    registered = pdfmetrics.getRegisteredFontNames()
    if FONT_REGULAR in registered and FONT_BOLD in registered:
        return
    fonts_dir = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
    for font_name, file_name in _FONT_FILES.items():
        if font_name not in registered:
            pdfmetrics.registerFont(TTFont(font_name, os.path.join(fonts_dir, file_name)))
    pdfmetrics.registerFontFamily(FONT_REGULAR, normal=FONT_REGULAR, bold=FONT_BOLD)


# ---------------------------------------------------------------------------
# Olculer ve renkler
# ---------------------------------------------------------------------------
PAGE_SIZE = A4
MARGIN_X = 18 * mm
MARGIN_TOP = 14 * mm
MARGIN_BOTTOM = 18 * mm
CONTENT_WIDTH = PAGE_SIZE[0] - (2 * MARGIN_X)

COLOR_TEXT = colors.HexColor("#111827")
COLOR_MUTED = colors.HexColor("#6b7280")
COLOR_BORDER = colors.HexColor("#4b5563")
COLOR_SECTION_BG = colors.HexColor("#e8e9f4")

FOOTER_NOTE = "Elektronik Ortamda Günceldir & Kontrolsüz Kopya"

# Tutanagin sol ust hucresine basilacak sirket logolari. Anahtarlar sirket
# adinin normallestirilmis (kucuk harf, Turkce karaktersiz) halidir; boylece
# "Engelsiz Çeviri" ve "Engelsiz Ceviri" yazimlarinin ikisi de eslesir.
COMPANY_LOGO_FILES = {
    "craniocatch": "craniologo.png",
    "engelsiz ceviri": "image.png",
    "nevisoft": "image2.png",
}

# Logo, baslik hucresini tasirmayacak sekilde bu sinirlar icinde olceklenir.
LOGO_MAX_WIDTH = 34 * mm
LOGO_MAX_HEIGHT = 16 * mm

_TURKISH_CHAR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")

# Iade tutanagindaki kutucuk metinleri. Model secenekleri (Assignment.
# ReturnCondition) kod genelindeki ASCII yazim kuralina uydugu icin, basili
# belgede kullanilacak Turkce karsiliklari burada tanimlanir.
RETURN_CONDITION_LABELS = {
    Assignment.ReturnCondition.UNDAMAGED: "Hasarsız ve Tam Olarak Teslim Edildi",
    Assignment.ReturnCondition.DAMAGED: "Hasarlı Teslim Edildi",
    Assignment.ReturnCondition.MISSING: "Eksik Teslim Edildi",
}

# ---------------------------------------------------------------------------
# Paragraf stilleri
# ---------------------------------------------------------------------------
STYLE_TITLE = ParagraphStyle(
    "ZimmetTitle",
    fontName=FONT_BOLD,
    fontSize=13,
    leading=16,
    alignment=1,
    textColor=COLOR_TEXT,
)
STYLE_CELL = ParagraphStyle(
    "ZimmetCell",
    fontName=FONT_REGULAR,
    fontSize=8.5,
    leading=11,
    textColor=COLOR_TEXT,
)
STYLE_CELL_BOLD = ParagraphStyle(
    "ZimmetCellBold",
    parent=STYLE_CELL,
    fontName=FONT_BOLD,
)


def _company_logo_path(company):
    """Sirkete ait logo dosyasinin tam yolunu dondurur; yoksa None.

    Eslesme sirket adi uzerinden yapilir (bkz. COMPANY_LOGO_FILES). Tanimsiz
    sirket ya da eksik dosya durumunda None doner; cagiran taraf logo alanini
    bos birakir.
    """
    if company is None:
        return None
    key = company.name.strip().translate(_TURKISH_CHAR_MAP).lower()
    file_name = COMPANY_LOGO_FILES.get(key)
    if not file_name:
        return None
    for directory in settings.STATICFILES_DIRS:
        path = os.path.join(directory, "img", file_name)
        if os.path.exists(path):
            return path
    return None


def _company_logo_cell(company):
    """Baslik tablosunun sol hucresi: sirket logosu ya da bos alan.

    Logo en-boy orani korunarak LOGO_MAX_WIDTH/HEIGHT sinirlarina sigdirilir.
    Dosya bulunamaz veya okunamazsa hata verilmez, hucre bos birakilir.
    """
    path = _company_logo_path(company)
    if not path:
        return ""
    try:
        image = Image(path)
    except Exception:
        # Bozuk/okunamayan gorsel tutanagin uretilmesini engellememelidir.
        return ""

    ratio = image.imageWidth / image.imageHeight
    width = LOGO_MAX_WIDTH
    height = width / ratio
    if height > LOGO_MAX_HEIGHT:
        height = LOGO_MAX_HEIGHT
        width = height * ratio
    image.drawWidth, image.drawHeight = width, height
    image.hAlign = "CENTER"
    return image


def _header_table(title, company=None):
    """Her iki tutanagin da ustunde yer alan baslik bloku.

    Sol hucrede calisanin bagli oldugu sirketin logosu yer alir; sag hucre
    (kurum kullanimi) bilerek bos birakilir.
    """
    table = Table(
        [[_company_logo_cell(company), Paragraph(title, STYLE_TITLE), ""]],
        colWidths=[38 * mm, CONTENT_WIDTH - 76 * mm, 38 * mm],
        rowHeights=[20 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _base_table_style(extra=None):
    """Tum bolum tablolarinin paylastigi temel gorunum."""
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_TEXT),
        ("GRID", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    commands.extend(extra or [])
    return TableStyle(commands)


def _section_header_style(row=0, span_to=-1):
    """Bir satiri bolum basligi (ortali, gri zeminli, kalin) haline getirir."""
    return [
        ("SPAN", (0, row), (span_to, row)),
        ("BACKGROUND", (0, row), (span_to, row), COLOR_SECTION_BG),
        ("FONTNAME", (0, row), (span_to, row), FONT_BOLD),
        ("ALIGN", (0, row), (span_to, row), "CENTER"),
    ]


def _label_value_section(title, rows, label_width=52 * mm):
    """'Baslik + etiket/deger satirlari' seklindeki standart bolum tablosu."""
    data = [[title, ""]]
    data += [[label, Paragraph(str(value), STYLE_CELL)] for label, value in rows]

    table = Table(data, colWidths=[label_width, CONTENT_WIDTH - label_width])
    table.setStyle(
        _base_table_style(
            _section_header_style()
            + [
                ("FONTNAME", (0, 1), (0, -1), FONT_BOLD),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#f7f7fb")),
            ]
        )
    )
    return table


def collect_delivery_items(assignment):
    """Ayni teslimde verilen cihazlari 'Cinsi / Miktar' satirlarina donusturur.

    Bir zimmet kaydi tek bir adedi temsil ettigi icin, ayni personele ayni
    teslim tarihinde verilen tum kayitlar tek tutanakta toplanir: ayni cihazdan
    birden fazla adet verildiyse tek satirda Miktar olarak gosterilir.
    Satirlar teslim sirasina (ilk kaydin id'sine) gore siralanir.
    """
    rows = (
        Assignment.objects.filter(
            employee_id=assignment.employee_id,
            assigned_date=assignment.assigned_date,
        )
        .values("device__name")
        .annotate(quantity=Count("id"), first_id=Min("id"))
        .order_by("first_id")
    )
    return [(row["device__name"], row["quantity"]) for row in rows]


def _delivered_items_section(items):
    """'Teslim Edilenler' bolumu: No / Cinsi / Birim / Miktar.

    Ornek tutanaktaki duzene sadik kalinir; No sutunu otomatik siralanir ve
    birden fazla cihaz icin satir sayisi kadar uzar.
    """
    data = [["TESLİM EDİLENLER", "", "", ""]]
    data.append([Paragraph(header, STYLE_CELL_BOLD) for header in ("No", "Cinsi", "Birim", "Miktar")])
    for index, (name, quantity) in enumerate(items, start=1):
        data.append(
            [
                Paragraph(str(index), STYLE_CELL),
                Paragraph(name, STYLE_CELL),
                Paragraph("Adet", STYLE_CELL),
                Paragraph(str(quantity), STYLE_CELL),
            ]
        )

    table = Table(data, colWidths=[14 * mm, CONTENT_WIDTH - 60 * mm, 24 * mm, 22 * mm])
    table.setStyle(
        _base_table_style(
            _section_header_style(row=0, span_to=3)
            + [
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f7f7fb")),
                # No / Birim / Miktar sutunlari ortali; yalnizca Cinsi sola yasli.
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (2, 1), (3, -1), "CENTER"),
            ]
        )
    )
    return table


def _checkbox(checked):
    """Isaretlenebilir kutucuk. Secili secenek 'X' ile isaretlenir."""
    mark = "X" if checked else ""
    box = Table([[mark]], colWidths=[5 * mm], rowHeights=[5 * mm])
    box.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.9, COLOR_TEXT),
                ("FONTNAME", (0, 0), (-1, -1), FONT_BOLD),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return box


def _condition_section(selected_condition):
    """Iade tutanagindaki 'Hasarsiz / Hasarli / Eksik' secim bloku.

    Model secenek etiketleri (kod tarafinda ASCII) yerine basili belgeye uygun
    Turkce metinler kullanilir; secili secenek 'X' ile isaretlenir.
    """
    # Cihaz bilgileri bu tutanakta listelenmedigi icin baslik "yukarida
    # belirtilen" ifadesini kullanmaz.
    data = [["İADE EDİLEN CİHAZ İŞYERİNE;", ""]]
    for value, label in RETURN_CONDITION_LABELS.items():
        data.append([Paragraph(label, STYLE_CELL), _checkbox(selected_condition == value)])

    table = Table(data, colWidths=[CONTENT_WIDTH - 20 * mm, 20 * mm])
    table.setStyle(
        _base_table_style(
            _section_header_style()
            + [("ALIGN", (1, 1), (1, -1), "CENTER")]
        )
    )
    return table


def _signature_section(blocks):
    """Imza bloklari.

    Args:
        blocks: (baslik, [(etiket, deger), ...]) ciftlerinden olusan liste.
            Her etiket/deger cifti solda, karsisinda bos imza alani yer alir.
    """
    data = []
    style_commands = []
    row = 0
    for title, fields in blocks:
        data.append([title, "", "", ""])
        style_commands.extend(_section_header_style(row=row))
        row += 1
        for label, value in fields:
            data.append([label, Paragraph(str(value), STYLE_CELL), "İmza", ""])
            style_commands.append(("FONTNAME", (0, row), (0, row), FONT_BOLD))
            style_commands.append(("FONTNAME", (2, row), (2, row), FONT_BOLD))
            style_commands.append(("BACKGROUND", (0, row), (0, row), colors.HexColor("#f7f7fb")))
            style_commands.append(("BACKGROUND", (2, row), (2, row), colors.HexColor("#f7f7fb")))
            row += 1

    label_width = 30 * mm
    signature_label_width = 18 * mm
    value_width = 56 * mm
    widths = [
        label_width,
        value_width,
        signature_label_width,
        CONTENT_WIDTH - label_width - value_width - signature_label_width,
    ]

    table = Table(data, colWidths=widths, rowHeights=_signature_row_heights(data))
    table.setStyle(_base_table_style(style_commands))
    return table


def _signature_row_heights(data):
    """Bolum basliklari kisa, imza satirlari el yazisina yer birakacak kadar yuksek."""
    heights = []
    for row in data:
        is_section_header = row[1] == "" and row[2] == ""
        heights.append(7 * mm if is_section_header else 13 * mm)
    return heights


def _draw_page_furniture(canvas, doc):
    """Her sayfanin altina sayfa numarasi ve kurumsal notu yazar."""
    canvas.saveState()
    canvas.setFont(FONT_REGULAR, 7)
    canvas.setFillColor(COLOR_MUTED)
    canvas.drawRightString(
        PAGE_SIZE[0] - MARGIN_X,
        MARGIN_BOTTOM - 8 * mm,
        f"Sayfa {canvas.getPageNumber()}",
    )
    canvas.drawString(MARGIN_X, MARGIN_BOTTOM - 8 * mm, FOOTER_NOTE)
    canvas.restoreState()


def _build_document(buffer, title, story):
    """Ortak SimpleDocTemplate yapilandirmasi ile PDF'i olusturur."""
    doc = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=title,
        author="Zimmet Sistemi",
    )
    doc.build(story, onFirstPage=_draw_page_furniture, onLaterPages=_draw_page_furniture)


def _format_date(value):
    return value.strftime("%d.%m.%Y") if value else "-"


# ---------------------------------------------------------------------------
# A) Zimmet Teslim Formu
# ---------------------------------------------------------------------------
def build_delivery_pdf(buffer, assignment):
    """Cihaz teslim edilirken kullanilan zimmet tutanagini uretir.

    Ayni personele ayni tarihte verilen tum cihazlar tek tutanakta listelenir
    (bkz. collect_delivery_items).
    """
    _register_fonts()
    employee = assignment.employee

    story = [
        _header_table("ZİMMET TUTANAĞI FORMU", company=employee.company),
        Spacer(1, 5 * mm),
        _label_value_section(
            "PERSONELİN",
            [
                ("Adı - Soyadı", employee.full_name),
                ("TC Kimlik No", employee.tc_kimlik_no),
                ("İşe Giriş Tarihi", _format_date(employee.hire_date)),
            ],
        ),
        Spacer(1, 5 * mm),
        _delivered_items_section(collect_delivery_items(assignment)),
        Spacer(1, 5 * mm),
        _label_value_section(
            "TESLİM BİLGİLERİ",
            [("Teslim Tarihi", _format_date(assignment.assigned_date))],
        ),
        Spacer(1, 5 * mm),
        _signature_section(
            [
                ("TESLİM ALAN PERSONEL", [("Ad - Soyad", employee.full_name)]),
                (
                    "TESLİM EDEN TAŞINIR KAYIT YETKİLİSİ",
                    [("Ad - Soyad", _user_display(assignment.assigned_by))],
                ),
            ]
        ),
    ]
    _build_document(buffer, f"Zimmet Tutanagi ZT-{assignment.pk:06d}", story)
    return buffer


# ---------------------------------------------------------------------------
# B) Iade Teslim Formu
# ---------------------------------------------------------------------------
def build_return_pdf(buffer, assignment, hr_user=None):
    """Cihaz geri alinirken kullanilan iade tutanagini uretir.

    Teslim tutanagindan bilincli olarak daha sadedir: personel ve cihaz
    bilgileri yer almaz, yalnizca iade tarihleri, iade durumu ve imza alanlari
    bulunur.

    Args:
        hr_user: Insan Kaynaklari imza blokuna adi yazilacak kullanici
            (tutanagi olusturan yetkili). Verilmezse alan bos birakilir.
    """
    _register_fonts()
    employee = assignment.employee

    story = [
        _header_table("İADE TESLİM TUTANAĞI FORMU", company=employee.company),
        Spacer(1, 5 * mm),
        _label_value_section(
            "İADE BİLGİLERİ",
            [
                ("Teslim Tarihi", _format_date(assignment.assigned_date)),
                ("İade Tarihi", _format_date(assignment.returned_date)),
            ],
        ),
        Spacer(1, 5 * mm),
        _condition_section(assignment.return_condition),
        Spacer(1, 5 * mm),
        _label_value_section(
            "AÇIKLAMALAR",
            [("Hasar / Eksik Açıklaması", assignment.damage_description or "-")],
        ),
        Spacer(1, 5 * mm),
        _signature_section(
            [
                ("TESLİM EDEN PERSONEL", [("Ad - Soyad", employee.full_name)]),
                ("İNSAN KAYNAKLARI", [("Ad - Soyad", _user_display(hr_user))]),
            ]
        ),
    ]
    _build_document(buffer, f"Iade Tutanagi IT-{assignment.pk:06d}", story)
    return buffer


def _user_display(user):
    """Tutanakta gosterilecek yetkili adi (tam ad yoksa kullanici adi)."""
    if not user:
        return ""
    return user.get_full_name() or user.get_username()
