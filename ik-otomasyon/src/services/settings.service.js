'use strict';

const fs = require('fs');
const path = require('path');

const dataDir = path.join(__dirname, '../../data');
const defaultSettingsFile = path.join(dataDir, 'settings.json');
function settingsFilePath() {
  return process.env.IK_SETTINGS_FILE || defaultSettingsFile;
}

function ensureDataDir() {
  fs.mkdirSync(dataDir, { recursive: true });
}

function toRecipientList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => `${item}`.trim()).filter(Boolean);
  }
  if (typeof value === 'string') {
    return value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean);
  }
  return [];
}

function loadSettings() {
  ensureDataDir();
  const defaults = {
    senderEmail: (process.env.MAIL_FROM || process.env.SMTP_USER || '').trim(),
    recipientEmails: toRecipientList(process.env.HR_EMAIL || ''),
    smtpHost: (process.env.SMTP_HOST || '').trim(),
    smtpPort: process.env.SMTP_PORT ? Number(process.env.SMTP_PORT) : undefined,
    smtpUser: (process.env.SMTP_USER || '').trim(),
    smtpPass: (process.env.SMTP_PASS || '').trim(),
    smtpSecure: process.env.SMTP_SECURE === 'true',
    mailFrom: (process.env.MAIL_FROM || '').trim(),
  };

  if (!fs.existsSync(settingsFilePath())) {
    return defaults;
  }

  try {
    const saved = JSON.parse(fs.readFileSync(settingsFilePath(), 'utf8'));
    return {
      senderEmail: (saved.senderEmail || defaults.senderEmail).trim(),
      recipientEmails: toRecipientList(saved.recipientEmails || defaults.recipientEmails),
      smtpHost: (saved.smtpHost || defaults.smtpHost || '').trim(),
      smtpPort: saved.smtpPort !== undefined ? Number(saved.smtpPort) : defaults.smtpPort,
      smtpUser: (saved.smtpUser || defaults.smtpUser || '').trim(),
      smtpPass: (saved.smtpPass || defaults.smtpPass || '').trim(),
      smtpSecure: saved.smtpSecure === true || defaults.smtpSecure === true,
      mailFrom: (saved.mailFrom || defaults.mailFrom || '').trim(),
    };
  } catch (error) {
    return defaults;
  }
}

function saveSettings(settings) {
  ensureDataDir();
  const nextSettings = {
    senderEmail: `${settings?.senderEmail || ''}`.trim(),
    recipientEmails: toRecipientList(settings?.recipientEmails || []),
    smtpHost: `${settings?.smtpHost || ''}`.trim(),
    smtpPort: settings?.smtpPort ? Number(settings.smtpPort) : undefined,
    smtpUser: `${settings?.smtpUser || ''}`.trim(),
    smtpPass: `${settings?.smtpPass || ''}`.trim(),
    smtpSecure: settings?.smtpSecure === 'true' || settings?.smtpSecure === true,
    mailFrom: `${settings?.mailFrom || ''}`.trim(),
  };
  fs.writeFileSync(settingsFilePath(), JSON.stringify(nextSettings, null, 2));
  return nextSettings;
}

module.exports = { loadSettings, saveSettings, toRecipientList };
