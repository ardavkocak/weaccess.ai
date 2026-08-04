'use strict';

/** Ayarlar rotaları. */

const express = require('express');
const settingsController = require('../controllers/settings.controller');

const router = express.Router();

router.get('/ayarlar', settingsController.showSettings);
router.post('/ayarlar', settingsController.updateSettings);
// Yönetici kullanıcı adı / parola değişikliği (ayrı form: mevcut parola sorulur).
router.post('/ayarlar/yonetici', settingsController.updateAdminAccount);
router.post('/ayarlar/test', settingsController.testDiscord);
router.post('/ayarlar/mesaj/:id/gonder', settingsController.sendMessageNow);
router.post('/ayarlar/token-sil', settingsController.clearToken);

module.exports = router;
