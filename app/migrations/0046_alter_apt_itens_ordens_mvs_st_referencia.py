# AJUSTE 2026-11-11 (JPC): MVS_ST_REFERENCIA em JSON, igual ao ZK (0048). So o tipo do campo no Django muda; o
# texto cru antigo continua legivel (app.services.referencia_padrao) e a sincronizacao nova normaliza.

import jsonfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0045_car_atributosreferencia_rat_ch_tipoconteudo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apt_itens_ordens',
            name='MVS_ST_REFERENCIA',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
    ]
