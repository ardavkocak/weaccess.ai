# -*- coding: utf-8 -*-
"""
Banka Sözleşme & Form -> Excel otomasyonu.

Kullanım:
    python main.py <URL>
    python main.py <URL> -o cikti.xlsx

Örnek:
    python main.py "https://www.tbank.com.tr/hakkimizda/detay/Sozlesmeler-ve-Formlar/188/275/0/"
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

from scraper import kaz
from excel_export import excele_yaz


def _varsayilan_dosya_adi(url: str) -> str:
    """URL'den okunabilir bir varsayılan dosya adı üretir."""
    alan = urlparse(url).netloc.replace("www.", "").split(".")[0] or "banka"
    alan = re.sub(r"[^a-zA-Z0-9_-]", "", alan)
    return f"{alan}_sozlesmeler_formlar_{datetime.now():%Y%m%d_%H%M}.xlsx"


def calistir(url: str, cikti: str | None = None) -> str:
    print(f"[1/3] Sayfa indiriliyor: {url}")
    belgeler = kaz(url)

    if not belgeler:
        print("  ! Uyarı: Sayfada hiç doküman (PDF/DOC/XLS) bağlantısı bulunamadı.")
        print("    Sayfa JavaScript ile mi yükleniyor? URL doğru mu?")
        sys.exit(2)

    sozlesme = sum(1 for b in belgeler if b.kategori == "Sözleşme")
    form = sum(1 for b in belgeler if b.kategori == "Form")
    diger = len(belgeler) - sozlesme - form
    print(f"[2/3] {len(belgeler)} belge bulundu "
          f"(Sözleşme: {sozlesme}, Form: {form}, Diğer: {diger}).")

    cikti = cikti or _varsayilan_dosya_adi(url)
    yol = excele_yaz(belgeler, cikti, kaynak_url=url)
    print(f"[3/3] Excel'e kaydedildi: {yol}")
    return yol


def main() -> None:
    ayrıstırıcı = argparse.ArgumentParser(
        description="Bir bankanın sözleşme & form sayfasındaki dokümanları Excel'e kaydeder."
    )
    ayrıstırıcı.add_argument("url", help="Sözleşmeler ve Formlar sayfasının URL'si")
    ayrıstırıcı.add_argument(
        "-o", "--output", dest="cikti", default=None,
        help="Çıktı Excel dosyası (varsayılan: otomatik ad)"
    )
    args = ayrıstırıcı.parse_args()

    try:
        calistir(args.url, args.cikti)
    except KeyboardInterrupt:
        print("\nİptal edildi.")
        sys.exit(130)
    except Exception as hata:  # noqa: BLE001
        print(f"HATA: {hata}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
