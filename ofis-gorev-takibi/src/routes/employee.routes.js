'use strict';

/** Personel yönetimi rotaları. */

const express = require('express');
const employeeController = require('../controllers/employee.controller');

const router = express.Router();

router.get('/personeller', employeeController.listEmployees);
router.get('/personeller/:id/duzenle', employeeController.showEditForm);

router.post('/personeller', employeeController.createEmployee);
router.post('/personeller/:id', employeeController.updateEmployee);
router.post('/personeller/:id/durum', employeeController.toggleActive);
router.post('/personeller/:id/sil', employeeController.deleteEmployee);
router.post('/personeller/:id/tasi', employeeController.moveEmployee);
router.post('/personeller/:id/sira', employeeController.setPosition);

// Listeden çıkmadan Discord ID girme (toplu ID ekleme için).
router.post('/personeller/:id/discord-id', employeeController.setDiscordId);

// Sürükle-bırak ile yeniden sıralama (tüm listeyi tek seferde kaydeder).
router.post('/gorev-sirasi/siralama', employeeController.reorderEmployees);

module.exports = router;
