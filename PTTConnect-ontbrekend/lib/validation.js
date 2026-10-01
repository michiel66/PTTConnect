export function sanitizeRoom(value) {
  return String(value ?? '')
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9_-]/g, '')
    .slice(0, 32);
}

export function sanitizeName(value) {
  const name = String(value ?? '')
    .trim()
    .replace(/[<>]/g, '')
    .slice(0, 32);

  return name || 'Gebruiker';
}

export function isSafeSignal(data) {
  if (!data || typeof data !== 'object') return false;
  const serialized = JSON.stringify(data);
  return serialized.length <= 24_000;
}
