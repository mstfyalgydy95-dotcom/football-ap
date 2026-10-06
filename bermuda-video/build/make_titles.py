"""Render Arabic overlay graphics (title card, chapter bars, map overlay, end card)."""
import os, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import common as C

W, H = C.W, C.H
GOLD = (232, 190, 92)
INK = (240, 244, 250)
DARK = (8, 12, 20)


def _soft(img, box, radius, fill, blur=18):
    """rounded translucent rect via separate blur layer"""
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, radius=radius, fill=fill)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)


def text_glow(img, xy, txt, fnt, fill, anchor='mm', glow=(0, 0, 0, 220), grow=6, spacing=None):
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.text(xy, txt, font=fnt, fill=glow, anchor=anchor, stroke_width=grow, stroke_fill=glow,
           spacing=spacing)
    lay = lay.filter(ImageFilter.GaussianBlur(7))
    img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    d.text(xy, txt, font=fnt, fill=fill, anchor=anchor, spacing=spacing)
    return img


def title_card():
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # vertical gradient dark at bottom
    grad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(H):
        a = int(215 * (y / H) ** 1.6)
        gd.line([(0, y), (W, y)], fill=(4, 8, 14, a))
    img.alpha_composite(grad)
    # thin gold rules
    d.line([(W * .18, 300), (W * .82, 300)], fill=GOLD + (200,), width=3)
    d.line([(W * .18, 700), (W * .82, 700)], fill=GOLD + (200,), width=3)
    text_glow(img, (W / 2, 415), C.ar('مثلث برمودا'), C.font(C.FONT_HEAD, 150), INK + (255,))
    text_glow(img, (W / 2, 560), C.ar('الأسطورة… والأرقام… والتفسير العلمي'),
              C.font(C.FONT_BODY, 56), GOLD + (255,))
    text_glow(img, (W / 2, 655), C.ar('وثائقي مُصوَّر — قراءة في أشهر لغز في المحيط الأطلسي'),
              C.font(C.FONT_BODY, 34), (200, 210, 222, 235))
    img.save(os.path.join(C.OV, 'title_card.png'))


def chapter_bar(bid, label, years):
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x_l, y0, x_r, y1 = W - 1360, H - 210, W - 90, H - 92
    _soft(img, (x_l - 20, y0 - 16, x_r + 20, y1 + 16), 26, (4, 8, 14, 150), blur=12)
    d.rounded_rectangle((x_l, y0, x_r, y1), radius=20, fill=(6, 10, 18, 195),
                        outline=(255, 255, 255, 45), width=2)
    d.rounded_rectangle((x_r - 14, y0, x_r, y1), radius=7, fill=GOLD + (255,))
    text_glow(img, (x_r - 48, (y0 + y1) / 2 - 14), C.ar(label), C.font(C.FONT_HEAD, 50),
              INK + (255,), anchor='rm')
    text_glow(img, (x_r - 48, y1 - 24), C.ar(years), C.font(C.FONT_BODY, 28),
              GOLD + (255,), anchor='rm')
    img.save(os.path.join(C.OV, 'bar_%s.png' % bid))


def watermark():
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((60, 52, 500, 122), radius=16, fill=(6, 10, 18, 120))
    d.rounded_rectangle((60, 52, 74, 122), radius=7, fill=GOLD + (220,))
    text_glow(img, (478, 87), C.ar('مثلث برمودا — وثائقي'), C.font(C.FONT_BODY, 34), (225, 232, 240, 215), anchor='rm')
    img.save(os.path.join(C.OV, 'watermark.png'))


def map_overlay():
    """triangle + arabic labels on the blank chart (chart is 1376x768 -> scale)."""
    sx, sy = W / 1376.0, H / 768.0
    pts = {'miami': (338, 392), 'bermuda': (1163, 103), 'pr': (1005, 690)}
    P = {k: (v[0] * sx, v[1] * sy) for k, v in pts.items()}
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tri = [P['miami'], P['bermuda'], P['pr']]
    d.polygon(tri, fill=(200, 60, 60, 55))
    for i in range(3):
        a, b = tri[i], tri[(i + 1) % 3]
        d.line([a, b], fill=(235, 80, 70, 235), width=6)
    for p in tri:
        d.ellipse((p[0] - 14, p[1] - 14, p[0] + 14, p[1] + 14), fill=(240, 220, 120, 255),
                  outline=(20, 20, 20, 255), width=3)
    labels = [('ميامي', P['miami'], (-30, 46)), ('برمودا', P['bermuda'], (-40, -52)), ('بورتوريكو', P['pr'], (40, 52))]
    for txt, p, off in labels:
        text_glow(img, (p[0] + off[0], p[1] + off[1]), C.ar(txt), C.font(C.FONT_HEAD, 54), (255, 240, 200, 255), anchor='mm')
    text_glow(img, (W / 2, 150), C.ar('حدود المثلث (تقريبية) — لا تعترف بها أي جهة رسمية'),
              C.font(C.FONT_BODY, 40), (255, 255, 255, 240), anchor='mm')
    img.save(os.path.join(C.OV, 'map_overlay.png'))


def end_card():
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    grad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(H):
        a = int(235 * (1 - y / H) ** 0.4 * 0.5 + 235 * (y / H) ** 1.3 * 0.9)
        gd.line([(0, y), (W, y)], fill=(3, 6, 12, min(255, a)))
    img.alpha_composite(grad)
    text_glow(img, (W / 2, H / 2 - 90), C.ar('هل أغلقنا الملف؟'), C.font(C.FONT_HEAD, 96), INK + (255,))
    text_glow(img, (W / 2, H / 2 + 30), C.ar('أخبرنا في التعليقات برأيك'), C.font(C.FONT_BODY, 52), GOLD + (255,))
    text_glow(img, (W / 2, H / 2 + 130), C.ar('اشترك وفعّل الجرس — الحلقة القادمة: مثلث التنين'),
              C.font(C.FONT_BODY, 40), (210, 218, 228, 240))
    img.save(os.path.join(C.OV, 'end_card.png'))


BARS = [
    ('B01', 'السرب التاسع عشر', '5 ديسمبر 1945 — فلوريدا'),
    ('B02', 'ما هو مثلث برمودا؟', 'المساحة والموقع'),
    ('B03', 'كيف وُلدت الأسطورة؟', '1492 → 1964 → 1974'),
    ('B04', 'الملفات: سايكلوبس — ديرينغ', '1918 / 1921'),
    ('B05', 'الملف الثالث: السرب التاسع عشر', 'من داخل قمرة القيادة'),
    ('B06', 'ستار تايغر — ستار أرييل — مارين سلفر كوين', '1948 / 1949 / 1963'),
    ('B07', 'لاري كوشي يذهب إلى الأرشيف', '1975'),
    ('B08', 'ماذا تقول المؤسسات؟', 'لويدز — خفر السواحل — WWF'),
    ('B09', 'التفسير العلمي: التيار والطقس والميثان', 'الجزء الأول'),
    ('B10', 'الموجات المارقة والبوصلة والعمق', 'وحادثة إل فارو 2015'),
    ('B11', 'لماذا نصدّق الأسطورة؟', 'الخاتمة'),
]

if __name__ == '__main__':
    title_card(); watermark(); map_overlay(); end_card()
    for b, l, y in BARS:
        chapter_bar(b, l, y)
    print('overlays:', sorted(os.listdir(C.OV)))
