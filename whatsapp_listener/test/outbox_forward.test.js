'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { Outbox } = require('../lib/outbox');
const { forward } = require('../lib/forward');

function tmpFile() {
  return path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'tn-outbox-')), 'outbox.jsonl');
}

const sample = (id) => ({ message_id: id, group_ref: '111@g.us', received_at: '2026-11-18T10:00:00.000Z', text: 'hello' });

test('outbox dedupes by message_id and keeps failures for retry', async () => {
  const outbox = new Outbox(tmpFile());
  assert.equal(outbox.enqueue(sample('A')), true);
  assert.equal(outbox.enqueue(sample('A')), false);
  outbox.enqueue(sample('B'));
  const sentIds = [];
  const result = await outbox.flush(async (p) => {
    if (p.message_id === 'B') return false;
    sentIds.push(p.message_id);
    return true;
  });
  assert.deepEqual(sentIds, ['A']);
  assert.equal(result.sent, 1);
  assert.equal(result.remaining, 1);
  assert.equal(outbox.size(), 1);
});

test('forward accepts 201 and 200 duplicate, refuses others, sends secret in header only', async () => {
  const seen = [];
  const fetchFn = async (url, opts) => {
    seen.push({ url, opts });
    return { status: seen.length === 1 ? 201 : seen.length === 2 ? 200 : 401 };
  };
  assert.equal(await forward(sample('X'), { url: 'http://127.0.0.1:8001/v1/listings/whatsapp', secret: 'S3', fetchFn }), true);
  assert.equal(await forward(sample('X'), { url: 'http://127.0.0.1:8001/v1/listings/whatsapp', secret: 'S3', fetchFn }), true);
  await assert.rejects(forward(sample('X'), { url: 'http://127.0.0.1:8001/v1/listings/whatsapp', secret: 'S3', fetchFn }));
  assert.equal(seen[0].opts.headers['x-webhook-secret'], 'S3');
  assert.ok(!seen[0].opts.body.includes('S3'));
});

test('forward refuses to run without url or secret', async () => {
  await assert.rejects(forward(sample('Y'), { url: '', secret: 'x' }));
});
