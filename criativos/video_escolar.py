#!/usr/bin/env python3
"""Vídeo (esboço/animatic) do Material Escolar do Rafa: "A lista que vira orçamento".
1080x1920, 30 fps, ~18 s. Conteúdo-chave entre y=300 e y=1620 (corte 4:5 do feed).
Uso: python3 criativos/video_escolar.py <pasta fotos .webp> <saida.mp4> [audio_voz.wav]
Sem voz: sai só com efeitos sintetizados (animatic). Com voz: mixa por cima, com ducking."""
import os, sys, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FOTOS, SAIDA = sys.argv[1], sys.argv[2]
VOZ = sys.argv[3] if len(sys.argv) > 3 else None
W, H, FPS, DUR = 1080, 1920, 30, 18.0
F = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
f = lambda w, s: ImageFont.truetype(F.format(w), s)
PAPEL, PAUTA, MARGEM = (251, 248, 241), (214, 226, 243), (238, 154, 154)
TINTA, TINTA2, AZUL, LAPIS, VERDE, LARANJA = (22, 33, 62), (59, 71, 102), (29, 58, 138), (246, 195, 67), (31, 175, 84), (238, 77, 45)
ease = lambda x: 1 - (1 - max(0, min(1, x))) ** 3
clamp = lambda x: max(0.0, min(1.0, x))
def over(x):  # easeOutBack
    x = clamp(x); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

ITENS = ["24 lápis de cor", "2 cadernos 96 folhas", "cola branca 90 g", "tesoura sem ponta", "borracha branca macia",
         "apontador com depósito", "papel sulfite A4", "pasta com elástico", "régua 30 cm", "caneta marca-texto",
         "massinha de modelar", "estojo com 2 zíperes"]
CARDS = [("lapis_cor", "801658-MLA118427441140_102026", "Lápis de cor 24", "R$ 24,58", "ML"),
         ("tesoura", "947285-MLA121394435671_112026", "Tesoura sem ponta", "R$ 19,00", "ML"),
         ("borracha", "914034-MLB113035273384_072026", "Borracha branca", "R$ 21,70", "ML"),
         ("regua", "615815-MLB103745708194_012026", "Régua 30 cm", "R$ 7,99", "ML"),
         ("sulfite", "634486-MLA113688161602_072026", "Sulfite A4", "R$ 19,00", "ML"),
         ("cola", "921787-MLA100041077461_122025", "Cola branca", "R$ 37,00", "ML")]

def fotos():
    d = {}
    for _, nm, *_ in CARDS:
        p = os.path.join(FOTOS, nm + ".webp")
        d[nm] = Image.open(p).convert("RGB") if os.path.exists(p) else None
    return d
IMG = fotos()

# fundo caderno (cache)
BG = Image.new("RGB", (W, H), PAPEL); _d = ImageDraw.Draw(BG)
for y in range(70, H, 54): _d.line([(0, y), (W, y)], fill=PAUTA, width=2)
_d.line([(92, 0), (92, H)], fill=MARGEM, width=3)

