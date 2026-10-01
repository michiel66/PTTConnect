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
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val PttConnectColors = lightColorScheme(
    primary = Color(0xFF0057B8),
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFFD8E9FF),
    onPrimaryContainer = Color(0xFF001B3D),
    secondary = Color(0xFF006B54),
    onSecondary = Color(0xFFFFFFFF),
    secondaryContainer = Color(0xFFB8F2DD),
    onSecondaryContainer = Color(0xFF002117),
    background = Color(0xFFF3F6FA),
    onBackground = Color(0xFF101820),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF101820),
    surfaceVariant = Color(0xFFE4EBF3),
    onSurfaceVariant = Color(0xFF303942),
    outline = Color(0xFF59636E),
    error = Color(0xFFC62828),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFFFDAD6),
    onErrorContainer = Color(0xFF410002),
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

import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
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
    val background = if (pressed) {
        MaterialTheme.colorScheme.error
    } else {
        MaterialTheme.colorScheme.primary
    }
    val foreground = if (pressed) {
        MaterialTheme.colorScheme.onError
    } else {
        MaterialTheme.colorScheme.onPrimary
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(320.dp),
        contentAlignment = Alignment.Center,
    ) {
        Surface(
            modifier = Modifier
                .size(265.dp)
                .alpha(if (enabled) 1f else 0.45f)
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
            shape = CircleShape,
            color = background,
            contentColor = foreground,
            tonalElevation = 10.dp,
            shadowElevation = 14.dp,
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(32.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = stringResource(if (pressed) R.string.ptt_active else R.string.ptt_hold),
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Black,
                    textAlign = TextAlign.Center,
                )
            }
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
        'versionName = "0.1.0"',
        'versionName = "0.1.2-pttconnect"',
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
        "            isAppearanceLightStatusBars = true\n"
        "            isAppearanceLightNavigationBars = true\n"
        "        }\n"
        "        requestPermissionsIfNeeded()",
    )

    settings = root / "app/src/main/java/com/toosarax/ts3client/settings/SettingsStore.kt"
    require_replace(settings, OLD_VOICE_MODE_SETTINGS, NEW_VOICE_MODE_SETTINGS)

    channel = root / "app/src/main/java/com/toosarax/ts3client/ui/ChannelScreen.kt"
    replace_section(
        channel,
        "@Composable\nprivate fun TalkTab(",
        "@Composable\nprivate fun RoomsTab(",
        TALK_TAB,
    )

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
    print("  fixes: high-contrast light UI, round Zello-style PTT, PTT-only mode, speaker route, RX jitter/clock")


if __name__ == "__main__":
    main()
