'''id_usuario = usuario
            id_ccusto = centrocusto
            v_params.append(usuario)
            v_params.append(centrocusto)
            #Busca Usuário
            v_usu = json.loads(lista_usuarios(usuario))
            for c_usu in v_usu:
                nomeusuario = c_usu['OPD_ST_NOME']
                filial = c_usu['FIL_IN_CODIGO']
                v_params.append(c_usu['FIL_IN_CODIGO'])
            #Formata os dados do código de barras da ordem;
            r_s = json.loads(formatar_ccusto(centrocusto))
            lis_ccusto = []
            for v_ord in r_s:
                request.session['ccusto'] = v_ord['reduzido']
                v_params.append(v_ord['reduzido'])
                lis_ccusto.append(v_ord['reduzido'])
                lis_ccusto.append(v_ord['padrao'])
                lis_ccusto.append(v_ord['extenso'])
                lis_ccusto.append(v_ord['tabela'])
                lis_ccusto.append(centrocusto)
            v_ret = json.loads(lista_ccusto(lis_ccusto))
            for v_rs in v_ret:
                ccustoDesc = v_rs['CUS_ST_DESCRICAO']
            #verifica se tem requisição em aberto para o usuário e centro de custos;
            cr_req = json.loads(buscarequisicao(v_params))
            if cr_req:
                for v_cur in cr_req:
                    v_req = v_cur['BXA_IN_SEQUENCIA']
            else:
                v_req = criarRequisicao(v_params)
            requisicao = v_req
            request.session['usuario'] = nomeusuario
            request.session['filial'] = filial
            request.session['ccustoDesc'] = ccustoDesc
            request.session['requisicao'] = requisicao
            request.session['idusuario'] = id_usuario
            request.session['idccusto'] = id_ccusto
        #print('Inválido')
    return render(request, template, {'title': 'Requisição de Estoque',
                                      'form': form,
                                      'requisicao': requisicao,
                                      'usuario':usuario,
                                      'filial':filial,
                                      'ccusto':ccusto,
                                      'ccustoDesc':ccustoDesc,
                                      })'''
