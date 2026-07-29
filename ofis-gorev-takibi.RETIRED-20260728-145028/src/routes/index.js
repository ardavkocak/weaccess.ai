'use strict';

/**
 * Rota toplayıcı.
 *
 * Giriş rotaları herkese açıktır; geri kalan tüm panel rotaları `requireAuth`
 * arkasındadır. Koruma burada tek noktadan uygulanır, böylece yeni bir sayfa
 * eklerken yetki kontrolünü unutmak mümkün olmaz.
 */

const express = require('express');
const { requireAuth } = require('../middleware/auth');

const authRoutes = require('./auth.routes');
const dashboardRoutes = require('./dashboard.routes');
const employeeRoutes = require('./employee.routes');
const rotationRoutes = require('./rotation.routes');
const historyRoutes = require('./history.routes');
const settingsRoutes = require('./settings.routes');
const mealRoutes = require('./meal.routes');

const router = express.Router();

// --- Herkese açık ---
router.use(authRoutes);

// --- Yalnızca admin ---
router.use(requireAuth, dashboardRoutes);
router.use(requireAuth, employeeRoutes);
router.use(requireAuth, rotationRoutes);
router.use(requireAuth, historyRoutes);
router.use(requireAuth, settingsRoutes);
// Yemek menüsü modülü — görev takibinden bağımsız; bu satır kaldırılırsa modül
// tamamen devre dışı kalır, sistemin geri kalanı etkilenmez.
router.use(requireAuth, mealRoutes);

module.exports = router;
