"""Assemble the final MP4: Ken-Burns segments + Arabic overlays + narration + ducked music."""
import json, os, subprocess
import numpy as np
import common as C
import make_music

FPS = C.FPS
W, H = C.W, C.H

# block -> ordered list of (image, treatment, weight)
PLAN = {
 'B01': [('01_hook_storm', 'zoom_in', 3), ('03_flight19_formation', 'pan_r', 3),
         ('04_cockpit_dusk', 'zoom_in', 2), ('05_night_search', 'zoom_out', 3)],
 'B02': [('02_chart_blank', 'zoom_in', 5), ('01_hook_storm', 'pan_l', 2)],
 'B03': [('10_desk_1970s', 'zoom_in', 3), ('02_chart_blank', 'pan_r', 2)],
 'B04': [('06_uss_cyclops', 'zoom_in', 3), ('07_deering', 'zoom_out', 3)],
 'B05': [('03_flight19_formation', 'zoom_in', 3), ('04_cockpit_dusk', 'pan_l', 3)],
 'B06': [('08_star_tiger', 'zoom_in', 3), ('09_tanker_storm', 'zoom_out', 2), ('07_deering', 'pan_r', 2)],
 'B07': [('11_archives', 'zoom_in', 3), ('10_desk_1970s', 'pan_l', 3)],
 'B08': [('12_lloyds_hall', 'zoom_in', 3), ('02_chart_blank', 'pan_l', 3)],
 'B09': [('13_gulfstream_satellite', 'zoom_in', 2), ('14_hurricane_wall', 'zoom_out', 3),
         ('15_hexagonal_clouds', 'pan_r', 2), ('16_methane_bubbles', 'zoom_in', 3)],
 'B10': [('17_rogue_wave', 'zoom_in', 3), ('18_compass', 'zoom_out', 2),
         ('19_trench_abyss', 'zoom_in', 2), ('20_elfaro', 'zoom_out', 3)],
 'B11': [('21_calm_night', 'zoom_in', 3), ('22_thumbnail_bg', 'zoom_out', 3)],
}
FALLBACK = ['01_hook_storm', '02_chart_blank', '03_flight19_formation']
GRADE = {'B04': 'arch', 'B05': 'arch', 'B06': 'arch', 'B07': 'cool', 'B08': 'cool'}
MAP_BLOCKS = {'B02'}


def pick(name):
    p = os.path.join(C.IMG, name + '.jpg')
    return p if os.path.exists(p) else os.path.join(C.IMG, FALLBACK[hash(name) % 3] + '.jpg')


def zoom_expr(treat, frames):
    N = max(frames, 2)
    cx = "iw/2-(iw/zoom/2)"; cy = "ih/2-(ih/zoom/2)"
    if treat == 'zoom_in':
        return "min(1+0.00058*on,1.24)", cx, cy
    if treat == 'zoom_out':
        return "max(1.24-0.00058*on,1.0)", cx, cy
    if treat == 'pan_r':
        return "1.18", "(iw-iw/zoom)*min(on/%d,1)" % N, cy
    if treat == 'pan_l':
        return "1.18", "(iw-iw/zoom)*(1-min(on/%d,1))" % N, cy
    return "min(1+0.00058*on,1.24)", cx, cy


def render_segment(idx, img, treat, dur, overlays):
    """overlays: list of (png, t0, t1 or None)"""
    frames = int(round(dur * FPS))
    z, x, y = zoom_expr(treat, frames)
    ins = ['-loop', '1', '-framerate', str(FPS), '-t', '%.3f' % dur, '-i', pick(img)]
    for png, _, _ in overlays:
        ins += ['-loop', '1', '-framerate', str(FPS), '-t', '%.3f' % dur, '-i', png]
    grade = {'arch': ",colorchannelmixer=.62:.30:.10:0:.18:.72:.14:0:.10:.24:.58",
             'cool': ",eq=saturation=0.82:contrast=1.04"}.get(GRADE_CURRENT, '')
    fc = "[0:v]scale=2880:1620:flags=lanczos,zoompan=z='%s':x='%s':y='%s':d=1:s=%dx%d:fps=%d," \
         "vignette=PI/5,eq=contrast=1.05:saturation=1.04%s,format=yuv420p[base]" % (z, x, y, W, H, FPS, grade)
    prev = 'base'
    for i, (_, t0, t1) in enumerate(overlays, start=1):
        nxt = 'o%d' % i
        en = '' if t1 is None else ":enable='between(t,%.2f,%.2f)'" % (t0, t1)
        fc += ";[%s][%d:v]overlay=0:0%s[%s]" % (prev, i, en, nxt)
        prev = nxt
    out = os.path.join(C.BLD, 'segs', 'seg%02d.mp4' % idx)
    C.run([C.FF, '-y'] + ins + ['-filter_complex', fc, '-map', '[%s]' % prev,
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-r', str(FPS),
           '-t', '%.3f' % dur, out])
    return out


