import numpy as np
import pygame

SAMPLE_RATE = 44100


def _make_array(duration, func):
    """func(t) -> [-1, 1] 신호를 16-bit stereo Surface로 변환."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    wave = np.clip(func(t), -1.0, 1.0)
    # int16 변환 후 stereo (N, 2)
    s16 = (wave * 32767).astype(np.int16)
    stereo = np.column_stack((s16, s16))
    return pygame.sndarray.make_sound(stereo)


def _sine(t, freq):
    return np.sin(2 * np.pi * freq * t)


def _square(t, freq):
    return np.sign(np.sin(2 * np.pi * freq * t))


def _noise(n):
    return np.random.uniform(-1, 1, n)


def _env_exp(t, attack=0.005, decay=None):
    """지수 감쇠 엔벨로프."""
    if decay is None:
        decay = t[-1]
    env = np.exp(-t / (decay * 0.3))
    env[:max(1, int(SAMPLE_RATE * attack))] *= np.linspace(0, 1, max(1, int(SAMPLE_RATE * attack)))
    return env


# ─────────────────────────────────────────────────────────────
#  개별 사운드 합성
# ─────────────────────────────────────────────────────────────

def _make_shoot():
    """복고풍 아케이드 '픽(Pew)' 소리 — 고주파에서 중저음으로 빠르게 내려오는 피치 스윕."""
    dur = 0.12
    def func(t):
        # 900 Hz → 180 Hz 로 지수 감소 (픽~ 하고 떨어지는 느낌)
        freq = 900 * np.exp(-t / 0.045) + 180
        # 순수 사인파 위주 + 2배음 살짝 → 귀엽고 맑은 톤
        sig = _sine(t, freq) * 0.75 + _sine(t, freq * 2) * 0.15
        # 빠른 어택(거의 즉시) + 완만한 감쇠
        env = np.exp(-t / 0.04)
        return sig * env
    snd = _make_array(dur, func)
    snd.set_volume(0.22)
    return snd


def _make_hit():
    """적 피격 – 매우 짧은 틱."""
    dur = 0.05
    def func(t):
        n = len(t)
        sig = _noise(n) * 0.6 + _sine(t, 800) * 0.4
        env = np.exp(-t / 0.015)
        return sig * env
    snd = _make_array(dur, func)
    snd.set_volume(0.5)
    return snd


def _make_explode():
    """적 폭발 – 낮고 짧은 폭발음."""
    dur = 0.25
    def func(t):
        n = len(t)
        sig = _noise(n) * 0.7 + _sine(t, 80) * 0.5 + _sine(t, 160) * 0.3
        env = np.exp(-t / 0.07)
        return sig * env
    return _make_array(dur, func)


def _make_boss_hit():
    """보스 피격 – 묵직한 저음 틱."""
    dur = 0.12
    def func(t):
        n = len(t)
        sig = (_noise(n) * 0.5
               + _sine(t, 200) * 0.5
               + _sine(t, 100) * 0.4)
        env = np.exp(-t / 0.04)
        return sig * env
    snd = _make_array(dur, func)
    snd.set_volume(0.7)
    return snd


def _make_boss_explode():
    """보스 폭발 – 크고 긴 폭발음."""
    dur = 1.2
    def func(t):
        n = len(t)
        # 저주파 폭발 + 노이즈 + 여진
        boom  = _sine(t, 60)  * np.exp(-t / 0.15) * 0.8
        rumble= _sine(t, 120) * np.exp(-t / 0.4)  * 0.5
        noise = _noise(n)     * np.exp(-t / 0.5)  * 0.6
        return boom + rumble + noise
    return _make_array(dur, func)


def _make_player_hit():
    """플레이어 피격 – 낮고 불쾌한 경고음."""
    dur = 0.35
    def func(t):
        # 내려가는 피치 + 노이즈
        freq = 400 * np.exp(-t * 3)
        sig = _sine(t, freq) * 0.6 + _square(t, freq * 0.5) * 0.3
        env = np.exp(-t / 0.12)
        return sig * env
    return _make_array(dur, func)


def _make_item_pickup():
    """아이템 획득 – 밝고 짧은 상승 멜로디 (3음)."""
    notes = [523, 659, 784]   # C5, E5, G5
    note_dur = 0.07
    gap = 0.02
    total = len(notes) * (note_dur + gap)
    n_total = int(SAMPLE_RATE * total)
    wave = np.zeros(n_total)

    for i, freq in enumerate(notes):
        start = int(i * (note_dur + gap) * SAMPLE_RATE)
        n = int(note_dur * SAMPLE_RATE)
        t = np.linspace(0, note_dur, n, endpoint=False)
        seg = (_sine(t, freq) * 0.6 + _sine(t, freq * 2) * 0.2)
        env = np.exp(-t / (note_dur * 0.4))
        wave[start:start + n] += seg * env

    wave = np.clip(wave, -1.0, 1.0)
    s16 = (wave * 32767).astype(np.int16)
    stereo = np.column_stack((s16, s16))
    snd = pygame.sndarray.make_sound(stereo)
    snd.set_volume(0.7)
    return snd


def _make_wave_clear():
    """웨이브 클리어 – 짧은 팡파르 (5음 상승)."""
    notes = [523, 659, 784, 1047, 1319]   # C5 E5 G5 C6 E6
    note_dur = 0.09
    gap = 0.01
    total = len(notes) * (note_dur + gap)
    n_total = int(SAMPLE_RATE * total)
    wave = np.zeros(n_total)

    for i, freq in enumerate(notes):
        start = int(i * (note_dur + gap) * SAMPLE_RATE)
        n = int(note_dur * SAMPLE_RATE)
        t = np.linspace(0, note_dur, n, endpoint=False)
        seg = _sine(t, freq) * 0.7 + _sine(t, freq * 2) * 0.15
        env = np.exp(-t / (note_dur * 0.5))
        wave[start:start + n] += seg * env

    wave = np.clip(wave, -1.0, 1.0)
    s16 = (wave * 32767).astype(np.int16)
    stereo = np.column_stack((s16, s16))
    snd = pygame.sndarray.make_sound(stereo)
    snd.set_volume(0.8)
    return snd


def _make_game_over():
    """게임오버 – 하강하는 슬픈 멜로디."""
    notes = [440, 392, 349, 294, 262]   # A4 G4 F4 D4 C4
    note_dur = 0.18
    gap = 0.03
    total = len(notes) * (note_dur + gap) + 0.3
    n_total = int(SAMPLE_RATE * total)
    wave = np.zeros(n_total)

    for i, freq in enumerate(notes):
        start = int(i * (note_dur + gap) * SAMPLE_RATE)
        n = int(note_dur * SAMPLE_RATE)
        t = np.linspace(0, note_dur, n, endpoint=False)
        seg = _sine(t, freq) * 0.5 + _sine(t, freq * 0.5) * 0.25
        env = np.exp(-t / (note_dur * 0.6))
        wave[start:start + n] += seg * env

    wave = np.clip(wave, -1.0, 1.0)
    s16 = (wave * 32767).astype(np.int16)
    stereo = np.column_stack((s16, s16))
    snd = pygame.sndarray.make_sound(stereo)
    snd.set_volume(0.8)
    return snd


def _make_clown_bounce():
    """삐에로 공 튕김 – 통통 튀는 짧은 탄성음."""
    dur = 0.12
    def func(t):
        freq = 700 * np.exp(-t / 0.04) + 250
        sig = _sine(t, freq) * 0.55 + _sine(t, freq * 2) * 0.15
        env = np.exp(-t / 0.04)
        return sig * env
    snd = _make_array(dur, func)
    snd.set_volume(0.35)
    return snd


def _make_laser_warning():
    """레이저 경고 – 고조되는 전기 차지음 (90프레임 = 약 1.5초 동안 깜빡임)."""
    dur = 1.4
    def func(t):
        # 200Hz → 800Hz 로 상승하는 사인파 (차지 느낌)
        freq = 200 + 600 * (t / dur) ** 1.5
        sig = _sine(t, freq) * 0.5 + _sine(t, freq * 1.5) * 0.2
        # 뒤로 갈수록 점점 커지는 엔벨로프
        env = (t / dur) * 0.8 + 0.2
        # 빠른 진폭 진동으로 전기 느낌 추가
        tremolo = 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 18 * t))
        return sig * env * tremolo
    snd = _make_array(dur, func)
    snd.set_volume(0.45)
    return snd


def _make_laser_fire():
    """레이저 발사 – 강렬한 고주파 빔음."""
    dur = 0.6
    def func(t):
        n = len(t)
        # 메인 빔: 800Hz 사인 + 고조파
        beam = (_sine(t, 800) * 0.4
                + _sine(t, 1600) * 0.2
                + _sine(t, 400) * 0.3)
        # 노이즈 레이어로 거친 느낌
        crackle = _noise(n) * 0.25
        sig = beam + crackle
        # 처음 순간 피크 후 빠르게 감쇠
        env = np.exp(-t / 0.18) * 0.7 + np.exp(-t / 0.55) * 0.3
        return sig * env
    snd = _make_array(dur, func)
    snd.set_volume(0.65)
    return snd


def _make_bgm():
    """단순한 전자음 비트 루프 (약 2초)."""
    bpm = 128
    beat = 60.0 / bpm
    bars = 4
    dur = beat * bars * 2   # 2마디 * 4비트
    n_total = int(SAMPLE_RATE * dur)
    wave = np.zeros(n_total)

    # 킥드럼 패턴 (1, 3박)
    kick_beats = [0, 2, 4, 6]
    for b in kick_beats:
        start = int(b * beat * SAMPLE_RATE)
        n = int(0.15 * SAMPLE_RATE)
        if start + n > n_total:
            continue
        t = np.linspace(0, 0.15, n, endpoint=False)
        kick = _sine(t, 180 * np.exp(-t * 25)) * np.exp(-t / 0.04) * 0.7
        wave[start:start + n] += kick

    # 하이햇 패턴 (8분음표)
    for b in range(bars * 4 * 2):
        start = int(b * beat * 0.5 * SAMPLE_RATE)
        n = int(0.04 * SAMPLE_RATE)
        if start + n > n_total:
            continue
        t = np.linspace(0, 0.04, n, endpoint=False)
        hat_n = len(t)
        hat = _noise(hat_n) * np.exp(-t / 0.008) * 0.25
        wave[start:start + n] += hat

    # 베이스 멜로디
    bass_notes = [110, 110, 130, 110, 98, 110, 130, 146]
    for i, freq in enumerate(bass_notes):
        start = int(i * beat * SAMPLE_RATE)
        n = int(beat * 0.8 * SAMPLE_RATE)
        if start + n > n_total:
            continue
        t = np.linspace(0, beat * 0.8, n, endpoint=False)
        bass = (_square(t, freq) * 0.3 + _sine(t, freq) * 0.2)
        env = np.exp(-t / (beat * 0.3))
        wave[start:start + n] += bass * env

    # 아르페지오 (고음)
    arp_freqs = [523, 659, 784, 659] * 2
    arp_step = beat * 0.5
    for i, freq in enumerate(arp_freqs):
        start = int(i * arp_step * SAMPLE_RATE)
        n = int(arp_step * 0.6 * SAMPLE_RATE)
        if start + n > n_total:
            continue
        t = np.linspace(0, arp_step * 0.6, n, endpoint=False)
        arp = _sine(t, freq) * 0.12
        env = np.exp(-t / (arp_step * 0.4))
        wave[start:start + n] += arp * env

    wave = np.clip(wave, -1.0, 1.0)
    s16 = (wave * 32767).astype(np.int16)
    stereo = np.column_stack((s16, s16))
    snd = pygame.sndarray.make_sound(stereo)
    snd.set_volume(0.35)
    return snd


# ─────────────────────────────────────────────────────────────
#  공개 API
# ─────────────────────────────────────────────────────────────

def init_sounds():
    """모든 사운드를 생성해서 딕셔너리로 반환."""
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(32)

    sounds = {}
    sounds['shoot']         = _make_shoot()
    sounds['hit']           = _make_hit()
    sounds['explode']       = _make_explode()
    sounds['boss_hit']      = _make_boss_hit()
    sounds['boss_explode']  = _make_boss_explode()
    sounds['player_hit']    = _make_player_hit()
    sounds['item']          = _make_item_pickup()
    sounds['wave_clear']    = _make_wave_clear()
    sounds['game_over']     = _make_game_over()
    sounds['laser_warning'] = _make_laser_warning()
    sounds['laser_fire']    = _make_laser_fire()
    sounds['clown_bounce']  = _make_clown_bounce()
    sounds['bgm']           = _make_bgm()
    return sounds
