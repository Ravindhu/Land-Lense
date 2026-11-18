'use strict';

// Only group chats on the allowlist are read. Direct chats, status updates and unknown groups are ignored.
// JIDs for groups end in "@g.us". Set GROUP_ALLOWLIST to a comma-separated list of group JIDs.

function parseAllowlist(value) {
  if (!value) return new Set();
  return new Set(
    String(value)
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.endsWith('@g.us'))
  );
}

function isAllowedGroup(jid, allowlist) {
  if (typeof jid !== 'string' || !jid.endsWith('@g.us')) return false;
  return allowlist.has(jid);
}

module.exports = { parseAllowlist, isAllowedGroup };
