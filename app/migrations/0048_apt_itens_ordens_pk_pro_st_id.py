# AJUSTE 2026-11-11 (JPC): decisao do usuario -- apt_itens_ordens passa a ter PK = PRO_ST_ID (igual ao NMV/ZK).
# Antes da troca, por seguranca (a 0044 ja faz isso): PRO_ST_ID nulo/vazio e montado com PRO_TAB/PAD/IN (mesmo
# formato de apontamento.api_view.monta_produto) e as linhas duplicadas saem -- fica a MAIS NOVA (maior
# TAB_IN_SEQUENCIA), regra do PRODUCAO. Escrita a mao. Sem volta: backup do producao.db antes do migrate.

from django.db import migrations, models


def _monta_produto(pro_tab, pro_pad, pro_in):
    return str(pro_tab).zfill(3) + str(pro_pad).zfill(3) + str(pro_in).zfill(7)


def preencher_e_deduplicar(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("SELECT TAB_IN_SEQUENCIA, PRO_TAB_IN_CODIGO, PRO_PAD_IN_CODIGO, PRO_IN_CODIGO "
                    "FROM apt_itens_ordens WHERE PRO_ST_ID IS NULL OR TRIM(PRO_ST_ID) = ''")
        for tab, *chave in cur.fetchall():
            cur.execute('UPDATE apt_itens_ordens SET PRO_ST_ID = %s WHERE TAB_IN_SEQUENCIA = %s',
                        [_monta_produto(*chave), tab])
        cur.execute('DELETE FROM apt_itens_ordens WHERE TAB_IN_SEQUENCIA NOT IN '
                    '(SELECT MAX(TAB_IN_SEQUENCIA) FROM apt_itens_ordens GROUP BY PRO_ST_ID)')


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0047_apt_pro_ordens_pk_ord_st_id'),
    ]

    operations = [
        migrations.RunPython(preencher_e_deduplicar, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='apt_itens_ordens',
            name='TAB_IN_SEQUENCIA',
        ),
        migrations.AlterField(
            model_name='apt_itens_ordens',
            name='PRO_ST_ID',
            field=models.CharField(default=None, max_length=13, primary_key=True, serialize=False,
                                   verbose_name='ITEM'),
            preserve_default=False,
        ),
    ]
