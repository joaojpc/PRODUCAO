#!/bin/bash
clear
cd /home/suporte/prod/almoxarifado
source /home/suporte/prod/prodenv/bin/activate
python3 integracao.py
deactivate
clear
