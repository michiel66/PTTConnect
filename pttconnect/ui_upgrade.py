#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")

    if old not in text:
        raise RuntimeError(
            f"PTTConnect UI upgrade: verwachte tekst niet gevonden in {path}: {old[:120]!r}"
        )

    path.write_text(
        text.replace(old, new, 1),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text.lstrip("\n"),
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
                ) ?: ThemeMode.SYSTEM.name,
            )
        }.getOrDefault(ThemeMode.SYSTEM)

        accent = runCatching {
            AccentChoice.valueOf(
                prefs.getString(
                    "accent",
                    AccentChoice.BLUE.name,
                ) ?: AccentChoice.BLUE.name,
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

    val useDarkTheme = when (PttAppearance.themeMode) {
        ThemeMode.SYSTEM -> isSystemInDarkTheme()
        ThemeMode.DARK -> true
        ThemeMode.LIGHT -> false
    }

    val darkAccent = when (PttAppearance.accent) {
        AccentChoice.BLUE -> Color(0xFF00A6FF)
        AccentChoice.GREEN -> Color(0xFF22D79A)
        AccentChoice.ORANGE -> Color(0xFFFF9D3D)
        AccentChoice.PURPLE -> Color(0xFFA98BFF)
    }

    val lightAccent = when (PttAppearance.accent) {
        AccentChoice.BLUE -> Color(0xFF006DB6)
        AccentChoice.GREEN -> Color(0xFF087F5B)
        AccentChoice.ORANGE -> Color(0xFFB85B00)
        AccentChoice.PURPLE -> Color(0xFF7048C1)
    }

    val colors = if (useDarkTheme) {
        darkColorScheme(
            primary = darkAccent,
            onPrimary = Color(0xFF00131F),
            primaryContainer = darkAccent.copy(alpha = 0.20f),
            onPrimaryContainer = Color(0xFFF4FAFF),

            secondary = darkAccent,
            onSecondary = Color(0xFF00131F),

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
            primary = lightAccent,
            onPrimary = Color.White,
            primaryContainer = lightAccent.copy(alpha = 0.12f),
            onPrimaryContainer = Color(0xFF10212E),

            secondary = lightAccent,
            onSecondary = Color.White,

            background = Color(0xFFF4F7FA),
            onBackground = Color(0xFF111820),

            surface = Color.White,
            onSurface = Color(0xFF111820),

            surfaceVariant = Color(0xFFE8EEF3),
            onSurfaceVariant = Color(0xFF41505D),

            outline = Color(0xFF71808C),
            outlineVariant = Color(0xFFD2DCE4),

            error = Color(0xFFBA1A1A),
            onError = Color.White,
            errorContainer = Color(0xFFFFDAD6),
            onErrorContainer = Color(0xFF410002),
        )
    }

    MaterialTheme(
        colorScheme = colors,
        content = content,
    )
}
'''


SETTINGS_SCREEN_KT = r'''
package com.toosarax.ts3client.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.toosarax.ts3client.ui.theme.AccentChoice
import com.toosarax.ts3client.ui.theme.PttAppearance
import com.toosarax.ts3client.ui.theme.ThemeMode

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
            IconButton(
                onClick = onBack,
            ) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.ArrowBack,
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

                Text(
                    text = "Thema",
                    style = MaterialTheme.typography.titleMedium,
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    ThemeChoiceButton(
                        label = "Systeem",
                        selected = PttAppearance.themeMode == ThemeMode.SYSTEM,
                        modifier = Modifier.weight(1f),
                        onClick = {
                            PttAppearance.setThemeMode(
                                context,
                                ThemeMode.SYSTEM,
                            )
                        },
                    )

                    ThemeChoiceButton(
                        label = "Donker",
                        selected = PttAppearance.themeMode == ThemeMode.DARK,
                        modifier = Modifier.weight(1f),
                        onClick = {
                            PttAppearance.setThemeMode(
                                context,
                                ThemeMode.DARK,
                            )
                        },
                    )

                    ThemeChoiceButton(
                        label = "Licht",
                        selected = PttAppearance.themeMode == ThemeMode.LIGHT,
                        modifier = Modifier.weight(1f),
                        onClick = {
                            PttAppearance.setThemeMode(
                                context,
                                ThemeMode.LIGHT,
                            )
                        },
                    )
                }

                Text(
                    text = "Accentkleur",
                    style = MaterialTheme.typography.titleMedium,
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    AccentChoiceButton(
                        label = "Blauw",
                        choice = AccentChoice.BLUE,
                        modifier = Modifier.weight(1f),
                    )

                    AccentChoiceButton(
                        label = "Groen",
                        choice = AccentChoice.GREEN,
                        modifier = Modifier.weight(1f),
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    AccentChoiceButton(
                        label = "Oranje",
                        choice = AccentChoice.ORANGE,
                        modifier = Modifier.weight(1f),
                    )

                    AccentChoiceButton(
                        label = "Paars",
                        choice = AccentChoice.PURPLE,
                        modifier = Modifier.weight(1f),
                    )
                }

                Text(
                    text = "De accentkleur wordt gebruikt voor knoppen, de PTT-knop en actieve sprekers.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        Card(
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Text(
                    text = "Meer instellingen",
                    fontWeight = FontWeight.Bold,
                )

                Text(
                    text = "Hier kunnen we later geluid, PTT, meldingen en andere opties onder toevoegen.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun ThemeChoiceButton(
    label: String,
    selected: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    if (selected) {
        Button(
            onClick = onClick,
            modifier = modifier,
        ) {
            Text(label)
        }
    } else {
        OutlinedButton(
            onClick = onClick,
            modifier = modifier,
        ) {
            Text(label)
        }
    }
}

@Composable
private fun AccentChoiceButton(
    label: String,
    choice: AccentChoice,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val selected = PttAppearance.accent == choice

    if (selected) {
        Button(
            onClick = {
                PttAppearance.setAccent(
                    context,
                    choice,
                )
            },
            modifier = modifier,
        ) {
            Text(label)
        }
    } else {
        OutlinedButton(
            onClick = {
                PttAppearance.setAccent(
                    context,
                    choice,
                )
            },
            modifier = modifier,
        ) {
            Text(label)
        }
    }
}
'''


CONNECT_SCREEN_KT = r'''
package com.toosarax.ts3client.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.toosarax.ts3client.BuildConfig
import com.toosarax.ts3client.R
import com.toosarax.ts3client.client.ClientState
import com.toosarax.ts3client.client.ConnectionStatus
import com.toosarax.ts3client.protocol.ConnectRequest
import com.toosarax.ts3client.settings.SavedServer

@Composable
fun ConnectScreen(
    state: ClientState,
    identityPreparing: Boolean,
    initialHost: String?,
    initialPort: Int?,
    initialNickname: String?,
    savedServers: List<SavedServer>,
    onConnect: (ConnectRequest, Boolean, String) -> Unit,
    onConnectSaved: (SavedServer, String, String?, String?) -> Unit,
    onRemoveSavedServer: (String) -> Unit,
) {
    var host by rememberSaveable {
        mutableStateOf(initialHost.orEmpty())
    }

    var port by rememberSaveable {
        mutableStateOf(
            (initialPort ?: 9987).toString()
        )
    }

    var nickname by rememberSaveable {
        mutableStateOf(initialNickname.orEmpty())
    }

    var serverPassword by rememberSaveable {
        mutableStateOf("")
    }

    var serverLabel by rememberSaveable {
        mutableStateOf(initialHost.orEmpty())
    }

    var rememberServer by rememberSaveable {
        mutableStateOf(true)
    }

    var showAdvanced by rememberSaveable {
        mutableStateOf(false)
    }

    var importedIdentity by rememberSaveable {
        mutableStateOf("")
    }

    var serverToDelete by rememberSaveable {
        mutableStateOf<SavedServer?>(null)
    }

    var showSettings by rememberSaveable {
        mutableStateOf(false)
    }

    val connecting =
        state.status == ConnectionStatus.CONNECTING

    if (showSettings) {
        AppearanceSettingsScreen(
            onBack = {
                showSettings = false
            },
        )

        return
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(
                rememberScrollState()
            )
            .padding(20.dp),
        verticalArrangement =
            Arrangement.spacedBy(14.dp),
    ) {

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment =
                Alignment.CenterVertically,
        ) {

            Column(
                modifier = Modifier.weight(1f),
            ) {

                Text(
                    text = "PTT Connect",
                    style =
                        MaterialTheme.typography
                            .headlineSmall,
                    fontWeight =
                        FontWeight.Bold,
                )

                Text(
                    text =
                        "Snel verbinden en praten",
                    style =
                        MaterialTheme.typography
                            .bodyMedium,
                    color =
                        MaterialTheme.colorScheme
                            .onSurfaceVariant,
                )
            }

            IconButton(
                onClick = {
                    showSettings = true
                },
            ) {
                Icon(
                    imageVector =
                        Icons.Default.Settings,
                    contentDescription =
                        "Instellingen",
                )
            }
        }

        if (identityPreparing) {

            Card(
                modifier =
                    Modifier.fillMaxWidth(),
                colors =
                    CardDefaults.cardColors(
                        containerColor =
                            MaterialTheme
                                .colorScheme
                                .primaryContainer,
                    ),
            ) {

                Row(
                    modifier =
                        Modifier.padding(12.dp),
                    horizontalArrangement =
                        Arrangement
                            .spacedBy(12.dp),
                    verticalAlignment =
                        Alignment
                            .CenterVertically,
                ) {

                    CircularProgressIndicator(
                        strokeWidth = 2.dp,
                    )

                    Text(
                        text =
                            stringResource(
                                R.string
                                    .status_identity_preparing,
                            ),
                    )
                }
            }
        }

        if (savedServers.isNotEmpty()) {

            Text(
                text =
                    stringResource(
                        R.string
                            .section_saved_servers,
                    ),
                style =
                    MaterialTheme.typography
                        .titleMedium,
                fontWeight =
                    FontWeight.Bold,
            )

            savedServers.forEach { server ->

                SavedServerCard(
                    server = server,
                    enabled = !connecting,

                    onConnect = {

                        if (nickname.isBlank()) {
                            nickname =
                                initialNickname
                                    .orEmpty()
                        }

                        onConnectSaved(
                            server,
                            nickname.trim(),
                            serverPassword
                                .ifBlank {
                                    null
                                },
                            importedIdentity
                                .ifBlank {
                                    null
                                },
                        )
                    },

                    onDelete = {
                        serverToDelete =
                            server
                    },
                )
            }
        }

        Text(
            text = "Nieuwe verbinding",
            style =
                MaterialTheme.typography
                    .titleMedium,
            fontWeight = FontWeight.Bold,
        )

        OutlinedTextField(
            value = host,

            onValueChange = {

                val oldHost = host

                host = it

                if (
                    serverLabel.isBlank() ||
                    serverLabel == oldHost
                ) {
                    serverLabel =
                        it.trim()
                }
            },

            label = {
                Text(
                    stringResource(
                        R.string.label_host
                    )
                )
            },

            placeholder = {
                Text(
                    stringResource(
                        R.string.label_host_hint
                    )
                )
            },

            modifier =
                Modifier.fillMaxWidth(),

            singleLine = true,
            enabled = !connecting,
        )

        OutlinedTextField(
            value = nickname,

            onValueChange = {
                nickname = it
            },

            label = {
                Text(
                    stringResource(
                        R.string.label_nickname
                    )
                )
            },

            placeholder = {
                Text(
                    stringResource(
                        R.string
                            .label_nickname_hint
                    )
                )
            },

            modifier =
                Modifier.fillMaxWidth(),

            singleLine = true,
            enabled = !connecting,
        )

        OutlinedButton(
            onClick = {
                showAdvanced =
                    !showAdvanced
            },

            modifier =
                Modifier.fillMaxWidth(),

            enabled = !connecting,
        ) {

            Icon(
                imageVector =
                    if (showAdvanced) {
                        Icons.Default.ExpandLess
                    } else {
                        Icons.Default.ExpandMore
                    },

                contentDescription = null,
            )

            Text(
                text =
                    if (showAdvanced) {
                        "Geavanceerde opties verbergen"
                    } else {
                        "Geavanceerde opties"
                    },

                modifier =
                    Modifier.padding(
                        start = 8.dp
                    ),
            )
        }

        if (showAdvanced) {

            Card(
                modifier =
                    Modifier.fillMaxWidth(),

                colors =
                    CardDefaults.cardColors(
                        containerColor =
                            MaterialTheme
                                .colorScheme
                                .surfaceVariant,
                    ),
            ) {

                Column(
                    modifier =
                        Modifier.padding(14.dp),

                    verticalArrangement =
                        Arrangement
                            .spacedBy(12.dp),
                ) {

                    OutlinedTextField(
                        value = port,

                        onValueChange = {
                            port =
                                it.filter { ch ->
                                    ch.isDigit()
                                }.take(5)
                        },

                        label = {
                            Text(
                                stringResource(
                                    R.string
                                        .label_port
                                )
                            )
                        },

                        modifier =
                            Modifier
                                .fillMaxWidth(),

                        singleLine = true,

                        keyboardOptions =
                            KeyboardOptions(
                                keyboardType =
                                    KeyboardType
                                        .Number,
                            ),

                        enabled = !connecting,
                    )

                    OutlinedTextField(
                        value =
                            serverPassword,

                        onValueChange = {
                            serverPassword = it
                        },

                        label = {
                            Text(
                                stringResource(
                                    R.string
                                        .label_server_password
                                )
                            )
                        },

                        modifier =
                            Modifier
                                .fillMaxWidth(),

                        singleLine = true,

                        visualTransformation =
                            PasswordVisualTransformation(),

                        enabled = !connecting,
                    )

                    Row(
                        modifier =
                            Modifier
                                .fillMaxWidth(),

                        verticalAlignment =
                            Alignment
                                .CenterVertically,
                    ) {

                        Checkbox(
                            checked =
                                rememberServer,

                            onCheckedChange = {
                                rememberServer = it
                            },

                            enabled =
                                !connecting,
                        )

                        Text(
                            text =
                                stringResource(
                                    R.string
                                        .label_remember_server
                                ),

                            modifier =
                                Modifier
                                    .weight(1f),
                        )
                    }

                    if (rememberServer) {

                        OutlinedTextField(
                            value =
                                serverLabel,

                            onValueChange = {
                                serverLabel = it
                            },

                            label = {
                                Text(
                                    stringResource(
                                        R.string
                                            .label_server_name
                                    )
                                )
                            },

                            modifier =
                                Modifier
                                    .fillMaxWidth(),

                            singleLine = true,

                            enabled =
                                !connecting,
                        )
                    }

                    Text(
                        text =
                            "Identiteit (optioneel)",

                        style =
                            MaterialTheme
                                .typography
                                .labelLarge,
                    )

                    OutlinedTextField(
                        value =
                            importedIdentity,

                        onValueChange = {
                            importedIdentity = it
                        },

                        label = {
                            Text(
                                stringResource(
                                    R.string
                                        .label_import_identity
                                )
                            )
                        },

                        placeholder = {
                            Text(
                                stringResource(
                                    R.string
                                        .label_import_identity_hint
                                )
                            )
                        },

                        modifier =
                            Modifier
                                .fillMaxWidth(),

                        minLines = 2,
                        maxLines = 4,

                        enabled =
                            !connecting,
                    )
                }
            }
        }

        state.error?.let { error ->

            Card(
                colors =
                    CardDefaults.cardColors(
                        containerColor =
                            MaterialTheme
                                .colorScheme
                                .errorContainer,
                    ),

                modifier =
                    Modifier
                        .fillMaxWidth(),
            ) {

                Text(
                    text =
                        error.userMessage(),

                    modifier =
                        Modifier
                            .padding(12.dp),

                    color =
                        MaterialTheme
                            .colorScheme
                            .onErrorContainer,
                )
            }
        }

        if (
            BuildConfig.DEBUG &&
            state.debugLines.isNotEmpty()
        ) {

            Card(
                modifier =
                    Modifier
                        .fillMaxWidth(),

                colors =
                    CardDefaults.cardColors(
                        containerColor =
                            MaterialTheme
                                .colorScheme
                                .surfaceVariant,
                    ),
            ) {

                Column(
                    modifier =
                        Modifier
                            .padding(12.dp),

                    verticalArrangement =
                        Arrangement
                            .spacedBy(4.dp),
                ) {

                    Text(
                        text = "Debug log",
                        style =
                            MaterialTheme
                                .typography
                                .labelLarge,
                    )

                    state.debugLines
                        .forEach { line ->

                            Text(
                                text = line,

                                style =
                                    MaterialTheme
                                        .typography
                                        .bodySmall,

                                fontFamily =
                                    androidx.compose
                                        .ui.text
                                        .font
                                        .FontFamily
                                        .Monospace,
                            )
                        }
                }
            }
        }

        Button(
            onClick = {

                onConnect(
                    ConnectRequest(
                        host = host.trim(),

                        port =
                            port.toIntOrNull()
                                ?: 9987,

                        nickname =
                            nickname.trim(),

                        serverPassword =
                            serverPassword
                                .ifBlank {
                                    null
                                },

                        importedIdentityIni =
                            importedIdentity
                                .ifBlank {
                                    null
                                },
                    ),

                    rememberServer,
                    serverLabel,
                )
            },

            enabled =
                !connecting &&
                host.isNotBlank() &&
                nickname.isNotBlank(),

            modifier =
                Modifier.fillMaxWidth(),
        ) {

            if (connecting) {

                CircularProgressIndicator(
                    modifier =
                        Modifier.padding(
                            end = 8.dp
                        ),

                    strokeWidth = 2.dp,
                )
            }

            Text(
                text =
                    if (connecting) {
                        stringResource(
                            R.string
                                .action_connecting
                        )
                    } else {
                        stringResource(
                            R.string
                                .action_connect
                        )
                    },
            )
        }
    }

    serverToDelete?.let { server ->

        AlertDialog(
            onDismissRequest = {
                serverToDelete = null
            },

            title = {
                Text(
                    stringResource(
                        R.string
                            .delete_server_title
                    )
                )
            },

            text = {
                Text(
                    stringResource(
                        R.string
                            .delete_server_body,
                        server.displayName,
                    )
                )
            },

            confirmButton = {

                TextButton(
                    onClick = {

                        onRemoveSavedServer(
                            server.id
                        )

                        serverToDelete = null
                    },
                ) {

                    Text(
                        stringResource(
                            R.string
                                .action_delete
                        )
                    )
                }
            },

            dismissButton = {

                TextButton(
                    onClick = {
                        serverToDelete = null
                    },
                ) {

                    Text(
                        stringResource(
                            R.string
                                .action_cancel
                        )
                    )
                }
            },
        )
    }
}

@Composable
private fun SavedServerCard(
    server: SavedServer,
    enabled: Boolean,
    onConnect: () -> Unit,
    onDelete: () -> Unit,
) {
    Card(
        modifier =
            Modifier.fillMaxWidth(),

        colors =
            CardDefaults.cardColors(
                containerColor =
                    MaterialTheme
                        .colorScheme
                        .surfaceVariant,
            ),
    ) {

        Row(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(12.dp),

            verticalAlignment =
                Alignment.CenterVertically,

            horizontalArrangement =
                Arrangement
                    .spacedBy(8.dp),
        ) {

            Icon(
                imageVector =
                    Icons.Default.History,

                contentDescription = null,

                tint =
                    MaterialTheme
                        .colorScheme
                        .primary,
            )

            Column(
                modifier =
                    Modifier.weight(1f),
            ) {

                Text(
                    text =
                        server.displayName,

                    fontWeight =
                        FontWeight.Medium,
                )

                Text(
                    text =
                        "${server.host}:${server.port}",

                    style =
                        MaterialTheme
                            .typography
                            .bodySmall,

                    color =
                        MaterialTheme
                            .colorScheme
                            .onSurfaceVariant,
                )
            }

            Button(
                onClick = onConnect,
                enabled = enabled,
            ) {
                Text(
                    stringResource(
                        R.string.action_connect
                    )
                )
            }

            IconButton(
                onClick = onDelete,
                enabled = enabled,
            ) {

                Icon(
                    imageVector =
                        Icons.Default.Delete,

                    contentDescription =
                        stringResource(
                            R.string
                                .action_delete
                        ),
                )
            }
        }
    }
}
'''


def upgrade_channel_screen(
    root: Path,
) -> None:

    path = (
        root
        / "app/src/main/java/com/toosarax/ts3client/ui/ChannelScreen.kt"
    )

    replace_once(
        path,
        "import androidx.compose.material.icons.filled.Refresh\n",
        "import androidx.compose.material.icons.filled.Refresh\n"
        "import androidx.compose.material.icons.filled.Settings\n",
    )

    replace_once(
        path,
        (
            "    var selectedTab by remember { "
            "mutableIntStateOf(InCallTab.Talk.ordinal) }\n"
        ),
        (
            "    var selectedTab by remember { "
            "mutableIntStateOf(InCallTab.Talk.ordinal) }\n"
            "    var showSettings by remember { "
            "mutableStateOf(false) }\n"
        ),
    )

    replace_once(
        path,
        (
            "    val peopleInRoom = "
            "state.clients.count { "
            "it.channelId == state.currentChannelId }\n\n"
            "    Scaffold(\n"
        ),
        (
            "    val peopleInRoom = "
            "state.clients.count { "
            "it.channelId == state.currentChannelId }\n\n"
            "    if (showSettings) {\n"
            "        AppearanceSettingsScreen(\n"
            "            onBack = { "
            "showSettings = false },\n"
            "        )\n"
            "        return\n"
            "    }\n\n"
            "    Scaffold(\n"
        ),
    )

    replace_once(
        path,
        (
            "                actions = {\n"
            "                    "
            "IconButton(onClick = onRefresh) {\n"
        ),
        (
            "                actions = {\n"
            "                    "
            "IconButton("
            "onClick = { showSettings = true }) {\n"
            "                        Icon(\n"
            "                            "
            "Icons.Default.Settings,\n"
            "                            "
            'contentDescription = "Instellingen",\n'
            "                        )\n"
            "                    }\n"
            "                    "
            "IconButton(onClick = onRefresh) {\n"
        ),
    )

    replace_once(
        path,
        (
            "private fun TalkTab(\n"
            "    state: ClientState,\n"
            "    onVoiceModeChanged: "
            "(VoiceMode) -> Unit,\n"
            "    onVadThresholdChanged: "
            "(Float) -> Unit,\n"
            "    onPushToTalkChanged: "
            "(Boolean) -> Unit,\n"
            ") {\n"
            "    Column(\n"
        ),
        (
            "private fun TalkTab(\n"
            "    state: ClientState,\n"
            "    onVoiceModeChanged: "
            "(VoiceMode) -> Unit,\n"
            "    onVadThresholdChanged: "
            "(Float) -> Unit,\n"
            "    onPushToTalkChanged: "
            "(Boolean) -> Unit,\n"
            ") {\n"
            "    val activeSpeakerNames = "
            "state.clients\n"
            "        .filter { client -> "
            "client.id in "
            "state.talkingClientIds }\n"
            "        .map { client -> "
            "client.nickname }\n\n"
            "    Column(\n"
        ),
    )

    replace_once(
        path,
        (
            "                Text(\n"
            "                    text = "
            "if (state.pushToTalkPressed) "
            '"ZENDEN" else '
            '"GEREED OM TE PRATEN",\n'
        ),
        (
            "                Text(\n"
            "                    text = when {\n"
            "                        "
            "state.pushToTalkPressed -> "
            '"Jij praat"\n'
            "                        "
            "activeSpeakerNames.isNotEmpty() ->\n"
            "                            "
            '"Nu aan het praten: '
            '${activeSpeakerNames.joinToString(", ")}"\n'
            "                        else -> "
            '"Niemand praat"\n'
            "                    },\n"
            "                    color = "
            "if (activeSpeakerNames.isNotEmpty()) {\n"
            "                        "
            "MaterialTheme.colorScheme.primary\n"
            "                    } else {\n"
            "                        "
            "MaterialTheme.colorScheme.onSurfaceVariant\n"
            "                    },\n"
            "                    style = "
            "MaterialTheme.typography.titleMedium,\n"
            "                    fontWeight = "
            "FontWeight.Bold,\n"
            "                    textAlign = "
            "TextAlign.Center,\n"
            "                    modifier = "
            "Modifier.fillMaxWidth(),\n"
            "                )\n\n"
            "                Text(\n"
            "                    text = "
            "if (state.pushToTalkPressed) "
            '"ZENDEN" else '
            '"GEREED OM TE PRATEN",\n'
        ),
    )


def upgrade_version(
    root: Path,
) -> None:

    path = root / "app/build.gradle.kts"

    text = path.read_text(
        encoding="utf-8"
    )

    if "versionCode = 2" in text:
        text = text.replace(
            "versionCode = 2",
            "versionCode = 3",
            1,
        )

    if (
        'versionName = "0.2.0-pttconnect-neon"'
        in text
    ):
        text = text.replace(
            'versionName = "0.2.0-pttconnect-neon"',
            'versionName = "0.3.0-pttconnect-ui"',
            1,
        )

    path.write_text(
        text,
        encoding="utf-8",
    )


def main() -> None:

    if len(sys.argv) != 2:
        raise SystemExit(
            "Gebruik: "
            "ui_upgrade.py <t3vox-root>"
        )

    root = Path(
        sys.argv[1]
    ).resolve()

    required = [
        (
            root
            / "app/src/main/java/com/toosarax/ts3client/ui/ConnectScreen.kt"
        ),
        (
            root
            / "app/src/main/java/com/toosarax/ts3client/ui/ChannelScreen.kt"
        ),
        (
            root
            / "app/src/main/java/com/toosarax/ts3client/ui/theme/Theme.kt"
        ),
        root / "app/build.gradle.kts",
    ]

    missing = [
        str(path)
        for path in required
        if not path.exists()
    ]

    if missing:
        raise RuntimeError(
            "PTTConnect UI upgrade: "
            "bestanden ontbreken: "
            + ", ".join(missing)
        )

    write_text(
        (
            root
            / "app/src/main/java/com/toosarax/ts3client/ui/theme/Theme.kt"
        ),
        THEME_KT,
    )

    write_text(
        (
            root
            / "app/src/main/java/com/toosarax/ts3client/ui/AppearanceSettingsScreen.kt"
        ),
        SETTINGS_SCREEN_KT,
    )

    write_text(
        (
            root
            / "app/src/main/java/com/toosarax/ts3client/ui/ConnectScreen.kt"
        ),
        CONNECT_SCREEN_KT,
    )

    upgrade_channel_screen(root)
    upgrade_version(root)

    print(
        "PTTConnect UI upgrade toegepast"
    )


if __name__ == "__main__":
    main()
