/*
 * AJUSTE 2026-11-03 (JPC): protecao contra duplo clique em todas as telas (incluido nos templates base).
 * Trazido do NMV (caso real la: dois cliques no "Efetivar Apontamento" gravaram o mesmo controle duas vezes).
 * Neste projeto existem duas copias iguais: apontamento/static/js (desenvolvimento) e static/js (servida pelo nginx).
 *  - formulario enviado: botoes de envio desabilitados; o clicado mostra "Aguarde..." (o valor dele segue
 *    no envio). Envio cancelado (confirm "Cancelar", campo obrigatorio vazio) nao trava;
 *  - link com cara de botao (a.btn com endereco): cliques seguintes ignorados ate a pagina trocar;
 *  - fora: target=_blank, "#", javascript:, download/exportacao (Excel, PDF, CSV) e data-sem-trava;
 *  - libera ao voltar pelo navegador e, por seguranca, depois de 60 s (download que nao troca de pagina).
 */
(function () {
    'use strict';

    var TEXTO = 'Aguarde...';
    var LIBERA_MS = 60000;
    var EXPORTACAO = /(excel|exportar|export|xlsx|csv|pdf|download)/i;

    function marcar(el, rotulo) {
        if (el.getAttribute('data-travado') === '1') {
            return;
        }
        el.setAttribute('data-travado', '1');
        el.classList.add('disabled');
        el.setAttribute('aria-disabled', 'true');
        if (el.tagName === 'A') {
            el.style.pointerEvents = 'none';
        } else {
            el.disabled = true;
        }
        if (rotulo) {
            if (el.tagName === 'INPUT') {
                el.setAttribute('data-texto-original', el.value);
                el.value = TEXTO;
            } else {
                el.setAttribute('data-texto-original', el.innerHTML);
                el.innerHTML = TEXTO;
            }
        }
    }

    function liberar() {
        var travados = document.querySelectorAll('[data-travado="1"]');
        for (var i = 0; i < travados.length; i++) {
            var el = travados[i];
            var original = el.getAttribute('data-texto-original');
            if (original !== null) {
                if (el.tagName === 'INPUT') {
                    el.value = original;
                } else {
                    el.innerHTML = original;
                }
                el.removeAttribute('data-texto-original');
            }
            el.removeAttribute('data-travado');
            el.classList.remove('disabled');
            el.removeAttribute('aria-disabled');
            el.style.pointerEvents = '';
            if (el.tagName !== 'A') {
                el.disabled = false;
            }
        }
        var forms = document.querySelectorAll('form[data-enviando="1"]');
        for (var j = 0; j < forms.length; j++) {
            forms[j].removeAttribute('data-enviando');
        }
    }

    function exportacao(endereco) {
        return !!endereco && EXPORTACAO.test(endereco);
    }

    document.addEventListener('submit', function (e) {
        var form = e.target;
        if (e.defaultPrevented || form.hasAttribute('data-sem-trava') || form.target === '_blank'
                || exportacao(form.getAttribute('action'))) {
            return;
        }
        if (form.getAttribute('data-enviando') === '1') {
            e.preventDefault();  // 2o envio do mesmo formulario
            return;
        }
        form.setAttribute('data-enviando', '1');
        var clicado = e.submitter || null;
        if (clicado && (clicado.hasAttribute('data-sem-trava') || exportacao(clicado.getAttribute('formaction')))) {
            form.removeAttribute('data-enviando');
            return;
        }
        // depois do envio montado (setTimeout 0): desabilitar antes tiraria o botao clicado dos dados enviados
        setTimeout(function () {
            var botoes = form.querySelectorAll('button[type="submit"], button:not([type]), input[type="submit"]');
            for (var i = 0; i < botoes.length; i++) {
                if (!botoes[i].hasAttribute('data-sem-trava')) {
                    marcar(botoes[i], botoes[i] === clicado);
                }
            }
        }, 0);
        setTimeout(liberar, LIBERA_MS);
    });

    document.addEventListener('click', function (e) {
        var link = e.target.closest ? e.target.closest('a.btn') : null;
        if (!link || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) {
            return;
        }
        if (link.getAttribute('data-travado') === '1') {
            e.preventDefault();
            return;
        }
        var href = link.getAttribute('href');
        if (!href || href.charAt(0) === '#' || href.indexOf('javascript:') === 0 || link.target === '_blank'
                || link.hasAttribute('download') || link.hasAttribute('data-sem-trava')
                || link.hasAttribute('data-toggle') || link.hasAttribute('data-bs-toggle') || exportacao(href)) {
            return;
        }
        // depois dos outros handlers: confirm() cancelado nao trava
        setTimeout(function () {
            if (!e.defaultPrevented) {
                marcar(link, true);
                setTimeout(liberar, LIBERA_MS);
            }
        }, 0);
    });

    window.addEventListener('pageshow', function (e) {
        if (e.persisted) {
            liberar();  // voltou pelo navegador (pagina restaurada do cache)
        }
    });
}());