def sombra(im, box, r, a=50, blur=16, off=18):
    x0, y0, x1, y1 = box; pad = blur * 3
    s = Image.new("RGBA", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(s).rounded_rectangle([pad, pad, pad + x1 - x0, pad + y1 - y0], radius=r, fill=(22, 33, 62, a))
    s = s.filter(ImageFilter.GaussianBlur(blur)); im.paste(s, (x0 - pad, y0 - pad + off), s)

def centro(d, y, txt, fonte, cor, cx=W // 2):
    w = d.textlength(txt, font=fonte); d.text((cx - w / 2, y), txt, font=fonte, fill=cor)

def marca(d, x, y, w, h, prog, cor=LAPIS):
    d.rectangle([x, y, x + w * prog, y + h], fill=cor)

def folha(im, x, y, w, h, linhas_vis, escala=1.0):
    """folha de lista; linhas_vis = nº de itens já escritos (float)"""
    sombra(im, (x, y, x + w, y + h), 18)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=(255, 255, 255), outline=(225, 225, 225), width=2)
    fo = f("SemiBold", int(40 * escala)); ft = f("Black", int(36 * escala))
    d.text((x + 50 * escala, y + 30 * escala), "LISTA DE MATERIAL · 1º ANO", font=ft, fill=AZUL)
    d.line([(x + 40 * escala, y + 92 * escala), (x + w - 40 * escala, y + 92 * escala)], fill=MARGEM, width=3)
    for i, t in enumerate(ITENS):
        a = clamp(linhas_vis - i)
        if a <= 0: break
        yy = y + (116 + i * 69) * escala
        d.ellipse([x + 52 * escala, yy + 18 * escala, x + 72 * escala, yy + 38 * escala], outline=TINTA2, width=3)
        full = t; n = int(len(full) * a)
        d.text((x + 100 * escala, yy), full[:n], font=fo, fill=TINTA)
        d.line([(x + 40 * escala, yy + 64 * escala), (x + w - 40 * escala, yy + 64 * escala)], fill=PAUTA, width=2)
    return im

def card(im, k, t0, t):
    _, nm, nome, preco, loja = CARDS[k]
    p = over((t - t0) / 0.45)
    if p <= 0: return
    s = 270; gap = 30; x0 = (W - (3 * s + 2 * gap)) // 2
    cx = x0 + (k % 3) * (s + gap); cy = 690 + (k // 3) * (s + 130)
    sc = max(.01, p)
    w = int(s * sc); h = int(s * sc)
    px, py = cx + (s - w) // 2, cy + (s - h) // 2
    sombra(im, (px, py, px + w, py + h), 22, 45, 12, 12)
    d = ImageDraw.Draw(im); d.rounded_rectangle([px, py, px + w, py + h], radius=22, fill=(255, 255, 255))
    img = IMG[nm]
    if img and w > 40:
        th = img.copy(); th.thumbnail((w - 28, h - 28)); im.paste(th, (px + (w - th.width) // 2, py + (h - th.height) // 2))
    if p > .6:
        a = clamp((p - .6) / .4)
        d.text((cx + 6, cy + s + 14), nome.upper(), font=f("Bold", 24), fill=AZUL)
        d.text((cx + 6, cy + s + 46), preco, font=f("Black", 40), fill=TINTA)
        b = f("Black", 22); wl = d.textlength(loja, font=b) + 26
        d.rounded_rectangle([cx + s - wl, cy + s + 56, cx + s, cy + s + 92], radius=18, fill=(255, 230, 0) if loja == "ML" else LARANJA)
        d.text((cx + s - wl + 13, cy + s + 61), loja, font=b, fill=(40, 40, 40) if loja == "ML" else (255, 255, 255))

TOTAL = 342
def frame(t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    # ---- Cena 1 (0–3.4): a lista chegou
    if t < 5.4:
        a1 = ease((t - .1) / .5)
        if t < 3.6:
            d.text((90, 330 - 30 * (1 - a1)), "A lista da escola", font=f("Black", 92), fill=TINTA)
            d.text((90, 440 - 30 * (1 - a1)), "chegou.", font=f("Black", 92), fill=TINTA)
            marca(d, 90, 560, 330 * ease((t - .6) / .5), 22, 1)  # marca-texto sob "chegou"
        lv = clamp((t - .5) / 2.6) * len(ITENS)
        # folha: sobe, depois encolhe pra "foto" (cena 2)
        if t < 3.6:
            folha(im, 130, 700, 820, 960, lv)
            if t > 2.5:
                b = over((t - 2.5) / .35); r = int(70 * b)
                if r > 0:
                    cx, cy = 880, 700
                    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=LARANJA)
                    if b > .8: centro(d, cy - 40, "33", f("Black", 56), (255, 255, 255), cx); centro(d, cy + 8, "itens", f("Bold", 24), (255, 255, 255), cx)
        else:
            q = ease((t - 3.6) / .6)
            sc = 1 - .45 * q
            w, h = int(820 * sc), int(960 * sc)
            x, y = (W - w) // 2, int(700 + (330 - 700) * 0 + 140 * q)
            folha(im, x, y, w, h, 99, escala=sc * 1.0)
            # mira de câmera
            if t > 3.8:
                L = 70; m = 24
                for (ax, ay, sx, sy) in [(x - m, y - m, 1, 1), (x + w + m, y - m, -1, 1), (x - m, y + h + m, 1, -1), (x + w + m, y + h + m, -1, -1)]:
                    d.line([(ax, ay), (ax + sx * L, ay)], fill=LARANJA, width=8); d.line([(ax, ay), (ax, ay + sy * L)], fill=LARANJA, width=8)
            d.text((90, 330), "Uma foto.", font=f("Black", 110), fill=TINTA)
            marca(d, 90, 470, 450 * ease((t - 4.0) / .5), 24, 1)
            # flash do obturador
        fl = clamp(1 - abs(t - 3.75) / .12)
        if fl > 0: im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), fl * .9)
        return im
    # ---- Cena 3 (5.4–12.6): orçamento
    d = ImageDraw.Draw(im)
    a = ease((t - 5.4) / .5)
    d.text((90, 330 - 20 * (1 - a)), "Orçamento pronto.", font=f("Black", 84), fill=TINTA)
    marca(d, 90, 438, 700 * ease((t - 5.8) / .6), 22, 1)
    for k in range(6): card(im, k, 6.2 + k * .55, t)
    # total
    d = ImageDraw.Draw(im)
    tp = clamp((t - 6.0) / 6.0); val = int(TOTAL * ease(tp))
    by = 1490
    if t > 5.8:
        sombra(im, (90, by, 990, by + 170), 26, 55, 14, 14); d = ImageDraw.Draw(im)
        d.rounded_rectangle([90, by, 990, by + 170], radius=26, fill=TINTA)
        d.text((130, by + 28), "TOTAL DA LISTA · 25 ITENS", font=f("Bold", 28), fill=(190, 200, 225))
        d.text((130, by + 70), f"R$ {val}", font=f("Black", 84), fill=(255, 255, 255))
        if t > 12.0:
            ok = ease((t - 12.0) / .4)
            d.rounded_rectangle([650, by + 52, 960, by + 118], radius=33, fill=VERDE)
            centro(d, by + 64, "✓ link de cada item", f("Bold", 28), (255, 255, 255), 805)
    # ---- Cena 4 (12.6–): mais barato entre ML e Shopee → CTA
    if t > 12.6:
        q = ease((t - 12.6) / .5)
        ov = Image.new("RGBA", (W, H), (251, 248, 241, int(250 * q))); im.paste(ov, (0, 0), ov); d = ImageDraw.Draw(im)
        if t > 12.9:
            a = ease((t - 12.9) / .5)
            d.text((90, 330 - 20 * (1 - a)), "O mais barato", font=f("Black", 92), fill=TINTA)
            d.text((90, 436 - 20 * (1 - a)), "entre os dois.", font=f("Black", 92), fill=TINTA)
            marca(d, 90, 548, 520 * ease((t - 13.2) / .5), 22, 1)
            for i, (nm, cor, tx) in enumerate([("Mercado Livre", (255, 230, 0), (40, 40, 40)), ("Shopee", LARANJA, (255, 255, 255))]):
                b = over((t - 13.4 - i * .25) / .4)
                if b > 0:
                    w = int(400 * b); x = 90 + i * 430
                    d.rounded_rectangle([x, 700, x + w, 820], radius=60, fill=cor)
                    if b > .9: centro(d, 736, nm, f("Black", 44), tx, x + 200)
        if t > 14.8:
            a = ease((t - 14.8) / .5)
            sombra(im, (90, 940, 990, 1290), 32, 50, 16, 16); d = ImageDraw.Draw(im)
            d.rounded_rectangle([90, 940, 990, 1290], radius=32, fill=(255, 255, 255))
            d.text((140, 990), "MATERIAL ESCOLAR", font=f("Black", 30), fill=AZUL)
            d.text((140, 1032), "do Rafa", font=f("Black", 96), fill=TINTA)
            d.text((140, 1160), "escolar.ofertadorafa.com.br", font=f("Bold", 44), fill=AZUL)
            d.text((140, 1220), "Manda a foto da lista. É grátis.", font=f("Medium", 32), fill=TINTA2)
        if t > 15.4:
            r = ease((t - 15.4) / .5)
            d.rounded_rectangle([90, 1380, 990, 1380 + int(130 * r)], radius=65, fill=VERDE)
            if r > .9: centro(d, 1415, "Toque em Saiba mais", f("Black", 50), (255, 255, 255))
    return im

# ---------------------------------------------------------------- áudio sintetizado
SR = 44100
def trilha():
    n = int(SR * DUR); a = np.zeros(n)
    rng = np.random.default_rng(3)
    def add(t0, s, g=1.0):
        i = int(t0 * SR); j = min(n, i + len(s)); a[i:j] += s[:j - i] * g
    def tom(fr, d, g=.4, dec=18):
        t = np.arange(int(SR * d)) / SR; return np.sin(2 * np.pi * fr * t) * np.exp(-t * dec) * g
    def ruido(d, g=.4, dec=40, hp=True):
        t = np.arange(int(SR * d)) / SR; x = rng.standard_normal(len(t)) * np.exp(-t * dec) * g
        return np.diff(x, prepend=0) if hp else x
    # lápis riscando (0.5–3.1): ruído filtrado em rajadas por item
    for k in range(len(ITENS)):
        t0 = .5 + k * (2.6 / len(ITENS)); add(t0, ruido(.17, .35, 9) * .5)
    add(2.5, tom(880, .25, .35, 14)); add(2.5, tom(1320, .25, .2, 14))      # selo "33 itens"
    # obturador (3.75)
    add(3.72, ruido(.05, .9, 60)); add(3.80, ruido(.08, .7, 45)); add(3.74, tom(180, .1, .5, 40))
    add(4.0, tom(520, .18, .3, 20))                                           # "uma foto"
    # cards surgindo: plim por item + tique do total
    for k in range(6):
        t0 = 6.2 + k * .55; add(t0, tom(660 + k * 70, .3, .38, 12)); add(t0 + .02, tom((660 + k * 70) * 2, .2, .15, 18))
    for t0 in np.arange(6.1, 12.0, .09): add(t0, tom(1900, .03, .12, 160))    # contador
    add(12.0, tom(784, .5, .35, 7)); add(12.08, tom(1175, .6, .3, 6))        # total fechado
    add(12.7, ruido(.35, .5, 10, False) * .6)                                 # whoosh
    add(13.4, tom(500, .25, .3, 14)); add(13.65, tom(750, .3, .3, 12))
    add(14.9, tom(523, .8, .3, 4)); add(14.95, tom(784, .8, .25, 4)); add(15.0, tom(1047, .9, .25, 4))
    return np.clip(a, -1, 1) * .8

def main():
    wav = "/tmp/vid/efeitos.wav"; s = trilha()
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((s * 32767).astype("<i2").tobytes())
    sem_audio = "/tmp/vid/sem_audio.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", sem_audio], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    if VOZ:
        fc = ("[1:a]highpass=f=80,afftdn,acompressor,loudnorm=I=-16[v];[2:a]volume=0.55[e];"
              "[e][v]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[ed];[v][ed]amix=inputs=2:normalize=0[a]")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", sem_audio, "-i", VOZ, "-i", wav, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", SAIDA]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", sem_audio, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", SAIDA]
    subprocess.run(cmd, check=True)
    print("ok", SAIDA)

if __name__ == "__main__":
    if os.environ.get("FOLHA"):
        os.makedirs("/tmp/vid/q", exist_ok=True)
        for k, t in enumerate([1.5, 3.0, 3.75, 4.8, 7.5, 10.0, 12.3, 14.0, 16.5]):
            frame(t).resize((360, 640)).save(f"/tmp/vid/q/{k}.png")
        sys.exit()
    main()
