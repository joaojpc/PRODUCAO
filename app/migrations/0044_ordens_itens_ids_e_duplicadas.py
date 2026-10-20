# AJUSTE 2026-10-20 (JPC): migracao SO de dados, para a Sincronizar Ordens (nova). Sem troca de PK
# (decisao do usuario): apt_pro_ordens e apt_itens_ordens seguem com PK TAB_IN_SEQUENCIA.
#  1) ORD_ST_ID (apt_pro_ordens) e PRO_ST_ID (apt_itens_ordens) vazios sao montados com as colunas
#     da chave (mesmo formato de apontamento.api_view.monta_ordem / monta_produto e do lpad do
#     Oracle; copiado aqui para a migracao nao depender do codigo). Linhas antigas (TAB 1201-1409
#     no banco local) foram gravadas sem os IDs -- a rotina nova as duplicaria.
#  2) Linhas duplicadas na mesma chave saem; fica a MAIS NOVA (maior TAB_IN_SEQUENCIA), que e a
#     ultima baixa do Mega e a que o Reglote ja usa hoje (prepara_apontamento fica com a ultima).
# Escrita a mao (sem AlterField): roda igual em qualquer versao do Django. Nao tem volta automatica
# (noop) -- fazer backup do producao.db antes do migrate.

from django.db import migrations


def _monta_ordem(org_tab, org_pad, org_in, org_tau, ord_tab, ord_seq, ord_in):
    return (str(org_tab).zfill(3) + str(org_pad).zfill(3) + str(org_in).zfill(7) + str(org_tau).zfill(3) +
            str(ord_tab).zfill(3) + str(ord_seq).zfill(3) + str(ord_in).zfill(20))


def _monta_produto(pro_tab, pro_pad, pro_in):
    return str(pro_tab).zfill(3) + str(pro_pad).zfill(3) + str(pro_in).zfill(7)


def preencher_e_deduplicar(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        # 1) IDs vazios
        cur.execute("SELECT TAB_IN_SEQUENCIA, ORG_TAB_IN_CODIGO, ORG_PAD_IN_CODIGO, ORG_IN_CODIGO, "
                    "ORG_TAU_ST_CODIGO, ORD_TAB_IN_CODIGO, ORD_SEQ_IN_CODIGO, ORD_IN_CODIGO "
                    "FROM apt_pro_ordens WHERE ORD_ST_ID IS NULL OR TRIM(ORD_ST_ID) = ''")
        for tab, *chave in cur.fetchall():
            cur.execute('UPDATE apt_pro_ordens SET ORD_ST_ID = %s WHERE TAB_IN_SEQUENCIA = %s',
                        [_monta_ordem(*chave), tab])
        cur.execute("SELECT TAB_IN_SEQUENCIA, PRO_TAB_IN_CODIGO, PRO_PAD_IN_CODIGO, PRO_IN_CODIGO "
                    "FROM apt_itens_ordens WHERE PRO_ST_ID IS NULL OR TRIM(PRO_ST_ID) = ''")
        for tab, *chave in cur.fetchall():
            cur.execute('UPDATE apt_itens_ordens SET PRO_ST_ID = %s WHERE TAB_IN_SEQUENCIA = %s',
                        [_monta_produto(*chave), tab])
        # 2) duplicadas: fica a mais nova
        cur.execute('DELETE FROM apt_pro_ordens WHERE TAB_IN_SEQUENCIA NOT IN '
                    '(SELECT MAX(TAB_IN_SEQUENCIA) FROM apt_pro_ordens GROUP BY ORD_ST_ID)')
        cur.execute('DELETE FROM apt_itens_ordens WHERE TAB_IN_SEQUENCIA NOT IN '
                    '(SELECT MAX(TAB_IN_SEQUENCIA) FROM apt_itens_ordens GROUP BY PRO_ST_ID)')


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0043_apt_apontaordem_gravacao_oracle'),
    ]

    operations = [
        migrations.RunPython(preencher_e_deduplicar, migrations.RunPython.noop),
    ]
