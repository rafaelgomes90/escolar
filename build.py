#!/usr/bin/env python3
"""Gera o site estático Material Escolar do Rafa a partir de produtos.json + painel/tipos.json.

Saída: produtos.js, index.html, sitemap.xml, robots.txt.  Rode:  python3 build.py
A leitura da foto acontece no servidor (painel/server.py → Gemini) e o orçamento é montado no navegador (assets/lista.js).
"""
import json, html, os

BASE = "https://escolar.ofertadorafa.com.br"
PIXEL = os.environ.get("PIXEL", "") or json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"))).get("pixel", "")
V = "6"  # suba quando mudar CSS/JS (cache)
ROOT = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(ROOT, "produtos.json"), encoding="utf-8"))
T = json.load(open(os.path.join(ROOT, "painel", "tipos.json"), encoding="utf-8"))
CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
GRUPO = CFG.get("grupo_whatsapp", "").strip()
TIPO = {t["id"]: t for t in T}
for p in P:
    if p.get("pic"):
        p["imagem"] = ("/img/s/" + p["pic"][2:] if p["pic"].startswith("s:") else "/img/" + p["pic"]) + ".webp"

e = lambda s: html.escape(str(s), quote=True)
def brl(n): return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def nota(n): return f"{n:.1f}".replace(".", ",")

ICON_EXT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>'
LOGO = open(os.path.join(ROOT, "favicon.svg"), encoding="utf-8").read().replace('<svg xmlns="http://www.w3.org/2000/svg"', '<svg aria-hidden="true"')

PIXEL_JS = f"""<script>
!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','{PIXEL}');fbq('track','PageView');
</script>
<noscript><img height="1" width="1" style="display:none" alt="" src="https://www.facebook.com/tr?id={PIXEL}&ev=PageView&noscript=1"></noscript>""" if PIXEL else ""


def head(title, desc, path):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE}{path}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:site_name" content="Material Escolar do Rafa">
<meta property="og:image" content="{BASE}/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1D3A8A">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Caveat:wght@600&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v={V}">
{PIXEL_JS}
</head>"""


def ml(p, inner, cls="", origem=""):
    return (f'<a class="{cls}" href="{e(p["link"])}" target="_blank" rel="noopener sponsored" '
            f'data-ml="{p["id"]}" data-origem="{origem}">{inner}</a>')


def card(p):
    t = TIPO[p["tipo"]]
    return f"""<article class="card">
  {ml(p, f'<img src="{e(p["imagem"])}" alt="{e(p["nome"])}" loading="lazy" decoding="async">', "foto", "catalogo-foto")}
  <div class="corpo">
    <p class="cat">{e(t['emoji'])} {e(t['nome'])}</p>
    <h3>{ml(p, e(p['nome']), "", "catalogo-nome")}</h3>
    <p class="aval">★ <b>{nota(p['nota'])}</b>{(' · +' + e(p['vendas']) + ' vendidos') if p.get('vendas') else ''}</p>
    <div class="linha"><p class="preco">R$ {brl(p['preco'])}</p>{ml(p, ('Ver na Shopee ' if p.get('loja') == 'shopee' else 'Ver no ML ') + ICON_EXT, "ml", "catalogo-botao")}</div>
  </div>
</article>"""


def grupo_bloco():
    if not GRUPO: return ""
    return f"""<section class="sec"><div class="wrap estreito">
  <div class="grupo">
    <div class="grupo-tx">
      <h3>Ainda vai demorar pra comprar?</h3>
      <p>Entra no grupo <b>Oferta do Rafa</b> no WhatsApp: cupons e quedas de preço do Mercado Livre todo dia, inclusive de material escolar até a volta às aulas.</p>
    </div>
    <a class="btn grupo-btn" href="{e(GRUPO)}" target="_blank" rel="noopener" data-grupo="home">Entrar no grupo grátis</a>
  </div>
