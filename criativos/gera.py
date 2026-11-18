#!/usr/bin/env python3
"""Criativos do Material Escolar do Rafa (feed 1080x1350 e stories 1080x1920) + og.jpg.
Uso: python3 criativos/gera.py <pasta com fotos .webp dos produtos>
Ângulos: A = dor (a lista chegou), B = como funciona/prova (foto -> orçamento com link), C = comparação (rodar papelaria x 1 foto).
Conteúdo-chave entre y=300 e y=1620 no 9:16 (corte 4:5 do feed)."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FOTOS = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fotos"
OUT = os.path.dirname(os.path.abspath(__file__))
F = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
f = lambda w, s: ImageFont.truetype(F.format(w), s)
PAPEL, PAUTA, MARGEM = (251, 248, 241), (214, 226, 243), (238, 154, 154)
TINTA, TINTA2, AZUL, LAPIS, VERDE = (22, 33, 62), (59, 71, 102), (29, 58, 138), (246, 195, 67), (31, 175, 84)
SITE = "escolar.ofertadorafa.com.br"

def foto(nome):
    p = os.path.join(FOTOS, nome + ".webp")
    return Image.open(p).convert("RGB") if os.path.exists(p) else None

def papel(W, H, margem=True):
    im = Image.new("RGB", (W, H), PAPEL); d = ImageDraw.Draw(im)
    for y in range(70, H, 54): d.line([(0, y), (W, y)], fill=PAUTA, width=2)
    if margem: d.line([(92, 0), (92, H)], fill=MARGEM, width=3)
    return im, d

def rr(d, box, r, **k): d.rounded_rectangle(box, radius=r, **k)

def cartao_foto(im, img, x, y, s, rot=0):
    c = Image.new("RGBA", (s, s), (0, 0, 0, 0)); dc = ImageDraw.Draw(c)
    dc.rounded_rectangle([0, 0, s - 1, s - 1], radius=26, fill=(255, 255, 255, 255))
    if img:
        t = img.copy(); t.thumbnail((s - 36, s - 36)); c.paste(t, ((s - t.width) // 2, (s - t.height) // 2))
    sh = Image.new("RGBA", (s + 60, s + 60), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([30, 36, s + 30, s + 36], radius=26, fill=(22, 33, 62, 45))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    if rot: c = c.rotate(rot, expand=True, resample=Image.BICUBIC); sh = sh.rotate(rot, expand=True, resample=Image.BICUBIC)
    im.paste(sh, (x - 30, y - 30), sh); im.paste(c, (x, y), c)

def texto_quebra(d, xy, txt, fonte, cor, larg, entre=1.12):
    x, y = xy; linhas, atual = [], ""
    for p in txt.split():
        t = (atual + " " + p).strip()
        if d.textlength(t, font=fonte) <= larg: atual = t
        else: linhas.append(atual); atual = p
    linhas.append(atual)
    for l in linhas: d.text((x, y), l, font=fonte, fill=cor); y += int(fonte.size * entre)
    return y

def marca_texto(d, x, y, txt, fonte, cor_fundo=LAPIS):
    w = d.textlength(txt, font=fonte)
    d.rectangle([x - 6, y + fonte.size * .48, x + w + 6, y + fonte.size * 1.08], fill=cor_fundo)
    d.text((x, y), txt, font=fonte, fill=TINTA)

def cta(d, W, y, txt="Mande a foto da lista: " + SITE, cor=AZUL):
    rr(d, [60, y, W - 60, y + 96], 26, fill=cor)
    fo = f("Bold", 34); w = d.textlength(txt, font=fo)
    if w > W - 160: fo = f("Bold", 30); w = d.textlength(txt, font=fo)
    d.text(((W - w) / 2, y + 28), txt, font=fo, fill=(255, 255, 255))

# --------------------------------------------------------------------- A: dor
def criativo_A(W, H):
    im, d = papel(W, H); top = 300 if H > 1400 else 90
    d.text((130, top), "VOLTA ÀS AULAS 2027", font=f("Bold", 30), fill=AZUL)
    y = texto_quebra(d, (130, top + 56), "A lista de material chegou.", f("Black", 84), TINTA, W - 190, 1.05)
    marca_texto(d, 130, y + 4, "E o susto também.", f("Black", 84))
    # folha da lista com itens riscados e preço
    lx, ly, lw = 150, y + 150, W - 300
    folha = Image.new("RGBA", (lw, 430), (255, 255, 255, 255)); df = ImageDraw.Draw(folha)
    for yy in range(70, 430, 52): df.line([(0, yy), (lw, yy)], fill=PAUTA, width=2)
    itens = [("2 cadernos brochura 96 fls", "✓"), ("1 cx lápis de cor 24 cores", "✓"), ("3 borrachas brancas", "✓"),
             ("2 colas brancas 90 g", "✓"), ("1 tesoura sem ponta", "✓"), ("1 pacote sulfite A4", "✓"), ("+ 14 itens…", "")]
    fi = f("SemiBold", 34)
    for i, (t, ok) in enumerate(itens):
        df.text((34, 26 + i * 52 + 14), t, font=fi, fill=TINTA2)
        if ok: df.text((lw - 70, 26 + i * 52 + 10), ok, font=f("Black", 38), fill=VERDE)
    folha = folha.rotate(-2.2, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))
    sh = Image.new("RGBA", folha.size, (0, 0, 0, 0)); sh.paste((22, 33, 62, 50), mask=folha.split()[3]); sh = sh.filter(ImageFilter.GaussianBlur(16))
    im.paste(sh, (lx + 10, ly + 18), sh); im.paste(folha, (lx, ly), folha)
    d = ImageDraw.Draw(im)
    yb = ly + folha.height + 40
    y2 = texto_quebra(d, (130, yb), "Tira uma foto da lista. A gente acha cada item mais barato no Mercado Livre, com o link de cada um.", f("SemiBold", 40), TINTA2, W - 200, 1.25)
    cta(d, W, min(y2 + 40, (1520 if H > 1400 else 1210)))
    return im

# --------------------------------------------------------------------- B: como funciona (foto -> orçamento)
def criativo_B(W, H):
    im, d = papel(W, H, margem=False); top = 300 if H > 1400 else 80
    fo = f("Black", 80)
    y = texto_quebra(d, (70, top), "Uma foto da lista.", fo, TINTA, W - 140, 1.04)
    marca_texto(d, 70, y, "O orçamento inteiro.", fo); y += 120
    # 6 produtos reais em grade, cada um com etiqueta
    nomes = [("943935-MLB96050893887_102025", "Caderno"), ("801658-MLA118427441140_102026", "Lápis de cor"), ("914034-MLB113035273384_072026", "Borracha"),
             ("947285-MLA121394435671_112026", "Tesoura"), ("921787-MLA100041077461_122025", "Cola branca"), ("634486-MLA113688161602_072026", "Sulfite")]
    s, gap = 290, 30; x0 = (W - (3 * s + 2 * gap)) // 2
    for k, (nm, rot) in enumerate(nomes):
        cx, cy = x0 + (k % 3) * (s + gap), y + (k // 3) * (s + 84)
        cartao_foto(im, foto(nm), cx, cy, s, rot=[-2, 1.5, -1, 2, -1.5, 1][k])
        d = ImageDraw.Draw(im); d.text((cx + 8, cy + s + 18), rot.upper(), font=f("Bold", 26), fill=AZUL)
    y = y + 2 * (s + 84) + 10
    d.text((70, y), "✓ o mais barato com boa nota", font=f("Bold", 38), fill=TINTA); y += 58
    d.text((70, y), "✓ link de cada item no Mercado Livre", font=f("Bold", 38), fill=TINTA); y += 58
    d.text((70, y), "✓ manda pro grupo da escola no WhatsApp", font=f("Bold", 38), fill=TINTA)
    cta(d, W, 1520 if H > 1400 else 1210)
    return im

# --------------------------------------------------------------------- C: comparação (tempo, não preço)
def criativo_C(W, H):
    im = Image.new("RGB", (W, H), PAPEL); d = ImageDraw.Draw(im); top = 300 if H > 1400 else 80
    d.text((70, top), "Comprar o material escolar:", font=f("Bold", 44), fill=TINTA2)
    meio = top + 90; alt = 860 if H > 1400 else 820; hw = (W - 70 * 2 - 30) // 2
    # lado ruim
    rr(d, [70, meio, 70 + hw, meio + alt], 30, fill=(236, 232, 223))
    d.text((100, meio + 34), "DO JEITO ANTIGO", font=f("Bold", 28), fill=(140, 132, 118))
    ruim = ["Rodar papelaria", "Fila no balcão", "Item em falta", "Voltar outro dia", "Anotar preço", "Somar tudo à mão"]
    for i, t in enumerate(ruim):
        yy = meio + 110 + i * 112
        d.text((102, yy - 6), "×", font=f("Black", 50), fill=(201, 79, 61)); d.text((150, yy + 2), t, font=f("SemiBold", 36), fill=(110, 104, 94))
    # lado bom
    bx = 70 + hw + 30
    rr(d, [bx, meio, bx + hw, meio + alt], 30, fill=AZUL)
    d.text((bx + 30, meio + 34), "COM O RAFA", font=f("Bold", 28), fill=LAPIS)
    bom = ["1 foto da lista", "A gente lê tudo", "Acha o mais barato", "Link de cada item", "Total na hora", "Compra no ML"]
    for i, t in enumerate(bom):
        yy = meio + 110 + i * 112
        d.text((bx + 30, yy), "✓", font=f("Black", 40), fill=LAPIS); d.text((bx + 80, yy + 2), t, font=f("SemiBold", 36), fill=(255, 255, 255))
    y = meio + alt + 40
    texto_quebra(d, (70, y), "Leva uns 20 segundos. A foto não fica guardada.", f("Medium", 34), TINTA2, W - 140)
    cta(d, W, 1520 if H > 1400 else 1210, cor=TINTA)
    return im

def og():
    W, H = 1200, 630
    im, d = papel(W, H)
    d.text((130, 70), "MATERIAL ESCOLAR DO RAFA", font=f("Bold", 28), fill=AZUL)
    y = texto_quebra(d, (130, 120), "Tira uma foto da lista.", f("Black", 70), TINTA, 760, 1.05)
    marca_texto(d, 130, y, "A gente acha mais barato.", f("Black", 58))
    d.text((130, y + 100), "Orçamento completo com o link de cada item no Mercado Livre.", font=f("Medium", 28), fill=TINTA2)
    for k, nm in enumerate(["801658-MLA118427441140_102026", "943935-MLB96050893887_102025"]):
        cartao_foto(im, foto(nm), 880 + k * 60, 140 + k * 190, 250, rot=[-4, 3][k])
    d = ImageDraw.Draw(im); d.text((130, 540), SITE, font=f("Bold", 30), fill=AZUL)
    return im

if __name__ == "__main__":
    for nome, fn in [("A", criativo_A), ("B", criativo_B), ("C", criativo_C)]:
        fn(1080, 1350).save(os.path.join(OUT, f"escolar_{nome}_F.jpg"), quality=90)
        fn(1080, 1920).save(os.path.join(OUT, f"escolar_{nome}_S.jpg"), quality=90)
    og().save(os.path.join(os.path.dirname(OUT), "og.jpg"), quality=88)
    print("ok")
