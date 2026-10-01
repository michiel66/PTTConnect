import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { WebSocketServer, WebSocket } from 'ws';
import { isSafeSignal, sanitizeName, sanitizeRoom } from './lib/validation.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const publicDir = path.join(__dirname, 'public');
const port = Number(process.env.PORT || 3000);

function parseIceServers() {
  const fallback = [{ urls: 'stun:stun.l.google.com:19302' }];
  if (!process.env.ICE_SERVERS_JSON) return fallback;

  try {
    const parsed = JSON.parse(process.env.ICE_SERVERS_JSON);
    return Array.isArray(parsed) && parsed.length ? parsed : fallback;
  } catch {
    console.warn('ICE_SERVERS_JSON is ongeldig; standaard STUN wordt gebruikt.');
    return fallback;
  }
}

const iceServers = parseIceServers();

const contentTypes = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.svg': 'image/svg+xml; charset=utf-8'
};

function setSecurityHeaders(res) {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Permissions-Policy', 'microphone=(self), camera=()');
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
}

async function serveStatic(req, res) {
  let requestPath = new URL(req.url, `http://${req.headers.host || 'localhost'}`).pathname;
  if (requestPath === '/') requestPath = '/index.html';

  if (requestPath === '/health') {
    setSecurityHeaders(res);
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ ok: true, app: 'PTTConnect' }));
    return;
  }

  if (requestPath === '/api/config') {
    setSecurityHeaders(res);
    res.setHeader('Cache-Control', 'no-store');
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ iceServers }));
    return;
  }

  const normalized = path.posix.normalize(requestPath).replace(/^\/+/, '');
  const filePath = path.join(publicDir, normalized);

  if (!filePath.startsWith(publicDir)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  try {
    const stat = await fs.stat(filePath);
    if (!stat.isFile()) throw new Error('not-file');
    const data = await fs.readFile(filePath);
    const ext = path.extname(filePath).toLowerCase();
    setSecurityHeaders(res);
    res.writeHead(200, {
      'Content-Type': contentTypes[ext] || 'application/octet-stream',
      'Cache-Control': ext === '.html' ? 'no-store' : 'public, max-age=300'
    });
    res.end(data);
  } catch {
    setSecurityHeaders(res);
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Niet gevonden');
  }
}

const server = http.createServer((req, res) => {
  serveStatic(req, res).catch((error) => {
    console.error(error);
    res.writeHead(500);
    res.end('Serverfout');
  });
});

const wss = new WebSocketServer({ server, maxPayload: 32 * 1024 });
const clients = new Map();

function peersInRoom(room, exceptId) {
  const peers = [];
  for (const client of clients.values()) {
    if (client.room === room && client.id !== exceptId) {
      peers.push({ id: client.id, name: client.name });
    }
  }
  return peers;
}

function findById(id) {
  for (const [socket, client] of clients.entries()) {
    if (client.id === id) return { socket, client };
  }
  return null;
}

function send(socket, message) {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message));
  }
}

function broadcast(room, message, exceptId = null) {
  for (const [socket, client] of clients.entries()) {
    if (client.room === room && client.id !== exceptId) {
      send(socket, message);
    }
  }
}

wss.on('connection', (socket) => {
  const client = {
    id: crypto.randomUUID(),
    room: null,
    name: 'Gebruiker',
    messageWindowStart: Date.now(),
    messageCount: 0
  };
  clients.set(socket, client);

  socket.on('message', (raw) => {
    const now = Date.now();
    if (now - client.messageWindowStart > 10_000) {
      client.messageWindowStart = now;
      client.messageCount = 0;
    }
    client.messageCount += 1;
    if (client.messageCount > 150) {
      socket.close(1008, 'Te veel berichten');
      return;
    }

    let message;
    try {
      message = JSON.parse(raw.toString());
    } catch {
      return;
    }

    if (message.type === 'join') {
      const room = sanitizeRoom(message.room);
      if (!room) {
        send(socket, { type: 'error', message: 'Ongeldige kamercode.' });
        return;
      }

      client.room = room;
      client.name = sanitizeName(message.name);
      send(socket, {
        type: 'joined',
        id: client.id,
        room,
        peers: peersInRoom(room, client.id)
      });
      broadcast(room, {
        type: 'peer-joined',
        peer: { id: client.id, name: client.name }
      }, client.id);
      return;
    }

    if (!client.room) return;

    if (message.type === 'signal' && message.target && isSafeSignal(message.data)) {
      const target = findById(String(message.target));
      if (target && target.client.room === client.room) {
        send(target.socket, {
          type: 'signal',
          from: client.id,
          data: message.data
        });
      }
      return;
    }

    if (message.type === 'speaking') {
      broadcast(client.room, {
        type: 'speaking',
        id: client.id,
        active: Boolean(message.active)
      }, client.id);
    }
  });

  socket.on('close', () => {
    if (client.room) {
      broadcast(client.room, { type: 'peer-left', id: client.id }, client.id);
    }
    clients.delete(socket);
  });
});

server.listen(port, '0.0.0.0', () => {
  console.log(`PTTConnect draait op poort ${port}`);
});
