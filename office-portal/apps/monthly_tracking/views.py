"""
Aylik Takip — Portal'in kendi native sayfasi.

Orijinal proje tamamen durumsuzdu (kalici veri yok); bu Django portu da
ayni sekilde her istegi bagimsiz isler, hicbir veri saklamaz.

HATA POLITIKASI (kullanicinin acik talebi uzerine): Dosya okunamiyorsa veya
hesaplama guvenilir yapilamiyorsa YARIM/YANLIS bir tablo GOSTERILMEZ; net,
Turkce bir hata mesaji ile durulur. Bu yuzden asagida her adim ayri ayri
try/except ile sarilir ve her hata turune ozel, anlasilir bir mesaj uretilir
(genel "bir hata olustu" yerine).
"""
from __future__ import annotations

from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from .services import parser
from .services.hesaplama import GUNLUK_SAAT, aylik_ozet
from .services.resmi_tatiller import RESMI_TATILLER, resmi_tatil_seti

# Arayuzdeki yil secimi 2026-2028 ile sinirlidir (2025 resmi_tatiller.py'de
# tanimli olsa da artik gecerli calisma donemi degil, dropdown'da gosterilmez).
YIL_SECENEKLERI = [y for y in sorted(RESMI_TATILLER.keys()) if y >= 2026]

PDF_TURLERI = {"application/pdf"}
WORD_TURLERI = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
GORSEL_TURLERI = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

