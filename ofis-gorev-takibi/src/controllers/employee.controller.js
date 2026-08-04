'use strict';

/** Personel yönetimi — ekleme, düzenleme, silme, aktif/pasif, sıralama. */

const employeeService = require('../services/employee.service');
const dutyTypeService = require('../services/dutyType.service');
const rotationService = require('../services/rotation.service');
const { safeRedirect } = require('../utils/redirect');

/** GET /personeller */
function listEmployees(req, res) {
  res.render('pages/employees', {
    pageTitle: 'Personeller',
    activeNav: 'employees',
    employees: employeeService.getAll(),
    counts: employeeService.getCounts(),
    // Form durumu: hata sonrası girilen değerleri geri doldurmak için.
    formErrors: [],
    formValues: { full_name: '', discord_user_id: '', is_active: 'on', position: '' },
    editing: null,
  });
}

/** GET /personeller/:id/duzenle */
function showEditForm(req, res) {
  const employee = employeeService.getById(Number(req.params.id));

  if (!employee) {
    req.flash('error', 'Çalışan bulunamadı.');
    return res.redirect('/personeller');
  }

  return res.render('pages/employees', {
    pageTitle: 'Personel Düzenle',
    activeNav: 'employees',
    employees: employeeService.getAll(),
    counts: employeeService.getCounts(),
    formErrors: [],
    formValues: {
      full_name: employee.full_name,
      discord_user_id: employee.discord_user_id ?? '',
      is_active: employee.is_active === 1 ? 'on' : '',
    },
    editing: employee,
  });
}

/**
 * POST /personeller — yeni çalışan.
 *
 * `position` alanı boşsa çalışan sıranın sonuna eklenir (eski davranış). Bir
 * numara seçildiyse o konuma yerleştirilir ve sonrasındaki herkes bir basamak
 * aşağı kayar.
 */
function createEmployee(req, res) {
  const { errors, data } = employeeService.validate(req.body);

  if (errors.length > 0) {
    return res.status(400).render('pages/employees', {
      pageTitle: 'Personeller',
      activeNav: 'employees',
      employees: employeeService.getAll(),
      counts: employeeService.getCounts(),
      formErrors: errors,
      formValues: req.body,
      editing: null,
    });
  }

  // Boş string = "sona ekle"; servis null'ı sona ekleme olarak yorumlar.
  const requested = String(req.body.position ?? '').trim();
  const employee = employeeService.create(data, requested === '' ? null : requested);

  // İlk çalışan ekleniyorsa sıra boştur; hemen ona atansın ki dashboard
  // "görevli yok" demeye devam etmesin.
  const dutyType = dutyTypeService.getDefault();
  if (dutyType) rotationService.resolveCurrent(dutyType.id);

  const isLast = employee.position === employeeService.getTotal();
  req.flash('success', isLast
    ? `${employee.full_name} sıranın sonuna eklendi.`
    : `${employee.full_name} ${employee.position}. sıraya eklendi. Sonraki personeller bir basamak kaydırıldı.`);

  return res.redirect('/personeller');
}

/** POST /personeller/:id — düzenleme kaydı. */
function updateEmployee(req, res) {
  const id = Number(req.params.id);
  const employee = employeeService.getById(id);

  if (!employee) {
    req.flash('error', 'Çalışan bulunamadı.');
    return res.redirect('/personeller');
  }

  const { errors, data } = employeeService.validate(req.body, id);

  if (errors.length > 0) {
    return res.status(400).render('pages/employees', {
      pageTitle: 'Personel Düzenle',
      activeNav: 'employees',
      employees: employeeService.getAll(),
      counts: employeeService.getCounts(),
      formErrors: errors,
      formValues: req.body,
      editing: employee,
    });
  }

  const updated = employeeService.update(id, data);

  // Pasife alındıysa ve sıra ondaysa otomatik atlansın.
  const dutyType = dutyTypeService.getDefault();
  if (dutyType) rotationService.resolveCurrent(dutyType.id);

  req.flash('success', `${updated.full_name} güncellendi.`);
  return res.redirect('/personeller');
}

/** POST /personeller/:id/durum — aktif/pasif değiştir. */
function toggleActive(req, res) {
  const id = Number(req.params.id);
  const employee = employeeService.toggleActive(id);

  if (!employee) {
    req.flash('error', 'Çalışan bulunamadı.');
    return res.redirect('/personeller');
  }

  // Pasife alınan kişi sıradaysa rotasyon onu atlasın.
  const dutyType = dutyTypeService.getDefault();
  if (dutyType) rotationService.resolveCurrent(dutyType.id);

  const state = employee.is_active === 1 ? 'aktif' : 'pasif';
  req.flash('success', `${employee.full_name} ${state} yapıldı.` +
    (employee.is_active === 0 ? ' Görev sırasından çıkarıldı.' : ''));

  return res.redirect(safeRedirect(req.body.redirectTo, '/personeller'));
}

