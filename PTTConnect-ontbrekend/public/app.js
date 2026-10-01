const $ = (id) => document.getElementById(id);

const joinPanel = $('joinPanel');
const radioPanel = $('radioPanel');
const nameInput = $('name');
const roomInput = $('room');
const joinButton = $('joinButton');
const randomRoomButton = $('randomRoom');
const pttButton = $('pttButton');
const leaveButton = $('leaveButton');
const copyLinkButton = $('copyLink');
const roomLabel = $('roomLabel');
const speakerStatus = $('speakerStatus');
const participantsElement = $('participants');
const participantCount = $('participantCount');
const connectionBadge = $('connectionBadge');
const notice = $('notice');

let socket;
let localStream;
let myId;
let joined = false;
let talking = false;
let currentRoom = '';
let iceServers = [{ urls: 'stun:stun.l.google.com:19302' }];
const peers = new Map();
const participants = new Map();
const pendingCandidates = new Map();
const speakingIds = new Set();

function setNotice(message = '') {
  notice.textContent = message;
}

function setOnline(isOnline) {
  connectionBadge.textContent = isOnline ? 'Online' : 'Offline';
  connectionBadge.className = `badge ${isOnline ? 'badge-online' : 'badge-offline'}`;
}

function sanitizeRoom(value) {
  return String(value ?? '')
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9_-]/g, '')
    .slice(0, 32);
}

function randomRoom() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  return Array.from({ length: 6 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
}

function renderParticipants() {
  participantsElement.replaceChildren();
  const entries = [...participants.entries()];
  participantCount.textContent = String(entries.length);

  for (const [id, name] of entries) {
    const row = document.createElement('div');
    row.className = `participant${speakingIds.has(id) ? ' speaking' : ''}`;

    const label = document.createElement('span');
    label.textContent = id === myId ? `${name} (jij)` : name;

    const dot = document.createElement('span');
    dot.className = 'dot';
    row.append(label, dot);
    participantsElement.append(row);
  }
}

function updateSpeakerStatus() {
  if (talking) {
    speakerStatus.textContent = 'Jij praat';
    speakerStatus.classList.add('active');
    return;
  }

  const remoteSpeakerId = [...speakingIds].find((id) => id !== myId);
  if (remoteSpeakerId) {
    speakerStatus.textContent = `${participants.get(remoteSpeakerId) || 'Iemand'} praat`;
    speakerStatus.classList.add('active');
  } else {
    speakerStatus.textContent = 'Kanaal vrij';
    speakerStatus.classList.remove('active');
  }
}

function wsSend(message) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message));
  }
}

async function loadConfig() {
  try {
    const response = await fetch('/api/config', { cache: 'no-store' });
    if (!response.ok) return;
    const config = await response.json();
    if (Array.isArray(config.iceServers) && config.iceServers.length) {
      iceServers = config.iceServers;
    }
  } catch {
    // Fallback STUN blijft actief.
  }
}

async function createPeer(peerId, initiator) {
  if (peers.has(peerId)) return peers.get(peerId);

  const pc = new RTCPeerConnection({ iceServers });
  peers.set(peerId, pc);
  pendingCandidates.set(peerId, []);

  for (const track of localStream.getTracks()) {
    pc.addTrack(track, localStream);
  }

  pc.onicecandidate = (event) => {
    if (event.candidate) {
      wsSend({ type: 'signal', target: peerId, data: { candidate: event.candidate } });
    }
  };

  pc.ontrack = (event) => {
    let audio = document.getElementById(`audio-${peerId}`);
    if (!audio) {
      audio = document.createElement('audio');
      audio.id = `audio-${peerId}`;
      audio.autoplay = true;
      audio.playsInline = true;
      document.body.append(audio);
    }
    audio.srcObject = event.streams[0];
    audio.play().catch(() => {});
  };

  pc.onconnectionstatechange = () => {
    if (['failed', 'closed'].includes(pc.connectionState)) {
      removePeer(peerId);
    }
  };

  if (initiator) {
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    wsSend({ type: 'signal', target: peerId, data: { description: pc.localDescription } });
  }

  return pc;
}

async function handleSignal(peerId, data) {
  const pc = await createPeer(peerId, false);

  if (data.description) {
    await pc.setRemoteDescription(data.description);

    for (const candidate of pendingCandidates.get(peerId) || []) {
      try { await pc.addIceCandidate(candidate); } catch {}
    }
    pendingCandidates.set(peerId, []);

    if (data.description.type === 'offer') {
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      wsSend({ type: 'signal', target: peerId, data: { description: pc.localDescription } });
    }
  }

  if (data.candidate) {
    if (pc.remoteDescription) {
      try { await pc.addIceCandidate(data.candidate); } catch {}
    } else {
      pendingCandidates.get(peerId)?.push(data.candidate);
    }
  }
}

function removePeer(peerId) {
  peers.get(peerId)?.close();
  peers.delete(peerId);
  pendingCandidates.delete(peerId);
  speakingIds.delete(peerId);
  document.getElementById(`audio-${peerId}`)?.remove();
}

