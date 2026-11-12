# AJUSTE 2026-11-11 (JPC): tipo do conteudo da caracteristica vindo do Mega ('N' = numerico), igual ao ZK (0047).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0044_ordens_itens_ids_e_duplicadas'),
    ]

    operations = [
        migrations.AddField(
            model_name='car_atributosreferencia',
            name='RAT_CH_TIPOCONTEUDO',
            field=models.CharField(blank=True, max_length=1, null=True, verbose_name='Tipo_Conteudo'),
        ),
    ]
