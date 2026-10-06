"""Procedural cinematic underscore: low drone + ocean noise + sub booms at chapter marks."""
import json, os
import numpy as np

SR = 48000


def _fade(x, n):
    f = np.ones_like(x)
    k = min(n, len(x) // 4)
    f[:k] = np.linspace(0, 1, k)
    f[-k:] = np.linspace(1, 0, k)
    return x * f


def noise_bed(n, seed=7):
    rng = np.random.default_rng(seed)
    w = rng.normal(0, 1, n)
    # brown-ish ocean: cumulative sum + lowpass
    b = np.cumsum(w)
    b -= np.mean(b)
    b /= (np.max(np.abs(b)) + 1e-9)
    # slow amplitude modulation = swell
    t = np.arange(n) / SR
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * 0.05 * t + 1.1) * np.sin(2 * np.pi * 0.013 * t)
    return b * swell


def drone(n):
    t = np.arange(n) / SR
    d = np.zeros(n)
    for f, a in [(55, .5), (82.41, .28), (110, .34), (164.81, .14), (220, .08)]:
        lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.021 * t + f)
        d += a * np.sin(2 * np.pi * f * t + np.sin(2 * np.pi * .07 * t) * .4) * lfo
    d /= np.max(np.abs(d)) + 1e-9
    return d


def boom(n, dur=3.2, f0=52):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 2.1) * (1 - np.exp(-t * 22))
    s = np.sin(2 * np.pi * f0 * t * (1 - 0.25 * np.exp(-t * 3))) * env
    click = np.exp(-t * 40) * np.sin(2 * np.pi * 210 * t) * .25
    return s + click


def make(total_sec, boom_times, out_path):
    n = int(total_sec * SR)
    mix = drone(n) * 0.62 + noise_bed(n) * 0.30
    for bt in boom_times:
        s = int(bt * SR)
        b = boom(n)
        e = min(n, s + len(b))
        mix[s:e] += b[:e - s] * 0.85
    # gentle high-shelf roll-off
    mix = np.convolve(mix, np.ones(9) / 9, mode='same')
    mix = _fade(mix, SR * 4)
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.9
    stereo = np.stack([mix * 0.98, mix], axis=1)
    pcm = (stereo * 32767).astype('<i2')
    import wave
    with wave.open(out_path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_path


if __name__ == '__main__':
    import sys
    total = float(sys.argv[1])
    booms = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music.wav')
    make(total, booms, out)
    print('music written', out, total, 's')