</div></section>"""


# ---------------------------------------------------------------- produtos.js
TIPOS_JS = [{k: t[k] for k in ("id", "nome", "unidade", "unidade_pl", "emoji", "grupo")} | ({"busca": t["busca"]} if t.get("busca") else {}) for t in T]
with open(os.path.join(ROOT, "produtos.js"), "w", encoding="utf-8") as f:
    f.write("// GERADO por build.py a partir de produtos.json e painel/tipos.json\n")
    f.write("window.PRODUTOS = " + json.dumps(P, ensure_ascii=False, separators=(",", ":")) + ";\n")
    f.write("window.TIPOS = " + json.dumps(TIPOS_JS, ensure_ascii=False, separators=(",", ":")) + ";\n")

# ---------------------------------------------------------------- vitrine: o campeão de cada tipo
GRUPOS = [("escrita", "Escrita"), ("cores", "Pra colorir"), ("cadernos", "Cadernos"), ("cola", "Colas"), ("corte", "Tesoura"),
          ("geometria", "Régua e geometria"), ("papeis", "Papéis e EVA"), ("arte", "Arte"), ("organizacao", "Organização"),
          ("mochila", "Mochila e lancheira"), ("higiene", "Higiene"), ("livros", "Livros, gibis e jogos")]
vit = ""
for gid, gnome in GRUPOS:
    cards = []
    for t in [t for t in T if t["grupo"] == gid]:
        ps = [p for p in P if p["tipo"] == t["id"]]
        if ps:
            cards.append(card(sorted(ps, key=lambda p: (-(p.get("campeao") or 0), p["preco"] / max(1, p.get("un", 1))))[0]))
    if cards:
        vit += f'<h3 class="cat-title" id="{gid}">{gnome}</h3>\n<div class="grid">\n' + "\n".join(cards) + "\n</div>\n"

FAQ = [("Como vocês leem a lista?", "Uma inteligência artificial lê a foto (vale lista impressa, escrita à mão, print ou PDF), separa item por item com a quantidade e a gente procura cada um no nosso catálogo de material escolar do Mercado Livre, sempre o mais barato que tem boa avaliação."),
       ("A foto da lista fica guardada?", "Não. A foto só é usada pra leitura e é descartada. Se você compartilhar o orçamento no WhatsApp, guardamos só a imagem do orçamento e os itens, pra quem receber o link conseguir abrir."),
       ("Por que cada item tem seu próprio botão?", "Porque cada produto é de uma loja diferente dentro do Mercado Livre. Você abre um por um, confere o preço do dia e põe no carrinho do ML. No fim paga tudo junto lá, e várias lojas dão frete grátis no carrinho."),
       ("Às vezes vem uma caixa com mais unidades do que a lista pede. Por quê?", "Porque muitas vezes a caixa com 12 ou 24 sai mais barata do que comprar 2 ou 3 soltos. Quando isso acontece, a gente avisa no item quantos vêm. Se quiser outra opção, toque em \"trocar\"."),
       ("Leu algum item errado?", "Toque em \"trocar\" pra ver outras opções do mesmo item. Se o item não estiver no catálogo, ele vai pra \"Pra buscar à parte\" com o link de busca do Mercado Livre."),
       ("Os preços são esses mesmo?", "São os preços que conferimos no Mercado Livre. Preço muda todo dia (às vezes cai com cupom), então o valor que vale é o que aparece no anúncio na hora da compra."),
       ("É seguro comprar pelo link?", "Sim. A compra é feita no próprio Mercado Livre, com Compra Garantida. A gente só indica e monta o orçamento.")]
faq = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in FAQ)

index = head("Material Escolar do Rafa: tire foto da lista e veja o orçamento mais barato",
             "Mande a foto da lista de material escolar: a gente lê item por item e monta o orçamento mais barato no Mercado Livre, com o link de cada produto.",
             "/") + f"""
