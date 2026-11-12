# AJUSTE 2026-11-11 (JPC): decisao do usuario -- apt_pro_ordens passa a ter PK = ORD_ST_ID (igual ao NMV/ZK).
# Antes da troca, por seguranca (a 0044 ja faz isso): ORD_ST_ID nulo/vazio e montado com as 7 colunas da chave
# (mesmo formato de apontamento.api_view.monta_ordem, copiado aqui para a migracao nao depender do codigo) e as
# linhas duplicadas saem -- fica a MAIS NOVA (maior TAB_IN_SEQUENCIA), regra do PRODUCAO (0044; no ZK fica a
# menor). Escrita a mao. Sem volta: backup do producao.db antes do migrate.

from django.db import migrations, models


def _monta_ordem(org_tab, org_pad, org_in, org_tau, ord_tab, ord_seq, ord_in):
    return (str(org_tab).zfill(3) + str(org_pad).zfill(3) + str(org_in).zfill(7) + str(org_tau).zfill(3) +
            str(ord_tab).zfill(3) + str(ord_seq).zfill(3) + str(ord_in).zfill(20))


def preencher_e_deduplicar(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("SELECT TAB_IN_SEQUENCIA, ORG_TAB_IN_CODIGO, ORG_PAD_IN_CODIGO, ORG_IN_CODIGO, "
                    "ORG_TAU_ST_CODIGO, ORD_TAB_IN_CODIGO, ORD_SEQ_IN_CODIGO, ORD_IN_CODIGO "
                    "FROM apt_pro_ordens WHERE ORD_ST_ID IS NULL OR TRIM(ORD_ST_ID) = ''")
        for tab, *chave in cur.fetchall():
            cur.execute('UPDATE apt_pro_ordens SET ORD_ST_ID = %s WHERE TAB_IN_SEQUENCIA = %s',
                        [_monta_ordem(*chave), tab])
        cur.execute('DELETE FROM apt_pro_ordens WHERE TAB_IN_SEQUENCIA NOT IN '
                    '(SELECT MAX(TAB_IN_SEQUENCIA) FROM apt_pro_ordens GROUP BY ORD_ST_ID)')


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0046_alter_apt_itens_ordens_mvs_st_referencia'),
    ]

    operations = [
        migrations.RunPython(preencher_e_deduplicar, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='apt_pro_ordens',
            name='TAB_IN_SEQUENCIA',
        ),
        migrations.AlterField(
            model_name='apt_pro_ordens',
            name='ORD_ST_ID',
            field=models.CharField(default=None, max_length=44, primary_key=True, serialize=False,
                                   verbose_name='ORDEM'),
            preserve_default=False,
        ),
    ]
