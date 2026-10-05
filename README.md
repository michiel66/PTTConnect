![PTTConnect voorbeeld](pttconnect-preview.png)
# PTTConnect Android

PTTConnect is an unofficial Android push-to-talk client for TeamSpeak 3 compatible servers.

## PTTConnect defaults

- Default server: `Heerlen.MIJNTS3.NL`
- Default voice port: `9987`
- Nickname: entered by the user
- Saved servers: users can save multiple server addresses and remove them later
- Voice: listen to supported TS3 Opus channels and hold the PTT button to transmit
- Channels: browse and join available channels

## How the build works

This repository intentionally stores only the PTTConnect overlay/build recipe. GitHub Actions:

1. Checks out this repository.
2. Clones the pinned Apache-2.0 licensed T3Vox Android client source.
3. Applies PTTConnect branding, package ID and default server settings.
4. Runs Android unit tests and builds a debug APK.
5. Uploads `PTTConnect-debug.apk` as a GitHub Actions artifact.

The upstream revision is pinned in `pttconnect/apply_overlay.py` and the workflow so builds remain reproducible.

## Downloading the APK after GitHub builds it

Open **Actions** in this repository, open the latest **Build PTTConnect APK** run and download the `PTTConnect-APK` artifact.

## Important

This is an unofficial community client. Voice compatibility must be tested on the target TeamSpeak server and on a physical Android device. Do not use it for emergency or safety-critical communication.

## Licensing

The PTTConnect overlay is distributed under Apache License 2.0. The automated build uses T3Vox, also Apache-2.0 licensed, and preserves its upstream `LICENSE`, `NOTICE`, and `THIRD_PARTY_NOTICES.md` inside the generated APK assets.
