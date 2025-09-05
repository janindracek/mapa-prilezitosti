// Minimal namespaced logger; easy to grep and disable later.
const NS = "[mp]"; // mapa-prilezitosti

export const log = {
  info: (...args) => console.info(NS, ...args),
  warn: (...args) => console.warn(NS, ...args),
  error: (...args) => console.error(NS, ...args),
};