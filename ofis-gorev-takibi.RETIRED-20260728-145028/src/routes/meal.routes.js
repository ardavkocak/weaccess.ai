'use strict';

/**
 * Yemek menüsü rotaları.
 *
 * Yükleme isteğinin multipart gövdesi `middleware/upload.js` tarafından, CSRF
 * kontrolünden ÖNCE ayrıştırılır (bkz. app.js). Burada ek bir middleware yoktur;
 * controller hazır `req.file` alır.
 */

const express = require('express');
const mealController = require('../controllers/meal.controller');

const router = express.Router();

router.get('/yemek-menusu', mealController.showMeals);
// Katılım kartlarının/listelerinin canlı tazelenmesi (panel JS'i çağırır).
router.get('/yemek-menusu/katilim.json', mealController.participationJson);
router.post('/yemek-menusu/yukle', mealController.uploadMenu);
router.post('/yemek-menusu/gonder', mealController.sendNow);
router.post('/yemek-menusu/saat', mealController.updateTime);
router.post('/yemek-menusu/oylari-sifirla', mealController.resetVotes);
router.post('/yemek-menusu/sil', mealController.removeAll);
// Tarih parametreli silme en sonda: /sil gibi sabit yolları gölgelemesin.
router.post('/yemek-menusu/:date/sil', mealController.removeOne);

module.exports = router;
