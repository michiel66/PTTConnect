#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(
            f"PTTConnect UI upgrade: verwachte tekst niet gevonden in {path}: {old[:160]!r}"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip("\n"), encoding="utf-8")


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
    PINK,
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

    fun setThemeMode(context: Context, value: ThemeMode) {
        themeMode = value
        context.getSharedPreferences(
            "pttconnect_appearance",
            Context.MODE_PRIVATE,
        ).edit()
            .putString("theme_mode", value.name)
            .apply()
    }

    fun setAccent(context: Context, value: AccentChoice) {
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
fun Ts3Theme(content: @Composable () -> Unit) {
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
        AccentChoice.PINK -> Color(0xFFFF4FA3)
    }

    val lightAccent = when (PttAppearance.accent) {
        AccentChoice.BLUE -> Color(0xFF006DB6)
        AccentChoice.GREEN -> Color(0xFF087F5B)
        AccentChoice.ORANGE -> Color(0xFFB85B00)
        AccentChoice.PURPLE -> Color(0xFF7048C1)
        AccentChoice.PINK -> Color(0xFFC2185B)
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
            onSurfaceVariant = Color(0xFFD0DEE9),
            outline = Color(0xFF5D7890),
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
import androidx.compose.foundation.layout.navigationBarsPadding
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
import androidx.compose.material3.Surface
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
fun AppearanceSettingsScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    PttAppearance.ensureLoaded(context)

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background,
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .navigationBarsPadding()
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(18.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconButton(onClick = onBack) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "Terug",
                    )
                }

                Column(modifier = Modifier.weight(1f)) {
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

            Card(modifier = Modifier.fillMaxWidth()) {
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
                            onClick = { PttAppearance.setThemeMode(context, ThemeMode.SYSTEM) },
                        )
                        ThemeChoiceButton(
                            label = "Donker",
                            selected = PttAppearance.themeMode == ThemeMode.DARK,
                            modifier = Modifier.weight(1f),
                            onClick = { PttAppearance.setThemeMode(context, ThemeMode.DARK) },
                        )
                        ThemeChoiceButton(
                            label = "Licht",
                            selected = PttAppearance.themeMode == ThemeMode.LIGHT,
                            modifier = Modifier.weight(1f),
                            onClick = { PttAppearance.setThemeMode(context, ThemeMode.LIGHT) },
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
                        AccentChoiceButton("Blauw", AccentChoice.BLUE, Modifier.weight(1f))
                        AccentChoiceButton("Groen", AccentChoice.GREEN, Modifier.weight(1f))
                    }

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        AccentChoiceButton("Oranje", AccentChoice.ORANGE, Modifier.weight(1f))
                        AccentChoiceButton("Paars", AccentChoice.PURPLE, Modifier.weight(1f))
                    }

                    AccentChoiceButton(
                        label = "Roze",
                        choice = AccentChoice.PINK,
                        modifier = Modifier.fillMaxWidth(),
                    )

                    Text(
                        text = "De accentkleur wordt gebruikt voor knoppen, de PTT-knop en actieve sprekers.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Text("Meer instellingen", fontWeight = FontWeight.Bold)
                    Text(
                        text = "Hier kunnen we later geluid, PTT, meldingen en andere opties onder toevoegen.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
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
        Button(onClick = onClick, modifier = modifier) { Text(label) }
    } else {
        OutlinedButton(onClick = onClick, modifier = modifier) { Text(label) }
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
            onClick = { PttAppearance.setAccent(context, choice) },
            modifier = modifier,
        ) { Text(label) }
    } else {
        OutlinedButton(
            onClick = { PttAppearance.setAccent(context, choice) },
            modifier = modifier,
        ) { Text(label) }
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
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
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
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
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

private const val PTT_CONNECT_VISIBLE_SUFFIX = "[PTT Connect]"

private fun nicknameForInput(value: String): String {
    val trimmed = value.trim()
    return if (trimmed.endsWith(PTT_CONNECT_VISIBLE_SUFFIX, ignoreCase = true)) {
        trimmed.dropLast(PTT_CONNECT_VISIBLE_SUFFIX.length).trimEnd()
    } else {
        trimmed
    }
}

@Composable
private fun pttTextFieldColors() = OutlinedTextFieldDefaults.colors(
    focusedTextColor = MaterialTheme.colorScheme.onSurface,
    unfocusedTextColor = MaterialTheme.colorScheme.onSurface,
    disabledTextColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.65f),
    cursorColor = MaterialTheme.colorScheme.primary,
    focusedLabelColor = MaterialTheme.colorScheme.primary,
    unfocusedLabelColor = MaterialTheme.colorScheme.onSurfaceVariant,
    disabledLabelColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.65f),
    focusedPlaceholderColor = MaterialTheme.colorScheme.onSurfaceVariant,
    unfocusedPlaceholderColor = MaterialTheme.colorScheme.onSurfaceVariant,
    disabledPlaceholderColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.55f),
    focusedBorderColor = MaterialTheme.colorScheme.primary,
    unfocusedBorderColor = MaterialTheme.colorScheme.outline,
    disabledBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.55f),
    focusedContainerColor = MaterialTheme.colorScheme.surface,
    unfocusedContainerColor = MaterialTheme.colorScheme.surface,
    disabledContainerColor = MaterialTheme.colorScheme.surface,
)

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
    var host by rememberSaveable { mutableStateOf(initialHost.orEmpty()) }
    var port by rememberSaveable { mutableStateOf((initialPort ?: 9987).toString()) }
    var nickname by rememberSaveable { mutableStateOf(nicknameForInput(initialNickname.orEmpty())) }
    var serverPassword by rememberSaveable { mutableStateOf("") }
    var serverLabel by rememberSaveable { mutableStateOf(initialHost.orEmpty()) }
    var rememberServer by rememberSaveable { mutableStateOf(true) }
    var showAdvanced by rememberSaveable { mutableStateOf(false) }
    var importedIdentity by rememberSaveable { mutableStateOf("") }
    var serverToDelete by rememberSaveable { mutableStateOf<SavedServer?>(null) }
    var showSettings by rememberSaveable { mutableStateOf(false) }

    val connecting = state.status == ConnectionStatus.CONNECTING

    if (showSettings) {
        AppearanceSettingsScreen(onBack = { showSettings = false })
        return
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        bottomBar = {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .navigationBarsPadding()
                    .imePadding(),
                color = MaterialTheme.colorScheme.background,
                tonalElevation = 4.dp,
            ) {
                Column(
                    modifier = Modifier.padding(horizontal = 20.dp, vertical = 12.dp),
                ) {
                    Button(
                        onClick = {
                            onConnect(
                                ConnectRequest(
                                    host = host.trim(),
                                    port = port.toIntOrNull() ?: 9987,
                                    nickname = nickname.trim(),
                                    serverPassword = serverPassword.ifBlank { null },
                                    importedIdentityIni = importedIdentity.ifBlank { null },
                                ),
                                rememberServer,
                                serverLabel,
                            )
                        },
                        enabled = !connecting && host.isNotBlank() && nickname.isNotBlank(),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        if (connecting) {
                            CircularProgressIndicator(
                                modifier = Modifier.padding(end = 8.dp),
                                strokeWidth = 2.dp,
                            )
                        }
                        Text(
                            text = if (connecting) {
                                stringResource(R.string.action_connecting)
                            } else {
                                stringResource(R.string.action_connect)
                            },
                        )
                    }
                }
            }
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "PTT Connect",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onBackground,
                    )
                    Text(
                        text = "Snel verbinden en praten",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }

                IconButton(onClick = { showSettings = true }) {
                    Icon(
                        imageVector = Icons.Default.Settings,
                        contentDescription = "Instellingen",
                        tint = MaterialTheme.colorScheme.onBackground,
                    )
                }
            }

            if (identityPreparing) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                    ),
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        CircularProgressIndicator(strokeWidth = 2.dp)
                        Text(stringResource(R.string.status_identity_preparing))
                    }
                }
            }

            if (savedServers.isNotEmpty()) {
                Text(
                    text = stringResource(R.string.section_saved_servers),
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onBackground,
                )

                savedServers.forEach { server ->
                    SavedServerCard(
                        server = server,
                        enabled = !connecting && nickname.isNotBlank(),
                        onConnect = {
                            if (nickname.isBlank()) {
                                nickname = nicknameForInput(initialNickname.orEmpty())
                            }
                            onConnectSaved(
                                server,
                                nickname.trim(),
                                serverPassword.ifBlank { null },
                                importedIdentity.ifBlank { null },
                            )
                        },
                        onDelete = { serverToDelete = server },
                    )
                }
            }

            Text(
                text = "Nieuwe verbinding",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground,
            )

            OutlinedTextField(
                value = host,
                onValueChange = {
                    val oldHost = host
                    host = it
                    if (serverLabel.isBlank() || serverLabel == oldHost) {
                        serverLabel = it.trim()
                    }
                },
                label = { Text(stringResource(R.string.label_host)) },
                placeholder = { Text(stringResource(R.string.label_host_hint)) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                enabled = !connecting,
                colors = pttTextFieldColors(),
            )

            OutlinedTextField(
                value = nickname,
                onValueChange = { nickname = it },
                label = { Text(stringResource(R.string.label_nickname)) },
                placeholder = { Text(stringResource(R.string.label_nickname_hint)) },
                supportingText = {
                    Text(
                        text = "Op TeamSpeak wordt automatisch [PTT Connect] achter je naam gezet.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                enabled = !connecting,
                colors = pttTextFieldColors(),
            )

            OutlinedButton(
                onClick = { showAdvanced = !showAdvanced },
                modifier = Modifier.fillMaxWidth(),
                enabled = !connecting,
            ) {
                Icon(
                    imageVector = if (showAdvanced) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                    contentDescription = null,
                )
                Text(
                    text = if (showAdvanced) {
                        "Geavanceerde opties verbergen"
                    } else {
                        "Geavanceerde opties"
                    },
                    modifier = Modifier.padding(start = 8.dp),
                )
            }

            if (showAdvanced) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant,
                    ),
                ) {
                    Column(
                        modifier = Modifier.padding(14.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        OutlinedTextField(
                            value = port,
                            onValueChange = {
                                port = it.filter { ch -> ch.isDigit() }.take(5)
                            },
                            label = { Text(stringResource(R.string.label_port)) },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            enabled = !connecting,
                            colors = pttTextFieldColors(),
                        )

                        OutlinedTextField(
                            value = serverPassword,
                            onValueChange = { serverPassword = it },
                            label = { Text(stringResource(R.string.label_server_password)) },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            visualTransformation = PasswordVisualTransformation(),
                            enabled = !connecting,
                            colors = pttTextFieldColors(),
                        )

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Checkbox(
                                checked = rememberServer,
                                onCheckedChange = { rememberServer = it },
                                enabled = !connecting,
                            )
                            Text(
                                text = stringResource(R.string.label_remember_server),
                                modifier = Modifier.weight(1f),
                                color = MaterialTheme.colorScheme.onSurface,
                            )
                        }

                        if (rememberServer) {
                            OutlinedTextField(
                                value = serverLabel,
                                onValueChange = { serverLabel = it },
                                label = { Text(stringResource(R.string.label_server_name)) },
                                modifier = Modifier.fillMaxWidth(),
                                singleLine = true,
                                enabled = !connecting,
                                colors = pttTextFieldColors(),
                            )
                        }

                        Text(
                            text = "Identiteit (optioneel)",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurface,
                        )

                        OutlinedTextField(
                            value = importedIdentity,
                            onValueChange = { importedIdentity = it },
                            label = { Text(stringResource(R.string.label_import_identity)) },
                            placeholder = { Text(stringResource(R.string.label_import_identity_hint)) },
                            modifier = Modifier.fillMaxWidth(),
                            minLines = 2,
                            maxLines = 4,
                            enabled = !connecting,
                            colors = pttTextFieldColors(),
                        )
                    }
                }
            }

            state.error?.let { error ->
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.errorContainer,
                    ),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(
                        text = error.userMessage(),
                        modifier = Modifier.padding(12.dp),
                        color = MaterialTheme.colorScheme.onErrorContainer,
                    )
                }
            }

            if (BuildConfig.DEBUG && state.debugLines.isNotEmpty()) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant,
                    ),
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp),
                    ) {
                        Text(
                            text = "Debug log",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurface,
                        )
                        state.debugLines.forEach { line ->
                            Text(
                                text = line,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace,
                            )
                        }
                    }
                }
            }
        }
    }

    serverToDelete?.let { server ->
        AlertDialog(
            onDismissRequest = { serverToDelete = null },
            title = { Text(stringResource(R.string.delete_server_title)) },
            text = {
                Text(
                    stringResource(
                        R.string.delete_server_body,
                        server.displayName,
                    )
                )
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        onRemoveSavedServer(server.id)
                        serverToDelete = null
                    },
                ) { Text(stringResource(R.string.action_delete)) }
            },
            dismissButton = {
                TextButton(onClick = { serverToDelete = null }) {
                    Text(stringResource(R.string.action_cancel))
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
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Icon(
                imageVector = Icons.Default.History,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
            )

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = server.displayName,
                    fontWeight = FontWeight.Medium,
                    color = MaterialTheme.colorScheme.onSurface,
                )
                Text(
                    text = "${server.host}:${server.port}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            Button(onClick = onConnect, enabled = enabled) {
                Text(stringResource(R.string.action_connect))
            }

            IconButton(onClick = onDelete, enabled = enabled) {
                Icon(
                    imageVector = Icons.Default.Delete,
                    contentDescription = stringResource(R.string.action_delete),
                )
            }
        }
    }
}
'''


CHANNEL_TREE_BUILDER_KT = r'''
package com.toosarax.ts3client.client

