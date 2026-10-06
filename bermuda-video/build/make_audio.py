"""Build trimmed/speed-adjusted narration tracks, concatenated master, timings + SRT skeleton."""
import json, os, re
import common as C

GAP = 0.9
LEAD = 1.6
TAIL = 6.5
TARGET_BLOCKS = 884.0   # seconds of narration we aim for (video lands ~15:00)


def sentence_split(text):
    parts = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # split on sentence terminators keeping them
        toks = re.split(r'(?<=[.؟!…])\s+', line)
        cur = ''
        for t in toks:
            cur = (cur + ' ' + t).strip()
            if len(cur) >= 55:
                parts.append(cur); cur = ''
        if cur:
            parts.append(cur)
    return parts


def build(atempo=1.0):
    os.makedirs(os.path.join(C.BLD, 'tracks'), exist_ok=True)
    blocks = C.blocks()
    outs, durs = [], []
    for bid, text in blocks:
        src = os.path.join(C.AUD, bid + '.mp3')
        dst = os.path.join(C.BLD, 'tracks', bid + '.wav')
        vf = 'silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=1:stop_threshold=-45dB'
        af = vf
        if abs(atempo - 1.0) > 1e-3:
            af = 'atempo=%.4f,' % atempo + vf
        C.run([C.FF, '-y', '-i', src, '-af', af, '-ar', '48000', '-ac', '2', dst])
        durs.append(C.ffprobe_dur(dst))
        outs.append(dst)
    raw = sum(durs)
    # concat with gaps
    starts = []
    t = LEAD
    for d in durs:
        starts.append(t)
        t += d + GAP
    total = t - GAP + TAIL
    # build silence-padded master via concat filter with adelay/apad is fiddly; use wav concat in numpy
    import numpy as np, wave

    def read_wav(p):
        with wave.open(p, 'rb') as w:
            sr = w.getframerate(); n = w.getnchannels(); sw = w.getsampwidth()
            data = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2')
        return sr, data.reshape(-1, n).astype(np.float32) / 32768.0

    sr, _ = read_wav(outs[0])
    master = np.zeros((int(total * sr), 2), np.float32)
    for (s, p) in zip(starts, outs):
        r, d = read_wav(p)
        i0 = int(s * sr); i1 = min(len(master), i0 + len(d))
        master[i0:i1] += d[:i1 - i0]
    pcm = (np.clip(master, -1, 1) * 32767).astype('<i2')
    narr = os.path.join(C.BLD, 'narration.wav')
    with wave.open(narr, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    timings = {'lead': LEAD, 'gap': GAP, 'tail': TAIL, 'total': total,
               'blocks': []}
    for (bid, text), s, d in zip(blocks, starts, durs):
        sents = sentence_split(text)
        tot_chars = sum(len(x) for x in sents) or 1
        timings['blocks'].append({'id': bid, 'start': s, 'dur': d, 'end': s + d,
                                  'sents': [{'t0': None, 't1': None, 'w': len(x) / tot_chars, 'txt': x} for x in sents]})
    # fill sentence times proportionally
    for b in timings['blocks']:
        t0 = b['start']
        for snt in b['sents']:
            snt['t0'] = round(t0, 3)
            t0 += snt['w'] * b['dur']
            snt['t1'] = round(t0, 3)
    json.dump(timings, open(os.path.join(C.BLD, 'timings.json'), 'w'), ensure_ascii=False, indent=1)
    print('narration master %.1fs  raw_blocks %.1fs  atempo %.3f' % (total, raw, atempo))
    return total


if __name__ == '__main__':
    import sys
    build(float(sys.argv[1]) if len(sys.argv) > 1 else 1.0)
