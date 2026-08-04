// Aylik calisma saati ve izin takip uygulamasi - Express backend.

const express = require('express');
const multer = require('multer');
const path = require('path');

const {
  pdfPersonelCikar,
  wordPersonelCikar,
  gorselOcr,
  izinKayitlariCikar,
  isimEslesir,
} = require('./parser');
const { aylikOzet } = require('./hesaplama');
const { resmiTatilSeti } = require('./resmiTatiller');

const app = express();
const PORT = process.env.PORT || 3000;

// Dosyalar bellekte tutulur (diske yazilmaz).
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 15 * 1024 * 1024 }, // 15 MB
});

app.use(express.static(path.join(__dirname, 'public')));

const PDF_TUR = 'application/pdf';
const WORD_TURLERI = [
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
];
const GORSEL_TURLERI = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];

app.post(
  '/hesapla',
  upload.fields([
    { name: 'calismaDosyasi', maxCount: 1 },
    { name: 'izinGorseli', maxCount: 1 },
  ]),
  async (req, res) => {
    try {
      const calismaFile = req.files?.calismaDosyasi?.[0];
      const izinFile = req.files?.izinGorseli?.[0];

      if (!calismaFile) {
        return res
          .status(400)
          .json({ hata: 'Calisma dosyasi (PDF/Word) gerekli.' });
      }
      if (!izinFile) {
        return res.status(400).json({ hata: 'Izin gorseli (PNG/JPEG/WebP) gerekli.' });
      }
      if (!GORSEL_TURLERI.includes(izinFile.mimetype)) {
        return res.status(400).json({
          hata: 'Izin dosyasi PNG/JPEG/WebP gorsel olmali. Gelen: ' +
            izinFile.mimetype,
        });
      }

      // Ay/yil: formdan gelir, yoksa bugunun degeri.
      const simdi = new Date();
      const yil = parseInt(req.body.yil, 10) || simdi.getFullYear();
      const ay = parseInt(req.body.ay, 10) || simdi.getMonth() + 1;

      // 1) Calisma dosyasindan personel + toplam sure.
      let personeller;
      if (calismaFile.mimetype === PDF_TUR) {
        personeller = await pdfPersonelCikar(calismaFile.buffer);
      } else if (WORD_TURLERI.includes(calismaFile.mimetype)) {
        personeller = await wordPersonelCikar(calismaFile.buffer);
      } else {
        return res.status(400).json({
          hata: 'Calisma dosyasi PDF veya Word olmali. Gelen: ' +
            calismaFile.mimetype,
        });
      }

      if (!personeller.length) {
        return res.status(422).json({
          hata:
            'Calisma dosyasindan personel okunamadi. Dosyanin Muafiyet Raporu formatinda oldugundan emin olun.',
        });
      }

      // 2) Izin gorselinden izin kayitlari (isim + tarih araligi).
      //    Resmi tatile denk gelen hafta ici gunler izinden dusulur; izin araligi
      //    komsu yila tasabildigi icin yil-1..yil+1 tatillerini kapsariz.
      const resmiSet = resmiTatilSeti(yil - 1, yil, yil + 1);
      const ocrMetin = await gorselOcr(izinFile.buffer);
      const izinler = izinKayitlariCikar(ocrMetin, resmiSet);

      // 3) Aylik ozet (kisi bazli, calismasi gereken saat dahil).
      const ozet = aylikOzet({ personeller, izinler, isimEslesir, yil, ay });

      res.json({
        ozet,
        detay: {
          personelSayisi: personeller.length,
          izinKaydiSayisi: izinler.length,
          ocrMetin: ocrMetin.slice(0, 400),
        },
      });
    } catch (err) {
      console.error(err);
      res.status(500).json({ hata: 'Islem sirasinda hata: ' + err.message });
    }
  }
);

app.listen(PORT, () => {
  console.log(`Sunucu calisiyor: http://localhost:${PORT}`);
});
