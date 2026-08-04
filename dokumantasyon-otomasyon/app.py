# -*- coding: utf-8 -*-
"""
Banka Sözleşme & Form -> Google Sheets otomasyonu — Web Arayüzü.

Kullanım:
    python app.py
    Tarayıcıda http://127.0.0.1:5000 adresini aç.

Gereken ortam değişkenleri (.env dosyasında):
    GOOGLE_SERVICE_ACCOUNT_JSON  -> servis hesabı JSON anahtar dosyasının yolu
                                    ya da JSON içeriğinin kendisi (tek satır)
    GOOGLE_SHEETS_URL            -> hedef Google Sheets dosyasının linki/ID'si
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, render_template, request

from scraper import kaz
from sheets_export import sheets_e_yaz

load_dotenv()

app = Flask(__name__)

SERVIS_HESABI = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")
SHEETS_URL = os.getenv("GOOGLE_SHEETS_URL", "")


def _servis_hesabi_tanimli_mi() -> bool:
    """Servis hesabı bilgisi (dosya yolu veya JSON içeriği) kullanılabilir mi kontrol eder."""
    if SERVIS_HESABI.strip().startswith("{"):
        return True  # Ortam değişkeninde doğrudan JSON içeriği verilmiş
    return os.path.exists(SERVIS_HESABI)


@app.route("/", methods=["GET", "POST"])
def index():
    sonuc = None
    hata = None

    if request.method == "POST":
        banka_adi = (request.form.get("banka_adi") or "").strip()
        sayfa_url = (request.form.get("sayfa_url") or "").strip()
        zorla_tarayici = request.form.get("zorla_tarayici") == "on"

        if not banka_adi or not sayfa_url:
            hata = "Banka adı ve sayfa URL'si zorunludur."
        elif not SHEETS_URL:
            hata = ("GOOGLE_SHEETS_URL tanımlı değil. Lütfen .env dosyasını "
                    "'.env.example' referans alarak oluşturun.")
        elif not _servis_hesabi_tanimli_mi():
            hata = (f"Servis hesabı bilgisi bulunamadı: {SERVIS_HESABI}. "
                    "README'deki kurulum adımlarını izleyin.")
        else:
            try:
                belgeler = kaz(sayfa_url, zorla_tarayici=zorla_tarayici)
                if not belgeler:
                    hata = ("Sayfada hiç doküman (PDF/DOC/XLS) bağlantısı bulunamadı. "
                            "'Tarayıcı ile aç (JS)' seçeneğini işaretleyip tekrar deneyin.")
                else:
                    sekme_url = sheets_e_yaz(
                        belgeler=belgeler,
                        spreadsheet_url_veya_id=SHEETS_URL,
                        banka_adi=banka_adi,
                        servis_hesabi=SERVIS_HESABI,
                    )
                    sozlesme = sum(1 for b in belgeler if b.kategori == "Sözleşme")
                    form = sum(1 for b in belgeler if b.kategori == "Form")
                    diger = len(belgeler) - sozlesme - form
                    sonuc = {
                        "banka_adi": banka_adi,
                        "toplam": len(belgeler),
                        "sozlesme": sozlesme,
                        "form": form,
                        "diger": diger,
                        "sekme_url": sekme_url,
                        "belgeler": belgeler,
                    }
            except Exception as e:  # noqa: BLE001
                hata = f"İşlem sırasında hata oluştu: {e}"

    return render_template("index.html", sonuc=sonuc, hata=hata)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
