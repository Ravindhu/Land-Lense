'use strict';

// Build the webhook payload from a Baileys message. Only text is forwarded.
// Media, sender identity and participant JIDs are never forwarded.

function extractText(message) {
  if (!message) return null;
  if (typeof message.conversation === 'string') return message.conversation;
  if (message.extendedTextMessage && typeof message.extendedTextMessage.text === 'string') {
    return message.extendedTextMessage.text;
  }
  return null;
}

function buildPayload(msg) {
  const text = extractText(msg.message);
  if (!text || !msg.key || !msg.key.id || !msg.key.remoteJid) return null;
  const ts = Number(msg.messageTimestamp) || Math.floor(Date.now() / 1000);
  return {
    message_id: String(msg.key.id),
    group_ref: String(msg.key.remoteJid),
    received_at: new Date(ts * 1000).toISOString(),
    text: text.slice(0, 2000),
  };
}

module.exports = { buildPayload, extractText };