AY_ADLARI = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        today = date.today()
        return render(request, "monthly_tracking/dashboard.html", {
            "ozet": None, "hata": None,
            "varsayilan_yil": today.year, "varsayilan_ay": today.month,
            "yil_secenekleri": YIL_SECENEKLERI,
        })

    def post(self, request):
        today = date.today()
        try:
            yil = int(request.POST.get("yil") or today.year)
            ay = int(request.POST.get("ay") or today.month)
            if not (1 <= ay <= 12):
                raise ValueError
        except (TypeError, ValueError):
            return self._hata_ile_don(request, "Geçerli bir yıl/ay girin.")

        context_ek = {"varsayilan_yil": yil, "varsayilan_ay": ay}

        calisma_dosyasi = request.FILES.get("calismaDosyasi")
        izin_gorseli = request.FILES.get("izinGorseli")

        if not calisma_dosyasi:
            return self._hata_ile_don(request, "Çalışma dosyası (PDF/Word) gerekli.", context_ek)
        if not izin_gorseli:
            return self._hata_ile_don(request, "İzin görseli (PNG/JPEG/WebP) gerekli.", context_ek)
        if izin_gorseli.content_type not in GORSEL_TURLERI:
            return self._hata_ile_don(
                request, f"İzin dosyası PNG/JPEG/WebP görsel olmalı. Gelen dosya türü: {izin_gorseli.content_type}", context_ek,
            )

        # 1) Çalışma dosyasından personel listesini çıkar.
        if calisma_dosyasi.content_type in PDF_TURLERI:
            try:
                personeller = parser.pdf_personel_cikar(calisma_dosyasi)
            except ImportError:
                return self._hata_ile_don(
                    request, "Sunucuda PDF okuma bileşeni (pdfplumber) kurulu değil. Sistem yöneticisine bildirin.", context_ek,
                )
            except Exception as exc:  # noqa: BLE001 — PDF kütüphanesi çok çeşitli hata sınıfı fırlatabilir
                return self._hata_ile_don(
                    request, f"PDF okunamadı; dosya bozuk veya şifreli olabilir. (Ayrıntı: {exc})", context_ek,
                )
        elif calisma_dosyasi.content_type in WORD_TURLERI:
            try:
                personeller = parser.word_personel_cikar(calisma_dosyasi)
            except ImportError:
                return self._hata_ile_don(
                    request, "Sunucuda Word okuma bileşeni (python-docx) kurulu değil. Sistem yöneticisine bildirin.", context_ek,
                )
            except Exception as exc:  # noqa: BLE001
                return self._hata_ile_don(request, f"Word dosyası okunamadı; dosya bozuk olabilir. (Ayrıntı: {exc})", context_ek)
        else:
            return self._hata_ile_don(
                request, f"Çalışma dosyası PDF veya Word olmalı. Gelen dosya türü: {calisma_dosyasi.content_type}", context_ek,
            )

        if not personeller:
            return self._hata_ile_don(
                request,
                "Çalışma dosyasından hiç personel okunamadı. Dosyanın Muafiyet Raporu formatında olduğundan "
                "ve tablo sütunlarının kaymadığından emin olun. Yanlış/eksik bir tablo gösterilmedi.",
                context_ek,
            )

        # 2) İzin görselinden OCR ile metin çıkar.
        try:
            ocr_metin = parser.gorsel_ocr(izin_gorseli)
        except ImportError:
            return self._hata_ile_don(
                request, "Sunucuda OCR bileşeni (pytesseract/Tesseract) kurulu değil. Sistem yöneticisine bildirin.", context_ek,
            )
        except Exception as exc:  # noqa: BLE001 — PIL/tesseract farkli hata siniflari firlatabilir
            return self._hata_ile_don(
                request, f"İzin görseli okunamadı; dosya bozuk veya desteklenmeyen bir görsel olabilir. (Ayrıntı: {exc})", context_ek,
            )

        if len((ocr_metin or "").strip()) < 10:
            return self._hata_ile_don(
                request,
                "İzin görselinden neredeyse hiç metin okunamadı. Görsel bulanık, çok küçük veya OCR'ın "
                "tanıyamayacağı bir formatta olabilir. Daha net bir görsel ile tekrar deneyin.",
                context_ek,
            )

        # 3) Hesaplama.
        try:
            resmi_set = resmi_tatil_seti(yil - 1, yil, yil + 1)
            izinler = parser.izin_kayitlari_cikar(ocr_metin, resmi_set)
            ozet = aylik_ozet(
                personeller=personeller, izinler=izinler,
                isim_eslesir=parser.isim_eslesir, yil=yil, ay=ay,
            )
        except Exception as exc:  # noqa: BLE001
            return self._hata_ile_don(request, f"Hesaplama sırasında beklenmeyen bir hata oluştu: {exc}", context_ek)

        if not ozet["resmi_tatiller_tum"] and yil not in (2025, 2026, 2027, 2028):
            # Resmi tatil listesi yalnızca 2025-2028 icin tanimli; bu araligin
            # disinda "resmi tatil = 0" YANLISLIKLA "hic tatil yok" gibi
            # gorunebilir. Kullaniciyi acikca uyar.
            ozet["resmi_tatil_uyarisi"] = (
                f"{yil} yılı için resmi tatil takvimi tanımlı değil; resmi tatil sayısı 0 olarak hesaplandı. "
                "Bu, o yıl gerçekten tatil olmadığı anlamına GELMEZ."
            )

        detay = {
            "personel_sayisi": len(personeller),
            "izin_kaydi_sayisi": len(izinler),
            "donem": f"{AY_ADLARI[ay]} {yil}",
            "gunluk_saat": GUNLUK_SAAT,
        }

        return render(request, "monthly_tracking/dashboard.html", {
            "ozet": ozet, "detay": detay, "hata": None,
            "yil_secenekleri": YIL_SECENEKLERI, **context_ek,
        })

    @staticmethod
    def _hata_ile_don(request, mesaj, ek_context=None):
        today = date.today()
        context = {
            "ozet": None, "hata": mesaj,
            "varsayilan_yil": today.year, "varsayilan_ay": today.month,
            "yil_secenekleri": YIL_SECENEKLERI,
        }
        context.update(ek_context or {})
        return render(request, "monthly_tracking/dashboard.html", context)
