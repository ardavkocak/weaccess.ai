'use strict';

const nodemailer = require('nodemailer');
const { loadSettings } = require('./settings.service');

function configured() {
  const s = loadSettings();
  const host = s.smtpHost || process.env.SMTP_HOST;
  const user = s.smtpUser || process.env.SMTP_USER;
  const pass = s.smtpPass || process.env.SMTP_PASS;
  const recipients = (s.recipientEmails && s.recipientEmails.length) ? s.recipientEmails : (process.env.HR_EMAIL ? process.env.HR_EMAIL.split(/[,\n]/).map((i)=>i.trim()).filter(Boolean) : []);
  return Boolean(host && user && pass && recipients.length);
}

function transporter() {
  const s = loadSettings();
  const host = s.smtpHost || process.env.SMTP_HOST;
  const port = s.smtpPort || Number(process.env.SMTP_PORT || 587);
  const secure = (s.smtpSecure === true) || (process.env.SMTP_SECURE === 'true');
  const user = s.smtpUser || process.env.SMTP_USER;
  const pass = s.smtpPass || process.env.SMTP_PASS;
  const auth = user && pass ? { user, pass } : undefined;
  const opts = { host, port, secure };
  if (auth) opts.auth = auth;
  return nodemailer.createTransport(opts);
}

async function sendReminder(subject, html) {
  if (!configured()) throw new Error('E-posta ayarları eksik. Lütfen ayarlardan SMTP ve alıcı bilgilerini girin.');
  const settings = loadSettings();
  const recipients = settings.recipientEmails.length ? settings.recipientEmails : (process.env.HR_EMAIL ? process.env.HR_EMAIL.split(/[,\n]/).map((i)=>i.trim()).filter(Boolean) : []);
  const from = settings.mailFrom || settings.senderEmail || process.env.MAIL_FROM || process.env.SMTP_USER;
  return transporter().sendMail({ from, to: recipients.join(','), subject, html });
}

module.exports = { configured, sendReminder };
