'use strict';

// Read-only WhatsApp listener (Phase 6). Runs on the secondary SIM only.
// It reads text from allowlisted groups and forwards it to the webhook. It never sends a message:
// there is no call to sendMessage anywhere in this file (docs/SECURITY_AND_LEGAL.md section 5).
// Baileys is unofficial and may get the account banned. The owner accepted that risk.

const path = require('path');
const { parseAllowlist, isAllowedGroup } = require('./lib/allowlist');
const { buildPayload } = require('./lib/payload');
const { Outbox } = require('./lib/outbox');
const { forward } = require('./lib/forward');

const ROOT = path.join(__dirname, '..');
const AUTH_DIR = path.join(ROOT, 'auth_session');
const STORAGE = process.env.TN_INTEL_STORAGE || path.join(ROOT, 'storage');
const WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://127.0.0.1:8001/v1/listings/whatsapp';
const FLUSH_EVERY_MS = 60 * 1000;
const RECONNECT_MS = 5 * 1000;

function log(msg, extra = {}) {
  // Counts and IDs only. Never log message text, phone numbers or the secret.
  console.log(JSON.stringify({ ts: new Date().toISOString(), msg, ...extra }));
}

async function main() {
  const allowlist = parseAllowlist(process.env.GROUP_ALLOWLIST);
  const secret = process.env.WEBHOOK_SECRET;
  if (allowlist.size === 0) {
    log('no allowed groups; set GROUP_ALLOWLIST to group JIDs ending in @g.us');
    process.exit(1);
  }
  if (!secret) {
    log('WEBHOOK_SECRET is not set');
    process.exit(1);
  }

  // Load Baileys here so tests and lint do not need the package installed.
  const baileys = require('baileys');
  const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = baileys;
  const outbox = new Outbox(path.join(STORAGE, 'whatsapp_outbox.jsonl'));

  async function send(payload) {
    return forward(payload, { url: WEBHOOK_URL, secret });
  }

  async function flush() {
    const result = await outbox.flush(send);
    if (result.sent || result.remaining) log('outbox flushed', result);
  }

  async function connect() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const sock = makeWASocket({ auth: state, browser: ['tn-intel', 'Chrome', '1.0'] });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
      const { connection, lastDisconnect } = update;
      if (update.qr) log('scan the QR code with the secondary SIM (printed to terminal)');
      if (connection === 'open') log('connected');
      if (connection === 'close') {
        const code = lastDisconnect && lastDisconnect.error && lastDisconnect.error.output && lastDisconnect.error.output.statusCode;
        if (code === DisconnectReason.loggedOut) {
          log('logged out; pair again. Stopping reconnects.');
          return;
        }
        log('disconnected; reconnecting', { code: code || null });
        setTimeout(connect, RECONNECT_MS);
      }
    });

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
      if (type !== 'notify') return;
      for (const msg of messages) {
        if (msg.key && msg.key.fromMe) continue;
        if (!isAllowedGroup(msg.key && msg.key.remoteJid, allowlist)) continue;
        const payload = buildPayload(msg);
        if (!payload) continue;
        try {
          await send(payload);
          log('forwarded', { message_id: payload.message_id });
        } catch (err) {
          outbox.enqueue(payload);
          log('queued for retry', { message_id: payload.message_id, reason: err.message });
        }
      }
    });
  }

  setInterval(() => flush().catch((e) => log('flush failed', { reason: e.message })), FLUSH_EVERY_MS);
  await connect();
  log('listener started', { groups: allowlist.size });
}

process.on('SIGTERM', () => process.exit(0));
main().catch((err) => {
  log('fatal', { reason: err.message });
  process.exit(1);
});
