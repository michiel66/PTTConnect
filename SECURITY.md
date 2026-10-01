# Security

## Melden

Meld beveiligingsproblemen bij voorkeur niet openbaar in een GitHub issue. Gebruik GitHub's private vulnerability reporting wanneer dat voor deze repository is ingeschakeld.

## Belangrijk voor productie

- Serveer PTTConnect altijd via HTTPS.
- Gebruik voor betrouwbare verbindingen een eigen TURN-server en sterke credentials.
- Zet TURN-credentials niet hardcoded in `public/`.
- Houd Node.js en de `ws` dependency actueel.
- Plaats een reverse proxy voor TLS, logging en eventueel rate limiting.
