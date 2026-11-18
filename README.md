# Material Escolar do Rafa

Tira foto da lista de material escolar → a IA (Gemini) lê item por item → o site monta o orçamento mais barato do catálogo do Mercado Livre (links de afiliado meli.la), com nome da criança e compartilhamento no WhatsApp. No ar em https://escolar.ofertadorafa.com.br

- `produtos.json`: catálogo (tipo, unidades no pacote, cores/folhas etc., link meli.la). Edite e rode `python3 build.py`.
- `painel/tipos.json`: categorias que a IA reconhece (com link de busca meli.la de cada uma). `painel/prompt.txt`: instrução de leitura.
- `painel/server.py`: `/api/lista` (Gemini), `/img/*` (cache das fotos do ML), `/api/kit` e `/api/k/*` (lista compartilhada com prévia), contador de visitas e painel.
- `assets/lista.js`: envio da foto, casamento item→produto (menor custo total; empate vai pra melhor nota), resultado, imagem e WhatsApp.
- `criativos/gera.py`: criativos A (dor), B (foto→orçamento), C (comparação), feed e stories.
- `instalar-escolar.sh`: publica na VPS (Caddy em Docker do painel achadinhos) e pede a chave do Gemini.
- Pixel: 1896450861799386 (Conta 2). Etiqueta de afiliado: ofertadorafa.
- Ao mudar CSS/JS, suba `V` no `build.py`.
