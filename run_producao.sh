#!/bin/bash
#clear
cd /home/suporte/prod
source /home/suporte/prod/prodenv/bin/activate
python3 api_producao.py
deactivate
#clear
