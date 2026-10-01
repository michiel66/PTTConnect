#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
from pathlib import Path

UPSTREAM_COMMIT = "6ff59cac87ad2b384d2704e663004c7e10dce26d"
DEFAULT_HOST = "Heerlen.MIJNTS3.NL"
DEFAULT_PORT = 9987
APP_ID = "nl.mijnts3.pttconnect"


def require_replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected text not found in {path}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply_overlay.py <upstream-root>")

    root = Path(sys.argv[1]).resolve()
    here = Path(__file__).resolve().parent

    required = [
        root / "app/build.gradle.kts",
        root / "app/src/main/java/com/toosarax/ts3client/ui/Ts3App.kt",
        root / "app/src/main/res/values/strings.xml",
        root / "LICENSE",
        root / "NOTICE",
        root / "THIRD_PARTY_NOTICES.md",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError("Upstream checkout is incomplete: " + ", ".join(missing))

    # Give the generated APK its own Android application ID while keeping the
    # upstream Kotlin namespace intact (so no mass source-package rewrite is needed).
    gradle = root / "app/build.gradle.kts"
    require_replace(
        gradle,
        'applicationId = "com.toosarax.ts3client"',
        f'applicationId = "{APP_ID}"',
    )
    require_replace(
        gradle,
        'versionName = "0.1.0"',
        'versionName = "0.1.0-pttconnect"',
    )

    # Pre-fill the requested server on a fresh install. The existing upstream
    # SettingsStore continues to remember the user's last server/nickname and
    # supports an arbitrary list of saved servers.
    app = root / "app/src/main/java/com/toosarax/ts3client/ui/Ts3App.kt"
    require_replace(
        app,
        "initialHost = lastHost,",
        f'initialHost = lastHost ?: "{DEFAULT_HOST}",',
    )
    require_replace(
        app,
        "initialPort = lastPort,",
        f"initialPort = lastPort ?: {DEFAULT_PORT},",
    )

    # Dutch PTTConnect branding/copy. Resource keys match upstream so the
    # existing UI and behavior remain unchanged.
    shutil.copy2(here / "strings.xml", root / "app/src/main/res/values/strings.xml")

    # Preserve upstream/third-party licensing in the distributed APK.
    assets = root / "app/src/main/assets/licenses"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "LICENSE", assets / "T3Vox-LICENSE-Apache-2.0.txt")
    shutil.copy2(root / "NOTICE", assets / "T3Vox-NOTICE.txt")
    shutil.copy2(root / "THIRD_PARTY_NOTICES.md", assets / "T3Vox-THIRD-PARTY-NOTICES.md")
    (assets / "PTTConnect-NOTICE.txt").write_text(
        "PTTConnect is an unofficial TeamSpeak 3 compatible Android client.\n"
        "It is not affiliated with, endorsed by, or sponsored by TeamSpeak Systems GmbH.\n"
        "Default server: Heerlen.MIJNTS3.NL:9987\n"
        f"Upstream T3Vox revision: {UPSTREAM_COMMIT}\n",
        encoding="utf-8",
    )

    print("PTTConnect overlay applied")
    print(f"  app id: {APP_ID}")
    print(f"  default server: {DEFAULT_HOST}:{DEFAULT_PORT}")
    print(f"  upstream: {UPSTREAM_COMMIT}")


if __name__ == "__main__":
    main()
