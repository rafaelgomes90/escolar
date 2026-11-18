/* Material Escolar do Rafa — lê a lista (foto/PDF/texto), casa com o catálogo e monta o orçamento */
(function(){
  var P = window.PRODUTOS || [], T = window.TIPOS || [], CSA = window.CSA || {track:function(){},trackC:function(){},esc:function(s){return s}};
  var esc = CSA.esc;
  var brl = function(n){ return Number(n).toLocaleString('pt-BR',{minimumFractionDigits:2, maximumFractionDigits:2}); };
  var brl0 = function(n){ return Number(Math.round(n)).toLocaleString('pt-BR'); };
  var TIPO = {}; T.forEach(function(t){ TIPO[t.id] = t; });
  var POR = {}; P.forEach(function(p){ (POR[p.tipo] = POR[p.tipo] || []).push(p); });
  var SITE = location.origin + '/';

  var form = document.getElementById('form-lista'), res = document.getElementById('resultado');
  if(!form) return;
  var inFoto = document.getElementById('foto'), inNome = document.getElementById('nome'), inTexto = document.getElementById('texto');
  var prev = document.getElementById('previas'), btEnviar = document.getElementById('enviar'), msg = document.getElementById('msg');
  var ARQS = [];
  var L = null; // {nome, serie, linhas:[{it, op:[produtos ordenados], k, custo, q}]}

  // ---------------------------------------------------------------- arquivos
  function reduzir(file){
    return new Promise(function(ok, erro){
      if(file.type === 'application/pdf'){
        if(file.size > 7e6) return erro('O PDF tem mais de 7 MB. Mande uma foto da lista.');
        var fr = new FileReader(); fr.onload = function(){ ok({mime:'application/pdf', dados:fr.result, nome:file.name}); }; fr.onerror = function(){ erro('Não consegui abrir o PDF.'); }; fr.readAsDataURL(file); return;
      }
      var url = URL.createObjectURL(file), im = new Image();
      im.onload = function(){
        var M = 2000, s = Math.min(1, M/Math.max(im.width, im.height)), cv = document.createElement('canvas');
        cv.width = Math.round(im.width*s); cv.height = Math.round(im.height*s);
        var c = cv.getContext('2d'); c.fillStyle = '#fff'; c.fillRect(0,0,cv.width,cv.height); c.drawImage(im, 0, 0, cv.width, cv.height);
        URL.revokeObjectURL(url);
        ok({mime:'image/jpeg', dados:cv.toDataURL('image/jpeg', .85), nome:file.name});
      };
      im.onerror = function(){ URL.revokeObjectURL(url); erro('Esse arquivo não é uma imagem que eu consiga abrir. Tente foto (JPG/PNG) ou PDF.'); };
      im.src = url;
    });
  }
  function desenharPrevias(){
    prev.innerHTML = ARQS.map(function(a, i){
      var mini = a.mime === 'application/pdf' ? '<span class="pdf">PDF</span>' : '<img src="'+a.dados+'" alt="">';
      return '<div class="prev">'+mini+'<button type="button" data-tira="'+i+'" aria-label="Tirar arquivo">×</button></div>';
    }).join('');
    document.getElementById('drop').classList.toggle('tem', ARQS.length > 0);
  }
  inFoto.addEventListener('change', function(){
    var fs = Array.prototype.slice.call(inFoto.files || [], 0, 4 - ARQS.length); msg.textContent = '';
    Promise.all(fs.map(reduzir)).then(function(r){ ARQS = ARQS.concat(r).slice(0,4); desenharPrevias(); }, function(e){ msg.textContent = e; });
    inFoto.value = '';
  });
  prev.addEventListener('click', function(e){ var b = e.target.closest('[data-tira]'); if(!b) return; ARQS.splice(+b.getAttribute('data-tira'), 1); desenharPrevias(); });
  document.getElementById('abre-texto').addEventListener('click', function(){ var w = document.getElementById('texto-wrap'); w.hidden = !w.hidden; if(!w.hidden) inTexto.focus(); });

  var ETAPAS = ['Lendo a lista…', 'Separando item por item…', 'Procurando o mais barato no Mercado Livre…', 'Somando tudo…'];
  form.addEventListener('submit', function(ev){
    ev.preventDefault(); msg.textContent = '';
    var texto = (inTexto.value || '').trim();
    if(!ARQS.length && !texto){ msg.textContent = 'Tire uma foto da lista (ou cole o texto) pra eu montar o orçamento.'; return; }
    btEnviar.disabled = true; var k = 0; btEnviar.textContent = ETAPAS[0];
    var tm = setInterval(function(){ k = Math.min(k+1, ETAPAS.length-1); btEnviar.textContent = ETAPAS[k]; }, 3500);
    document.body.classList.add('lendo');
    CSA.trackC('EnviouLista', {arquivos:ARQS.length, texto:texto ? 1 : 0});
    fetch('/api/lista', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({arquivos:ARQS.map(function(a){ return {mime:a.mime, dados:a.dados}; }), texto:texto})})
      .then(function(r){ return r.json().catch(function(){ return {}; }).then(function(d){ if(!r.ok) throw (d.erro || 'Não consegui ler agora. Tente de novo.'); return d; }); })
      .then(function(d){
        if(!d.itens || !d.itens.length || d.legivel === false) throw 'Não achei itens de material nessa imagem. Tente uma foto mais de perto, com boa luz, ou cole o texto da lista.';
        var nome = (inNome.value || '').trim() || d.aluno || '';
        nome = nome.split(/\s+/)[0]; if(nome) nome = nome.charAt(0).toUpperCase() + nome.slice(1).toLowerCase();
        L = montar(d.itens, nome, d.serie || '');
        desenhar(); res.hidden = false; form.closest('.envio').classList.add('feito');
        res.scrollIntoView({behavior:'smooth', block:'start'});
        var t = total();
        CSA.trackC('ListaLida', {itens:d.itens.length, achados:L.linhas.filter(function(x){ return x.op.length; }).length, total:Math.round(t.v)});
        CSA.track('ViewContent', {content_name:'Orçamento de material escolar', content_type:'product_group', content_ids:L.linhas.filter(function(x){ return x.op.length; }).map(function(x){ return x.op[x.k].id; }).slice(0,40), value:Math.round(t.v), currency:'BRL'});
        if(CSA.hit) CSA.hit('lista', faixa(t.v)+' · '+d.itens.length+' itens');
      })
      .catch(function(e){ msg.textContent = typeof e === 'string' ? e : 'A conexão caiu. Tente de novo.'; })
      .then(function(){ clearInterval(tm); btEnviar.disabled = false; btEnviar.textContent = L ? 'Ler outra lista' : 'Montar meu orçamento'; document.body.classList.remove('lendo'); });
  });
  function faixa(v){ return v < 100 ? 'até R$ 100' : v < 200 ? 'R$ 100–200' : v < 350 ? 'R$ 200–350' : v < 500 ? 'R$ 350–500' : 'R$ 500+'; }

  // ---------------------------------------------------------------- casamento item -> produto
  function temDet(it, re){ return re.test(((it.det || '') + ' ' + (it.t || '')).toLowerCase()); }
  function opcoes(it){
    var c = (POR[it.tipo] || []).slice();
    if(!c.length) return [];
    var q = Math.max(1, it.q || 1);
    // quantidade de cores / folhas: igual, senão a mais próxima acima, senão a mais próxima
    function porAttr(lista, attr, alvo){
      if(!alvo) return lista;
      var com = lista.filter(function(p){ return p[attr]; }); if(!com.length) return lista;
      var igual = com.filter(function(p){ return p[attr] === alvo; }); if(igual.length) return igual;
      var acima = com.filter(function(p){ return p[attr] > alvo; });
      if(acima.length){ var m = Math.min.apply(null, acima.map(function(p){ return p[attr]; })); return acima.filter(function(p){ return p[attr] === m; }); }
      var mx = Math.max.apply(null, com.map(function(p){ return p[attr]; })); return com.filter(function(p){ return p[attr] === mx; });
    }
    c = porAttr(c, 'cores', it.cores);
    c = porAttr(c, 'folhas', it.folhas);
    var mat = (temDet(it, /(\d+)\s*mat[ée]ria/) && +((it.det + ' ' + it.t).toLowerCase().match(/(\d+)\s*mat[ée]ria/)[1])) || 0;
    if(mat) c = porAttr(c, 'materias', mat);
    // preferências por detalhe (filtro que relaxa se zerar)
    function pref(lista, cond){ var f = lista.filter(cond); return f.length ? f : lista; }
    if(it.tipo === 'lapis') c = temDet(it, /\b[2-8]b\b/) ? pref(c, function(p){ return p.b2; }) : pref(c, function(p){ return !p.b2; });
    if(it.tipo === 'lapis' || it.tipo === 'lapis_cor' || it.tipo === 'giz_cera') c = temDet(it, /jumbo|grosso|gizão|gizao|triangular/) ? pref(c, function(p){ return p.jumbo; }) : pref(c, function(p){ return !p.jumbo; });
    if(/caderno/.test(it.tipo)) c = temDet(it, /capa dura/) ? pref(c, function(p){ return p.capadura; }) : c;
    if(it.tipo === 'regua') c = temDet(it, /15\s*cm/) ? pref(c, function(p){ return p.cm === 15; }) : temDet(it, /20\s*cm/) ? pref(c, function(p){ return p.cm === 20; }) : pref(c, function(p){ return p.cm === 30; });
    if(it.tipo === 'cola_branca'){ var g = (it.det + ' ' + it.t).toLowerCase().match(/(\d{2,4})\s*g/); if(g) c = pref(c, function(p){ return p.g && p.g >= +g[1]; }); }
    if(it.tipo === 'sulfite_a3' || it.tipo === 'sulfite'){ /* folha a folha */ }
    if(it.tipo === 'mochila') c = temDet(it, /rodinha/) ? pref(c, function(p){ return p.rodinha; }) : pref(c, function(p){ return !p.rodinha; });
    return c.map(function(p){
      var pk = Math.ceil(q / (p.un || 1));
      return {p:p, pk:pk, custo:pk * p.preco, sobra:pk*(p.un||1) - q};
    }).sort(function(a, b){
      // mais barato no total; empate (até 5%) vai pra melhor nota e comissão
      var d = a.custo - b.custo;
      if(Math.abs(d) <= Math.max(a.custo, b.custo) * .05) return (b.p.nota - a.p.nota) || ((b.p.comissao||0) - (a.p.comissao||0)) || d;
      return d;
    });
  }
  function montar(itens, nome, serie){
    return {nome:nome, serie:serie, linhas:itens.map(function(it){ return {it:it, op:opcoes(it), k:0}; })};
  }
  function total(){
    var v = 0, n = 0, f = 0;
    L.linhas.forEach(function(x){ if(x.op.length){ v += x.op[x.k].custo; n++; } else f++; });
    return {v:v, n:n, f:f};
  }
  function buscaML(it){
    var t = (it.busca || it.t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9 ]/g,' ').trim().replace(/\s+/g,'-');
    var tp = TIPO[it.tipo]; if(tp && tp.busca) return tp.busca;
    return 'https://lista.mercadolivre.com.br/' + t;
  }

  // ---------------------------------------------------------------- resultado
  function titulo(){ return L.nome ? 'A lista do ' + L.nome : 'Sua lista de material'; }
  function linhaHTML(x, i){
    var it = x.it, tp = TIPO[it.tipo] || {emoji:'🔎', nome:'Outro'};
    if(!x.op.length){
      return '<li class="ln fora"><div class="ln-ic">'+(tp.emoji||'🔎')+'</div><div class="ln-tx"><p class="pediu">'+esc(it.t)+'</p>'+
        '<p class="nao">Não está no nosso catálogo. <a href="'+esc(buscaML(it))+'" target="_blank" rel="noopener sponsored" data-busca="'+esc(it.tipo)+'">Buscar no Mercado Livre</a></p></div></li>';
    }
    var o = x.op[x.k], p = o.p;
    var qtxt = o.pk > 1 ? o.pk + ' × ' : '';
    var sobra = o.sobra > 0 && p.un > 1 ? '<span class="sobra">vem '+(o.pk*p.un)+' '+(TIPO[p.tipo]||{}).unidade_pl+', pediu '+it.q+'</span>' : '';
    var troca = x.op.length > 1 ? '<button type="button" class="troca" data-troca="'+i+'">trocar ('+(x.op.length-1)+')</button>' : '';
    return '<li class="ln"><a class="ln-foto" href="'+esc(p.link)+'" target="_blank" rel="noopener sponsored" data-ml="'+p.id+'" data-origem="lista-foto"><img src="'+esc(p.imagem)+'" alt="" loading="lazy"></a>'+
      '<div class="ln-tx"><p class="pediu">'+esc(it.t)+'</p>'+
      '<p class="nome"><a href="'+esc(p.link)+'" target="_blank" rel="noopener sponsored" data-ml="'+p.id+'" data-origem="lista-nome">'+qtxt+esc(p.nome)+'</a></p>'+
      '<p class="meta">★ '+String(p.nota).replace('.',',')+(p.vendas?' · +'+esc(p.vendas)+' vendidos':'')+sobra+'</p>'+
      '<div class="ln-acao"><b class="preco">R$ '+brl(o.custo)+'</b>'+troca+
      '<a class="comprar" href="'+esc(p.link)+'" target="_blank" rel="noopener sponsored" data-ml="'+p.id+'" data-origem="lista-botao">Comprar</a></div></div></li>';
  }
  function desenhar(){
    var t = total();
    var ok = L.linhas.filter(function(x){ return x.op.length; }), fora = L.linhas.filter(function(x){ return !x.op.length; });
    res.innerHTML =
      '<div class="res-topo"><p class="eyebrow">'+(L.serie ? esc(L.serie)+' · ' : '')+L.linhas.length+' itens lidos</p>'+
      '<h2>'+esc(titulo())+' ficou <span class="total">R$ '+brl(t.v)+'</span></h2>'+
      '<p class="sub">'+t.n+' itens com o menor preço que achamos no Mercado Livre'+(t.f ? ' · '+t.f+' pra você buscar' : '')+'. Cada item tem seu botão: você abre, confere o preço do dia e põe no carrinho do ML.</p>'+
      '<div class="res-btns"><button type="button" class="btn wa compartilha">Mandar a lista no WhatsApp</button><button type="button" class="btn sec salva-img">Salvar imagem</button></div></div>'+
      '<ol class="linhas">'+L.linhas.map(function(x, i){ return x.op.length ? linhaHTML(x, i) : ''; }).join('')+'</ol>'+
      (fora.length ? '<h3 class="fora-tit">Pra buscar à parte</h3><ol class="linhas">'+L.linhas.map(function(x, i){ return x.op.length ? '' : linhaHTML(x, i); }).join('')+'</ol>' : '')+
      '<div class="res-fim"><p>Total aproximado <b>R$ '+brl(t.v)+'</b></p><p class="disc">Preços do Mercado Livre conferidos por nós e que mudam todo dia; o valor que vale é o do anúncio. Frete à parte (muitos têm frete grátis acima de R$ 79 no carrinho).</p>'+
      '<button type="button" class="btn wa compartilha">Mandar a lista no WhatsApp</button></div>';
    prepararImagem();
  }
  res.addEventListener('click', function(e){
    var b = e.target.closest('[data-troca]');
    if(b){ var x = L.linhas[+b.getAttribute('data-troca')]; x.k = (x.k + 1) % x.op.length; desenhar(); var li = res.querySelectorAll('[data-troca="'+b.getAttribute('data-troca')+'"]')[0]; if(li) li.closest('.ln').scrollIntoView({block:'center'}); return; }
    if(e.target.closest('.compartilha')) return compartilhar();
    if(e.target.closest('.salva-img')) return salvarImagem();
    var bu = e.target.closest('a[data-busca]'); if(bu){ CSA.trackC('BuscaForaCatalogo', {tipo:bu.getAttribute('data-busca')}); if(CSA.hit) CSA.hit('click', 'Busca: '+bu.getAttribute('data-busca')); }
  });

  // ---------------------------------------------------------------- compartilhar
  function textoLista(link){
    var t = total(), l = [];
    var cab = (L.nome ? '📚 A lista de material do '+L.nome : '📚 A lista de material') + ' ficou *R$ '+brl0(t.v)+'* lá no Oferta do Rafa!';
    if(link) l.push(cab, '👉 Veja e monte a sua: '+link, ''); else l.push(cab, '', 'Monte a sua: '+SITE, '');
    L.linhas.forEach(function(x){
      if(!x.op.length) return;
      var o = x.op[x.k], p = o.p, tp = TIPO[p.tipo] || {};
      l.push((tp.emoji||'•')+' *'+(o.pk > 1 ? o.pk+'× ' : '')+p.nome+'* · R$ '+brl(o.custo));
      l.push('👉 '+p.link);
    });
    var fora = L.linhas.filter(function(x){ return !x.op.length; });
    if(fora.length){ l.push('', '🔎 Pra buscar à parte:'); fora.forEach(function(x){ l.push('• '+x.it.t); }); }
    l.push('', '💰 *Total: R$ '+brl(t.v)+'*', '_Preços aproximados do Mercado Livre; o valor do dia aparece no anúncio._');
    if(link) l.push('', 'Tire uma foto da sua lista e veja quanto fica:', SITE);
    return l.join('\n');
  }
  var IMG_DATA = null, IMG_SEQ = 0, LISTA_ID = null;
  function carregar(src){ return new Promise(function(ok){ var im = new Image(); im.onload = function(){ ok(im); }; im.onerror = function(){ ok(null); }; im.src = src; }); }
  function rr(c, x, y, w, h, r){ c.beginPath(); c.moveTo(x+r,y); c.arcTo(x+w,y,x+w,y+h,r); c.arcTo(x+w,y+h,x,y+h,r); c.arcTo(x,y+h,x,y,r); c.arcTo(x,y,x+w,y,r); c.closePath(); }
  function destaques(){
    // principais itens: os de maior valor, um por tipo
    var vistos = {}, out = [];
    L.linhas.filter(function(x){ return x.op.length; }).slice().sort(function(a, b){ return b.op[b.k].custo - a.op[a.k].custo; }).forEach(function(x){
      var p = x.op[x.k].p; if(vistos[p.tipo] || out.length >= 6) return; vistos[p.tipo] = 1; out.push(x);
    });
    return out;
  }
  function prepararImagem(){
    var seq = ++IMG_SEQ; IMG_DATA = null; LISTA_ID = null;
    if(!window.HTMLCanvasElement) return;
    var ds = destaques(), t = total();
    var fontes = document.fonts ? Promise.all(['800 64px "Bricolage Grotesque"','700 40px Inter','600 30px Inter','600 40px Caveat'].map(function(f){ return document.fonts.load(f).catch(function(){}); })) : Promise.resolve();
    Promise.all([fontes].concat(ds.map(function(x){ return carregar(x.op[x.k].p.imagem); }))).then(function(r){
      if(seq !== IMG_SEQ) return;
      var fotos = r.slice(1), W = 1080, H = 1350, cv = document.createElement('canvas'); cv.width = W; cv.height = H;
      var c = cv.getContext('2d');
      // folha de caderno
      c.fillStyle = '#FBF8F1'; c.fillRect(0,0,W,H);
      c.strokeStyle = '#D6E2F3'; c.lineWidth = 2; for(var y = 60; y < H; y += 48){ c.beginPath(); c.moveTo(0,y); c.lineTo(W,y); c.stroke(); }
      c.strokeStyle = '#EE9A9A'; c.lineWidth = 3; c.beginPath(); c.moveTo(96,0); c.lineTo(96,H); c.stroke();
      c.fillStyle = '#1D3A8A'; c.font = '700 26px Inter, sans-serif'; c.fillText((L.serie ? L.serie.toUpperCase()+' · ' : '')+'LISTA DE MATERIAL', 130, 116);
      c.fillStyle = '#16213E'; c.font = '800 66px "Bricolage Grotesque", Inter, sans-serif';
      var tit = L.nome ? 'A lista do '+L.nome : 'Minha lista'; c.fillText(tit, 130, 196);
      c.font = '700 40px Inter, sans-serif'; c.fillStyle = '#3B4766'; c.fillText('ficou', 130, 262);
      var lw = c.measureText('ficou ').width;
      c.font = '800 46px Inter, sans-serif'; var tw = c.measureText('R$ '+brl0(t.v)).width;
      c.fillStyle = '#F6C343'; rr(c, 130+lw+2, 212, tw + 28, 66, 14); c.fill();
      c.fillStyle = '#16213E'; c.fillText('R$ '+brl0(t.v), 130+lw+16, 262);
      // grade de fotos
      var cx = 130, cy = 318, cw = W - 130 - 60, cols = 3, gap = 22, tw2 = (cw - gap*(cols-1))/cols;
      ds.forEach(function(x, k){
        var o = x.op[x.k], p = o.p, f = fotos[k], col = k % cols, lin = Math.floor(k / cols);
        var px = cx + col*(tw2+gap), py = cy + lin*(tw2 + 96 + gap);
        c.save(); c.shadowColor = 'rgba(22,33,62,.14)'; c.shadowBlur = 18; c.shadowOffsetY = 6; c.fillStyle = '#fff'; rr(c, px, py, tw2, tw2, 20); c.fill(); c.restore();
        c.save(); rr(c, px+10, py+10, tw2-20, tw2-20, 14); c.clip();
        if(f){ var s = Math.min((tw2-20)/f.width, (tw2-20)/f.height); c.drawImage(f, px+10+(tw2-20-f.width*s)/2, py+10+(tw2-20-f.height*s)/2, f.width*s, f.height*s); }
        c.restore();
        c.fillStyle = '#1D3A8A'; c.font = '700 21px Inter, sans-serif'; c.fillText(((TIPO[p.tipo]||{}).nome||'').toUpperCase().slice(0,22), px+4, py+tw2+34);
        c.fillStyle = '#16213E'; c.font = '700 32px Inter, sans-serif'; c.fillText('R$ '+brl(o.custo), px+4, py+tw2+74);
      });
      var resto = t.n - ds.length;
      c.fillStyle = '#3B4766'; c.font = '600 44px Caveat, cursive';
      c.fillText(resto > 0 ? '+ '+resto+' itens, tudo com link do Mercado Livre' : 'tudo com link do Mercado Livre', 130, 1176);
      c.fillStyle = '#1D3A8A'; rr(c, 60, 1222, W-120, 84, 24); c.fill();
      c.fillStyle = '#fff'; c.font = '700 31px Inter, sans-serif'; c.textAlign = 'center'; c.fillText('Mande a foto da sua: escolar.ofertadorafa.com.br', W/2, 1275); c.textAlign = 'left';
      try{ IMG_DATA = cv.toDataURL('image/jpeg', .84); }catch(e){ IMG_DATA = null; }
    });
  }
  function metaLista(){
    var t = total();
    return {nome:L.nome, total:Math.round(t.v),
      itens:L.linhas.filter(function(x){ return x.op.length; }).map(function(x){ var o = x.op[x.k]; return {id:o.p.id, q:o.pk, l:x.it.t}; }),
      fora:L.linhas.filter(function(x){ return !x.op.length; }).map(function(x){ return x.it.t; }),
      titulo:(L.nome ? 'A lista de material do '+L.nome : 'Lista de material escolar')+' ficou R$ '+brl0(t.v),
      resumo:t.n+' itens com link do Mercado Livre. Tire uma foto da sua lista e veja quanto fica.'};
  }
  function salvarLista(){
    if(LISTA_ID) return Promise.resolve(LISTA_ID);
    if(!IMG_DATA || !window.fetch) return Promise.reject();
    return fetch('/api/kit', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({img:IMG_DATA, kit:metaLista()})})
      .then(function(r){ if(!r.ok) throw r.status; return r.json(); }).then(function(d){ LISTA_ID = d.id; return d.id; });
  }
  function compartilhar(){
    CSA.trackC('CompartilhouLista', {total:Math.round(total().v)});
    var celular = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    var janela = celular ? null : window.open('about:blank', '_blank');
    var bts = res.querySelectorAll('.compartilha'); [].forEach.call(bts, function(b){ b.disabled = true; b.textContent = 'Abrindo o WhatsApp…'; });
    function ir(texto){
      var u = 'https://api.whatsapp.com/send?text='+encodeURIComponent(texto);
      if(janela){ janela.location = u; } else { location.href = u; }
      setTimeout(function(){ [].forEach.call(bts, function(b){ b.disabled = false; b.textContent = 'Mandar a lista no WhatsApp'; }); }, 1500);
    }
    var espera = IMG_DATA ? Promise.resolve() : new Promise(function(ok){ setTimeout(ok, 1200); });
    espera.then(salvarLista).then(function(id){ ir(textoLista(location.origin+'/api/k/'+id)); }, function(){ ir(textoLista(null)); });
  }
  function salvarImagem(){
    if(!IMG_DATA) return;
    var nomeArq = 'lista-de-material'+(L.nome ? '-'+L.nome.toLowerCase() : '')+'.jpg';
    fetch(IMG_DATA).then(function(r){ return r.blob(); }).then(function(bl){
      var f = new File([bl], nomeArq, {type:'image/jpeg'}), d = {files:[f]};
      if(navigator.canShare && navigator.canShare(d) && /Android|iPhone|iPad/i.test(navigator.userAgent)) return navigator.share(d).catch(function(){});
      var a = document.createElement('a'); a.href = IMG_DATA; a.download = nomeArq; document.body.appendChild(a); a.click(); a.remove();
    });
  }

  // ---------------------------------------------------------------- lista aberta por link: /?lista=xxxxxxxx
  function abrirCompartilhada(id){
    fetch('/api/k/'+id+'.json').then(function(r){ if(!r.ok) throw 0; return r.json(); }).then(function(m){
      var by = {}; P.forEach(function(p){ by[p.id] = p; });
      var linhas = (m.itens||[]).filter(function(i){ return by[i.id]; }).map(function(i){
        var p = by[i.id]; return {it:{t:i.l || p.nome, tipo:p.tipo, q:i.q*(p.un||1)}, op:[{p:p, pk:i.q, custo:i.q*p.preco, sobra:0}], k:0};
      }).concat((m.fora||[]).map(function(t){ return {it:{t:t, tipo:'outro', q:1, busca:t}, op:[], k:0}; }));
      if(!linhas.length) throw 0;
      L = {nome:m.nome || '', serie:'', linhas:linhas, compartilhada:true};
      desenhar(); res.hidden = false;
      var av = document.getElementById('aviso-comp'); if(av){ av.hidden = false; av.querySelector('b').textContent = L.nome ? 'Essa é a lista do '+L.nome+'.' : 'Essa é uma lista que te mandaram.'; }
      res.scrollIntoView({block:'start'});
      CSA.trackC('AbriuListaCompartilhada', {total:m.total||0});
      if(CSA.hit) CSA.hit('lista', 'Lista compartilhada aberta');
    }).catch(function(){});
  }
  var q = null; try{ q = new URLSearchParams(location.search); }catch(e){}
  var lid = q && (q.get('lista') || q.get('kit'));
  if(lid && /^[0-9a-f]{8}$/.test(lid)) abrirCompartilhada(lid);
})();
