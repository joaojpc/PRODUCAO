import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from oracle_connection import getOracleConnection
from url_projeto import geturlapp, geturlapi, geturlprod, geturlest, geturlinv
import os
print(os.path.abspath(__file__))
  # agora você pode importar arquivo_de_prod.py de prod/