'use strict';

/** Görev Sırası sayfası — sıranın tamamı ve manuel müdahaleler. */

const dutyTypeService = require('../services/dutyType.service');
const rotationService = require('../services/rotation.service');
const employeeService = require('../services/employee.service');
const scheduledMessageService = require('../services/scheduledMessage.service');

/** GET /gorev-sirasi */
function showQueue(req, res) {
  const dutyTypes = dutyTypeService.getAll();

  // Birden fazla görev türü olabilir; ?tur=<id> ile seçilir, yoksa varsayılan.
  const requestedId = Number(req.query.tur);
  const dutyType = dutyTypes.find((d) => d.id === requestedId) ?? dutyTypeService.getDefault();

  if (!dutyType) {
    return res.render('pages/queue', {
      pageTitle: 'Görev Sırası',
      activeNav: 'queue',
      dutyTypes: [],
      dutyType: null,
      overview: null,
      dutyMessage: null,
      counts: employeeService.getCounts(),
    });
  }

  return res.render('pages/queue', {
    pageTitle: 'Görev Sırası',
    activeNav: 'queue',
    dutyTypes,
    dutyType,
    overview: rotationService.getOverview(dutyType.id),
    // Şablon önizlemesi: şablonlar artık scheduled_messages'ta yaşıyor.
    dutyMessage: scheduledMessageService.getDutyMessageFor(dutyType.id),
    counts: employeeService.getCounts(),
  });
}

module.exports = { showQueue };