import com.toosarax.ts3client.protocol.ChannelInfo

object ChannelTreeBuilder {
    fun build(flatChannels: List<ChannelInfo>): List<ChannelTreeNode> {
        if (flatChannels.isEmpty()) return emptyList()

        val channelIds = flatChannels.map { it.id }.toSet()
        val childrenByParent = flatChannels.groupBy { it.parentId }
        val originalIndex = flatChannels
            .withIndex()
            .associate { indexed -> indexed.value.id to indexed.index }

        fun orderSiblings(siblings: List<ChannelInfo>): List<ChannelInfo> {
            if (siblings.size <= 1) return siblings

            val siblingIds = siblings.map { it.id }.toSet()
            val followers = siblings.groupBy { it.predecessorId }
            val visited = mutableSetOf<Int>()
            val ordered = mutableListOf<ChannelInfo>()

            fun walk(start: ChannelInfo) {
                var current: ChannelInfo? = start
                while (current != null && visited.add(current.id)) {
                    ordered += current
                    current = followers[current.id]
                        .orEmpty()
                        .filter { it.id !in visited }
                        .minByOrNull { originalIndex[it.id] ?: Int.MAX_VALUE }
                }
            }

            val heads = siblings
                .filter { channel ->
                    channel.predecessorId == 0 ||
                        channel.predecessorId !in siblingIds
                }
                .sortedBy { originalIndex[it.id] ?: Int.MAX_VALUE }

            heads.forEach(::walk)

            siblings
                .filter { it.id !in visited }
                .sortedBy { originalIndex[it.id] ?: Int.MAX_VALUE }
                .forEach(::walk)

            return ordered
        }

        fun buildLevel(parentId: Int): List<ChannelTreeNode> =
            orderSiblings(childrenByParent[parentId].orEmpty()).map { channel ->
                ChannelTreeNode(
                    channel = channel,
                    children = buildLevel(channel.id),
                )
            }

        val rootParentIds = flatChannels
            .map { it.parentId }
            .filter { it !in channelIds }
            .distinct()

        return rootParentIds.flatMap(::buildLevel)
    }
}
'''


TRANSMIT_ENGINE_KT = r'''
package com.toosarax.ts3client.audio.tx

