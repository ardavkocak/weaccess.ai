'use strict';

/** Dashboard ve görev eylemleri. */

const express = require('express');
const dashboardController = require('../controllers/dashboard.controller');

const router = express.Router();

router.get('/', dashboardController.showDashboard);

// Görevi bir sonraki aktif çalışana aktar.
router.post('/gorev/:dutyTypeId/sirayi-gec', dashboardController.skipTurn);

// Bugünkü Discord mesajını elle gönder (sırayı ilerletmez).
router.post('/gorev/:dutyTypeId/simdi-gonder', dashboardController.sendNow);

// Yanlış "Evet" düzeltmesi: bugünkü onayı sıfırla ve soruyu yeniden sor.
router.post('/gorev/:dutyTypeId/onayi-sifirla', dashboardController.resetConfirmation);

module.exports = router;
