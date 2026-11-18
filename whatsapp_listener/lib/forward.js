'use strict';

// POST one payload to the webhook. The secret is sent only in the header and is never logged.
// Returns true when the webhook accepted it (201 created or 200 duplicate). Throws on other results.

async function forward(payload, { url, secret, fetchFn = fetch, timeoutMs = 10000 }) {
  if (!url || !secret) throw new Error('webhook url and secret must be set');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetchFn(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-webhook-secret': secret },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (res.status === 201 || res.status === 200) return true;
    throw new Error(`webhook refused with status ${res.status}`);
  } finally {
    clearTimeout(timer);
  }
}

module.exports = { forward };
