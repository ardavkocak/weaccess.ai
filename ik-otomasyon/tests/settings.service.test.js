const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { loadSettings, saveSettings } = require('../src/services/settings.service');

test('loadSettings normalizes sender and recipient values from environment', () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ik-settings-'));
  process.env.IK_SETTINGS_FILE = path.join(tempDir, 'settings.json');
  process.env.MAIL_FROM = 'sender@example.com';
  process.env.HR_EMAIL = 'one@example.com, two@example.com';

  const settings = loadSettings();

  assert.equal(settings.senderEmail, 'sender@example.com');
  assert.deepEqual(settings.recipientEmails, ['one@example.com', 'two@example.com']);
});

test('saveSettings writes the updated settings to disk', () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ik-settings-'));
  process.env.IK_SETTINGS_FILE = path.join(tempDir, 'settings.json');

  const saved = saveSettings({ senderEmail: 'ops@example.com', recipientEmails: ['a@example.com', 'b@example.com'] });
  const onDisk = JSON.parse(fs.readFileSync(process.env.IK_SETTINGS_FILE, 'utf8'));

  assert.equal(saved.senderEmail, 'ops@example.com');
  assert.deepEqual(onDisk.recipientEmails, ['a@example.com', 'b@example.com']);
});
