'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { buildPayload } = require('../lib/payload');

test('forwards only id, group, time and text', () => {
  const payload = buildPayload({
    key: { id: 'M1', remoteJid: '111@g.us', participant: '9876543210@s.whatsapp.net' },
    messageTimestamp: 1763450400,
    message: { conversation: 'Village: Ingur Survey 12/3' },
    pushName: 'Seller Name',
  });
  assert.deepEqual(Object.keys(payload).sort(), ['group_ref', 'message_id', 'received_at', 'text']);
  assert.equal(payload.message_id, 'M1');
  assert.ok(!JSON.stringify(payload).includes('9876543210'));
  assert.ok(!JSON.stringify(payload).includes('Seller Name'));
});

test('media-only messages are skipped', () => {
  const payload = buildPayload({ key: { id: 'M2', remoteJid: '111@g.us' }, message: { imageMessage: {} } });
  assert.equal(payload, null);
});

test('extended text is read and long text is capped', () => {
  const payload = buildPayload({
    key: { id: 'M3', remoteJid: '111@g.us' },
    message: { extendedTextMessage: { text: 'x'.repeat(5000) } },
  });
  assert.equal(payload.text.length, 2000);
});
