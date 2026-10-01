import test from 'node:test';
import assert from 'node:assert/strict';
import { isSafeSignal, sanitizeName, sanitizeRoom } from '../lib/validation.js';

test('sanitizeRoom maakt veilige hoofdletter-kamercodes', () => {
  assert.equal(sanitizeRoom('  test kamer!_42 '), 'TESTKAMER_42');
});

test('sanitizeName verwijdert simpele HTML-hoekhaken', () => {
  assert.equal(sanitizeName('<Michiel>'), 'Michiel');
  assert.equal(sanitizeName('   '), 'Gebruiker');
});

test('isSafeSignal weigert extreem grote signalen', () => {
  assert.equal(isSafeSignal({ candidate: 'x'.repeat(100) }), true);
  assert.equal(isSafeSignal({ candidate: 'x'.repeat(30_000) }), false);
});
