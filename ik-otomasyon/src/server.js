'use strict';

require('dotenv').config();
const path = require('path');
const express = require('express');
const multer = require('multer');
const cron = require('node-cron');
const { readEmployees } = require('./services/excel.service');
const reminders = require('./services/reminder.service');
const { loadSettings, saveSettings } = require('./services/settings.service');

const app = express();
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024, files: 1 },
});
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '../views'));
app.use(express.urlencoded({ extended: false }));
app.use('/public', express.static(path.join(__dirname, '../public')));

app.get('/', (req, res) => {
  const data = reminders.loadEmployees();
  const settings = loadSettings();
  res.render('dashboard', { ...data, settings, message: req.query.message || '', error: req.query.error || '', showSettings: false });
});

app.get('/ayarlar', (req, res) => {
  const password = req.query.password || '';
  if (password !== 'admin123') {
    return res.redirect('/?error=' + encodeURIComponent('Ayarlar sayfasına erişmek için doğru şifreyi girin.'));
  }
  const settings = loadSettings();
  return res.render('dashboard', { ...reminders.loadEmployees(), settings, message: '', error: '', showSettings: true });
});

app.post('/ayarlar/guncelle', (req, res) => {
  const password = req.body.password || '';
  if (password !== 'admin123') {
    return res.redirect('/?error=' + encodeURIComponent('Şifre yanlış. Ayarlar güncellenemedi.'));
  }

  const nextSettings = saveSettings({
    senderEmail: req.body.senderEmail,
    recipientEmails: req.body.recipientEmails,
    smtpHost: req.body.smtpHost,
    smtpPort: req.body.smtpPort,
    smtpUser: req.body.smtpUser,
    smtpPass: req.body.smtpPass,
    smtpSecure: req.body.smtpSecure === 'true',
    mailFrom: req.body.mailFrom,
  });

  return res.redirect('/?message=' + encodeURIComponent(`Ayarlar kaydedildi. Gönderen: ${nextSettings.senderEmail || '-'}, Alıcılar: ${nextSettings.recipientEmails.join(', ') || '-'}`));
});

// `any()` kullanımı, tarayıcı/form tarafında alan adı "excel" yerine "file"
// gibi farklı bir adla gönderilse bile dosyanın kaybolmasını önler.
app.post('/excel-yukle', upload.any(), (req, res) => {
  try {
    const file = req.files?.[0];
    if (!file?.buffer) throw new Error('Dosya seçilmedi. Lütfen .xlsx, .xls veya .csv dosyasını seçip yeniden deneyin.');
    if (!/\.(xlsx|xls|csv)$/i.test(file.originalname || '')) {
      throw new Error('Bu dosya türü desteklenmiyor. Lütfen .xlsx, .xls veya .csv dosyası seçin.');
    }
    const data = readEmployees(file.buffer);
      // Date nesneleri JSON'a ISO olarak yazılır ve cron sırasında tekrar Date'e çevrilir.
      reminders.saveEmployees(data);
      let message = `${data.employees.length} çalışan yüklendi.`;
      let errorMsg = '';
      if (data.missing && data.missing.length) {
        // Show as error banner to draw attention
        errorMsg = `Excel başlıklarında eksik alanlar: ${data.missing.join(', ')}. Bu alanlar boş olarak kaydedildi.`;
      }
      res.redirect(`/?message=${encodeURIComponent(message)}&error=${encodeURIComponent(errorMsg)}`);
  } catch (error) {
    res.redirect(`/?error=${encodeURIComponent(error.message)}`);
  }
});

// Multer'ın boyut/ağ isteği hatalarını kullanıcı için okunur hale getirir.
app.use((error, req, res, next) => {
  if (error instanceof multer.MulterError && error.code === 'LIMIT_FILE_SIZE') {
    return res.redirect('/?error=' + encodeURIComponent('Dosya boyutu en fazla 10 MB olabilir.'));
  }
  return next(error);
});

app.post('/hatirlatmalari-test-et', async (req, res) => {
  try {
    const result = await reminders.runTestReminders();
    res.redirect(`/?message=${encodeURIComponent(`Test başarılı: İK adresine 2 test e-postası gönderildi (${result.birthdays} doğum günü, ${result.anniversaries} plaket kaydı).`)}`);
  } catch (error) {
    res.redirect(`/?error=${encodeURIComponent(error.message)}`);
  }
});

// Her iş günü 09:00'da tarih kuralları ve gönderim tekrarı kontrol edilir.
cron.schedule('0 9 * * 1-5', () => reminders.runDailyReminders().catch(console.error), { timezone: process.env.TZ || 'Europe/Istanbul' });

app.listen(Number(process.env.PORT || 3002), () => console.log(`İK Otomasyon: http://localhost:${process.env.PORT || 3002}`));
