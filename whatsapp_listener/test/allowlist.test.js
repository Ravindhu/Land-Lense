'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { parseAllowlist, isAllowedGroup } = require('../lib/allowlist');

test('only @g.us JIDs are kept in the allowlist', () => {
  const list = parseAllowlist('111-222@g.us, 999@s.whatsapp.net,333@g.us');
  assert.equal(list.size, 2);
  assert.ok(list.has('111-222@g.us'));
});

test('direct chats and unknown groups are rejected', () => {
  const list = parseAllowlist('111@g.us');
  assert.equal(isAllowedGroup('111@g.us', list), true);
  assert.equal(isAllowedGroup('555@g.us', list), false);
  assert.equal(isAllowedGroup('9876@s.whatsapp.net', list), false);
  assert.equal(isAllowedGroup('status@broadcast', list), false);
  assert.equal(isAllowedGroup(undefined, list), false);
});
