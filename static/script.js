(function () {
  'use strict';

  var CHAVE = 'ceu-prefs';
  var FONTE_MIN = 80, FONTE_MAX = 160, PASSO = 10;
  var estado = { contraste: false, fonte: 100 };

  function carregar() {
    try {
      var salvo = JSON.parse(localStorage.getItem(CHAVE));
      if (salvo) {
        estado.contraste = !!salvo.contraste;
        estado.fonte = Math.min(FONTE_MAX, Math.max(FONTE_MIN, Number(salvo.fonte) || 100));
      }
    } catch (e) { /* armazenamento indisponível: usa padrão */ }
  }
  function salvar() {
    try { localStorage.setItem(CHAVE, JSON.stringify(estado)); } catch (e) {}
  }
  function aplicar() {
    document.body.classList.toggle('alto-contraste', estado.contraste);
    document.documentElement.style.setProperty('--fonte-base', estado.fonte + '%');
    var btn = document.getElementById('btn-contraste');
    if (btn) btn.setAttribute('aria-pressed', String(estado.contraste));
  }
  function alternarContraste() { estado.contraste = !estado.contraste; aplicar(); salvar(); }
  function mudarFonte(delta) {
    estado.fonte = Math.min(FONTE_MAX, Math.max(FONTE_MIN, estado.fonte + delta * PASSO));
    aplicar(); salvar();
  }

  function cpfValido(valor) {
    var c = valor.replace(/\D/g, '');
    if (c.length !== 11 || /^(\d)\1{10}$/.test(c)) return false;
    for (var t = 9; t < 11; t++) {
      var soma = 0;
      for (var i = 0; i < t; i++) soma += Number(c[i]) * (t + 1 - i);
      var dv = ((soma * 10) % 11) % 10;
      if (dv !== Number(c[t])) return false;
    }
    return true;
  }
  function mascararCpf(v) {
    v = v.replace(/\D/g, '').slice(0, 11);
    return v.replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  }
  function erro(campo, idErro, msg) {
    var p = document.getElementById(idErro);
    campo.setAttribute('aria-invalid', msg ? 'true' : 'false');
    p.textContent = msg || '';
    p.hidden = !msg;
    return !msg;
  }

  function carregarLista(url, idContainer, campoBadge) {
    var box = document.getElementById(idContainer);
    fetch(url).then(function (r) { return r.json(); }).then(function (itens) {
      box.textContent = '';
      if (!itens.length) { box.textContent = 'Nenhum item publicado no momento.'; return; }
      itens.forEach(function (it) {
        var card = document.createElement('article'); card.className = 'card';
        var b = document.createElement('span'); b.className = 'badge'; b.textContent = it[campoBadge];
        var h = document.createElement('h3'); h.textContent = it.titulo;
        var p = document.createElement('p'); p.textContent = it.texto;
        card.append(b, h, p); box.appendChild(card);
      });
    }).catch(function () { box.textContent = 'Não foi possível carregar. Tente recarregar a página.'; });
  }

  document.addEventListener('DOMContentLoaded', function () {
    carregar(); aplicar();
    document.getElementById('btn-contraste').addEventListener('click', alternarContraste);
    document.getElementById('btn-fonte-mais').addEventListener('click', function () { mudarFonte(1); });
    document.getElementById('btn-fonte-menos').addEventListener('click', function () { mudarFonte(-1); });

    var form = document.getElementById('form-cadastro');
    var nome = document.getElementById('nome-completo');
    var cpf = document.getElementById('cpf-municipe');
    var aceite = document.getElementById('consentimento');
    var status = document.getElementById('status-form');

    cpf.addEventListener('input', function () { cpf.value = mascararCpf(cpf.value); });

    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      status.textContent = '';
      var ok = [
        erro(nome, 'erro-nome', nome.value.trim().split(/\s+/).length < 2 ? 'Informe o nome e o sobrenome.' : ''),
        erro(cpf, 'erro-cpf', cpfValido(cpf.value) ? '' : 'Informe um CPF válido.'),
        erro(aceite, 'erro-consent', aceite.checked ? '' : 'Marque a autorização para continuar.')
      ];
      var primeiro = [nome, cpf, aceite][ok.indexOf(false)];
      if (primeiro) { primeiro.focus(); return; }
      fetch('/api/municipes', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome: nome.value.trim(), cpf: cpf.value, consentimento: aceite.checked })
      }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (res) {
          if (res.ok) { status.textContent = 'Cadastro realizado com sucesso.'; form.reset(); return; }
          var e = res.j.erros || {};
          erro(cpf, 'erro-cpf', e.cpf || '');
          erro(nome, 'erro-nome', e.nome || '');
          erro(aceite, 'erro-consent', e.consentimento || '');
          status.textContent = 'Não foi possível cadastrar. Corrija os campos indicados.';
        })
        .catch(function () { status.textContent = 'Servidor indisponível. Tente novamente em instantes.'; });
    });

    carregarLista('/api/avisos', 'lista-avisos', 'unidade');
    carregarLista('/api/eventos', 'lista-eventos', 'categoria');

    var formAviso = document.getElementById('form-aviso');
    var statusAviso = document.getElementById('status-aviso');
    formAviso.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var dados = {
        unidade: document.getElementById('av-unidade').value,
        titulo: document.getElementById('av-titulo').value,
        texto: document.getElementById('av-texto').value
      };
      fetch('/api/avisos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Token': document.getElementById('av-token').value },
        body: JSON.stringify(dados)
      }).then(function (r) {
        if (r.status === 201) {
          statusAviso.textContent = 'Aviso publicado.'; formAviso.reset();
          carregarLista('/api/avisos', 'lista-avisos', 'unidade');
        } else if (r.status === 401) { statusAviso.textContent = 'Código de acesso incorreto.'; }
        else { statusAviso.textContent = 'Preencha unidade, título e texto.'; }
      }).catch(function () { statusAviso.textContent = 'Servidor indisponível.'; });
    });
  });
})();
