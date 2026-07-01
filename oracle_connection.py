import oracledb as cxo
import platform
_oracle_inited = False

def _init_oracle():
    global _oracle_inited
    if _oracle_inited: 
        return
    if platform.system() == "Linux":
        cxo.init_oracle_client(lib_dir="/opt/oracle/instantclient_21_7")
    elif platform.system() == "Windows":
        cxo.init_oracle_client(lib_dir=r"C:\Client_Oracle\instantclient_19_27")
    _oracle_inited = True
        
def getOracleConnection():
    _init_oracle() # só inicia aqui
    return cxo.connect(
        user='idp', 
        password='megamega', 
        dsn='10.101.235.105:1521/ORCL_gru1x6.subnetskydbindu.vcnrootautoskyo.oraclevcn.com'
    )