async function joinRoom() {
  if (joined) return;
  setNotice('');

  currentRoom = sanitizeRoom(roomInput.value);
  const name = (nameInput.value.trim() || 'Gebruiker').slice(0, 32);
  if (!currentRoom) {
    setNotice('Vul een geldige kamercode in.');
    return;
  }

  joinButton.disabled = true;
  joinButton.textContent = 'Verbinden...';

  try {
    localStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
    });
    localStream.getAudioTracks().forEach((track) => { track.enabled = false; });
  } catch {
    setNotice('Microfoontoegang is nodig om PTTConnect te gebruiken.');
    joinButton.disabled = false;
    joinButton.textContent = 'Verbinden';
    return;
  }

  await loadConfig();
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  socket = new WebSocket(`${protocol}//${location.host}`);

  socket.addEventListener('open', () => {
    wsSend({ type: 'join', room: currentRoom, name });
  });

  socket.addEventListener('message', async (event) => {
    let message;
    try { message = JSON.parse(event.data); } catch { return; }

    if (message.type === 'joined') {
      myId = message.id;
      joined = true;
      participants.set(myId, name);
      for (const peer of message.peers) participants.set(peer.id, peer.name);
      renderParticipants();
      setOnline(true);
      roomLabel.textContent = currentRoom;
      joinPanel.classList.add('hidden');
      radioPanel.classList.remove('hidden');
      pttButton.disabled = false;
      const url = new URL(location.href);
      url.searchParams.set('room', currentRoom);
      history.replaceState({}, '', url);

      for (const peer of message.peers) {
        await createPeer(peer.id, true);
      }
    }

    if (message.type === 'peer-joined') {
      participants.set(message.peer.id, message.peer.name);
      renderParticipants();
    }

    if (message.type === 'signal') {
      await handleSignal(message.from, message.data);
    }

    if (message.type === 'peer-left') {
      removePeer(message.id);
      participants.delete(message.id);
      renderParticipants();
      updateSpeakerStatus();
    }

    if (message.type === 'speaking') {
      if (message.active) speakingIds.add(message.id);
      else speakingIds.delete(message.id);
      renderParticipants();
      updateSpeakerStatus();
    }

    if (message.type === 'error') setNotice(message.message || 'Er ging iets mis.');
  });

  socket.addEventListener('close', () => {
    if (joined) setNotice('De verbinding met de server is verbroken.');
    setOnline(false);
    pttButton.disabled = true;
  });

  socket.addEventListener('error', () => {
    setNotice('Kan geen verbinding maken met de PTTConnect-server.');
  });
}

function startTalking() {
  if (!joined || talking || !localStream) return;
  talking = true;
  speakingIds.add(myId);
  localStream.getAudioTracks().forEach((track) => { track.enabled = true; });
  pttButton.classList.add('active');
  pttButton.querySelector('.ptt-main').textContent = 'PRATEN';
  wsSend({ type: 'speaking', active: true });
  renderParticipants();
  updateSpeakerStatus();
}

function stopTalking() {
  if (!talking || !localStream) return;
  talking = false;
  speakingIds.delete(myId);
  localStream.getAudioTracks().forEach((track) => { track.enabled = false; });
  pttButton.classList.remove('active');
  pttButton.querySelector('.ptt-main').textContent = 'HOUD INGEDRUKT';
  wsSend({ type: 'speaking', active: false });
  renderParticipants();
  updateSpeakerStatus();
}

function leaveRoom() {
  stopTalking();
  for (const peerId of [...peers.keys()]) removePeer(peerId);
  socket?.close();
  localStream?.getTracks().forEach((track) => track.stop());
  participants.clear();
  speakingIds.clear();
  myId = undefined;
  joined = false;
  localStream = undefined;
  socket = undefined;
  setOnline(false);
  renderParticipants();
  radioPanel.classList.add('hidden');
  joinPanel.classList.remove('hidden');
  joinButton.disabled = false;
  joinButton.textContent = 'Verbinden';
  const url = new URL(location.href);
  url.searchParams.delete('room');
  history.replaceState({}, '', url.pathname);
}

joinButton.addEventListener('click', joinRoom);
randomRoomButton.addEventListener('click', () => { roomInput.value = randomRoom(); });
leaveButton.addEventListener('click', leaveRoom);
copyLinkButton.addEventListener('click', async () => {
  const url = new URL(location.href);
  url.searchParams.set('room', currentRoom);
  try {
    await navigator.clipboard.writeText(url.toString());
    copyLinkButton.textContent = 'Gekopieerd';
    setTimeout(() => { copyLinkButton.textContent = 'Deellink kopiëren'; }, 1400);
  } catch {
    setNotice('Kon de link niet automatisch kopiëren.');
  }
});

pttButton.addEventListener('pointerdown', (event) => { event.preventDefault(); startTalking(); });
window.addEventListener('pointerup', stopTalking);
window.addEventListener('pointercancel', stopTalking);
window.addEventListener('blur', stopTalking);
window.addEventListener('keydown', (event) => {
  const tag = document.activeElement?.tagName;
  if (event.code === 'Space' && !['INPUT', 'TEXTAREA', 'BUTTON'].includes(tag)) {
    event.preventDefault();
    startTalking();
  }
});
window.addEventListener('keyup', (event) => {
  if (event.code === 'Space') stopTalking();
});

const roomFromUrl = sanitizeRoom(new URL(location.href).searchParams.get('room'));
if (roomFromUrl) roomInput.value = roomFromUrl;

if ('serviceWorker' in navigator && location.protocol === 'https:') {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}
