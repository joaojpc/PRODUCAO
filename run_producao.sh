#!/bin/bash
# AJUSTE 2026-10-06: trava (flock) copiada do projeto MP -- impede execucoes sobrepostas
# do cron (processos api_producao.py empilhados, todos integrando contra o Oracle ao mesmo
# tempo). flock -n desiste na hora se outra instancia ja estiver rodando. bash -c (e nao
# -c/dash) para o "source" do venv funcionar.
exec flock -n /tmp/run_producao.lock bash -c '
#clear
cd /home/suporte/prod
source /home/suporte/prod/prodenv/bin/activate
python3 api_producao.py
deactivate
#clear
'