<body>
<header class="hdr"><div class="wrap">
  <a class="logo" href="/" aria-label="Material Escolar do Rafa">{LOGO}<span>Material Escolar <i>do Rafa</i></span></a>
  <nav class="menu" aria-label="Menu"><a href="#enviar-lista">Mandar lista</a><a href="#catalogo">Produtos</a><a class="hide-sm" href="#duvidas">Dúvidas</a></nav>
</div></header>
<main>
<section class="hero" id="enviar-lista"><div class="wrap">
  <div class="hero-tx">
    <p class="eyebrow">Volta às aulas 2027 · Mercado Livre</p>
    <h1>Tira uma foto da lista de material. <span class="marca">A gente acha tudo mais barato.</span></h1>
    <p class="sub">Lemos item por item, procuramos o menor preço com boa avaliação e devolvemos o orçamento completo, com o link de cada produto.</p>
    <ol class="passos"><li><b>1</b> Foto da lista</li><li><b>2</b> A gente lê</li><li><b>3</b> Orçamento com links</li></ol>
  </div>
  <div class="envio">
    <form id="form-lista" novalidate>
      <label class="campo"><span>Nome da criança <small>(opcional)</small></span>
        <input id="nome" name="nome" type="text" maxlength="30" autocomplete="off" placeholder="Ex.: Noah"></label>
      <label class="drop" id="drop">
        <input id="foto" type="file" accept="image/*,application/pdf" multiple>
        <span class="drop-ic" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg></span>
        <span class="drop-tx"><b>Tirar foto da lista</b><small>ou escolher foto/PDF · até 4 páginas</small></span>
      </label>
      <div class="previas" id="previas"></div>
      <button type="button" class="link" id="abre-texto">Prefiro colar o texto da lista</button>
      <div id="texto-wrap" hidden><textarea id="texto" rows="6" maxlength="6000" placeholder="Cole aqui a lista (do WhatsApp, e-mail, site da escola…)"></textarea></div>
      <button class="btn grande" id="enviar" type="submit">Montar meu orçamento</button>
      <p class="msg" id="msg" role="alert"></p>
      <p class="nota">Leva uns 20 segundos. A foto não fica guardada.</p>
    </form>
  </div>
</div></section>
<p class="aviso-comp" id="aviso-comp" hidden><b></b> Quer a da sua escola? <a href="#enviar-lista">Mande a foto aqui</a>.</p>
<section class="resultado wrap" id="resultado" hidden aria-live="polite"></section>

<section class="sec alt" id="catalogo"><div class="wrap">
  <div class="sec-title"><h2>Os campeões de cada item</h2><p>O mais barato com boa nota em cada categoria do nosso catálogo.</p></div>
  {vit}
  <p class="disc">Preços conferidos no Mercado Livre e que mudam todo dia. O valor final, o frete e os cupons aparecem no anúncio.</p>
</div></section>
{grupo_bloco()}
<section class="sec" id="duvidas"><div class="wrap estreito">
  <div class="sec-title"><h2>Dúvidas</h2></div>
  <div class="faq">{faq}</div>
</div></section>
</main>
<footer><div class="in">
  <p>Material Escolar do Rafa © 2026 · Uma página do <b>Oferta do Rafa</b>. Indicamos produtos vendidos no Mercado Livre; ao comprar pelos nossos links podemos receber uma comissão, sem custo extra pra você. Preços e estoque mudam todo dia: o valor final é o do Mercado Livre.</p>
  <a href="#enviar-lista">Mandar lista</a> · <a href="#catalogo">Produtos</a> · <a href="/privacidade.html">Política de privacidade</a>
</div></footer>
<script src="/produtos.js?v={V}"></script>
<script src="/assets/app.js?v={V}"></script>
<script src="/assets/lista.js?v={V}"></script>
</body>
</html>
"""
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(index)
open(os.path.join(ROOT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    f"  <url><loc>{BASE}/</loc></url>\n</urlset>\n")
open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: {BASE}/sitemap.xml\n")
print("ok:", len(P), "produtos,", len(T), "tipos")
