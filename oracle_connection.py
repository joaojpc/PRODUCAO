import oracledb as cxo
import platform
import sys
import os

nome_so = platform.system()
if nome_so == "Linux":
    # For Linux, specify the path to the Oracle Instant Client libraries
    cxo.init_oracle_client(lib_dir="/opt/oracle/instantclient_21_7")
elif nome_so == "Windows":
    cxo.init_oracle_client(lib_dir=r"C:\Client_Oracle\instantclient_19_27")
else:
    print("Unsupported operating system. Please use Linux or Windows.")
    sys.exit(1)
        
def getOracleConnection():
    username = 'idp'
    password = 'megamega'
    dsn = '10.101.235.105:1521/ORCL_gru1x6.subnetskydbindu.vcnrootautoskyo.oraclevcn.com'
    try:
        connection = cxo.connect(user=username, password=password, dsn=dsn)
        return connection
    
    except cxo.DatabaseError as e:
        print(f"Error connecting to Oracle Database: {e}")
        return None