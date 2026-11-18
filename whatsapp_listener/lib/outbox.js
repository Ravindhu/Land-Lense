'use strict';

// Disk queue for payloads the webhook could not accept (webhook down, network error, 5xx).
// Stored as JSON lines. Duplicates by message_id are dropped on enqueue. The webhook is also
// idempotent, so a resend after a crash is safe.

const fs = require('fs');
const path = require('path');

class Outbox {
  constructor(file) {
    this.file = file;
    fs.mkdirSync(path.dirname(file), { recursive: true });
  }

  _read() {
    if (!fs.existsSync(this.file)) return [];
    return fs
      .readFileSync(this.file, 'utf8')
      .split('\n')
      .filter((line) => line.trim().length > 0)
      .map((line) => JSON.parse(line));
  }

  _write(items) {
    const tmp = `${this.file}.tmp`;
    fs.writeFileSync(tmp, items.map((i) => JSON.stringify(i)).join('\n') + (items.length ? '\n' : ''));
    fs.renameSync(tmp, this.file);
  }

  size() {
    return this._read().length;
  }

  enqueue(payload) {
    const items = this._read();
    if (items.some((i) => i.message_id === payload.message_id)) return false;
    items.push(payload);
    this._write(items);
    return true;
  }

  // send(payload) must resolve to true when the payload is accepted (201 or 200 duplicate).
  async flush(send) {
    const items = this._read();
    const remaining = [];
    let sent = 0;
    for (const item of items) {
      let ok = false;
      try {
        ok = await send(item);
      } catch (_err) {
        ok = false;
      }
      if (ok) sent += 1;
      else remaining.push(item);
    }
    this._write(remaining);
    return { sent, remaining: remaining.length };
  }
}

module.exports = { Outbox };