GRADE_CURRENT = None


def build():
    T = json.load(open(os.path.join(C.BLD, 'timings.json')))
    os.makedirs(os.path.join(C.BLD, 'segs'), exist_ok=True)
    segs = []
    idx = 0
    boom_times = [0.0]
    for b in T['blocks']:
        global GRADE_CURRENT
        GRADE_CURRENT = GRADE.get(b['id'])
        boom_times.append(b['start'])
        plan = PLAN[b['id']]
        wsum = sum(p[2] for p in plan)
        for k, (img, treat, w) in enumerate(plan):
            dur = b['dur'] * w / wsum
            ov = [(os.path.join(C.OV, 'watermark.png'), 0, None)]
            if k == 0:
                ov.append((os.path.join(C.OV, 'bar_%s.png' % b['id']), 0.4, min(6.2, dur)))
                if b['id'] == 'B01':
                    ov.insert(0, (os.path.join(C.OV, 'title_card.png'), 0, 6.0))
            if b['id'] in MAP_BLOCKS and img == '02_chart_blank':
                ov.append((os.path.join(C.OV, 'map_overlay.png'), 0, None))
            if b['id'] == 'B11' and k == len(plan) - 1:
                ov.append((os.path.join(C.OV, 'end_card.png'), max(0, dur - 8.5), None))
            idx += 1
            segs.append(render_segment(idx, img, treat, dur, ov))
    # concat
    lst = os.path.join(C.BLD, 'segs.txt')
    open(lst, 'w').write('\n'.join("file '%s'" % s for s in segs))
    vid = os.path.join(C.BLD, 'video_only.mp4')
    C.run([C.FF, '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid])
    # ducked music
    total = T['total']
    mw = os.path.join(C.BLD, 'music.wav')
    make_music.make(total + 2.0, boom_times, mw)
    import wave
    with wave.open(mw, 'rb') as w:
        sr = w.getframerate()
        m = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').reshape(-1, 2).astype(np.float32) / 32768
    env = np.full(len(m), 0.15, np.float32)
    n = int(sr * T['lead'] * 0.7)
    env[:n] = 0.34
    for b in T['blocks']:
        i0 = int(sr * (b['end'] - 0.15)); i1 = int(sr * (b['end'] + T['gap'] + 0.15))
        env[i0:min(len(env), i1)] = 0.30
    env[int(sr * (total - T['tail'])):] = 0.34
    m = m[:len(env)] * env[:, None]
    mp = os.path.join(C.BLD, 'music_ducked.wav')
    with wave.open(mp, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(m, -1, 1) * 32767).astype('<i2').tobytes())
    # srt
    write_srt(T)
    # final mux
    final = os.path.join(C.OUT, 'bermuda_triangle_15min.mp4')
    C.run([C.FF, '-y', '-i', vid, '-i', os.path.join(C.BLD, 'narration.wav'), '-i', mp,
           '-filter_complex', '[1:a][2:a]amix=inputs=2:duration=first:dropout_transition=0:weights=1 1[a]',
           '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
           '-movflags', '+faststart', '-shortest', final])
    print('FINAL', final, C.ffprobe_dur(final))


def ts(s):
    s = max(0.0, s)
    return '%02d:%02d:%02d,%03d' % (s // 3600, (s % 3600) // 60, s % 60, (s % 1) * 1000)


def write_srt(T):
    lines = []
    i = 1
    for b in T['blocks']:
        for snt in b['sents']:
            lines += [str(i), ts(snt['t0']) + ' --> ' + ts(snt['t1']), snt['txt'], '']
            i += 1
    open(os.path.join(C.OUT, 'bermuda_triangle_ar.srt'), 'w', encoding='utf-8-sig').write('\n'.join(lines))
    print('srt entries', i - 1)


if __name__ == '__main__':
    build()
