# -*- coding: utf-8 -*-
"""
services.py - acesso ao banco (SQL puro) para o fechamento diário de OP.
AJUSTE 2026-10-06: copiado do projeto MP (oee/services.py), sem pendente e sem romaneio.
Tabelas: Apt_Controle (campos FEC_*), Apt_ApontaOrdem, Apt_Pro_Demandas, apt_pro_ordens.
Função burra: só select/update. Regra de negócio fica na classe Fechamento (api_view.py).
"""
from datetime import timedelta
from django.db import connection, transaction
from django.utils import timezone


def dia_util_anterior(data):
    """Último dia útil antes de 'data', pulando sábado/domingo (regra do NMV)."""
    anterior = data - timedelta(days=1)
    while anterior.weekday() >= 5:  # 5=sabado, 6=domingo
        anterior -= timedelta(days=1)
    return anterior


class controle_db:
    def _exec(self, query, params=None):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query, params or [])
                return cursor.rowcount

    def _fetch_all(self, query, params=None):
        with connection.cursor() as cursor:
            cursor.execute(query, params or [])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _fetch_one(self, query, params=None):
        res = self._fetch_all(query, params)
        return res[0] if res else None

    def _fetch_val(self, query, params=None):
        with connection.cursor() as cursor:
            cursor.execute(query, params or [])
            row = cursor.fetchone()
            return row[0] if row else None

    def get_controle_ativo_ordem(self, fil_in_codigo, ord_in_codigo, ctl_in_codigo):
        controle = self._fetch_one(
            "SELECT * FROM Apt_Controle WHERE CTL_IN_CODIGO = %s and CTL_ST_STATUS = 'A'",
            [ctl_in_codigo]
        )
        if controle:
            return controle

        return self._fetch_one(
            """SELECT * FROM Apt_Controle
            WHERE FIL_IN_CODIGO = %s
                AND ORD_IN_CODIGO = %s
                AND CTL_ST_STATUS = 'A'
            ORDER BY CTL_DT_LOGIN DESC, FEC_HR_INICIO DESC
            LIMIT 1""",
            [fil_in_codigo, ord_in_codigo])

    def ordem_existe(self, ord_in_codigo):
        return self._fetch_val("SELECT COUNT(*) FROM apt_pro_ordens WHERE ORD_IN_CODIGO =%s", [ord_in_codigo]) > 0

    def get_ordem_info(self, fil_in_codigo, ord_in_codigo):
        return self._fetch_all("SELECT * FROM apt_pro_ordens WHERE FIL_IN_CODIGO =%s AND ORD_IN_CODIGO =%s",
                               [fil_in_codigo, ord_in_codigo])

    def get_totais_dia(self, pdados):
        """
        Produzida: Apt_ApontaOrdem com APT_CH_STATUS 'A' (aberto) ou 'I' (integrado) - ignora cancelado.
        Demandas: Apt_Pro_Demandas com MOV_ST_STATUS diferente de 'C' (cancelado).
        """
        fil_in_codigo = pdados.get('filial')
        ord_in_codigo = pdados.get('ordem')
        data_apontamento = pdados.get('data_apontamento')
        if hasattr(data_apontamento, 'date'):
            data_apontamento = data_apontamento.date()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(SUM(ORL_RE_QTDLOTE), 0)
                FROM Apt_ApontaOrdem
                WHERE ORD_IN_CODIGO = %s AND FIL_IN_CODIGO = %s
                  AND APT_CH_STATUS IN ('A', 'I')
                  AND date(APT_DT_APONTAMENTO) = %s
            """, [ord_in_codigo, fil_in_codigo, data_apontamento])
            total_prod = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM(d.PRO_RE_QTDLOTE), 0)
                FROM Apt_Pro_Demandas d
                WHERE d.ORD_IN_CODIGO = %s AND d.FIL_IN_CODIGO = %s
                  AND d.MOV_ST_STATUS <> 'C'
                  AND d.MOV_DT_INCLUSAO = %s
            """, [ord_in_codigo, fil_in_codigo, data_apontamento])
            total_dem = cursor.fetchone()[0]

        return {
            'produzida': total_prod,
            'demandas': total_dem,
        }

    def criar_fechamento(self, dados):
        str_now = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')

        total_produzido = float(dados.get('total_produzido', 0) or 0)
        total_demandas = float(dados.get('total_demandas', 0) or 0)

        ctl_in_codigo = dados.get('ctl_in_codigo') or dados.get('CTL_IN_CODIGO')
        if not ctl_in_codigo:
            raise ValueError('CTL_IN_CODIGO não informado para fechar esta OP')

        query = """UPDATE Apt_Controle
                SET CTL_DT_LOGOUT = %s,
                    CTL_ST_STATUS = 'F',
                    CTL_RE_TOTAL_PROD = %s,
                    FEC_DT_APONTAMENTO = %s,
                    FEC_HR_INICIO = %s,
                    FEC_HR_FIM = %s,
                    FEC_RE_QTD_PRODUZIDA = %s,
                    FEC_RE_QTD_DEMANDAS = %s,
                    FEC_USU_INCLUSAO = %s,
                    FEC_DT_INCLUSAO = %s,
                    FEC_IN_TEMPO_TOTAL = %s,
                    FEC_IN_TEMPO_LIQUIDO = %s,
                    FEC_IN_DESC_CAFE = %s,
                    FEC_IN_DESC_ALMOCO = %s
                WHERE CTL_IN_CODIGO = %s"""

        self._exec(query, [
            str_now,
            dados.get('ctl_re_total_prod', total_produzido),
            dados.get('data_apontamento'),
            dados.get('hr_inicio'),
            dados.get('hr_fim'),
            total_produzido,
            total_demandas,
            dados.get('usuario'),
            str_now,
            dados.get('tempo_total_minutos'),
            dados.get('tempo_liquido_minutos'),
            dados.get('desconto_cafe_minutos'),
            dados.get('desconto_almoco_minutos'),
            ctl_in_codigo,
        ])

    def alinhar_demandas_do_controle(self, ctl_in_codigo, data_para):
        """Demandas do controle passam a ter a data do fechamento. Retorna linhas alteradas."""
        return self._exec(
            "UPDATE Apt_Pro_Demandas SET MOV_DT_INCLUSAO=%s WHERE CTL_IN_CODIGO=%s AND MOV_DT_INCLUSAO<>%s",
            [data_para, ctl_in_codigo, data_para],
        )

    def alinhar_lotes_do_controle(self, ctl_in_codigo, data_para):
        """Lotes apontados do controle passam a ter a data do fechamento. Retorna linhas alteradas."""
        return self._exec(
            "UPDATE Apt_ApontaOrdem SET APT_DT_APONTAMENTO=%s WHERE CTL_IN_CODIGO=%s AND APT_DT_APONTAMENTO<>%s",
            [data_para, ctl_in_codigo, data_para],
        )
