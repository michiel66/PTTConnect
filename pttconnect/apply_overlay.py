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


def replace_section(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    start_pos = text.find(start)
    end_pos = text.find(end, start_pos + len(start))
    if start_pos < 0 or end_pos < 0:
        raise RuntimeError(f"Expected section markers not found in {path}")
    path.write_text(text[:start_pos] + replacement + text[end_pos:], encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text.lstrip("\n"), encoding="utf-8")


THEME_KT = r'''
package com.toosarax.ts3client.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val NeonBlue = Color(0xFF009BFF)
private val NeonBlueSoft = Color(0xFF40C4FF)
private val DeepBackground = Color(0xFF020711)
private val DeepSurface = Color(0xFF07111F)
private val DeepSurface2 = Color(0xFF0A1829)

private val PttConnectColors = darkColorScheme(
    primary = NeonBlue,
    onPrimary = Color.White,
    primaryContainer = Color(0xFF003B66),
    onPrimaryContainer = Color(0xFFD6EEFF),
    secondary = NeonBlueSoft,
    onSecondary = Color(0xFF001B2B),
    secondaryContainer = Color(0xFF07314A),
    onSecondaryContainer = Color(0xFFC6E9FF),
    background = DeepBackground,
    onBackground = Color(0xFFF4F8FF),
    surface = DeepSurface,
    onSurface = Color(0xFFF4F8FF),
    surfaceVariant = DeepSurface2,
    onSurfaceVariant = Color(0xFFAFC4D8),
    outline = Color(0xFF27435E),
    outlineVariant = Color(0xFF142A40),
    error = Color(0xFFFF334F),
    onError = Color.White,
    errorContainer = Color(0xFF5A0B17),
    onErrorContainer = Color(0xFFFFD9DE),
)

@Composable
fun Ts3Theme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = PttConnectColors,
        content = content,
    )
}
'''

PTT_BUTTON_KT = r'''
package com.toosarax.ts3client.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.toosarax.ts3client.R

@Composable
fun PttButton(
    pressed: Boolean,
    enabled: Boolean,
    onPressedChange: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
) {
    val accent = if (pressed) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary
    val glow = accent.copy(alpha = if (pressed) 0.42f else 0.32f)

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(330.dp),
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .size(292.dp)
                .clip(CircleShape)
                .background(glow.copy(alpha = 0.10f)),
        )
        Box(
            modifier = Modifier
                .size(276.dp)
                .clip(CircleShape)
                .background(glow.copy(alpha = 0.14f))
                .border(7.dp, glow, CircleShape),
        )
        Box(
            modifier = Modifier
                .size(254.dp)
                .alpha(if (enabled) 1f else 0.42f)
                .clip(CircleShape)
                .background(Color(0xFF05101D))
                .border(4.dp, accent, CircleShape)
                .pointerInput(enabled) {
                    if (!enabled) return@pointerInput
                    detectTapGestures(
                        onPress = {
                            onPressedChange(true)
                            try {
                                tryAwaitRelease()
                            } finally {
                                onPressedChange(false)
                            }
                        },
                    )
                },
            contentAlignment = Alignment.Center,
        ) {
            Box(
                modifier = Modifier
                    .size(226.dp)
                    .clip(CircleShape)
                    .border(1.dp, accent.copy(alpha = 0.55f), CircleShape),
                contentAlignment = Alignment.Center,
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.padding(horizontal = 24.dp),
                ) {
                    Icon(
                        imageVector = Icons.Default.Mic,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(62.dp),
                    )
                    Text(
                        text = stringResource(if (pressed) R.string.ptt_active else R.string.ptt_hold),
                        color = if (pressed) MaterialTheme.colorScheme.error else Color.White,
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Black,
                        textAlign = TextAlign.Center,
                    )
                }
            }
        }
    }
}
'''

CHANNEL_SCREEN_KT = r'''
package com.toosarax.ts3client.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ExitToApp
import androidx.compose.material.icons.filled.ChatBubble
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.Group
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.toosarax.ts3client.R
import com.toosarax.ts3client.client.ChannelTreeNode
import com.toosarax.ts3client.client.ClientState
import com.toosarax.ts3client.protocol.RemoteClientInfo
import com.toosarax.ts3client.protocol.VoiceMode

private enum class InCallTab { Talk, Rooms, People }

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChannelScreen(
    state: ClientState,
    onRefresh: () -> Unit,
    onDisconnect: () -> Unit,
    onJoinChannel: (Int, String?) -> Unit,
    onVoiceModeChanged: (VoiceMode) -> Unit,
    onVadThresholdChanged: (Float) -> Unit,
    onPushToTalkChanged: (Boolean) -> Unit,
) {
    var selectedTab by remember { mutableIntStateOf(InCallTab.Talk.ordinal) }
    var passwordChannelId by remember { mutableStateOf<Int?>(null) }
    var channelPassword by remember { mutableStateOf("") }
    val tabs = InCallTab.entries
    val peopleInRoom = state.clients.count { it.channelId == state.currentChannelId }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                    titleContentColor = MaterialTheme.colorScheme.onBackground,
                    actionIconContentColor = MaterialTheme.colorScheme.onBackground,
                ),
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(13.dp)
                                .clip(CircleShape)
                                .background(MaterialTheme.colorScheme.primary),
                        )
                        Spacer(Modifier.width(10.dp))
                        Column {
                            Text(
                                text = state.connectedHost.ifBlank { stringResource(R.string.status_connected) },
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                            )
                            if (state.currentChannelName.isNotBlank()) {
                                Text(
                                    text = stringResource(R.string.status_in_channel, state.currentChannelName),
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    }
                },
                actions = {
                    IconButton(onClick = onRefresh) {
                        Icon(Icons.Default.Refresh, contentDescription = stringResource(R.string.action_refresh))
                    }
                    IconButton(onClick = onDisconnect) {
                        Icon(
                            Icons.AutoMirrored.Filled.ExitToApp,
                            contentDescription = stringResource(R.string.action_disconnect),
                        )
                    }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 8.dp),
        ) {
            if (state.unsupportedCodec) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 6.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                ) {
                    Text(
                        text = stringResource(R.string.unsupported_codec),
                        modifier = Modifier.padding(12.dp),
                        color = MaterialTheme.colorScheme.onErrorContainer,
                    )
                }
            }

            state.error?.let { error ->
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 6.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                ) {
                    Text(
                        text = error.userMessage(),
                        modifier = Modifier.padding(12.dp),
                        color = MaterialTheme.colorScheme.onErrorContainer,
                    )
                }
            }

            NeonTabs(tabs = tabs, selectedTab = selectedTab, onSelected = { selectedTab = it })
            Spacer(Modifier.height(10.dp))

            when (tabs[selectedTab]) {
                InCallTab.Talk -> TalkTab(
                    state = state,
                    onVoiceModeChanged = onVoiceModeChanged,
                    onVadThresholdChanged = onVadThresholdChanged,
                    onPushToTalkChanged = onPushToTalkChanged,
                )
                InCallTab.Rooms -> RoomsTab(
                    channels = state.channels,
                    currentChannelId = state.currentChannelId,
                    onJoin = { channel ->
                        if (channel.hasPassword) {
                            passwordChannelId = channel.id
                            channelPassword = ""
                        } else {
                            onJoinChannel(channel.id, null)
                        }
                    },
                )
                InCallTab.People -> PeopleTab(
                    clients = state.clients.filter { it.channelId == state.currentChannelId },
                    talkingClientIds = state.talkingClientIds,
                    peopleCountLabel = stringResource(R.string.people_count, peopleInRoom),
                )
            }
        }
    }

    if (passwordChannelId != null) {
        AlertDialog(
            onDismissRequest = { passwordChannelId = null },
            title = { Text(stringResource(R.string.label_channel_password)) },
            text = {
                OutlinedTextField(
                    value = channelPassword,
                    onValueChange = { channelPassword = it },
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        onJoinChannel(passwordChannelId!!, channelPassword.ifBlank { null })
                        passwordChannelId = null
                    },
                ) { Text(stringResource(R.string.action_join)) }
            },
            dismissButton = {
                Button(onClick = { passwordChannelId = null }) {
                    Text(stringResource(R.string.action_cancel))
                }
            },
        )
    }
}

@Composable
private fun NeonTabs(
    tabs: List<InCallTab>,
    selectedTab: Int,
    onSelected: (Int) -> Unit,
) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(18.dp),
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(18.dp)),
    ) {
        Row(modifier = Modifier.padding(5.dp)) {
            tabs.forEachIndexed { index, tab ->
                val selected = selectedTab == index
                val icon = when (tab) {
                    InCallTab.Talk -> Icons.Default.ChatBubble
                    InCallTab.Rooms -> Icons.Default.List
                    InCallTab.People -> Icons.Default.Group
                }
                val label = when (tab) {
                    InCallTab.Talk -> stringResource(R.string.tab_talk)
                    InCallTab.Rooms -> stringResource(R.string.tab_rooms)
                    InCallTab.People -> stringResource(R.string.tab_people)
                }
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(14.dp))
                        .background(
                            if (selected) MaterialTheme.colorScheme.primary.copy(alpha = 0.18f)
                            else Color.Transparent,
                        )
                        .border(
                            width = if (selected) 1.dp else 0.dp,
                            color = if (selected) MaterialTheme.colorScheme.primary.copy(alpha = 0.75f)
                            else Color.Transparent,
                            shape = RoundedCornerShape(14.dp),
                        )
                        .clickable { onSelected(index) }
                        .padding(vertical = 10.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = if (selected) MaterialTheme.colorScheme.primary
                        else MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(25.dp),
                    )
                    Text(
                        text = label,
                        color = if (selected) MaterialTheme.colorScheme.primary
                        else MaterialTheme.colorScheme.onSurfaceVariant,
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                    )
                }
            }
        }
    }
}

@Composable
@Suppress("UNUSED_PARAMETER")
private fun TalkTab(
    state: ClientState,
    onVoiceModeChanged: (VoiceMode) -> Unit,
    onVadThresholdChanged: (Float) -> Unit,
    onPushToTalkChanged: (Boolean) -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            color = MaterialTheme.colorScheme.surface,
            shape = RoundedCornerShape(20.dp),
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.16f)),
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(44.dp)
                            .clip(CircleShape)
                            .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.18f)),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(Icons.Default.Mic, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    }
                    Spacer(Modifier.width(12.dp))
                    Column {
                        Text(
                            text = "Push-to-talk",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            text = "Houd de knop ingedrukt terwijl je praat",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }

                Spacer(Modifier.height(4.dp))

                PttButton(
                    pressed = state.pushToTalkPressed,
                    enabled = !state.unsupportedCodec,
                    onPressedChange = onPushToTalkChanged,
                    modifier = Modifier.weight(1f),
                )

                Text(
                    text = if (state.pushToTalkPressed) "ZENDEN" else "GEREED OM TE PRATEN",
                    color = if (state.pushToTalkPressed) MaterialTheme.colorScheme.error
                    else MaterialTheme.colorScheme.primary,
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        }

        ListeningPanel(isReceiving = state.talkingClientIds.isNotEmpty())
    }
}

@Composable
private fun ListeningPanel(isReceiving: Boolean) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(20.dp),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)),
    ) {
        Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(38.dp)
                        .clip(CircleShape)
                        .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.18f)),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        Icons.Default.VolumeUp,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(23.dp),
                    )
                }
                Spacer(Modifier.width(10.dp))
                Column {
                    Text("Luisteren", fontWeight = FontWeight.Bold)
                    Text(
                        text = if (isReceiving) "Audio wordt ontvangen" else "Stand-by",
                        style = MaterialTheme.typography.labelSmall,
                        color = if (isReceiving) MaterialTheme.colorScheme.primary
                        else MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            Spacer(Modifier.height(10.dp))
            Waveform(active = isReceiving)
        }
    }
}

@Composable
private fun Waveform(active: Boolean) {
    val heights = listOf(10, 18, 28, 17, 35, 22, 44, 31, 56, 36, 25, 48, 29, 18, 32, 22, 13, 25, 16, 9)
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(62.dp),
        horizontalArrangement = Arrangement.SpaceEvenly,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        heights.forEachIndexed { index, h ->
            val bright = active || index in 6..13
            Box(
                modifier = Modifier
                    .width(4.dp)
                    .height(h.dp)
                    .clip(RoundedCornerShape(4.dp))
                    .background(
                        MaterialTheme.colorScheme.primary.copy(
                            alpha = if (bright) 0.95f else 0.35f,
                        ),
                    ),
            )
        }
    }
}

@Composable
private fun RoomsTab(
    channels: List<ChannelTreeNode>,
    currentChannelId: Int,
    onJoin: (com.toosarax.ts3client.protocol.ChannelInfo) -> Unit,
) {
    if (channels.isEmpty()) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text(stringResource(R.string.rooms_empty), color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        return
    }
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        channels.forEach { node ->
            channelItems(node, depth = 0, currentChannelId, onJoin)
        }
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.channelItems(
    node: ChannelTreeNode,
    depth: Int,
    currentChannelId: Int,
    onJoin: (com.toosarax.ts3client.protocol.ChannelInfo) -> Unit,
) {
    val channel = node.channel
    val isCurrent = channel.id == currentChannelId
    item(key = "channel-${channel.id}") {
        ChannelRow(
            name = channel.name,
            depth = depth,
            isCurrent = isCurrent,
            locked = channel.hasPassword,
            onClick = { onJoin(channel) },
        )
    }
    node.children.forEach { child ->
        channelItems(child, depth + 1, currentChannelId, onJoin)
    }
}

@Composable
private fun ChannelRow(
    name: String,
    depth: Int,
    isCurrent: Boolean,
    locked: Boolean,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(
                if (isCurrent) MaterialTheme.colorScheme.primary.copy(alpha = 0.16f)
                else MaterialTheme.colorScheme.surface,
            )
            .border(
                1.dp,
                if (isCurrent) MaterialTheme.colorScheme.primary.copy(alpha = 0.45f)
                else MaterialTheme.colorScheme.outlineVariant,
                RoundedCornerShape(14.dp),
            )
            .clickable(onClick = onClick)
            .padding(start = (12 + depth * 16).dp, top = 12.dp, end = 12.dp, bottom = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Icon(Icons.Default.Folder, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
        Column(modifier = Modifier.weight(1f)) {
            Text(text = name, fontWeight = if (isCurrent) FontWeight.Bold else FontWeight.Medium)
            if (isCurrent) {
                Text(
                    text = stringResource(R.string.channel_current),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary,
                )
            }
        }
        if (locked) {
            Icon(
                Icons.Default.Lock,
                contentDescription = stringResource(R.string.channel_locked),
                modifier = Modifier.size(18.dp),
            )
        }
    }
}

@Composable
private fun PeopleTab(
    clients: List<RemoteClientInfo>,
    talkingClientIds: Set<Int>,
    peopleCountLabel: String,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(peopleCountLabel, color = MaterialTheme.colorScheme.onSurfaceVariant)
        if (clients.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text(stringResource(R.string.people_empty), color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(clients, key = { it.id }) { client ->
                    PersonRow(client = client, talking = client.id in talkingClientIds)
                }
            }
        }
    }
}

@Composable
private fun PersonRow(client: RemoteClientInfo, talking: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(MaterialTheme.colorScheme.surface)
            .border(
                1.dp,
                if (talking) MaterialTheme.colorScheme.primary.copy(alpha = 0.55f)
                else MaterialTheme.colorScheme.outlineVariant,
                RoundedCornerShape(14.dp),
            )
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Icon(
            Icons.Default.Person,
            contentDescription = null,
            tint = if (talking) MaterialTheme.colorScheme.primary
            else MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(client.nickname, modifier = Modifier.weight(1f), fontWeight = FontWeight.Medium)
        if (talking) {
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primary),
            )
            Text(
                text = stringResource(R.string.user_talking),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold,
            )
        }
    }
}
'''

ANDROID_AUDIO_SESSION_KT = r'''
package com.toosarax.ts3client.audio

import android.content.Context
import android.media.AudioDeviceInfo
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.os.Build
import com.toosarax.ts3client.client.ClientError

class AndroidAudioSession(context: Context) {
    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private var focusRequest: AudioFocusRequest? = null
    private var previousMode: Int = AudioManager.MODE_NORMAL
    private var previousSpeakerphoneOn: Boolean = false
    private var routedToSpeaker: Boolean = false
    var onFocusLoss: (() -> Unit)? = null
    var onFocusGain: (() -> Unit)? = null

    private val focusListener = AudioManager.OnAudioFocusChangeListener { change ->
        when (change) {
            AudioManager.AUDIOFOCUS_GAIN,
            AudioManager.AUDIOFOCUS_GAIN_TRANSIENT,
            AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK,
            -> onFocusGain?.invoke()

            AudioManager.AUDIOFOCUS_LOSS,
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT,
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK,
            -> onFocusLoss?.invoke()
        }
    }

    fun acquire() {
        previousMode = audioManager.mode
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            @Suppress("DEPRECATION")
            previousSpeakerphoneOn = audioManager.isSpeakerphoneOn
        }

        audioManager.mode = AudioManager.MODE_IN_COMMUNICATION
        routeToBuiltInSpeaker()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val request = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT)
                .setAudioAttributes(
                    android.media.AudioAttributes.Builder()
                        .setUsage(android.media.AudioAttributes.USAGE_VOICE_COMMUNICATION)
                        .setContentType(android.media.AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build(),
                )
                .setOnAudioFocusChangeListener(focusListener)
                .build()
            focusRequest = request
            val result = audioManager.requestAudioFocus(request)
            if (result != AudioManager.AUDIOFOCUS_REQUEST_GRANTED) {
                throw ClientError.AudioInitialization("Audio focus not granted")
            }
        } else {
            @Suppress("DEPRECATION")
            audioManager.requestAudioFocus(
                focusListener,
                AudioManager.STREAM_VOICE_CALL,
                AudioManager.AUDIOFOCUS_GAIN_TRANSIENT,
            )
        }
    }

    private fun routeToBuiltInSpeaker() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val speaker = audioManager.availableCommunicationDevices.firstOrNull {
                it.type == AudioDeviceInfo.TYPE_BUILTIN_SPEAKER
            }
            routedToSpeaker = speaker != null && audioManager.setCommunicationDevice(speaker)
        } else {
            @Suppress("DEPRECATION")
            audioManager.isSpeakerphoneOn = true
            routedToSpeaker = true
        }
    }

    fun release() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            focusRequest?.let { audioManager.abandonAudioFocusRequest(it) }
            focusRequest = null
        } else {
            @Suppress("DEPRECATION")
            audioManager.abandonAudioFocus(focusListener)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (routedToSpeaker) {
                audioManager.clearCommunicationDevice()
            }
        } else {
            @Suppress("DEPRECATION")
            audioManager.isSpeakerphoneOn = previousSpeakerphoneOn
        }
        routedToSpeaker = false
        audioManager.mode = previousMode
    }
}
'''

ANDROID_PCM_OUTPUT_KT = r'''
package com.toosarax.ts3client.audio.rx

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import com.toosarax.ts3client.audio.AudioConstants
import com.toosarax.ts3client.audio.PcmOutput
import com.toosarax.ts3client.client.ClientError

class AndroidPcmOutput : PcmOutput {
    private var track: AudioTrack? = null

    override fun start() {
        val minBuffer = AudioTrack.getMinBufferSize(
            AudioConstants.SAMPLE_RATE,
            AudioFormat.CHANNEL_OUT_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
        )
        if (minBuffer <= 0) {
            throw ClientError.AudioInitialization("AudioTrack min buffer size invalid: $minBuffer")
        }

        val bufferSize = maxOf(minBuffer * 2, AudioConstants.FRAME_BYTES * 4)
        val audioTrack = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build(),
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setSampleRate(AudioConstants.SAMPLE_RATE)
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .build(),
            )
            .setTransferMode(AudioTrack.MODE_STREAM)
            .setBufferSizeInBytes(bufferSize)
            .build()

        if (audioTrack.state != AudioTrack.STATE_INITIALIZED) {
            audioTrack.release()
            throw ClientError.AudioInitialization("AudioTrack failed to initialize")
        }

        audioTrack.play()
        track = audioTrack
    }

    override fun write(samples: ShortArray, count: Int) {
        val audioTrack = track ?: return
        var offset = 0
        while (offset < count) {
            val written = audioTrack.write(
                samples,
                offset,
                count - offset,
                AudioTrack.WRITE_BLOCKING,
            )
            if (written < 0) {
                throw ClientError.AudioInitialization("AudioTrack write error: $written")
            }
            if (written == 0) return
            offset += written
        }
    }

    override fun stop() {
        track?.run {
            runCatching { stop() }
            release()
        }
        track = null
    }

    override fun close() {
        stop()
    }
}
'''

SPEAKER_STREAM_KT = r'''
package com.toosarax.ts3client.audio.rx

import com.toosarax.ts3client.audio.AudioConstants
import com.toosarax.ts3client.audio.VoiceDecoder
import com.toosarax.ts3client.protocol.EncodedVoicePacket

class SpeakerStream(
    val clientId: Int,
    private val decoder: VoiceDecoder,
    private val clock: () -> Long = System::currentTimeMillis,
) {
    private val jitter = ArrayDeque<EncodedVoicePacket>(AudioConstants.JITTER_FRAMES)
    private var expectedSequence: Int? = null
    private var lastActivityMs: Long = clock()
    private var sessionMarker: Byte? = null
    private var talking = false
    private var playoutStarted = false
    private var consecutivePlcFrames = 0
    private val pcmBuffer = ShortArray(AudioConstants.FRAME_SAMPLES)

    fun isTalking(): Boolean = talking

    fun offer(packet: EncodedVoicePacket): Boolean {
        lastActivityMs = clock()
        if (packet.payload.isEmpty()) {
            closeStream()
            return false
        }

        if (sessionMarker != null &&
            packet.sessionMarker != null &&
            packet.sessionMarker != sessionMarker
        ) {
            closeStream()
        }
        if (packet.sessionMarker != null) {
            sessionMarker = packet.sessionMarker
        }

        val expected = expectedSequence
        if (expected != null) {
            if (isDuplicate(packet.sequence, expected)) return false
            if (isLate(packet.sequence, expected)) return false
        }

        if (jitter.size >= AudioConstants.JITTER_FRAMES) {
            jitter.removeFirst()
        }
        jitter.addLast(packet)
        return true
    }

    fun renderFrame(nowMs: Long): ShortArray? {
        if (nowMs - lastActivityMs > AudioConstants.STREAM_IDLE_TIMEOUT_MS) {
            closeStream()
            return null
        }

        if (!playoutStarted) {
            if (jitter.size < AudioConstants.INITIAL_PLAYOUT_FRAMES) return null
            playoutStarted = true
            expectedSequence = jitter.first().sequence
        }

        while (true) {
            val expected = expectedSequence ?: return null
            val packet = jitter.firstOrNull()

            if (packet == null) {
                if (consecutivePlcFrames >= AudioConstants.MAX_PLC_GAP) {
                    talking = false
                    return null
                }
                consecutivePlcFrames += 1
                expectedSequence = (expected + 1) and 0xFFFF
                talking = true
                return decodePlc()
            }

            val diff = (packet.sequence - expected) and 0xFFFF
            when {
                diff == 0 -> {
                    jitter.removeFirst()
                    expectedSequence = (expected + 1) and 0xFFFF
                    consecutivePlcFrames = 0
                    talking = true
                    val decoded = decoder.decode(packet.payload, pcmBuffer)
                    return if (decoded > 0) pcmBuffer.copyOf(decoded) else null
                }

                diff > 0x8000 -> {
                    jitter.removeFirst()
                }

                diff <= AudioConstants.MAX_PLC_GAP &&
                    consecutivePlcFrames < AudioConstants.MAX_PLC_GAP -> {
                    consecutivePlcFrames += 1
                    expectedSequence = (expected + 1) and 0xFFFF
                    talking = true
                    return decodePlc()
                }

                else -> {
                    expectedSequence = packet.sequence
                    consecutivePlcFrames = 0
                }
            }
        }
    }

    fun closeStream() {
        talking = false
        jitter.clear()
        expectedSequence = null
        sessionMarker = null
        playoutStarted = false
        consecutivePlcFrames = 0
    }

    fun resetDecoder() {
        closeStream()
    }

    private fun decodePlc(): ShortArray? {
        val decoded = decoder.decode(null, pcmBuffer)
        return if (decoded > 0) pcmBuffer.copyOf(decoded) else null
    }

    companion object {
        fun isDuplicate(sequence: Int, expected: Int): Boolean {
            return sequence == ((expected - 1) and 0xFFFF)
        }

        fun isLate(sequence: Int, expected: Int): Boolean {
            val diff = (sequence - expected) and 0xFFFF
            return diff > 0x8000
        }

        fun gapFrames(from: Int, to: Int): Int {
            return (to - from) and 0xFFFF
        }
    }
}
'''

INCOMING_VOICE_ENGINE_KT = r'''
package com.toosarax.ts3client.audio.rx

import com.toosarax.ts3client.audio.AudioConstants
import com.toosarax.ts3client.audio.VoiceDecoderFactory
import com.toosarax.ts3client.protocol.EncodedVoicePacket
import com.toosarax.ts3client.protocol.IncomingVoiceSink
import com.toosarax.ts3client.protocol.VoiceCodec
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.atomic.AtomicInteger

class IncomingVoiceEngine(
    private val output: AndroidPcmOutput,
    private val decoderFactory: VoiceDecoderFactory = ConcentusVoiceDecoderFactory,
    private val scope: CoroutineScope,
) : IncomingVoiceSink {
    private val ingress = ArrayBlockingQueue<EncodedVoicePacket>(AudioConstants.MAX_INGRESS_PACKETS)
    private val droppedPackets = AtomicInteger(0)
    private val streams = mutableMapOf<Int, SpeakerStream>()
    private var renderJob: Job? = null
    private var ownClientId: Int = -1
    private var currentChannelId: Int = -1
    private val clientChannelLookup = mutableMapOf<Int, Int>()
    var onTalkingChanged: ((Set<Int>) -> Unit)? = null

    override fun tryOffer(packet: EncodedVoicePacket): Boolean {
        if (packet.codec != VoiceCodec.OPUS_VOICE) return false
        if (packet.clientId == ownClientId) return false
        val clientChannel = clientChannelLookup[packet.clientId]
        if (clientChannel == null || clientChannel != currentChannelId) return false
        val accepted = ingress.offer(packet)
        if (!accepted) {
            droppedPackets.incrementAndGet()
        }
        return accepted
    }

    fun start() {
        output.start()
        renderJob = scope.launch(Dispatchers.IO) {
            android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_AUDIO)
            val mixBuffer = ShortArray(AudioConstants.FRAME_SAMPLES)

            while (isActive) {
                drainIngress()
                val now = System.currentTimeMillis()
                val activeFrames = streams.values.mapNotNull { it.renderFrame(now) }
                PcmMixer.mix(activeFrames, mixBuffer, AudioConstants.FRAME_SAMPLES)
                output.write(mixBuffer, AudioConstants.FRAME_SAMPLES)
                publishTalkingState()
            }
        }
    }

    fun stop() {
        renderJob?.cancel()
        renderJob = null
        ingress.clear()
        streams.values.forEach { it.closeStream() }
        streams.clear()
        output.stop()
    }

    fun reset() {
        ingress.clear()
        streams.values.forEach { it.closeStream() }
        streams.clear()
        publishTalkingState()
    }

    fun updateDirectoryContext(
        ownClientId: Int,
        currentChannelId: Int,
        clientChannels: Map<Int, Int>,
    ) {
        this.ownClientId = ownClientId
        this.currentChannelId = currentChannelId
        clientChannelLookup.clear()
        clientChannelLookup.putAll(clientChannels)
        val stale = streams.keys.filter { clientId ->
            clientChannelLookup[clientId] != currentChannelId
        }
        stale.forEach { clientId ->
            streams.remove(clientId)?.closeStream()
        }
        publishTalkingState()
    }

    fun droppedCount(): Int = droppedPackets.get()

    private fun drainIngress() {
        while (true) {
            val packet = ingress.poll() ?: break
            val stream = streams.getOrPut(packet.clientId) {
                SpeakerStream(packet.clientId, decoderFactory.create())
            }
            stream.offer(packet)
        }
    }

    private fun publishTalkingState() {
        val talking = streams.filterValues { it.isTalking() }.keys
        onTalkingChanged?.invoke(talking)
    }
}
'''

TALK_TAB = r'''
@Composable
@Suppress("UNUSED_PARAMETER")
private fun TalkTab(
    state: ClientState,
    onVoiceModeChanged: (VoiceMode) -> Unit,
    onVadThresholdChanged: (Float) -> Unit,
    onPushToTalkChanged: (Boolean) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(
            text = stringResource(R.string.mode_ptt),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = stringResource(R.string.mode_ptt_desc),
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        PttButton(
            pressed = state.pushToTalkPressed,
            enabled = !state.unsupportedCodec,
            onPressedChange = onPushToTalkChanged,
            modifier = Modifier.weight(1f),
        )

        Text(
            text = stringResource(
                if (state.pushToTalkPressed) R.string.status_talking else R.string.status_listening,
            ),
            style = MaterialTheme.typography.titleMedium,
            color = if (state.pushToTalkPressed) {
                MaterialTheme.colorScheme.error
            } else {
                MaterialTheme.colorScheme.onSurfaceVariant
            },
        )
    }
}

'''

OLD_VOICE_MODE_SETTINGS = r'''    val voiceMode: Flow<VoiceMode> = context.dataStore.data.map { prefs ->
        when (prefs[voiceModeKey]) {
            VoiceMode.VOICE_ACTIVATION.name -> VoiceMode.VOICE_ACTIVATION
            else -> VoiceMode.PUSH_TO_TALK
        }
    }
'''

NEW_VOICE_MODE_SETTINGS = r'''    val voiceMode: Flow<VoiceMode> = context.dataStore.data.map {
        VoiceMode.PUSH_TO_TALK
    }
'''


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply_overlay.py <upstream-root>")

    root = Path(sys.argv[1]).resolve()
    here = Path(__file__).resolve().parent

    required = [
        root / "app/build.gradle.kts",
        root / "app/src/main/java/com/toosarax/ts3client/ui/Ts3App.kt",
        root / "app/src/main/java/com/toosarax/ts3client/MainActivity.kt",
        root / "app/src/main/java/com/toosarax/ts3client/ui/ChannelScreen.kt",
        root / "app/src/main/java/com/toosarax/ts3client/ui/PttButton.kt",
        root / "app/src/main/java/com/toosarax/ts3client/ui/theme/Theme.kt",
        root / "app/src/main/java/com/toosarax/ts3client/settings/SettingsStore.kt",
        root / "app/src/main/java/com/toosarax/ts3client/audio/AndroidAudioSession.kt",
        root / "app/src/main/java/com/toosarax/ts3client/audio/rx/AndroidPcmOutput.kt",
        root / "app/src/main/java/com/toosarax/ts3client/audio/rx/SpeakerStream.kt",
        root / "app/src/main/java/com/toosarax/ts3client/audio/rx/IncomingVoiceEngine.kt",
        root / "app/src/main/res/values/strings.xml",
        root / "LICENSE",
        root / "NOTICE",
        root / "THIRD_PARTY_NOTICES.md",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError("Upstream checkout is incomplete: " + ", ".join(missing))

    gradle = root / "app/build.gradle.kts"
    require_replace(
        gradle,
        'applicationId = "com.toosarax.ts3client"',
        f'applicationId = "{APP_ID}"',
    )
    require_replace(
        gradle,
        'versionCode = 1',
        'versionCode = 2',
    )
    require_replace(
        gradle,
        'versionName = "0.1.0"',
        'versionName = "0.2.0-pttconnect-neon"',
    )

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

    main_activity = root / "app/src/main/java/com/toosarax/ts3client/MainActivity.kt"
    require_replace(
        main_activity,
        "import androidx.core.content.ContextCompat\n",
        "import androidx.core.content.ContextCompat\nimport androidx.core.view.WindowCompat\n",
    )
    require_replace(
        main_activity,
        "        enableEdgeToEdge()\n        requestPermissionsIfNeeded()",
        "        enableEdgeToEdge()\n"
        "        WindowCompat.getInsetsController(window, window.decorView).apply {\n"
        "            isAppearanceLightStatusBars = false\n"
        "            isAppearanceLightNavigationBars = false\n"
        "        }\n"
        "        requestPermissionsIfNeeded()",
    )

    settings = root / "app/src/main/java/com/toosarax/ts3client/settings/SettingsStore.kt"
    require_replace(settings, OLD_VOICE_MODE_SETTINGS, NEW_VOICE_MODE_SETTINGS)

    channel = root / "app/src/main/java/com/toosarax/ts3client/ui/ChannelScreen.kt"
    write_text(channel, CHANNEL_SCREEN_KT)

    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/ui/theme/Theme.kt",
        THEME_KT,
    )
    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/ui/PttButton.kt",
        PTT_BUTTON_KT,
    )
    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/audio/AndroidAudioSession.kt",
        ANDROID_AUDIO_SESSION_KT,
    )
    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/audio/rx/AndroidPcmOutput.kt",
        ANDROID_PCM_OUTPUT_KT,
    )
    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/audio/rx/SpeakerStream.kt",
        SPEAKER_STREAM_KT,
    )
    write_text(
        root / "app/src/main/java/com/toosarax/ts3client/audio/rx/IncomingVoiceEngine.kt",
        INCOMING_VOICE_ENGINE_KT,
    )

    strings = root / "app/src/main/res/values/strings.xml"
    shutil.copy2(here / "strings.xml", strings)
    require_replace(
        strings,
        '<string name="ptt_hold">INGEDRUKT HOUDEN OM TE PRATEN</string>',
        '<string name="ptt_hold">PTT\nINGEDRUKT HOUDEN</string>',
    )
    require_replace(
        strings,
        '<string name="ptt_active">JE PRAAT…</string>',
        '<string name="ptt_active">PRATEN\nLAAT LOS OM TE STOPPEN</string>',
    )

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
    print("  design: dark neon PTT UI, large ring button, talk/rooms/people tabs, listening panel")
    print("  audio: speaker route and RX jitter/clock fixes retained")


if __name__ == "__main__":
    main()
