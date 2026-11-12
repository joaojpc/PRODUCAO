# -*- coding: utf-8 -*-
"""
AJUSTE 2026-11-11 (JPC): decisao do usuario -- "itens ja existentes deverao ser atualizados, inclusive ordens nao
encerradas no Mega". Script de atualizacao em massa pela rotina nova de sincronizacao (app/sincronizacao.py):

  1. normaliza o JSON dos itens gravados no padrao antigo (uma vez, so o formato muda);
  2. para CADA ordem do app que NAO esta encerrada no Mega (apt_intprod2.f_valida_sitordem <> 'EN'): le no Mega e
     atualiza ordem, itens e caracteristicas -- so o que estiver diferente (INSERT do novo, UPDATE das colunas
     diferentes); ordem encerrada no Mega fica como esta;
  3. atualiza o tipo (RAT_CH_TIPOCONTEUDO) de todas as caracteristicas do app (uma leitura so).

Erros cercados: falha numa OP nao derruba as outras (vai para o resumo e para logs/integracao.log); sem conexao com
o Mega, nada e gravado. Uma conexao Oracle so (with). Nada e gravado no Mega.

Uso (no servidor, dentro de ~/prod):
    prodenv/bin/python manage.py atualizar_ordens_mega --simular      # so compara, nao grava nada
    prodenv/bin/python manage.py atualizar_ordens_mega                # grava
    prodenv/bin/python manage.py atualizar_ordens_mega --filial 3 --ordem 69205
Fazer backup do producao.db antes de gravar.
"""
import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Atualiza pelo Mega as ordens do app nao encerradas no Mega, com itens e caracteristicas (rotina nova).'

    def add_arguments(self, parser):
        parser.add_argument('--simular', action='store_true', help='so compara; nada e gravado')
        parser.add_argument('--filial', type=int, help='so esta filial')
        parser.add_argument('--ordem', type=int, help='so esta ordem')

    def handle(self, *args, **opcoes):
        from app import sincronizacao
        from app.models import apt_pro_ordens
        gravar = not opcoes['simular']
        inicio = time.perf_counter()
        resumo = {'ordens_app': 0, 'encerradas_mega': 0, 'atualizadas': 0, 'iguais': 0, 'novas': 0,
                  'itens_diferentes': 0, 'itens_novos': 0, 'itens_normalizados': 0, 'caracteristicas_tipo': 0,
                  'erros': []}

        ordens = apt_pro_ordens.objects.all()
        if opcoes.get('filial'):
            ordens = ordens.filter(FIL_IN_CODIGO=opcoes['filial'])
        if opcoes.get('ordem'):
            ordens = ordens.filter(ORD_IN_CODIGO=opcoes['ordem'])
        pares = sorted({(o.FIL_IN_CODIGO, o.ORD_IN_CODIGO) for o in ordens.only('FIL_IN_CODIGO', 'ORD_IN_CODIGO')
                        if o.FIL_IN_CODIGO and o.ORD_IN_CODIGO})
        resumo['ordens_app'] = len(pares)
        self.stdout.write(f"{'SIMULACAO (nada sera gravado)' if not gravar else 'GRAVANDO'} -- {len(pares)} ordem(ns) no app")

        con = sincronizacao.conexao_oracle_testada(timeout=15)
        if not con:
            self.stderr.write('Sem conexao com o Oracle (Mega). Nada foi feito.')
            self._registrar(resumo, gravar, 'sem conexao com o Mega')
            return
        with con:
            if gravar:
                resumo['itens_normalizados'], erros = sincronizacao.normalizar_itens_existentes()
                resumo['erros'] += erros
            for n, (fil, ord_) in enumerate(pares, 1):
                try:
                    if self._encerrada(con, fil, ord_):
                        resumo['encerradas_mega'] += 1
                        continue
                    r = sincronizacao.sincronizar_ordens(sincronizacao.org_da_filial(fil), fil, ord_, 'N',
                                                         conexao=con, gravar=gravar, normalizar=False, tipos=False)
                    if r.get('erro_conexao'):
                        resumo['erros'].append(f'OP {ord_} (filial {fil}): {r["erro_conexao"]}')
                        continue
                    for o in r.get('ordens', []):
                        chave = {'diferente': 'atualizadas', 'igual': 'iguais', 'nova': 'novas'}.get(o.get('situacao'))
                        if chave:
                            resumo[chave] += 1
                    itens = r.get('itens') or {}
                    resumo['itens_diferentes'] += len(itens.get('diferentes', []))
                    resumo['itens_novos'] += itens.get('novos', 0)
                    resumo['erros'] += [f'OP {ord_} (filial {fil}): {e}' for e in r.get('erros', [])]
                except Exception as e:  # erro cercado: segue para a proxima OP
                    resumo['erros'].append(f'OP {ord_} (filial {fil}): {e}')
                if n % 50 == 0:
                    self.stdout.write(f'  ... {n}/{len(pares)}')
            fil_tipos = opcoes.get('filial') or (pares[0][0] if pares else None)
            if fil_tipos is not None:
                try:
                    resumo['caracteristicas_tipo'], erros = sincronizacao.atualizar_tipos_caracteristicas(
                        con, fil_tipos, gravar=gravar)
                    resumo['erros'] += erros
                except Exception as e:
                    resumo['erros'].append(f'Tipo das características: {e}')

        resumo['tempo_s'] = round(time.perf_counter() - inicio, 1)
        for k in ('ordens_app', 'encerradas_mega', 'novas', 'atualizadas', 'iguais', 'itens_novos', 'itens_diferentes',
                  'itens_normalizados', 'caracteristicas_tipo', 'tempo_s'):
            self.stdout.write(f'{k:22} {resumo[k]}')
        for e in resumo['erros'][:50]:
            self.stderr.write(f'ERRO: {e}')
        if len(resumo['erros']) > 50:
            self.stderr.write(f"... mais {len(resumo['erros']) - 50} erro(s) -- ver logs/integracao.log")
        self._registrar(resumo, gravar)

    @staticmethod
    def _encerrada(con, fil, ord_):
        with con.cursor() as cur:
            return cur.callfunc('apt_intprod2.f_valida_sitordem', str, [int(fil), int(ord_)]) == 'EN'

    @staticmethod
    def _registrar(resumo, gravar, erro=None):
        try:
            from apontamento.integracao_apontamento import registrar_evento
            registrar_evento('atualizar_ordens_mega', erro=erro or (resumo['erros'][:20] or None),
                             gravado=gravar, **{k: v for k, v in resumo.items() if k != 'erros'})
        except Exception:
            pass
