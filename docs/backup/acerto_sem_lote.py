# Acerto 23/11/2026 JPC: exclui os movimentos sem lote de um documento/produto (Excluirmovimento do Mega)
# e refaz o saldo do produto pelos lotes (p_refazsaldoestoquefil, 'N'); tudo numa transacao, commit so' se conferir.
import sys, time
sys.path.insert(0, '/home/suporte/prod')
from oracle_connection import getOracleConnection
doc, pro = sys.argv[1], int(sys.argv[2])
MANCO = """from est_movimento m where m.mvt_st_numdoc = :doc and m.fil_in_codigo = 3 and m.pro_in_codigo = :pro
           and not exists (select 1 from est_lotesmovimento l where l.org_tab_in_codigo=m.org_tab_in_codigo and l.org_pad_in_codigo=m.org_pad_in_codigo
               and l.org_in_codigo=m.org_in_codigo and l.org_tau_st_codigo=m.org_tau_st_codigo and l.ser_tab_in_codigo=m.ser_tab_in_codigo
               and l.ser_in_sequencia=m.ser_in_sequencia and l.mvt_in_lancam=m.mvt_in_lancam)"""
with getOracleConnection() as con:
    cur = con.cursor()
    def saldo():
        cur.execute("""select alm_in_codigo, loc_in_codigo, nat_st_codigo, sum(mvs_re_quantidade) from est_movsumarizado
                        where fil_in_codigo=3 and pro_in_codigo=:p group by alm_in_codigo, loc_in_codigo, nat_st_codigo order by 1,2,3""", p=pro)
        return {(a, l, n): q for a, l, n, q in cur}
    def mancos():
        cur.execute(f"select m.org_in_codigo, m.ser_in_sequencia, m.mvt_in_lancam {MANCO}", doc=doc, pro=pro)
        return cur.fetchall()
    antes = saldo(); lista = mancos()
    print(f"{doc} item {pro}: {len(lista)} movimento(s) sem lote; saldo antes {antes}", flush=True)
    t = time.time()
    try:
        for i, (org, ser, lan) in enumerate(lista, 1):
            cur.callproc("idp.adm_pck_movimentoestoque.Excluirmovimento", [org, ser, lan])
            if i % 200 == 0: print(f"  excluidos {i} ({time.time()-t:.0f}s)", flush=True)
        cur.execute("begin p_refazsaldoestoquefil(pfil_in => 3, ppro_pad => 1, ppro_cod => :p, pcontrolatransacao => 'N'); end;", p=pro)
        depois = saldo(); resto = mancos()
        print(f"  saldo depois {depois}; sem lote restantes {len(resto)} ({time.time()-t:.0f}s)", flush=True)
        # saldo do lote nao pode mudar (os sem lote nunca mexeram nele) e o kardex tem que bater com o saldo
        mudou = {k: (antes.get(k), depois.get(k)) for k in set(antes) | set(depois) if abs((antes.get(k) or 0) - (depois.get(k) or 0)) > 1e-6}
        cur.execute("select nvl(sum(decode(substr(mvt_st_entrsaida,1,1),'E',1,-1)*mvt_re_quantidade),0) from est_movimento where fil_in_codigo=3 and pro_in_codigo=:p", p=pro)
        kardex = cur.fetchone()[0]; total = sum(depois.values())
        print(f"  kardex (movimentos) = {kardex}; saldo (lotes) = {total}", flush=True)
        if not resto and not mudou and abs(kardex - total) < 1e-6:
            con.commit(); print("  COMMIT", flush=True)
        else:
            con.rollback(); print(f"  ROLLBACK: restantes={len(resto)} mudou={mudou} kardex={kardex} saldo={total}", flush=True)
    except Exception as e:
        con.rollback(); print("  ERRO -> ROLLBACK:", str(e)[:500], flush=True)