import com.toosarax.ts3client.audio.AudioConstants
import com.toosarax.ts3client.audio.PcmInput
import com.toosarax.ts3client.protocol.OutgoingVoiceSource
import com.toosarax.ts3client.protocol.VoiceMode
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.util.concurrent.atomic.AtomicBoolean

class TransmitEngine(
    private val pcmInput: PcmInput,
    private val encoder: ConcentusVoiceEncoder = ConcentusVoiceEncoder(),
    private val packetBuffer: EncodedPacketBuffer = EncodedPacketBuffer(),
    private val scope: CoroutineScope,
) : OutgoingVoiceSource {
    private val transmitGate = AtomicBoolean(false)
    private val assembler = PcmFrameAssembler()
    private var captureJob: Job? = null
    private var voiceMode: VoiceMode = VoiceMode.PUSH_TO_TALK
    private var pushToTalkPressed = false
    private var muted = false
    private var vadThresholdDbfs: () -> Float = { -42f }
    private val vad = RmsVad(thresholdDbfs = { vadThresholdDbfs() })
    private val readBuffer = ShortArray(AudioConstants.FRAME_SAMPLES)
    private val encodeBuffer = ByteArray(AudioConstants.OPUS_MAX_PACKET_BYTES)
    var onVadOpenChanged: ((Boolean) -> Unit)? = null

    fun start() {
        pcmInput.start()
        captureJob = scope.launch(Dispatchers.IO) {
            android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_AUDIO)
            while (isActive) {
                val read = pcmInput.read(readBuffer, 0, readBuffer.size)
                if (read <= 0) continue
                assembler.push(readBuffer, 0, read) { frame ->
                    handleFrame(frame)
                }
            }
        }
    }

    fun stop() {
        captureJob?.cancel()
        captureJob = null
        pushToTalkPressed = false
        muted = false
        closeTransmitGate()
        assembler.reset()
        pcmInput.stop()
    }

    fun setVoiceMode(mode: VoiceMode) {
        if (voiceMode == mode) return
        closeTransmitGate()
        packetBuffer.clear()
        vad.reset()
        onVadOpenChanged?.invoke(false)
        voiceMode = mode
    }

    fun setPushToTalkPressed(pressed: Boolean) {
        pushToTalkPressed = pressed && !muted
        updateGate()
    }

    fun setMuted(value: Boolean) {
        muted = value
        if (value) {
            pushToTalkPressed = false
            closeTransmitGate()
        } else {
            updateGate()
        }
    }

    fun setVadThresholdDbfs(threshold: Float) {
        vadThresholdDbfs = { threshold }
    }

    fun closeTransmitGate() {
        transmitGate.set(false)
        packetBuffer.clear()
        vad.reset()
        onVadOpenChanged?.invoke(false)
    }

    override fun isReady(): Boolean = transmitGate.get()

    override fun pollPacket(): ByteArray? = packetBuffer.poll()

    private fun handleFrame(frame: ShortArray) {
        if (muted) {
            onVadOpenChanged?.invoke(false)
            updateGate(false)
            return
        }

        val shouldTransmit = when (voiceMode) {
            VoiceMode.PUSH_TO_TALK -> pushToTalkPressed
            VoiceMode.VOICE_ACTIVATION -> vad.evaluate(frame, AudioConstants.FRAME_SAMPLES)
        }
        onVadOpenChanged?.invoke(vad.isOpen())
        updateGate(shouldTransmit)
        if (!shouldTransmit) return

        val encodedSize = encoder.encode(frame, AudioConstants.FRAME_SAMPLES, encodeBuffer)
        if (encodedSize > 0) {
            packetBuffer.offer(encodeBuffer.copyOf(encodedSize))
        }
    }

    private fun updateGate(shouldTransmit: Boolean = computeShouldTransmit()) {
        transmitGate.set(shouldTransmit)
        if (!shouldTransmit) {
            packetBuffer.clear()
        }
    }

    private fun computeShouldTransmit(): Boolean {
        if (muted) return false
        return when (voiceMode) {
            VoiceMode.PUSH_TO_TALK -> pushToTalkPressed
            VoiceMode.VOICE_ACTIVATION -> vad.isOpen()
        }
    }
}
'''


def upgrade_client_models(root: Path) -> None:
    path = root / "app/src/main/java/com/toosarax/ts3client/client/ClientModels.kt"
    replace_once(
        path,
        "    val debugLines: List<String> = emptyList(),\n)",
        "    val debugLines: List<String> = emptyList(),\n"
        "    val microphoneMuted: Boolean = false,\n)",
    )


def upgrade_client_controller(root: Path) -> None:
    path = root / "app/src/main/java/com/toosarax/ts3client/client/ClientController.kt"
    replace_once(
        path,
        "    fun setPushToTalkPressed(pressed: Boolean)\n"
        "    fun setVadThresholdDbfs(threshold: Float)\n",
        "    fun setPushToTalkPressed(pressed: Boolean)\n"
        "    fun setMicrophoneMuted(muted: Boolean) = Unit\n"
        "    fun setVadThresholdDbfs(threshold: Float)\n",
    )


def upgrade_protocol_models(root: Path) -> None:
    path = root / "app/src/main/java/com/toosarax/ts3client/protocol/ProtocolModels.kt"
    replace_once(
        path,
        "    suspend fun joinChannel(channelId: Int, password: String?)\n"
        "    suspend fun disconnect(reason: String? = null)\n",
        "    suspend fun joinChannel(channelId: Int, password: String?)\n"
        "    suspend fun setMicrophoneMuted(muted: Boolean) = Unit\n"
        "    suspend fun disconnect(reason: String? = null)\n",
    )


def upgrade_ts3j_protocol(root: Path) -> None:
    path = root / "app/src/main/java/com/toosarax/ts3client/protocol/ts3j/Ts3jProtocol.kt"

    replace_once(
        path,
        "import com.github.manevolent.ts3j.api.Codec\n"
        "import com.github.manevolent.ts3j.command.CommandException\n",
        "import com.github.manevolent.ts3j.api.Codec\n"
        "import com.github.manevolent.ts3j.command.CommandException\n"
        "import com.github.manevolent.ts3j.command.SingleCommand\n"
        "import com.github.manevolent.ts3j.command.parameter.CommandSingleParameter\n"
        "import com.github.manevolent.ts3j.protocol.ProtocolRole\n",
    )

    replace_once(
        path,
        "    override suspend fun joinChannel(channelId: Int, password: String?) = withContext(ioDispatcher) {\n"
        "        socket.joinChannel(channelId, password)\n"
        "    }\n\n"
        "    override suspend fun disconnect(reason: String?) = withContext(ioDispatcher) {\n",
        "    override suspend fun joinChannel(channelId: Int, password: String?) = withContext(ioDispatcher) {\n"
        "        socket.joinChannel(channelId, password)\n"
        "    }\n\n"
        "    override suspend fun setMicrophoneMuted(muted: Boolean) = withContext(ioDispatcher) {\n"
        "        val command = SingleCommand(\"clientupdate\", ProtocolRole.CLIENT)\n"
        "        command.add(\n"
        "            CommandSingleParameter(\n"
        "                \"client_input_muted\",\n"
        "                if (muted) \"1\" else \"0\",\n"
        "            ),\n"
        "        )\n"
        "        socket.executeCommand(command).complete()\n"
        "    }\n\n"
        "    override suspend fun disconnect(reason: String?) = withContext(ioDispatcher) {\n",
    )


def upgrade_default_runtime(root: Path) -> None:
    path = root / "app/src/main/java/com/toosarax/ts3client/client/DefaultClientRuntime.kt"

    replace_once(
        path,
        "    override fun setPushToTalkPressed(pressed: Boolean) {\n"
        "        transmitEngine.setPushToTalkPressed(pressed)\n"
        "        stateFlow.update { it.copy(pushToTalkPressed = pressed) }\n"
        "    }\n\n"
        "    override fun setVadThresholdDbfs(threshold: Float) {\n",
        "    override fun setPushToTalkPressed(pressed: Boolean) {\n"
        "        val allowed = pressed && !stateFlow.value.microphoneMuted\n"
        "        transmitEngine.setPushToTalkPressed(allowed)\n"
        "        stateFlow.update { it.copy(pushToTalkPressed = allowed) }\n"
        "    }\n\n"
        "    override fun setMicrophoneMuted(muted: Boolean) {\n"
        "        scope.launch {\n"
        "            transmitEngine.setMuted(muted)\n"
        "            stateFlow.update {\n"
        "                it.copy(\n"
        "                    microphoneMuted = muted,\n"
        "                    pushToTalkPressed = false,\n"
        "                    vadOpen = false,\n"
        "                )\n"
        "            }\n"
        "            protocol?.let { activeProtocol ->\n"
        "                runCatching { activeProtocol.setMicrophoneMuted(muted) }\n"
        "                    .onFailure { error ->\n"
        "                        appendDebug(\n"
        "                            \"TeamSpeak mute-status kon niet worden bijgewerkt: ${error.message}\",\n"
        "                        )\n"
        "                    }\n"
        "            }\n"
        "        }\n"
        "    }\n\n"
        "    override fun setVadThresholdDbfs(threshold: Float) {\n",
    )

    replace_once(
        path,
        "                pushToTalkPressed = false,\n"
        "                vadOpen = false,\n"
        "                connectedHost = \"\",\n",
        "                pushToTalkPressed = false,\n"
        "                vadOpen = false,\n"
        "                microphoneMuted = false,\n"
        "                connectedHost = \"\",\n",
    )


def upgrade_client_view_model(root: Path) -> None:
    path = root / "app/src/main/java/com/toosarax/ts3client/ui/ClientViewModel.kt"

    replace_once(
        path,
        "import kotlinx.coroutines.launch\n\n"
        "class ClientViewModel(\n",
        "import kotlinx.coroutines.launch\n\n"
        "private const val PTT_CONNECT_SUFFIX = \" [PTT Connect]\"\n"
        "private const val TS3_NICKNAME_MAX_LENGTH = 30\n\n"
        "private fun brandedPttNickname(raw: String): String {\n"
        "    val trimmed = raw.trim()\n"
        "    val visibleSuffix = PTT_CONNECT_SUFFIX.trimStart()\n"
        "    val base = if (trimmed.endsWith(visibleSuffix, ignoreCase = true)) {\n"
        "        trimmed.dropLast(visibleSuffix.length).trimEnd()\n"
        "    } else {\n"
        "        trimmed\n"
        "    }\n"
        "    if (base.isBlank()) return \"\"\n"
        "    val maxBaseLength = (TS3_NICKNAME_MAX_LENGTH - PTT_CONNECT_SUFFIX.length).coerceAtLeast(1)\n"
        "    return base.take(maxBaseLength).trimEnd() + PTT_CONNECT_SUFFIX\n"
        "}\n\n"
        "class ClientViewModel(\n",
    )

    replace_once(
        path,
        "        viewModelScope.launch {\n"
        "            val result = controller.connect(request)\n"
        "            if (result.isSuccess && rememberServer) {\n",
        "        viewModelScope.launch {\n"
        "            val brandedRequest = request.copy(\n"
        "                nickname = brandedPttNickname(request.nickname),\n"
        "            )\n"
        "            val result = controller.connect(brandedRequest)\n"
        "            if (result.isSuccess && rememberServer) {\n",
    )

    replace_once(
        path,
        "    fun setVoiceMode(mode: VoiceMode) = controller.setVoiceMode(mode)\n"
        "    fun setPushToTalkPressed(pressed: Boolean) = controller.setPushToTalkPressed(pressed)\n"
        "    fun setVadThresholdDbfs(threshold: Float) = controller.setVadThresholdDbfs(threshold)\n",
        "    fun setVoiceMode(mode: VoiceMode) = controller.setVoiceMode(mode)\n"
        "    fun setPushToTalkPressed(pressed: Boolean) = controller.setPushToTalkPressed(pressed)\n"
        "    fun setMicrophoneMuted(muted: Boolean) = controller.setMicrophoneMuted(muted)\n"
        "    fun setVadThresholdDbfs(threshold: Float) = controller.setVadThresholdDbfs(threshold)\n",
    )


def upgrade_ts3_app(root: Path) -> None:
    path = root / "app/src/main/java/com/toosarax/ts3client/ui/Ts3App.kt"
    replace_once(
        path,
        "                onVadThresholdChanged = viewModel::setVadThresholdDbfs,\n"
        "                onPushToTalkChanged = viewModel::setPushToTalkPressed,\n"
        "            )\n",
        "                onVadThresholdChanged = viewModel::setVadThresholdDbfs,\n"
        "                onPushToTalkChanged = viewModel::setPushToTalkPressed,\n"
        "                onMicrophoneMutedChanged = viewModel::setMicrophoneMuted,\n"
        "            )\n",
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
        "    onVadThresholdChanged: (Float) -> Unit,\n"
        "    onPushToTalkChanged: (Boolean) -> Unit,\n"
        ") {\n",
        "    onVadThresholdChanged: (Float) -> Unit,\n"
        "    onPushToTalkChanged: (Boolean) -> Unit,\n"
        "    onMicrophoneMutedChanged: (Boolean) -> Unit,\n"
        ") {\n",
    )

    replace_once(
        path,
        "    var selectedTab by remember { mutableIntStateOf(InCallTab.Talk.ordinal) }\n",
        "    var selectedTab by remember { mutableIntStateOf(InCallTab.Talk.ordinal) }\n"
        "    var showSettings by remember { mutableStateOf(false) }\n",
    )

    replace_once(
        path,
        "    val peopleInRoom = state.clients.count { it.channelId == state.currentChannelId }\n\n"
        "    Scaffold(\n",
        "    val peopleInRoom = state.clients.count { it.channelId == state.currentChannelId }\n\n"
        "    if (showSettings) {\n"
        "        AppearanceSettingsScreen(onBack = { showSettings = false })\n"
        "        return\n"
        "    }\n\n"
        "    Scaffold(\n",
    )

    replace_once(
        path,
        "                actions = {\n"
        "                    IconButton(onClick = onRefresh) {\n",
        "                actions = {\n"
        "                    IconButton(onClick = { showSettings = true }) {\n"
        "                        Icon(\n"
        "                            Icons.Default.Settings,\n"
        "                            contentDescription = \"Instellingen\",\n"
        "                        )\n"
        "                    }\n"
        "                    IconButton(onClick = onRefresh) {\n",
    )

    replace_once(
        path,
        "                    onVadThresholdChanged = onVadThresholdChanged,\n"
        "                    onPushToTalkChanged = onPushToTalkChanged,\n"
        "                )\n",
        "                    onVadThresholdChanged = onVadThresholdChanged,\n"
        "                    onPushToTalkChanged = onPushToTalkChanged,\n"
        "                    onMicrophoneMutedChanged = onMicrophoneMutedChanged,\n"
        "                )\n",
    )

    replace_once(
        path,
        "                InCallTab.Rooms -> RoomsTab(\n"
        "                    channels = state.channels,\n"
        "                    currentChannelId = state.currentChannelId,\n"
        "                    onJoin = { channel ->\n",
        "                InCallTab.Rooms -> RoomsTab(\n"
        "                    channels = state.channels,\n"
        "                    clients = state.clients,\n"
        "                    ownClientId = state.ownClientId,\n"
        "                    talkingClientIds = state.talkingClientIds,\n"
        "                    currentChannelId = state.currentChannelId,\n"
        "                    onJoin = { channel ->\n",
    )

    replace_once(
        path,
        "@Composable\n"
        "private fun RoomsTab(\n"
        "    channels: List<ChannelTreeNode>,\n"
        "    currentChannelId: Int,\n"
        "    onJoin: (com.toosarax.ts3client.protocol.ChannelInfo) -> Unit,\n"
        ") {\n"
        "    if (channels.isEmpty()) {\n",
        "@Composable\n"
        "private fun RoomsTab(\n"
        "    channels: List<ChannelTreeNode>,\n"
        "    clients: List<RemoteClientInfo>,\n"
        "    ownClientId: Int,\n"
        "    talkingClientIds: Set<Int>,\n"
        "    currentChannelId: Int,\n"
        "    onJoin: (com.toosarax.ts3client.protocol.ChannelInfo) -> Unit,\n"
        ") {\n"
        "    if (channels.isEmpty()) {\n",
    )

    replace_once(
        path,
        "        channels.forEach { node ->\n"
        "            channelItems(node, depth = 0, currentChannelId, onJoin)\n"
        "        }\n",
        "        channels.forEach { node ->\n"
        "            channelItems(\n"
        "                node = node,\n"
        "                depth = 0,\n"
        "                currentChannelId = currentChannelId,\n"
        "                clients = clients,\n"
        "                ownClientId = ownClientId,\n"
        "                talkingClientIds = talkingClientIds,\n"
        "                onJoin = onJoin,\n"
        "            )\n"
        "        }\n",
    )

    replace_once(
        path,
        "private fun androidx.compose.foundation.lazy.LazyListScope.channelItems(\n"
        "    node: ChannelTreeNode,\n"
        "    depth: Int,\n"
        "    currentChannelId: Int,\n"
        "    onJoin: (com.toosarax.ts3client.protocol.ChannelInfo) -> Unit,\n"
        ") {\n"
        "    val channel = node.channel\n"
        "    val isCurrent = channel.id == currentChannelId\n",
        "private fun androidx.compose.foundation.lazy.LazyListScope.channelItems(\n"
        "    node: ChannelTreeNode,\n"
        "    depth: Int,\n"
        "    currentChannelId: Int,\n"
        "    clients: List<RemoteClientInfo>,\n"
        "    ownClientId: Int,\n"
        "    talkingClientIds: Set<Int>,\n"
        "    onJoin: (com.toosarax.ts3client.protocol.ChannelInfo) -> Unit,\n"
        ") {\n"
        "    val channel = node.channel\n"
        "    val isCurrent = channel.id == currentChannelId\n"
        "    val channelClients = clients\n"
        "        .filter { client -> client.channelId == channel.id }\n"
        "        .sortedWith(\n"
        "            compareBy<RemoteClientInfo> { client -> client.id != ownClientId }\n"
        "                .thenBy { client -> client.nickname.lowercase() },\n"
        "        )\n",
    )

    replace_once(
        path,
        "    node.children.forEach { child ->\n"
        "        channelItems(child, depth + 1, currentChannelId, onJoin)\n"
        "    }\n"
        "}\n\n"
        "@Composable\n"
        "private fun ChannelRow(\n",
        "    channelClients.forEach { client ->\n"
        "        item(key = \"channel-${channel.id}-client-${client.id}\") {\n"
        "            ChannelUserRow(\n"
        "                client = client,\n"
        "                depth = depth,\n"
        "                isOwnUser = client.id == ownClientId,\n"
        "                talking = client.id in talkingClientIds,\n"
        "            )\n"
        "        }\n"
        "    }\n"
        "    node.children.forEach { child ->\n"
        "        channelItems(\n"
        "            node = child,\n"
        "            depth = depth + 1,\n"
        "            currentChannelId = currentChannelId,\n"
        "            clients = clients,\n"
        "            ownClientId = ownClientId,\n"
        "            talkingClientIds = talkingClientIds,\n"
        "            onJoin = onJoin,\n"
        "        )\n"
        "    }\n"
        "}\n\n"
        "@Composable\n"
        "private fun ChannelUserRow(\n"
        "    client: RemoteClientInfo,\n"
        "    depth: Int,\n"
        "    isOwnUser: Boolean,\n"
        "    talking: Boolean,\n"
        ") {\n"
        "    Row(\n"
        "        modifier = Modifier\n"
        "            .fillMaxWidth()\n"
        "            .padding(start = (32 + depth * 16).dp, end = 8.dp)\n"
        "            .clip(RoundedCornerShape(12.dp))\n"
        "            .background(\n"
        "                if (talking) MaterialTheme.colorScheme.primary.copy(alpha = 0.12f)\n"
        "                else Color.Transparent,\n"
        "            )\n"
        "            .padding(horizontal = 12.dp, vertical = 8.dp),\n"
        "        verticalAlignment = Alignment.CenterVertically,\n"
        "        horizontalArrangement = Arrangement.spacedBy(10.dp),\n"
        "    ) {\n"
        "        Icon(\n"
        "            imageVector = if (talking) Icons.Default.Mic else Icons.Default.Person,\n"
        "            contentDescription = null,\n"
        "            tint = if (talking) MaterialTheme.colorScheme.primary\n"
        "            else MaterialTheme.colorScheme.onSurfaceVariant,\n"
        "            modifier = Modifier.size(20.dp),\n"
        "        )\n"
        "        Column(modifier = Modifier.weight(1f)) {\n"
        "            Text(\n"
        "                text = client.nickname,\n"
        "                style = MaterialTheme.typography.bodyMedium,\n"
        "                fontWeight = if (isOwnUser || talking) FontWeight.Bold else FontWeight.Medium,\n"
        "                color = if (talking) MaterialTheme.colorScheme.primary\n"
        "                else MaterialTheme.colorScheme.onSurface,\n"
        "            )\n"
        "            if (isOwnUser) {\n"
        "                Text(\n"
        "                    text = \"Jij\",\n"
        "                    style = MaterialTheme.typography.labelSmall,\n"
        "                    color = MaterialTheme.colorScheme.primary,\n"
        "                )\n"
        "            }\n"
        "        }\n"
        "        if (talking) {\n"
        "            Text(\n"
        "                text = \"Praat\",\n"
        "                style = MaterialTheme.typography.labelSmall,\n"
        "                fontWeight = FontWeight.Bold,\n"
        "                color = MaterialTheme.colorScheme.primary,\n"
        "            )\n"
        "        }\n"
        "    }\n"
        "}\n\n"
        "@Composable\n"
        "private fun ChannelRow(\n",
    )

    replace_once(
        path,
        "private fun TalkTab(\n"
        "    state: ClientState,\n"
        "    onVoiceModeChanged: (VoiceMode) -> Unit,\n"
        "    onVadThresholdChanged: (Float) -> Unit,\n"
        "    onPushToTalkChanged: (Boolean) -> Unit,\n"
        ") {\n"
        "    Column(\n",
        "private fun TalkTab(\n"
        "    state: ClientState,\n"
        "    onVoiceModeChanged: (VoiceMode) -> Unit,\n"
        "    onVadThresholdChanged: (Float) -> Unit,\n"
        "    onPushToTalkChanged: (Boolean) -> Unit,\n"
        "    onMicrophoneMutedChanged: (Boolean) -> Unit,\n"
        ") {\n"
        "    val activeSpeakerNames = state.clients\n"
        "        .filter { client -> client.id in state.talkingClientIds }\n"
        "        .map { client -> client.nickname }\n\n"
        "    Column(\n",
    )

    replace_once(
        path,
        "                    enabled = !state.unsupportedCodec,\n",
        "                    enabled = !state.unsupportedCodec && !state.microphoneMuted,\n",
    )

    replace_once(
        path,
        "                Text(\n"
        "                    text = if (state.pushToTalkPressed) \"ZENDEN\" else \"GEREED OM TE PRATEN\",\n"
        "                    color = if (state.pushToTalkPressed) MaterialTheme.colorScheme.error\n"
        "                    else MaterialTheme.colorScheme.primary,\n"
        "                    style = MaterialTheme.typography.labelLarge,\n"
        "                    fontWeight = FontWeight.Bold,\n"
        "                    textAlign = TextAlign.Center,\n"
        "                    modifier = Modifier.fillMaxWidth(),\n"
        "                )\n",
        "                Text(\n"
        "                    text = when {\n"
        "                        state.pushToTalkPressed -> \"Jij praat\"\n"
        "                        activeSpeakerNames.isNotEmpty() ->\n"
        "                            \"Nu aan het praten: ${activeSpeakerNames.joinToString(\", \")}\"\n"
        "                        else -> \"Niemand praat\"\n"
        "                    },\n"
        "                    color = if (activeSpeakerNames.isNotEmpty()) {\n"
        "                        MaterialTheme.colorScheme.primary\n"
        "                    } else {\n"
        "                        MaterialTheme.colorScheme.onSurfaceVariant\n"
        "                    },\n"
        "                    style = MaterialTheme.typography.titleMedium,\n"
        "                    fontWeight = FontWeight.Bold,\n"
        "                    textAlign = TextAlign.Center,\n"
        "                    modifier = Modifier.fillMaxWidth(),\n"
        "                )\n\n"
        "                Text(\n"
        "                    text = when {\n"
        "                        state.microphoneMuted -> \"MICROFOON GEMUTE\"\n"
        "                        state.pushToTalkPressed -> \"ZENDEN\"\n"
        "                        else -> \"GEREED OM TE PRATEN\"\n"
        "                    },\n"
        "                    color = when {\n"
        "                        state.microphoneMuted -> MaterialTheme.colorScheme.error\n"
        "                        state.pushToTalkPressed -> MaterialTheme.colorScheme.error\n"
        "                        else -> MaterialTheme.colorScheme.primary\n"
        "                    },\n"
        "                    style = MaterialTheme.typography.labelLarge,\n"
        "                    fontWeight = FontWeight.Bold,\n"
        "                    textAlign = TextAlign.Center,\n"
        "                    modifier = Modifier.fillMaxWidth(),\n"
        "                )\n\n"
        "                Button(\n"
        "                    onClick = {\n"
        "                        onMicrophoneMutedChanged(!state.microphoneMuted)\n"
        "                    },\n"
        "                    modifier = Modifier.fillMaxWidth(),\n"
        "                ) {\n"
        "                    Text(\n"
        "                        if (state.microphoneMuted) {\n"
        "                            \"Microfoon aanzetten\"\n"
        "                        } else {\n"
        "                            \"Microfoon dempen\"\n"
        "                        },\n"
        "                    )\n"
        "                }\n",
    )


def upgrade_version(root: Path) -> None:
    path = root / "app/build.gradle.kts"
    text = path.read_text(encoding="utf-8")

    if "versionCode = 2" in text:
        text = text.replace("versionCode = 2", "versionCode = 5", 1)

    if 'versionName = "0.2.0-pttconnect-neon"' in text:
        text = text.replace(
            'versionName = "0.2.0-pttconnect-neon"',
            'versionName = "0.5.0-pttconnect-channels"',
            1,
        )

    path.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Gebruik: ui_upgrade.py <t3vox-root>")

    root = Path(sys.argv[1]).resolve()

    required = [
        root / "app/src/main/java/com/toosarax/ts3client/ui/ConnectScreen.kt",
        root / "app/src/main/java/com/toosarax/ts3client/ui/ChannelScreen.kt",
        root / "app/src/main/java/com/toosarax/ts3client/ui/Ts3App.kt",
        root / "app/src/main/java/com/toosarax/ts3client/ui/ClientViewModel.kt",
        root / "app/src/main/java/com/toosarax/ts3client/ui/theme/Theme.kt",
        root / "app/src/main/java/com/toosarax/ts3client/client/ClientModels.kt",
        root / "app/src/main/java/com/toosarax/ts3client/client/ClientController.kt",
        root / "app/src/main/java/com/toosarax/ts3client/client/DefaultClientRuntime.kt",
        root / "app/src/main/java/com/toosarax/ts3client/protocol/ProtocolModels.kt",
        root / "app/src/main/java/com/toosarax/ts3client/protocol/ts3j/Ts3jProtocol.kt",
        root / "app/src/main/java/com/toosarax/ts3client/audio/tx/TransmitEngine.kt",
        root / "app/src/main/java/com/toosarax/ts3client/client/ChannelTreeBuilder.kt",
        root / "app/build.gradle.kts",
    ]

    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(
            "PTTConnect UI upgrade: bestanden ontbreken: " + ", ".join(missing)
        )

    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/ui/theme/Theme.kt",
        THEME_KT,
    )
    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/ui/AppearanceSettingsScreen.kt",
        SETTINGS_SCREEN_KT,
    )
    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/ui/ConnectScreen.kt",
        CONNECT_SCREEN_KT,
    )
    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/audio/tx/TransmitEngine.kt",
        TRANSMIT_ENGINE_KT,
    )
    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/client/ChannelTreeBuilder.kt",
        CHANNEL_TREE_BUILDER_KT,
    )

    upgrade_client_models(root)
    upgrade_client_controller(root)
    upgrade_protocol_models(root)
    upgrade_ts3j_protocol(root)
    upgrade_default_runtime(root)
    upgrade_client_view_model(root)
    upgrade_ts3_app(root)
    upgrade_channel_screen(root)
    upgrade_version(root)

    print("PTTConnect UI + kanalenvolgorde + online gebruikers toegepast")


if __name__ == "__main__":
    main()
