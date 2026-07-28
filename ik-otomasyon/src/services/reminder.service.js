'use strict';

const fs = require('fs');
const path = require('path');
const { birthdayReminderDate, anniversaryDate, anniversaryReminderDate, toISODate } = require('./date.service');
const mail = require('./mail.service');

const dataDir = path.join(__dirname, '../../data');
const employeeFile = path.join(dataDir, 'employees.json');
const sentFile = path.join(dataDir, 'sent-reminders.json');

function ensureDataDir() { fs.mkdirSync(dataDir, { recursive: true }); }
function loadEmployees() { return fs.existsSync(employeeFile) ? JSON.parse(fs.readFileSync(employeeFile, 'utf8')) : { headers: [], employees: [] }; }
function saveEmployees(data) { ensureDataDir(); fs.writeFileSync(employeeFile, JSON.stringify(data, null, 2)); }
function loadSent() { return fs.existsSync(sentFile) ? new Set(JSON.parse(fs.readFileSync(sentFile, 'utf8'))) : new Set(); }
function saveSent(sent) { ensureDataDir(); fs.writeFileSync(sentFile, JSON.stringify([...sent], null, 2)); }

function hydrate(employee) {
  return { ...employee, birthDate: employee.birthDate ? new Date(employee.birthDate) : null, hireDate: employee.hireDate ? new Date(employee.hireDate) : null };
}

function list(items) { return `<ul>${items.map((item) => `<li>${item}</li>`).join('')}</ul>`; }

/**
 * Yönetici panelindeki test düğmesi için iki deneme e-postası üretir.
 * Bu işlev bilerek tarih koşullarına ve "daha önce gönderildi" kaydına bakmaz:
 * her tıklama SMTP/İK adresi kontrolü için yeni iki e-posta oluşturur.
 */
async function runTestReminders(today = new Date()) {
  const { employees } = loadEmployees();
  const people = employees.map(hydrate);
  const birthdayPeople = people.filter((person) => person.birthDate && person.birthDate.getMonth() === today.getMonth());
  const anniversaryPeople = people
    .filter((person) => person.hireDate)
    .map((person) => ({ person, years: today.getFullYear() - person.hireDate.getFullYear() }))
    .filter(({ years }) => years >= 3 && years % 3 === 0);

  await mail.sendReminder(
    '[TEST] Doğum günü kutlama hazırlığı',
    `<p>Bu bir test e-postasıdır. Bu ay doğan çalışanlar:</p>${list(birthdayPeople.length ? birthdayPeople.map((person) => person.fullName) : ['Bu ay doğum günü kaydı bulunamadı.'])}`
  );
  await mail.sendReminder(
    '[TEST] Plaket hazırlık hatırlatması',
    `<p>Bu bir test e-postasıdır. 3 yıl ve katlarına ulaşan çalışanlar:</p>${list(anniversaryPeople.length ? anniversaryPeople.map(({ person, years }) => `${person.fullName} — ${years}. yıl`) : ['Bu yıl için plaket kaydı bulunamadı.'])}`
  );

  return { birthdays: birthdayPeople.length, anniversaries: anniversaryPeople.length, emailsSent: 2 };
}

async function runDailyReminders(today = new Date()) {
  const dateKey = toISODate(today);
  const { employees } = loadEmployees();
  const sent = loadSent();
  const output = { birthdays: 0, anniversaries: 0, skipped: [] };

  // O ayın son cuma kutlaması için yalnızca hazırlık gününde mail atılır.
  if (toISODate(birthdayReminderDate(today.getFullYear(), today.getMonth())) === dateKey) {
    const people = employees.map(hydrate).filter((person) => person.birthDate && person.birthDate.getMonth() === today.getMonth());
    const key = `birthday:${today.getFullYear()}-${today.getMonth() + 1}`;
    if (people.length && !sent.has(key)) {
      await mail.sendReminder('Doğum günü kutlama hazırlığı', `<p>Bu ay doğan çalışanlar:</p>${list(people.map((person) => person.fullName))}`);
      sent.add(key); output.birthdays = people.length;
    }
  }

  for (const raw of employees) {
    const person = hydrate(raw);
    if (!person.hireDate) continue;
    const years = today.getFullYear() - person.hireDate.getFullYear();
    if (years < 3 || years % 3 !== 0) continue;
    const milestone = anniversaryDate(person.hireDate, today.getFullYear());
    if (toISODate(anniversaryReminderDate(milestone)) !== dateKey) continue;
    const key = `anniversary:${person.rowNumber}:${today.getFullYear()}`;
    if (sent.has(key)) continue;
    await mail.sendReminder('Plaket hazırlık hatırlatması', `<p>Plaket hazırlanacak çalışan:</p>${list([`${person.fullName} — ${years}. yıl`])}`);
    sent.add(key); output.anniversaries += 1;
  }
  saveSent(sent);
  return output;
}

module.exports = { loadEmployees, saveEmployees, runDailyReminders, runTestReminders };
