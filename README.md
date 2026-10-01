# PTTConnect

PTTConnect is een eenvoudige push-to-talk webapp. Gebruikers gaan een kamer in, houden de grote knop ingedrukt en sturen dan live audio naar de andere deelnemers via WebRTC.

## Functies

- Push-to-talk via knop of spatiebalk
- Kamercodes en deellinks
- WebRTC peer-to-peer audio
- WebSocket-signaling
- Deelnemerslijst en spreekstatus
- Mobielvriendelijke interface
- PWA/installeerbaar op ondersteunde apparaten
- Docker-ondersteuning
- GitHub Actions CI
- STUN standaard, TURN configureerbaar

## Lokaal starten

Vereisten: Node.js 20 of nieuwer.

```bash
npm install
npm start
```

Open daarna `http://localhost:3000`.

## Testen

```bash
npm run check
npm test
```

## Docker

```bash
docker compose up --build
```

Daarna draait de app op `http://localhost:3000`.

## Internet / productie

Microfoontoegang werkt op internet alleen betrouwbaar via HTTPS. Gebruik daarom een hostingplatform of reverse proxy met TLS.

PTTConnect gebruikt standaard Google's publieke STUN-server. Voor gebruikers achter strengere firewalls/NAT is een TURN-server nodig. Zet die via `ICE_SERVERS_JSON`:

```env
ICE_SERVERS_JSON=[{"urls":"stun:stun.l.google.com:19302"},{"urls":"turn:turn.example.com:3478","username":"user","credential":"secret"}]
```

## Architectuur

De Node-server verzorgt statische bestanden en WebSocket-signaling. Audio loopt rechtstreeks tussen browsers via WebRTC en gaat dus niet via de Node-server. Deze mesh-opzet is bedoeld voor kleine groepen; voor grote kanalen is een SFU-architectuur geschikter.

## Privacy

De server slaat geen audio op. Gebruikersnamen en kamercodes bestaan alleen in het geheugen zolang de verbinding actief is.
