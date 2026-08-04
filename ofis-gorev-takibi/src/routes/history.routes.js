'use strict';

/** Görev geçmişi rotaları. */

const express = require('express');
const historyController = require('../controllers/history.controller');

const router = express.Router();

router.get('/gorev-gecmisi', historyController.showHistory);

module.exports = router;
