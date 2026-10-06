# -*- coding: utf-8 -*-
# AJUSTE 2026-10-06: decorators copiados do projeto MP.
# Diferença: no MP o operador_required manda para 'login_operador' (app parada), que não
# existe aqui; no PRODUCAO o operador entra pelo login do apontamento ('demos_sessions').
from __future__ import unicode_literals
from functools import wraps
from django.shortcuts import redirect


def operador_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Usa sessão própria, não request.user
        if not request.session.get('usuario'):
            return redirect('demos_sessions')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def ordem_required(view_func):
    """
    Mesmo padrão de operador_required, mas para a sessão de apontamento
    (login por ordem via session_demo), que usa a chave 'ordem'.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('ordem'):
            return redirect('demos_sessions')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
