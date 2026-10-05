#!/usr/bin/env python3

from pathlib import Path
import sys


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")

    if old not in text:
        raise RuntimeError(
            f"PTTConnect UI upgrade: tekst niet gevonden in {path}: {old[:100]!r}"
        )

    path.write_text(
        text.replace(old, new, 1),
        encoding="utf-8",
    )
  THEME_KT = r'''
package com.toosarax.ts3client.ui.theme

import android.content.Context
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

enum class ThemeMode {
    SYSTEM,
    DARK,
    LIGHT,
}

enum class AccentChoice {
    BLUE,
    GREEN,
    ORANGE,
    PURPLE,
}

object PttAppearance {

    var themeMode by mutableStateOf(ThemeMode.SYSTEM)
        private set

    var accent by mutableStateOf(AccentChoice.BLUE)
        private set

    private var loaded = false

    fun ensureLoaded(context: Context) {
        if (loaded) return

        val prefs = context.getSharedPreferences(
            "pttconnect_appearance",
            Context.MODE_PRIVATE,
        )

        themeMode = runCatching {
            ThemeMode.valueOf(
                prefs.getString(
                    "theme_mode",
                    ThemeMode.SYSTEM.name,
                ) ?: ThemeMode.SYSTEM.name
            )
        }.getOrDefault(ThemeMode.SYSTEM)

        accent = runCatching {
            AccentChoice.valueOf(
                prefs.getString(
                    "accent",
                    AccentChoice.BLUE.name,
                ) ?: AccentChoice.BLUE.name
            )
        }.getOrDefault(AccentChoice.BLUE)

        loaded = true
    }

    fun setThemeMode(
        context: Context,
        value: ThemeMode,
    ) {
        themeMode = value

        context.getSharedPreferences(
            "pttconnect_appearance",
            Context.MODE_PRIVATE,
        ).edit()
            .putString("theme_mode", value.name)
            .apply()
    }

    fun setAccent(
        context: Context,
        value: AccentChoice,
    ) {
        accent = value

        context.getSharedPreferences(
            "pttconnect_appearance",
            Context.MODE_PRIVATE,
        ).edit()
            .putString("accent", value.name)
            .apply()
    }
}
@Composable
fun Ts3Theme(
    content: @Composable () -> Unit,
) {
    val context = LocalContext.current

    PttAppearance.ensureLoaded(context)

    val darkTheme = when (PttAppearance.themeMode) {
        ThemeMode.SYSTEM -> isSystemInDarkTheme()
        ThemeMode.DARK -> true
        ThemeMode.LIGHT -> false
    }

    val accentDark = when (PttAppearance.accent) {
        AccentChoice.BLUE -> Color(0xFF00A6FF)
        AccentChoice.GREEN -> Color(0xFF20D79A)
        AccentChoice.ORANGE -> Color(0xFFFF9C35)
        AccentChoice.PURPLE -> Color(0xFFA985FF)
    }

    val accentLight = when (PttAppearance.accent) {
        AccentChoice.BLUE -> Color(0xFF006EB8)
        AccentChoice.GREEN -> Color(0xFF087F5B)
        AccentChoice.ORANGE -> Color(0xFFB85A00)
        AccentChoice.PURPLE -> Color(0xFF7048C1)
    }

    val colors = if (darkTheme) {
        darkColorScheme(
            primary = accentDark,
            onPrimary = Color.Black,
            background = Color(0xFF020711),
            onBackground = Color(0xFFF4F8FF),
            surface = Color(0xFF07111F),
            onSurface = Color(0xFFF4F8FF),
            surfaceVariant = Color(0xFF0A1829),
            onSurfaceVariant = Color(0xFFBED0E0),
            outline = Color(0xFF46627B),
            outlineVariant = Color(0xFF1D3449),
            error = Color(0xFFFF455D),
            onError = Color.White,
            errorContainer = Color(0xFF5A0B17),
            onErrorContainer = Color(0xFFFFD9DE),
        )
    } else {
        lightColorScheme(
            primary = accentLight,
            onPrimary = Color.White,
            background = Color(0xFFF4F7FA),
            onBackground = Color(0xFF111820),
            surface = Color.White,
            onSurface = Color(0xFF111820),
            surfaceVariant = Color(0xFFE8EEF3),
            onSurfaceVariant = Color(0xFF41505D),
            outline = Color(0xFF71808C),
            error = Color(0xFFBA1A1A),
            onError = Color.White,
        )
    }

    MaterialTheme(
        colorScheme = colors,
        content = content,
    )
}
'''
def upgrade_connect_screen(root: Path) -> None:
    path = root / "app/src/main/java/com/toosarax/ts3client/ui/ConnectScreen.kt"

    replace_once(
        path,
        "import androidx.compose.material.icons.Icons\n",
        "import androidx.compose.material.icons.Icons\n"
        "import androidx.compose.material.icons.automirrored.filled.ArrowBack\n",
    )

    replace_once(
        path,
        "import androidx.compose.material.icons.filled.History\n",
        "import androidx.compose.material.icons.filled.History\n"
        "import androidx.compose.material.icons.filled.Settings\n",
    )

    replace_once(
        path,
        "import androidx.compose.ui.Alignment\n",
        "import androidx.compose.ui.Alignment\n"
        "import androidx.compose.ui.platform.LocalContext\n",
    )

    replace_once(
        path,
        "import com.toosarax.ts3client.settings.SavedServer\n",
        "import com.toosarax.ts3client.settings.SavedServer\n"
        "import com.toosarax.ts3client.ui.theme.AccentChoice\n"
        "import com.toosarax.ts3client.ui.theme.PttAppearance\n"
        "import com.toosarax.ts3client.ui.theme.ThemeMode\n",
    )
      replace_once(
        path,
        '''    var serverToDelete by rememberSaveable { mutableStateOf<SavedServer?>(null) }
    val connecting = state.status == ConnectionStatus.CONNECTING
''',
        '''    var serverToDelete by rememberSaveable { mutableStateOf<SavedServer?>(null) }
    var showSettings by rememberSaveable { mutableStateOf(false) }
    val connecting = state.status == ConnectionStatus.CONNECTING

    if (showSettings) {
        AppearanceSettingsScreen(
            onBack = { showSettings = false },
        )
        return
    }
''',
    )

    replace_once(
        path,
        '''    ) {
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
''',
        '''    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(
                modifier = Modifier.weight(1f),
            ) {
                Text(
                    text = "PTT Connect",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold,
                )

                Text(
                    text = "TeamSpeak push-to-talk",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            IconButton(
                onClick = { showSettings = true },
            ) {
                Icon(
                    imageVector = Icons.Default.Settings,
                    contentDescription = "Instellingen",
                )
            }
        }

        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
''',
    )
    text = path.read_text(encoding="utf-8")

    settings_screen = r'''

@Composable
fun AppearanceSettingsScreen(
    onBack: () -> Unit,
) {
    val context = LocalContext.current

    PttAppearance.ensureLoaded(context)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(
                    Icons.AutoMirrored.Filled.ArrowBack,
                    contentDescription = "Terug",
                )
            }

            Column(
                modifier = Modifier.weight(1f),
            ) {
                Text(
                    text = "Instellingen",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold,
                )

                Text(
                    text = "PTT Connect aanpassen",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        Card(
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                Text(
                    text = "Uiterlijk",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                )

                Text("Thema")

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    OutlinedButton(
                        modifier = Modifier.weight(1f),
                        onClick = {
                            PttAppearance.setThemeMode(
                                context,
                                ThemeMode.SYSTEM,
                            )
                        },
                    ) {
                        Text("Systeem")
                    }

                    OutlinedButton(
                        modifier = Modifier.weight(1f),
                        onClick = {
                            PttAppearance.setThemeMode(
                                context,
                                ThemeMode.DARK,
                            )
                        },
                    ) {
                        Text("Donker")
                    }

                    OutlinedButton(
                        modifier = Modifier.weight(1f),
                        onClick = {
                            PttAppearance.setThemeMode(
                                context,
                                ThemeMode.LIGHT,
                            )
                        },
                    ) {
                        Text("Licht")
                    }
                }

                Text("Accentkleur")

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    OutlinedButton(
                        modifier = Modifier.weight(1f),
                        onClick = {
                            PttAppearance.setAccent(
                                context,
                                AccentChoice.BLUE,
                            )
                        },
                    ) {
                        Text("Blauw")
                    }

                    OutlinedButton(
                        modifier = Modifier.weight(1f),
                        onClick = {
                            PttAppearance.setAccent(
                                context,
                                AccentChoice.GREEN,
                            )
                        },
                    ) {
                        Text("Groen")
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    OutlinedButton(
                        modifier = Modifier.weight(1f),
                        onClick = {
                            PttAppearance.setAccent(
                                context,
                                AccentChoice.ORANGE,
                            )
                        },
                    ) {
                        Text("Oranje")
                    }

                    OutlinedButton(
                        modifier = Modifier.weight(1f),
                        onClick = {
                            PttAppearance.setAccent(
                                context,
                                AccentChoice.PURPLE,
                            )
                        },
                    ) {
                        Text("Paars")
                    }
                }

                Text(
                    text = "Hier kunnen we later meer instellingen onder zetten.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
'''

    if "fun AppearanceSettingsScreen(" not in text:
        path.write_text(
            text.rstrip() + "\n" + settings_screen.lstrip(),
            encoding="utf-8",
        )
      def upgrade_channel_screen(root: Path) -> None:
    path = root / "app/src/main/java/com/toosarax/ts3client/ui/ChannelScreen.kt"

    replace_once(
        path,
        "import androidx.compose.material.icons.filled.Refresh\n",
        "import androidx.compose.material.icons.filled.Refresh\n"
        "import androidx.compose.material.icons.filled.Settings\n",
    )

    replace_once(
        path,
        '''    var selectedTab by remember { mutableIntStateOf(InCallTab.Talk.ordinal) }
''',
        '''    var selectedTab by remember { mutableIntStateOf(InCallTab.Talk.ordinal) }
    var showSettings by remember { mutableStateOf(false) }
''',
    )

    replace_once(
        path,
        '''    val peopleInRoom = state.clients.count { it.channelId == state.currentChannelId }

    Scaffold(
''',
        '''    val peopleInRoom = state.clients.count { it.channelId == state.currentChannelId }

    if (showSettings) {
        AppearanceSettingsScreen(
            onBack = { showSettings = false },
        )
        return
    }

    Scaffold(
''',
    )

    replace_once(
        path,
        '''                actions = {
                    IconButton(onClick = onRefresh) {
''',
        '''                actions = {
                    IconButton(
                        onClick = { showSettings = true },
                    ) {
                        Icon(
                            Icons.Default.Settings,
                            contentDescription = "Instellingen",
                        )
                    }

                    IconButton(onClick = onRefresh) {
''',
    )

    replace_once(
        path,
        '''private fun TalkTab(
    state: ClientState,
    onVoiceModeChanged: (VoiceMode) -> Unit,
    onVadThresholdChanged: (Float) -> Unit,
    onPushToTalkChanged: (Boolean) -> Unit,
) {
    Column(
''',
        '''private fun TalkTab(
    state: ClientState,
    onVoiceModeChanged: (VoiceMode) -> Unit,
    onVadThresholdChanged: (Float) -> Unit,
    onPushToTalkChanged: (Boolean) -> Unit,
) {
    val activeSpeakerNames = state.clients
        .filter { client -> client.id in state.talkingClientIds }
        .map { client -> client.nickname }

    Column(
''',
    )

    replace_once(
        path,
        '''                Text(
                    text = if (state.pushToTalkPressed) "ZENDEN" else "GEREED OM TE PRATEN",
''',
        '''                Text(
                    text = when {
                        state.pushToTalkPressed ->
                            "Jij praat"

                        activeSpeakerNames.isNotEmpty() ->
                            "Nu aan het praten: ${activeSpeakerNames.joinToString(", ")}"

                        else ->
                            "Niemand praat"
                    },
                    color = if (activeSpeakerNames.isNotEmpty()) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.onSurfaceVariant
                    },
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth(),
                )

                Text(
                    text = if (state.pushToTalkPressed) "ZENDEN" else "GEREED OM TE PRATEN",
''',
    )


def upgrade_theme(root: Path) -> None:
    path = root / "app/src/main/java/com/toosarax/ts3client/ui/theme/Theme.kt"

    path.write_text(
        THEME_KT.lstrip(),
        encoding="utf-8",
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Gebruik: ui_upgrade.py <t3vox-root>"
        )

    root = Path(sys.argv[1]).resolve()

    upgrade_connect_screen(root)
    upgrade_channel_screen(root)
    upgrade_theme(root)

    print("PTTConnect nieuwe UI toegepast")


if __name__ == "__main__":
    main()