/** POST /personeller/:id/sil */
function deleteEmployee(req, res) {
  const id = Number(req.params.id);
  const employee = employeeService.getById(id);

  if (!employee) {
    req.flash('error', 'Çalışan bulunamadı.');
    return res.redirect('/personeller');
  }

  employeeService.remove(id);

  // Silinen kişi sıradaysa `current` NULL olur; sonraki aktife kaydır.
  const dutyType = dutyTypeService.getDefault();
  if (dutyType) rotationService.resolveCurrent(dutyType.id);

  req.flash('success', `${employee.full_name} silindi. Görev geçmişindeki kayıtları korundu.`);
  return res.redirect('/personeller');
}

/** POST /personeller/:id/tasi — sırada yukarı/aşağı taşı. */
function moveEmployee(req, res) {
  const id = Number(req.params.id);
  const direction = req.body.direction === 'up' ? 'up' : 'down';

  const moved = employeeService.move(id, direction);
  if (!moved) {
    // Taşıma yalnızca çalışan listenin ucundaysa başarısız olur.
    req.flash('error', direction === 'up'
      ? 'Çalışan zaten sıranın başında.'
      : 'Çalışan zaten sıranın sonunda.');
  }

  return res.redirect(safeRedirect(req.body.redirectTo, '/gorev-sirasi'));
}

/**
 * POST /personeller/:id/discord-id — yalnızca Discord ID'sini günceller.
 *
 * Listeden çıkmadan ID girebilmek için vardır: 20+ kişiye ID eklerken her biri
 * için düzenleme sayfasına gidip dönmek yorucudur. Doğrulama tam kayıt akışıyla
 * AYNI `validate()` fonksiyonundan geçer (format + benzersizlik), böylece iki
 * yol arasında kural farkı oluşmaz.
 */
function setDiscordId(req, res) {
  const id = Number(req.params.id);
  const employee = employeeService.getById(id);

  if (!employee) {
    req.flash('error', 'Çalışan bulunamadı.');
    return res.redirect('/personeller');
  }

  // Diğer alanları mevcut değerleriyle gönderiyoruz; yalnızca ID değişiyor.
  const { errors, data } = employeeService.validate({
    full_name: employee.full_name,
    discord_user_id: req.body.discord_user_id,
    is_active: employee.is_active === 1 ? '1' : '',
  }, id);

  if (errors.length > 0) {
    req.flash('error', `${employee.full_name}: ${errors.join(' ')}`);
  } else {
    employeeService.update(id, data);
    req.flash('success', data.discord_user_id
      ? `${employee.full_name} için Discord ID kaydedildi; mesajlarda etiketlenecek.`
      : `${employee.full_name} için Discord ID kaldırıldı.`);
  }

  return res.redirect(safeRedirect(req.body.redirectTo, '/personeller'));
}

/**
 * POST /personeller/:id/sira — çalışanı doğrudan girilen sıra numarasına taşır.
 * Sıra numarası kutusunun ("3" yazıp Enter) ve JavaScript kapalıyken
 * sürükle-bırakın yerine geçen yolun uç noktasıdır.
 */
function setPosition(req, res) {
  const id = Number(req.params.id);
  const result = employeeService.moveToPosition(id, req.body.position);

  if (!result.ok) {
    req.flash('error', result.message);
  } else if (result.from === result.to) {
    req.flash('success', `${result.employee.full_name} zaten ${result.to}. sırada.`);
  } else {
    req.flash('success', `${result.employee.full_name} ${result.to}. sıraya taşındı.`);
  }

  return res.redirect(safeRedirect(req.body.redirectTo, '/gorev-sirasi'));
}

/**
 * POST /gorev-sirasi/siralama — sürükle-bırak ile oluşan yeni sıranın tamamını
 * kaydeder. `order` alanı virgülle ayrılmış çalışan ID listesidir.
 */
function reorderEmployees(req, res) {
  const ids = String(req.body.order ?? '')
    .split(',')
    .map((value) => Number(value.trim()))
    .filter((value) => Number.isInteger(value) && value > 0);

  const result = employeeService.reorder(ids);
  req.flash(result.ok ? 'success' : 'error',
    result.ok ? 'Görev sırası güncellendi.' : result.message);

  return res.redirect(safeRedirect(req.body.redirectTo, '/gorev-sirasi'));
}

module.exports = {
  listEmployees,
  showEditForm,
  createEmployee,
  updateEmployee,
  toggleActive,
  deleteEmployee,
  moveEmployee,
  setPosition,
  setDiscordId,
  reorderEmployees,
};
