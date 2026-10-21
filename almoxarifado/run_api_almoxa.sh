#!/bin/bash
# AJUSTE 2026-10-21: trava (flock), igual ao run_producao.sh -- impede execucoes sobrepostas
# do cron (a cada 10 min) do integracao.py contra o Oracle. flock -n desiste na hora se outra
# instancia ja estiver rodando. Volta a ser executavel (perdeu o +x no deploy de 06/10). - JPC - João Castro
exec flock -n /tmp/run_api_almoxa.lock bash -c '
#clear
cd /home/suporte/prod/almoxarifado
source /home/suporte/prod/prodenv/bin/activate
python3 integracao.py
deactivate
#clear
'
