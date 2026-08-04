'use strict';

/** Görev sırası rotaları. */

const express = require('express');
const rotationController = require('../controllers/rotation.controller');

const router = express.Router();

router.get('/gorev-sirasi', rotationController.showQueue);

module.exports = router;
