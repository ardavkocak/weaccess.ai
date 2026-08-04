'use strict';

/** Giriş / çıkış rotaları (kimlik doğrulama gerektirmez). */

const express = require('express');
const authController = require('../controllers/auth.controller');
const { redirectIfAuthenticated, requireAuth } = require('../middleware/auth');

const router = express.Router();

router.get('/giris', redirectIfAuthenticated, authController.showLogin);
router.post('/giris', redirectIfAuthenticated, authController.login);
router.post('/cikis', requireAuth, authController.logout);

module.exports = router;
