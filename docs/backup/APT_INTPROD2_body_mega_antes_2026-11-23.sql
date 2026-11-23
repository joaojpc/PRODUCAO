PACKAGE BODY APT_INTPROD2 is

  -- Private type declarations
vTAB_APT IDP.apt_apontaordem%rowtype;
vAPT_LOTE IDP.apt_apontaordem_lote%rowtype;
vAPT_SUB pro_ordemlotesub%rowtype;
vAPT_DEM IDP.apt_apontademanda_estoque%rowtype;
vTAB_DEP pro_demanda_dep%rowtype;
vTAB_DDE IDP.apt_apontademanda%rowtype;
vTAB_CFM apt_pro_maquina_config%rowtype;
--vTAB_MVT est_movimento%rowtype;
--vTAB_MVL est_lotesmovimento%rowtype;
vTAB_APO pro_apontaordem%rowtype;
vTAB_PRG pro_prog_ordem%rowtype;
vTAB_ORD pro_ordens%rowtype;
vTAB_TPO pro_tipoordens%rowtype;
vTAB_TMO pro_tipomovto%rowtype;
vTAB_REF pro_apontarefugo%rowtype;
vTAB_SUP pro_ordemsubprod%rowtype;
vTAB_PRO est_produtos%rowtype;
vTAB_EMM pro_estmovtomanuf%rowtype;
vTAB_MVF pro_movtomanuf%rowtype;
vTAB_REQ IDP.apt_pro_requisicao%rowtype;
vTAB_REI IDP.apt_pro_itensrequisicao%rowtype;
vTAB_CFG IDP.apt_baixatipomovto_config%rowtype;
vTAB_SDT IDP.apt_baixatipomovto_config%rowtype;
vTAB_PRL est_produtolocaliza%rowtype;
vTAB_MVS est_movsumarizado%rowtype;
vTAB_INV IDP.apt_pro_inventario%rowtype;
vTAB_IIT IDP.apt_pro_itensinventario%rowtype;
vTAB_CAL cus_tb_api_almoxloc%rowtype;
vMVS est_movsumarizado%rowtype;
vOCE  pro_ordenscmpesp%rowtype;
vTAB_OS cus_tb_osmovimento%rowtype;
v_Encerra char(1);
vTAB_PAR est_parametros%rowtype;
vTAB_LOC est_produtolocaliza%rowtype;
v_apontamento char(1);
vTAB_WS ws_coletor_app%rowtype;
vTAB_IVA est_inventario%rowtype;
vTAB_AVR cus_tb_api_avisoreceb%rowtype;
vAVR cus_tb_api_avisoreceb%rowtype;
vTAB_AVI cus_tb_api_itensavisoreceb%rowtype;
vTAB_AVL cus_tb_api_lotesavisoreceb%rowtype;
vTAB_ORG glo_vw_organizacao%rowtype;
vPRO_PAD_IN_CODIGO est_produtos.pro_pad_in_codigo%type;
vRCI cli_aviso_receb_item_lote%rowtype;


procedure Inicializa is
  begin
      -- se houver, apaga todos os registros da coleção de lotes auxiliar para os movimentos como reserva on-line.
      if (vTAB_MVT is not null) and (vTAB_MVT.count > 0) then
         vTAB_MVT.delete;
      end if;
      if (vTAB_MVL is not null) and (vTAB_MVL.count > 0) then
         vTAB_MVL.delete;
      end if;
      -- zera a variável da coleção de movimento de estoque.
      vTAB_MVT := Est_Typ_Movestoquetab();
      -- zera a variável da coleção de lotes do movimento.
      vTAB_MVL := Est_Typ_Lotesmovtab();
      vTAB_CFG:= null;
      vTAB_SDT:= null;
      vTAB_CFG:= null;
      vTAB_PRO:= null;
      vTAB_PRL:= null;
      vTAB_MVS:= null;
      
  end Inicializa;
  function f_origemlote(pfil_in_codigo in number,
                      pmvs_st_lote in varchar2) return char is
  vORIGEM char(2);
  begin
     vpro_pad_in_codigo:=pck_mega.achapadraodatabela(pfil_in_codigo,100,sysdate);
     vORIGEM := 'N'; -- Não Encontrado   
     -- Busca o saldo na tabela movsumarizado;
     for cMVS in(
        select mvs.*
          from est_movsumarizado mvs
         where mvs.fil_in_codigo = pfil_in_codigo
           and mvs.mvs_st_loteforne = pmvs_st_lote
           and mvs.pro_pad_in_codigo = vpro_pad_in_codigo
          
        )
     loop
        return('ES'); -- estoque
     end loop;   
     -- Busca o na tabela do aviso customizado filial 3;
     if pfil_in_codigo = 3 then
        for cMVS in(
           select lot.*
             from cli_aviso_receb_item_lote lot,
                  cli_aviso_receb_item itn                
            where lot.org_tab_in_codigo = itn.org_tab_in_codigo
              and lot.org_pad_in_codigo = itn.org_pad_in_codigo
              and lot.org_in_codigo     = itn.org_in_codigo    
              and lot.org_tau_st_codigo = itn.org_tau_st_codigo
              and lot.avr_in_codigo     = itn.avr_in_codigo    
              and lot.iar_in_sequencia  = itn.iar_in_sequencia 
              and lot.mvl_st_loteforne  = pmvs_st_lote
              and itn.pro_pad_in_codigo = vpro_pad_in_codigo
              and not exists
                  (select 1
                     from est_lotesmovimento mvl,
                          est_movimento mvt
                    where mvl.org_tab_in_codigo = mvt.org_tab_in_codigo
                      and mvl.org_pad_in_codigo = mvt.org_pad_in_codigo
                      and mvl.org_in_codigo     = mvt.org_in_codigo
                      and mvl.org_tau_st_codigo = mvt.org_tau_st_codigo
                      and mvl.ser_tab_in_codigo = mvt.ser_tab_in_codigo
                      and mvl.ser_in_sequencia  = mvt.ser_in_sequencia
                      and mvl.mvt_in_lancam     = mvt.mvt_in_lancam
                      and mvl.org_tab_in_codigo = itn.org_tab_in_codigo
                      and mvl.org_pad_in_codigo = itn.org_pad_in_codigo
                      and mvl.org_in_codigo     = itn.org_in_codigo
                      and mvl.org_tau_st_codigo = itn.org_tau_st_codigo
                      and mvl.pro_tab_in_codigo = itn.pro_tab_in_codigo
                      and mvl.pro_pad_in_codigo = itn.pro_pad_in_codigo
                      and mvl.pro_in_codigo     = itn.pro_in_codigo
                      and mvl.mvl_st_loteforne  = lot.mvl_st_loteforne)          
           )
        loop
           return('AV');-- Aviso
        end loop;
        -- Estoque não disponível
        for cMVT in(   
           select 1
             from est_lotesmovimento mvl,
                  est_movimento mvt
            where mvl.org_tab_in_codigo = mvt.org_tab_in_codigo
              and mvl.org_pad_in_codigo = mvt.org_pad_in_codigo
              and mvl.org_in_codigo     = mvt.org_in_codigo
              and mvl.org_tau_st_codigo = mvt.org_tau_st_codigo
              and mvl.ser_tab_in_codigo = mvt.ser_tab_in_codigo
              and mvl.ser_in_sequencia  = mvt.ser_in_sequencia
              and mvl.mvt_in_lancam     = mvt.mvt_in_lancam
              and mvt.mvt_st_entrsaida  = 'ED'
              and mvl.fil_in_codigo = pfil_in_codigo
              and mvl.mvl_st_loteforne = pmvs_st_lote
              and mvl.pro_pad_in_codigo = vpro_pad_in_codigo
             order by mvl.mvl_in_sequencia 
             fetch first row only)
        loop
           return('ND');
        end loop;         
     end if; 
     return(vORIGEM);
  end f_origemlote;
  Procedure p_saldolote(pfil_in_codigo in number,
                      pmvs_st_lote in varchar2,
                      pRESULT IN OUT SYS_REFCURSOR
                      ) is
  vORIGEM char(2);                      
  vTAM_LOTE number;                       
                        
  begin
     vORIGEM := f_origemlote(pfil_in_codigo,pmvs_st_lote);
     vTAM_LOTE := length(pmvs_st_lote);
     if vpro_pad_in_codigo is null then
        vpro_pad_in_codigo:=pck_mega.achapadraodatabela(pfil_in_codigo,100,sysdate);
     end if;
     if vORIGEM = 'ES' then
        open pRESULT for
            select mvs.pro_tab_in_codigo,
                   mvs.pro_pad_in_codigo,
                   mvs.pro_in_codigo,
                   pro.pro_st_descricao,
                   sum(mvs.mvs_re_quantidade)mvs_re_quantidade
              from idp.est_movsumarizado mvs,
                   idp.est_produtos pro
             where pro.pro_tab_in_codigo = mvs.pro_tab_in_codigo
               and pro.pro_pad_in_codigo = mvs.pro_pad_in_codigo
               and pro.pro_in_codigo     = mvs.pro_in_codigo
               and mvs.fil_in_codigo     = pfil_in_codigo
               and (
                      (vTAM_LOTE = 22 and
                       pro.pro_bo_controlalotes = 'S' and 
                       mvs.mvs_st_loteforne = pmvs_st_lote)
                    or(vTAM_LOTE < 13 and 
                       pro.pro_bo_controlalotes = 'S' and
                       mvs.mvs_st_loteforne like '%' || pmvs_st_lote)
                    
                    or(vTAM_LOTE = 13 and
                       pro.pro_bo_controlalotes = 'N' and 
                       lpad(mvs.pro_tab_in_codigo,3,'0')||
                       lpad(mvs.pro_pad_in_codigo,3,'0')||
                       lpad(mvs.pro_in_codigo,7,'0') = pmvs_st_lote) 
                       
                    or (pro.pro_bo_controlalotes = 'N' and 
                        mvs.pro_in_codigo = pmvs_st_lote)                                       
                    )
              and mvs.pro_pad_in_codigo = vPRO_PAD_IN_CODIGO
                  
            group by mvs.pro_tab_in_codigo,
                  mvs.pro_pad_in_codigo,
                  mvs.pro_in_codigo,
                  pro.pro_st_descricao;
     elsif vORIGEM = 'AV' and pfil_in_codigo = 3 then
        open pRESULT for 
            select itn.pro_tab_in_codigo,
                 itn.pro_pad_in_codigo,
                 itn.pro_in_codigo,
                 pro.pro_st_descricao,
                 sum(lot.iar_re_quantconf)mvs_re_quantidade
              from cli_aviso_receb_item_lote lot,
                   cli_aviso_receb_item itn,
                   est_produtos pro
          where itn.pro_tab_in_codigo = pro.pro_tab_in_codigo
            and itn.pro_pad_in_codigo = pro.pro_pad_in_codigo
            and itn.pro_in_codigo     = pro.pro_in_codigo
            and lot.org_tab_in_codigo = itn.org_tab_in_codigo
            and lot.org_pad_in_codigo = itn.org_pad_in_codigo
            and lot.org_in_codigo     = itn.org_in_codigo    
            and lot.org_tau_st_codigo = itn.org_tau_st_codigo
            and lot.avr_in_codigo     = itn.avr_in_codigo    
            and lot.iar_in_sequencia  = itn.iar_in_sequencia             
            and itn.pro_pad_in_codigo = vpro_pad_in_codigo
            and (
                    (vTAM_LOTE = 22 and
                     pro.pro_bo_controlalotes = 'S' and 
                     lot.mvl_st_loteforne = pmvs_st_lote)
                  or(vTAM_LOTE < 13 and 
                     pro.pro_bo_controlalotes = 'S' and
                     lot.mvl_st_loteforne like '%' || pmvs_st_lote)
                )
           group by itn.pro_tab_in_codigo,
                itn.pro_pad_in_codigo,
                itn.pro_in_codigo,
                pro.pro_st_descricao;
     elsif vORIGEM = 'ND' and pfil_in_codigo = 3 then
        open pRESULT for
           select mvl.pro_tab_in_codigo,
                 mvl.pro_pad_in_codigo,
                 mvl.pro_in_codigo,
                 pro.pro_st_descricao,
                 0 mvs_re_quantidade
            from est_lotesmovimento mvl,
                 est_movimento mvt,
                 est_produtos pro
           where mvl.org_tab_in_codigo = mvt.org_tab_in_codigo
             and mvl.org_pad_in_codigo = mvt.org_pad_in_codigo
             and mvl.org_in_codigo     = mvt.org_in_codigo
             and mvl.org_tau_st_codigo = mvt.org_tau_st_codigo
             and mvl.ser_tab_in_codigo = mvt.ser_tab_in_codigo
             and mvl.ser_in_sequencia  = mvt.ser_in_sequencia
             and mvl.mvt_in_lancam     = mvt.mvt_in_lancam
             and pro.pro_tab_in_codigo = mvt.pro_tab_in_codigo
             and pro.pro_pad_in_codigo = mvt.pro_pad_in_codigo
             and pro.pro_in_codigo     = mvt.pro_in_codigo            
             and mvt.mvt_st_entrsaida  = 'ED'
             and mvt.pro_pad_in_codigo = vPRO_PAD_IN_CODIGO 
             and (
                    (vTAM_LOTE = 22 and
                     pro.pro_bo_controlalotes = 'S' and 
                     mvl.mvl_st_loteforne = pmvs_st_lote)
                  or(vTAM_LOTE < 13 and 
                     pro.pro_bo_controlalotes = 'S' and
                     mvl.mvl_st_loteforne like '%' || pmvs_st_lote)
                )
                        
         order by mvl.mvl_in_sequencia 
           fetch first row only;
     elsif vORIGEM = 'N' then
        open pRESULT for
           select 0 pro_tab_in_codigo,
                  0 pro_pad_in_codigo,
                  0 pro_in_codigo,
                 'Item Não Encontrado' pro_st_descricao,
                  0 mvs_re_quantidade
            from dual;
                 
     end if;
  end;
  function f_saldolote(pfil_in_codigo in number,
                       pmvs_st_lote in varchar2)
                       return number is
  v_SLD TCURSOR;
  begin
     p_saldolote(pfil_in_codigo,pmvs_st_lote,v_SLD);
     loop
        fetch v_SLD into vSLD;
        exit when v_SLD%notfound;
        dbms_output.put_line(vSLD.pro_in_codigo || ' - ' || vSLD.mvs_re_quantidade);
     end loop;     
     close v_SLD;
     return vSLD.mvs_re_quantidade; 
  end f_saldolote;
  
  procedure p_carregaorg(pFIL in number) is
  begin
     for cORG in(
        select org.*
          from glo_vw_organizacao org
         where org.ORG_IN_CODIGO = pFIL
        )
     loop
        vTAB_ORG := cORG;
     end loop;
  end p_carregaorg;
  procedure Addmov(Vtabmov in out nocopy Est_Typ_Movestoquetab) is
  begin
    -- adiciona um registro na coleção.
    Vtabmov.extend;
    -- zera os valores da coleção para receber valores.
    Vtabmov(Vtabmov.last) := Est_Typ_Movestoque(null, --ORG_TAB_IN_CODIGO NUMBER(3)
                                                      null, --ORG_PAD_IN_CODIGO NUMBER(3)
                                                      null, --ORG_IN_CODIGO NUMBER(7)
                                                      null, --ORG_TAU_ST_CODIGO VARChAR2(3)
                                                      null, --SER_TAB_IN_CODIGO NUMBER(3)
                                                      null, --SER_IN_SEQUENCIA NUMBER(3)
                                                      null, --MVT_IN_LANCAM NUMBER(8)
                                                      null, --FIL_IN_CODIGO NUMBER(7)
                                                      null, --ACAO_TAB_IN_CODIGO NUMBER(3)
                                                      null, --ACAO_PAD_IN_CODIGO NUMBER(3)
                                                      null, --ACAO_IN_CODIGO NUMBER(3)
                                                      null, --ACAOM_IN_SEQUENCIA NUMBER(20)
                                                      null, --MVT_CH_ORIGEM VARCHAR2(1)
                                                      null, --TPM_TAB_IN_CODIGO NUMBER(3)
                                                      null, --TPM_PAD_IN_CODIGO NUMBER(3)
                                                      null, --TPM_IN_CODIGO NUMBER(3)
                                                      null, --MVT_ST_ENTRSAIDA VARCHAR2(2)
                                                      null, --MVT_ST_NUMDOC VARCHAR2(20)
                                                      null, --MVT_DT_DOCUMENTO DATE
                                                      null, --MVT_DT_MOVIMENTO DATE
                                                      null, --USU_IN_INCLUSAO NUMBER(5)
                                                      null, --MVT_DT_INCLUSAO DATE
                                                      null, --USU_IN_ALTERA NUMBER(5)
                                                      null, --MVT_DT_ALTERA DATE
                                                      null, --MVT_IN_VINCULO NUMBER(9)
                                                      null, --PRO_TAB_IN_CODIGO NUMBER(3)
                                                      null, --PRO_PAD_IN_CODIGO NUMBER(3)
                                                      null, --PRO_IN_CODIGO NUMBER(7)
                                                      --VMP 11/03/2013 PM744372
                                                      null, --PRO_ST_ALTERNATIVO VARCHAR2(50)
                                                      null, --APL_TAB_IN_CODIGO NUMBER(3)
                                                      null, --APL_PAD_IN_CODIGO NUMBER(3)
                                                      null, --APL_IN_CODIGO NUMBER(3)
                                                      null, --MVT_RE_QUANTIDADE NUMBER(15,3)
                                                      null, --MVT_RE_AQUISICAO NUMBER
                                                      null, --MVT_RE_VLUNITARIO NUMBER
                                                      null, --ALM_PAD_IN_CODIGO NUMBER(3)
                                                      null, --ALM_IN_CODIGO NUMBER(6)
                                                      null, --ALM_TAB_IN_CODIGO NUMBER(3)
                                                      null, --LOC_IN_CODIGO NUMBER(6)
                                                      null, --MVT_ST_DOCOFS VARCHAR2(8)
                                                      null, --MVS_IN_RESERVA NUMBER(20)
                                                      null, --MVS_IN_RESERVADEST NUMBER(20)
                                                      null, --PRO_IN_CODIGODEST NUMBER(7)
                                                      --VMP 11/03/2013 PM744372
                                                      null, --PRO_ST_ALTERNATIVODEST VARCHAR2(50)
                                                      null, --APL_IN_CODIGODEST NUMBER(3)
                                                      null, --MVT_RE_QUANTIDADEDEST NUMBER(15,3)
                                                      null, --MVT_RE_QUANTIDADEMOV NUMBER(15,3)
                                                      null, --MVT_RE_AQUISICAODEST NUMBER
                                                      null, --MVT_BO_PENDENTE VARCHAR2(1)
                                                      null, --NAT_TAB_IN_CODIGO NUMBER(3)
                                                      null, --NAT_PAD_IN_CODIGO NUMBER(3)
                                                      null, --NAT_ST_CODIGO VARCHAR2(3)
                                                      null, --NAT_ST_CODIGODEST VARCHAR2(3)
                                                      null, --ALM_IN_CODIGODEST NUMBER(6)
                                                      null, --LOC_IN_CODIGODEST NUMBER(6)
                                                      null, --TPM_IN_CODIGODEST NUMBER(3)
                                                      null, --AGN_IN_CODIGODEST NUMBER(7)
                                                      null, --IRE_CH_TIPORESERVA VARCHAR2(2)
                                                      null, --CUS_TAB_IN_CODIGO NUMBER(3)
                                                      null, --CUS_PAD_IN_CODIGO NUMBER(3)
                                                      null, --CUS_IDE_ST_CODIGO VARCHAR2(5)
                                                      null, --CUS_IN_REDUZIDO NUMBER(7)
                                                      --VMP 11/03/2013 PM744372
                                                      null, --CUS_ST_EXTENSO VARCHAR2(25),
                                                      null, --CUS_ST_APELIDO VARCHAR2(15),
                                                      null, --PROJ_TAB_IN_CODIGO NUMBER(3)
                                                      null, --PROJ_PAD_IN_CODIGO NUMBER(3)
                                                      null, --PROJ_IDE_ST_CODIGO VARCHAR2(5)
                                                      null, --PROJ_IN_REDUZIDO NUMBER(7)
                                                      --VMP 11/03/2013 PM744372
                                                      null, --PROJ_ST_EXTENSO VARCHAR2(25),
                                                      null, --PROJ_ST_APELIDO VARCHAR2(20),
                                                      null, --AGN_TAB_IN_CODIGO NUMBER(3)
                                                      null, --AGN_PAD_IN_CODIGO NUMBER(3)
                                                      null, --AGN_IN_CODIGO NUMBER(7)
                                                      null, --AGN_TAU_ST_CODIGO VARCHAR2(3)
                                                      NULL, --CFOP_TAB_IN_CODIGO NUMBER(3)
                                                      NULL, --CFOP_PAD_IN_CODIGO NUMBER(3)
                                                      NULL, --CFOP_IDE_ST_CODIGO VARCHAR2(5)
                                                      NULL, --CFOP_IN_CODIGO NUMBER(4)
                                                      NULL, --MVT_BO_CONTROLATERCEIRO VARCHAR2(1)
                                                      null, --MVT_BO_SALDONEG VARCHAR2(1)
                                                      null, --MIE_IN_SEQMATTITDOC NUMBER()
                                                      NULL, --MIE_IN_SEQMATTITDOCDEST NUMBER()
                                                      null, --FRO_SEQ_IN_CODIGO NUMBER(3)
                                                      null, --OSERV_IN_NUMERO NUMBER(10)
                                                      -- DSP 21/07/2010 PM442761 - Adicionando campos referente a departamento
                                                      Null, --ORF_TAB_IN_CODIGO NUMBER(3)
                                                      Null, --ORF_PAD_IN_CODIGO NUMBER(3)
                                                      Null, --ORF_IDE_ST_CODIGO VARCHAR2(5)
                                                      Null, --ORF_IN_REDUZIDO NUMBER(4)
                                                      NULL, -- MVT_ST_ORIGEMPROCESSO VARCHAR2(1)
                                                      -- MKL 31/01/12 PM265855 - Adicionado campo referente a Observação de Movimentação.
                                                      NULL, -- MVT_ST_OBSERVACAO CLOB
                                                      -- GGB 27/03/2013 PM755704 - Adicionado o campo de vínculo com orçamento de obra.
                                                      NULL,--ROC_IN_SEQUENCIA NUMBER(10)
                                                      NULL,--MVT_BO_VALIDAALMOXUSU VARCHAR2(1)
                                                      NULL,--MVT_DT_MOVIMENTOOLD PMAT-1791
                                                      NULL,
                                                      null,
                                                      null,
                                                      null,
                                                      null); --MVT_BO_ATUALIZAACAOMOV PMCQ-2864
  end Addmov;
  procedure Addlotesmov(Vtabitem in out nocopy Est_Typ_Lotesmovtab) is
  begin
    -- cria um registro em branco na coleção.
    Vtabitem.extend;
    -- zera as colunas da coleção.
    Vtabitem(Vtabitem.last) := Est_Typ_Lotesmov(null, --IID NUMBER(7)
                                                      null, --MVL_IN_SEQUENCIA NUMBER(20)
                                                      null, --ORG_TAB_IN_CODIGO NUMBER(3)
                                                      null, --ORG_PAD_IN_CODIGO NUMBER(3)
                                                      null, --ORG_IN_CODIGO NUMBER(7)
                                                      null, --ORG_TAU_ST_CODIGO VARCHAR2(3)
                                                      null, --SER_TAB_IN_CODIGO NUMBER(3)
                                                      null, --SER_IN_SEQUENCIA NUMBER(3)
                                                      null, --MVT_IN_LANCAM NUMBER(8)
                                                      null, --FIL_IN_CODIGO NUMBER(7)
                                                      null, --MVL_ST_LOTEFORNE VARCHAR2(50)
                                                      null, --MVT_DT_MOVIMENTO DATE
                                                      null, --MVT_DT_VALIDADE DATE
                                                      null, --PRO_TAB_IN_CODIGO NUMBER(3)
                                                      null, --PRO_PAD_IN_CODIGO NUMBER(3)
                                                      null, --PRO_IN_CODIGO NUMBER(7)
                                                      null, --PRO_ST_ALTERNATIVO VARCHAR2(50)
                                                      null, --ALM_TAB_IN_CODIGO NUMBER(3)
                                                      null, --ALM_PAD_IN_CODIGO NUMBER(3)
                                                      null, --ALM_IN_CODIGO NUMBER(6)
                                                      null, --LOC_IN_CODIGO NUMBER(6)
                                                      null, --MVL_RE_QUANTIDADE NUMBER(15 3)
                                                      null, --MVL_RE_SALDO NUMBER(15 3)
                                                      null, --NAT_TAB_IN_CODIGO NUMBER(3)
                                                      null, --NAT_PAD_IN_CODIGO NUMBER(3)
                                                      null, --NAT_ST_CODIGO VARCHAR2(3)
                                                      null, --MVL_DT_ENTRADA DATE
                                                      null, --MVL_IN_RESERVA NUMBER(20)
                                                      null, --MVL_ST_REFERENCIA VARCHAR2(1400)
                                                      null, --MVL_RE_QTDERESERVA NUMBER(15 3)
                                                      null, --PRO_IN_CODIGODEST NUMBER(7)
                                                      null, --PRO_ST_ALTERNATIVODEST VARCHAR2(50)
                                                      null, --MVS_IN_RESERVADEST NUMBER(20)
                                                      null, --NAT_ST_CODIGODEST VARCHAR2(3)
                                                      null, --NAT_CH_TIPO VARCHAR2(2)
                                                      null, --MIE_IN_SEQMATTITDOC NUMBER()
                                                      null, --MIE_IN_SEQMATTITDOCDEST NUMBER()
                                                      null, --AGN_TAB_IN_CODIGO NUMBER(3)
                                                      null, --AGN_PAD_IN_CODIGO NUMBER(3)
                                                      null, --AGN_IN_CODIGO NUMBER(7)
                                                      null, --AGN_TAU_ST_CODIGO VARCHAR2(3)
                                                      null);--AGN_IN_CODIGODEST NUMBER(7)

    -- atribui sequencia na coleção.
    Vtabitem(Vtabitem.last).Iid := Vtabitem.last;
  end;


procedure apt_retornacaracteristica (pFIL_IN_CODIGO NUMBER,
                                     pPRO_IN_CODIGO NUMBER,
                                     pRESULT            IN OUT SYS_REFCURSOR) is


begin
--Raise_application_error(-20000, pFIL_IN_CODIGO);
open pRESULT for

SELECT a.RAT_IN_CODIGO,
       a.RAT_ST_OPCOES,
       replace(REPLACE(REPLACE(REPLACE(A.RAT_ST_ITENS,', ',';'),',','.'),';',','),'c','c') ITN_DESC,
        REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(A.RAT_ST_DESCRICAO,'.',''),'i','I'),'e','e'),'c','c'),' ','_') RAT_DESC,
        a.RAT_CH_TIPO,
        CASE WHEN A.RAT_CH_TIPO = 'P' THEN
                lpad(a.rat_in_codigo,7,'0')||'='||a.rat_in_codigo
             ELSE lpad(a.rat_in_codigo,7,'0')||'='
             END AS REF_RAT_VALUE,
        a.RFC_IN_CODIGO,
 ROWNUM AS RAT_IN_SEQUENCIA
   FROM    IDP.APT_VW_CARACTERISTICA A
   WHERE A.RFC_IN_CODIGO     =
         (SELECT P.RFC_IN_CODIGO
            FROM EST_PRODUTOS P
           WHERE P.RFC_TAB_IN_CODIGO  = A.RFC_TAB_IN_CODIGO
             AND P.RFC_PAD_IN_CODIGO  = A.RFC_PAD_IN_CODIGO
             AND P.RFC_IN_CODIGO      = A.RFC_IN_CODIGO
             AND P.PRO_PAD_IN_CODIGO = PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO, 100, SYSDATE)
             AND P.PRO_IN_CODIGO      = pPRO_IN_CODIGO

         );

END apt_retornacaracteristica;

procedure apt_retornaDemandaDisp(pFIL_IN_CODIGO NUMBER,
                                 pORD_IN_CODIGO NUMBER,
                                 pRESULT            IN OUT SYS_REFCURSOR) is
begin
   --Raise_application_error(-20000, pFIL_IN_CODIGO ||'-'||pORD_IN_CODIGO);
   open pRESULT for
      select produtos.* from
      (
      select mvs.pro_in_codigo,
             pro.pro_st_descricao,
             mvs.mvs_re_quantidade,
             mvs.mvs_st_loteforne,
             substr(adm_pck_util.f_formatacaract(mvs.mvs_st_referencia),1,200) mvs_st_referenciadesc,
             /*NVL(mvs.mvs_re_quantidade/
             IDP.cli_pck_especificosmanuf.f_converteunidade(mvs.pro_pad_in_codigo,
                                                              mvs.pro_in_codigo,
             IDP.cli_pck_especificosmanuf .cli_f_conversor(mvs.pro_pad_in_codigo,
                                                            mvs.pro_in_codigo,
                                                            mvs.mvs_st_loteforne),
                                                            1),0)*/ 0 conversor,
             mvs.mvs_st_referencia
        from est_movsumarizado mvs,
             est_produtos pro
       where pro.pro_tab_in_codigo = mvs.pro_tab_in_codigo
         and pro.pro_pad_in_codigo = mvs.pro_pad_in_codigo
         and pro.pro_in_codigo = mvs.pro_in_codigo
--         and length(mvs.mvs_st_loteforne) = 22
--         and rownum < 2
         and exists
             (select *
                from pro_demanda_dep dep
               where dep.com_tab_in_codigo = mvs.pro_tab_in_codigo
                 and dep.com_pad_in_codigo = mvs.pro_pad_in_codigo
                 and dep.com_in_codigo     = mvs.pro_in_codigo
                 and dep.ord_in_codigo     = pORD_IN_CODIGO
                 and dep.com_pad_in_codigo = pck_mega.achapadraodatabela(pFIL_IN_CODIGO,100,sysdate)

              )
      union all


      select lot.pro_in_codigo,
             pro.pro_st_descricao,
             lot.orl_re_qtdlote as mvs_re_quantidade,
             lot.orl_st_lotefabricacao mvs_st_loteforne,
             substr(adm_pck_util.f_formatacaract(lot.orl_st_referencia),1,200) mvs_st_referenciadesc,
             0  as conversor,
             lot.orl_st_referencia as mvs_st_referencia
        from IDP.apt_apontaordem_lote lot,
             IDP.apt_apontaordem apt,
             est_produtos pro
       where lot.pro_tab_in_codigo = pro.pro_tab_in_codigo
         and lot.pro_pad_in_codigo = pro.pro_pad_in_codigo
         and lot.pro_in_codigo     = pro.pro_in_codigo
         and apt.apt_in_sequencia  = lot.apt_in_sequencia(+)
         and apt.apt_ch_status = 'A'
         and exists
             (select *
                from pro_demanda_dep dep
               where dep.com_tab_in_codigo = lot.pro_tab_in_codigo
                 and dep.com_pad_in_codigo = lot.pro_pad_in_codigo
                 and dep.com_in_codigo     = lot.pro_in_codigo
                 and dep.ord_in_codigo     = pORD_IN_CODIGO
                 and dep.com_pad_in_codigo = pck_mega.achapadraodatabela(pFIL_IN_CODIGO,100,sysdate)

              )) produtos;
end apt_retornaDemandaDisp;

procedure apt_retornaatributo(pFIL_IN_CODIGO NUMBER,
                              pPRO_IN_CODIGO NUMBER,
                              pRESULT            IN OUT SYS_REFCURSOR) is


begin
   open pRESULT for
      select ar.PAI_RAT_IN_CODIGO,
             ar.RAT_IN_CODIGO,
             ar.RAT_ST_DESCRICAO,
             CASE WHEN AR.RAT_CH_TIPO = 'P' THEN
                lpad(ar.pai_rat_in_codigo,7,'0')||'='||ar.rat_in_codigo
             ELSE lpad(ar.pai_rat_in_codigo,7,'0')||'='
             END AS RAT_VALUE,
             AR.RAT_CH_TIPO
        from est_atributoreferencia ar,
             est_caracatributoreferencia cr,
             est_produtos pr
       where ar.rat_tab_in_codigo = cr.rat_tab_in_codigo
             and ar.rat_pad_in_codigo = cr.rat_pad_in_codigo
             and ar.rat_in_codigo = cr.rat_in_codigo
             and cr.rfc_tab_in_codigo = pr.rfc_tab_in_codigo
             and cr.rfc_pad_in_codigo = pr.rfc_pad_in_codigo
             and cr.rfc_in_codigo = pr.rfc_in_codigo
             and ar.rat_in_codigo <> ar.pai_rat_in_codigo
             and pr.pro_pad_in_codigo = pck_mega.achapadraodatabela(pFIL_IN_CODIGO, 100, sysdate)
             and pr.pro_in_codigo      = pPRO_IN_CODIGO;
END apt_retornaatributo;

procedure p_DefineLocalizacaoItem is
  v_PRIORITEM char(1);
  v_achou char(1);
  begin
     -- Se o item estiver configurado para considerar prioridade do item considerar do produto;
     v_PRIORITEM := 'N';
     v_achou := 'N';
     begin
        select nvl(pce.pro_bo_prioritem,'N')
          into v_PRIORITEM
          from est_produtoscmpesp pce
         where pce.pro_tab_in_codigo = vLOC.pro_tab_in_codigo
           and pce.pro_pad_in_codigo = vLOC.pro_pad_in_codigo
           and pce.pro_in_codigo     = vLOC.pro_in_codigo;
     exception when others then
        v_PRIORITEM := 'N';
     end;
     if vLOC.mov_st_origem = 'TR' then
        For cPRL in (
           Select a.*
             From est_produtolocaliza a
            Where a.org_tab_in_codigo = vLOC.org_tab_in_codigo
              And a.org_pad_in_codigo = vLOC.org_pad_in_codigo
              And a.org_in_codigo     = vLOC.org_in_codigo
              And a.org_tau_st_codigo = vLOC.org_tau_st_codigo
              And a.fil_in_codigo     = vLOC.fil_in_codigo
              And a.pro_tab_in_codigo = vLOC.pro_tab_in_codigo
              And a.pro_pad_in_codigo = vLOC.pro_pad_in_codigo
              And a.pro_in_codigo     = vLOC.pro_in_codigo              
              And a.prl_in_prioridade = (Select min(pl.prl_in_prioridade)
                                           From est_produtolocaliza pl
                                          Where pl.org_tab_in_codigo = a.org_tab_in_codigo
                                            And pl.org_pad_in_codigo = a.org_pad_in_codigo
                                            And pl.org_in_codigo     = a.org_in_codigo
                                            And pl.org_tau_st_codigo = a.org_tau_st_codigo
                                            And pl.fil_in_codigo     = a.fil_in_codigo
                                            And pl.pro_tab_in_codigo = a.pro_tab_in_codigo
                                            And pl.pro_pad_in_codigo = a.pro_pad_in_codigo
                                            And pl.pro_in_codigo     = a.pro_in_codigo
                                        )
           )
        Loop
           vTAB_PRL := cPRL;
           v_achou := 'S';                   
        End Loop;                             
        if lpad(vTAB_PRL.alm_tab_in_codigo,3,0)||
               lpad(vTAB_PRL.alm_pad_in_codigo,3,0)||
               lpad(vTAB_PRL.alm_in_codigo,6,0)||
               lpad(vTAB_PRL.loc_in_codigo,6,0) = vLOC.bxi_id_almoxa then                  
           For cPRL in (
              Select a.*
                From est_produtolocaliza a
               Where a.org_tab_in_codigo = vLOC.org_tab_in_codigo
                 And a.org_pad_in_codigo = vLOC.org_pad_in_codigo
                 And a.org_in_codigo     = vLOC.org_in_codigo
                 And a.org_tau_st_codigo = vLOC.org_tau_st_codigo
                 And a.fil_in_codigo     = vLOC.fil_in_codigo
                 And a.pro_tab_in_codigo = vLOC.pro_tab_in_codigo
                 And a.pro_pad_in_codigo = vLOC.pro_pad_in_codigo
                 And a.pro_in_codigo     = vLOC.pro_in_codigo                 
                 And a.prl_in_prioridade = (Select min(pl.prl_in_prioridade)
                                              From est_produtolocaliza pl
                                             Where pl.org_tab_in_codigo = a.org_tab_in_codigo
                                               And pl.org_pad_in_codigo = a.org_pad_in_codigo
                                               And pl.org_in_codigo     = a.org_in_codigo
                                               And pl.org_tau_st_codigo = a.org_tau_st_codigo
                                               And pl.fil_in_codigo     = a.fil_in_codigo
                                               And pl.pro_tab_in_codigo = a.pro_tab_in_codigo
                                               And pl.pro_pad_in_codigo = a.pro_pad_in_codigo
                                               And pl.pro_in_codigo     = a.pro_in_codigo
                                               and (
                                                       (vLOC.bxi_id_almoxa is null) 
                                                     or(lpad(pl.alm_tab_in_codigo,3,0)||
                                                        lpad(pl.alm_pad_in_codigo,3,0)||
                                                        lpad(pl.alm_in_codigo,6,0)||
                                                        lpad(pl.loc_in_codigo,6,0) <> vLOC.bxi_id_almoxa)
                                                   )
                                           )
              )
           Loop
              vTAB_PRL := cPRL;
              v_achou := 'S';                         
           End Loop;                             
        end if;
     elsif v_PRIORITEM = 'S' or vLOC.mov_st_origem <> 'PR' then
        -- Busca a prioridade da localização de estoque;
        For cPRL in (
           Select a.*
             From est_produtolocaliza a
            Where a.org_tab_in_codigo = vLOC.org_tab_in_codigo
              And a.org_pad_in_codigo = vLOC.org_pad_in_codigo
              And a.org_in_codigo     = vLOC.org_in_codigo
              And a.org_tau_st_codigo = vLOC.org_tau_st_codigo
              And a.fil_in_codigo     = vLOC.fil_in_codigo
              And a.pro_tab_in_codigo = vLOC.pro_tab_in_codigo
              And a.pro_pad_in_codigo = vLOC.pro_pad_in_codigo
              And a.pro_in_codigo     = vLOC.pro_in_codigo
              And a.prl_in_prioridade = (Select min(pl.prl_in_prioridade)
                                           From est_produtolocaliza pl
                                          Where pl.org_tab_in_codigo = a.org_tab_in_codigo
                                            And pl.org_pad_in_codigo = a.org_pad_in_codigo
                                            And pl.org_in_codigo     = a.org_in_codigo
                                            And pl.org_tau_st_codigo = a.org_tau_st_codigo
                                            And pl.fil_in_codigo     = a.fil_in_codigo
                                            And pl.pro_tab_in_codigo = a.pro_tab_in_codigo
                                            And pl.pro_pad_in_codigo = a.pro_pad_in_codigo
                                            And pl.pro_in_codigo     = a.pro_in_codigo
                                        )
           )
        Loop
           vTAB_PRL := cPRL;
           v_achou := 'S';
        End Loop;               
     else
        -- Busca prioridade dos parâmetros da integração do centro de trabalho;
        For cPRL in (
          Select a.*
            From est_produtolocaliza a,
                 IDP.apt_pro_maquina_prod prd
           Where a.alm_tab_in_codigo = prd.alm_tab_in_codigo
             And a.alm_pad_in_codigo = prd.alm_pad_in_codigo
             And a.alm_in_codigo     = prd.alm_in_codigo
             and a.loc_in_codigo     = prd.loc_in_codigo
             and a.org_tab_in_codigo = vLOC.org_tab_in_codigo
             And a.org_pad_in_codigo = vLOC.org_pad_in_codigo
             And a.org_in_codigo     = vLOC.org_in_codigo
             And a.org_tau_st_codigo = vLOC.org_tau_st_codigo
             And a.fil_in_codigo     = vLOC.fil_in_codigo
             And a.pro_tab_in_codigo = vLOC.pro_tab_in_codigo
             And a.pro_pad_in_codigo = vLOC.pro_pad_in_codigo
             And a.pro_in_codigo     = vLOC.pro_in_codigo
             And prd.ctr_in_codigo   = vLOC.Apt_Maq_In_Codigo
             and (prd.cmaq_in_codigo  = vLOC.cmaq_in_codigo or vLOC.cmaq_in_codigo is null)
             and prd.opr_in_codigo   = vLOC.opr_in_codigo
             -- Alterado por JPC em 14/09/2020
             -- Permitir movimentação material em Jumirim (BAGGIO)
             -- Solicitado por Lazão e Gabriel
             And (
                     (vLOC.tpo_st_codigo_tipo = 'OT001' AND prd.maq_in_prioridade = 0)
                  or (vLOC.tpo_st_codigo_tipo <> 'OT001' AND a.prl_in_prioridade = 1)
                  or (vLOC.tpo_st_codigo_tipo = 'OP001' AND a.prl_in_prioridade = 1)
                  or (vLOC.tpo_st_codigo_tipo = 'OP003' AND prd.maq_in_prioridade = 0)
                 ))
        Loop
           vTAB_PRL := cPRL;
           v_achou := 'S';
        End Loop;
        if v_achou = 'N' then
           Raise_application_error(-20000, 'O item: ' || vLOC.pro_in_codigo || ' está sem almoxarifado definido para a Filial: ' || vLOC.fil_in_codigo);
        End if;
     end if;
  end p_DefineLocalizacaoItem;      
procedure apt_retornaitens(pFIL_IN_CODIGO NUMBER,
                           pORD_IN_CODIGO NUMBER,
                           pRESULT IN OUT SYS_REFCURSOR) is

begin
   --Raise_application_error(-20000, pPRO_IN_CODIGO);
   if pORD_IN_CODIGO is not null then
      open pRESULT for
         select p.pro_tab_in_codigo,
                p.pro_pad_in_codigo,
                p.pro_in_codigo,
                p.pro_st_descricao,
                p.uni_st_unidade,
                nvl(p.rfc_in_codigo,0) rfc_in_codigo,
                nvl(c.pro_re_comprimento,0) pro_re_comprimento,
                nvl(c.pro_re_largura,0) pro_re_largura,
                nvl(c.pro_re_espessura,0) pro_re_espessura,
                nvl((select cpr.clp_st_descricao as pro_st_madeira
                   from est_produtoscmpesp cen,
                        IDP.cli_tb_classe_produto cpr
                  where cen.pro_tab_in_codigo = p.pro_tab_in_codigo
                    and cen.pro_pad_in_codigo = p.pro_pad_in_codigo
                    and cen.pro_in_codigo     = p.pro_in_codigo
                    and cen.pro_in_classe     = cpr.pro_in_classe),'Indefinido') as pro_st_madeira,
                nvl(r.mvs_st_referencia,'Indefinido')mvs_st_referencia,
                lpad(p.pro_tab_in_codigo,3,'0')||
                lpad(p.pro_pad_in_codigo,3,'0')||
                lpad(p.pro_in_codigo,7,'0') as pro_st_id,
                nvl((select cie.cie_st_descricao as pro_st_nmcientifico
                from est_produtoscmpesp cen,
                     IDP.CUS_TB_PRODCIENTIFICO cie                     
               where cen.pro_tab_in_codigo = p.pro_tab_in_codigo
                 and cen.pro_pad_in_codigo = p.pro_pad_in_codigo
                 and cen.pro_in_codigo     = p.pro_in_codigo
                 and cen.cie_in_sequencia  = cie.cie_in_sequencia),'Indefinido') as pro_st_nmcientifico,
                nvl(p.pro_re_perda,0) pro_re_perda,
                'Produto' as Tipo_item
           from est_produtos p,
                pro_ordens o,
                est_revisaolistamateriais l,
                est_produtocampoespecifico c,
                IDP.cus_tb_estprodutoreferencia r
          where p.pro_tab_in_codigo = l.pro_tab_in_codigo
            and p.pro_pad_in_codigo = l.pro_pad_in_codigo
            and p.pro_in_codigo     = l.pro_in_codigo
            and o.pro_tab_in_codigo = p.pro_tab_in_codigo
            and o.pro_pad_in_codigo = p.pro_pad_in_codigo
            and o.pro_in_codigo     = p.pro_in_codigo
            and p.pro_st_cestoque   = 'S'
            and p.pro_tab_in_codigo = c.pro_tab_in_codigo (+)
            and p.pro_pad_in_codigo = c.pro_pad_in_codigo (+)
            and p.pro_in_codigo     = c.pro_in_codigo     (+)
            and p.pro_tab_in_codigo = r.pro_tab_in_codigo (+)
            and p.pro_pad_in_codigo = r.pro_pad_in_codigo (+)
            and p.pro_in_codigo     = r.pro_in_codigo     (+)
            and p.pro_pad_in_codigo = pck_mega.achapadraodatabela(pFIL_IN_CODIGO, 100, sysdate)
            and o.ord_in_codigo     = pORD_IN_CODIGO
            and l.lis_in_revisao    = adm_pck_util.f_revisao_atual(p.pro_pad_in_codigo,p.pro_in_codigo,0,sysdate)
            union all
         select a.com_tab_in_codigo,
                a.com_pad_in_codigo,
                a.com_in_codigo,
                b.pro_st_descricao,
                b.uni_st_unidade,
                nvl(b.rfc_in_codigo,0) rfc_in_codigo,
                nvl(c.pro_re_comprimento,0) pro_re_comprimento,
                nvl(c.pro_re_largura,0) pro_re_largura,
                nvl(c.pro_re_espessura,0) pro_re_espessura,
                nvl((select cpr.clp_st_descricao as pro_st_madeira
                   from est_produtoscmpesp cen,
                        IDP.cli_tb_classe_produto cpr
                  where cen.pro_tab_in_codigo = b.pro_tab_in_codigo
                    and cen.pro_pad_in_codigo = b.pro_pad_in_codigo
                    and cen.pro_in_codigo     = b.pro_in_codigo
                    and cen.pro_in_classe     = cpr.pro_in_classe),'Indefinido') as pro_st_madeira,
                nvl(r.mvs_st_referencia,'Indefinido')mvs_st_referencia,
                lpad(b.pro_tab_in_codigo,3,'0')||
                lpad(b.pro_pad_in_codigo,3,'0')||
                lpad(b.pro_in_codigo,7,'0') as pro_st_id,
                nvl((select cie.cie_st_descricao as pro_st_nmcientifico
                       from est_produtoscmpesp cen,
                            IDP.CUS_TB_PRODCIENTIFICO cie                     
                      where cen.pro_tab_in_codigo = b.pro_tab_in_codigo
                        and cen.pro_pad_in_codigo = b.pro_pad_in_codigo
                        and cen.pro_in_codigo     = b.pro_in_codigo
                        and cen.cie_in_sequencia  = cie.cie_in_sequencia),'Indefinido') as pro_st_nmcientifico,
                nvl(b.pro_re_perda,0) pro_re_perda,
                'SubProduto' as Tipo_item
           from IDP.ia_tb_listasubprodutositens a,
                est_produtos                   b,
                pro_ordens                     o,
                est_produtocampoespecifico     c,
                IDP.cus_tb_estprodutoreferencia r
          where a.com_tab_in_codigo = b.pro_tab_in_codigo
            and a.com_pad_in_codigo = b.pro_pad_in_codigo
            and a.com_in_codigo     = b.pro_in_codigo
            and o.pro_tab_in_codigo = a.pro_tab_in_codigo
            and o.pro_pad_in_codigo = a.pro_pad_in_codigo
            and o.pro_in_codigo     = a.pro_in_codigo
            and b.pro_tab_in_codigo = c.pro_tab_in_codigo (+)
            and b.pro_pad_in_codigo = c.pro_pad_in_codigo (+)
            and b.pro_in_codigo     = c.pro_in_codigo     (+)
            and b.pro_tab_in_codigo = r.pro_tab_in_codigo (+)
            and b.pro_pad_in_codigo = r.pro_pad_in_codigo (+)
            and b.pro_in_codigo     = r.pro_in_codigo     (+)
            and b.pro_st_cestoque   = 'S'
            and a.pro_pad_in_codigo = pck_mega.achapadraodatabela(pFIL_IN_CODIGO, 100, sysdate)
            and o.ord_in_codigo     = pORD_IN_CODIGO
            and a.lis_in_revisao    = adm_pck_util.f_revisao_atual(a.pro_pad_in_codigo,a.pro_in_codigo,0,sysdate);
   else
      open pRESULT for
         select p.pro_tab_in_codigo,
                p.pro_pad_in_codigo,
                p.pro_in_codigo,
                p.pro_st_descricao,
                p.uni_st_unidade,
                nvl(p.rfc_in_codigo,0) rfc_in_codigo,
                nvl(c.pro_re_comprimento,0) pro_re_comprimento,
                nvl(c.pro_re_largura,0) pro_re_largura,
                nvl(c.pro_re_espessura,0) pro_re_espessura,
                nvl((select cpr.clp_st_descricao as pro_st_madeira
                   from est_produtoscmpesp cen,
                        IDP.cli_tb_classe_produto cpr
                  where cen.pro_tab_in_codigo = p.pro_tab_in_codigo
                    and cen.pro_pad_in_codigo = p.pro_pad_in_codigo
                    and cen.pro_in_codigo     = p.pro_in_codigo
                    and cen.pro_in_classe     = cpr.pro_in_classe),'Indefinido') as pro_st_madeira,
                nvl(r.mvs_st_referencia,'Indefinido')mvs_st_referencia,
                lpad(p.pro_tab_in_codigo,3,'0')||
                lpad(p.pro_pad_in_codigo,3,'0')||
                lpad(p.pro_in_codigo,7,'0') as pro_st_id,
                nvl((select cie.cie_st_descricao as pro_st_nmcientifico
                from est_produtoscmpesp cen,
                     IDP.CUS_TB_PRODCIENTIFICO cie                     
               where cen.pro_tab_in_codigo = p.pro_tab_in_codigo
                 and cen.pro_pad_in_codigo = p.pro_pad_in_codigo
                 and cen.pro_in_codigo     = p.pro_in_codigo
                 and cen.cie_in_sequencia  = cie.cie_in_sequencia),'Indefinido') as pro_st_nmcientifico,
                 nvl(p.pro_re_perda,0) pro_re_perda
           from est_produtos p,
                est_produtocampoespecifico c,
                IDP.cus_tb_estprodutoreferencia r
          where p.pro_st_cestoque   = 'S'
            and p.pro_tab_in_codigo = c.pro_tab_in_codigo (+)
            and p.pro_pad_in_codigo = c.pro_pad_in_codigo (+)
            and p.pro_in_codigo     = c.pro_in_codigo     (+)
            and p.pro_tab_in_codigo = r.pro_tab_in_codigo (+)
            and p.pro_pad_in_codigo = r.pro_pad_in_codigo (+)
            and p.pro_in_codigo     = r.pro_in_codigo     (+)
            and p.pro_pad_in_codigo = pck_mega.achapadraodatabela(pFIL_IN_CODIGO, 100, sysdate)
            and p.pro_st_defitem    = 'MP';         
   end if;    
end apt_retornaitens;
-- Função para validar se existe produção já integrada;
function f_valida_intproducao RETURN CHAR is
v_existe number;
v_retorno char(1);
begin
   select count(*)
     into v_existe
     from IDP.apt_apontaordem_lote mvp
    where mvp.org_tab_in_codigo = vAPT_LOTE.Org_Tab_In_Codigo
      and mvp.org_pad_in_codigo = vAPT_LOTE.Org_Pad_In_Codigo
      and mvp.org_in_codigo     = vAPT_LOTE.Org_In_Codigo
      and mvp.org_tau_st_codigo = vAPT_LOTE.Org_Tau_St_Codigo
      and mvp.ord_tab_in_codigo = vAPT_LOTE.Ord_Tab_In_Codigo
      and mvp.ord_seq_in_codigo = vAPT_LOTE.Ord_Seq_In_Codigo
      and mvp.ord_in_codigo     = vAPT_LOTE.Ord_In_Codigo
      --and mvp.ctl_in_codigo     = vAPT_LOTE.Ctl_In_Codigo
      and mvp.mvp_in_sequencia  = vAPT_LOTE.Mvp_In_Sequencia;
   if v_existe > 0 then
      v_retorno := 'S';
   else
      v_retorno := 'N';
   end if;
   return(v_retorno);
end f_valida_intproducao;

-- Função para validar se existe produção já integrada;
function f_valida_apontamento RETURN CHAR is
v_existe number;
v_retorno char(1);
begin
   select count(*)
     into v_existe
     from IDP.apt_apontaordem apt
    where apt.org_tab_in_codigo = vTAB_ORD.Org_Tab_In_Codigo
      and apt.org_pad_in_codigo = vTAB_ORD.Org_Pad_In_Codigo
      and apt.org_in_codigo     = vTAB_ORD.Org_In_Codigo
      and apt.org_tau_st_codigo = vTAB_ORD.Org_Tau_St_Codigo
      and apt.ord_tab_in_codigo = vTAB_ORD.Ord_Tab_In_Codigo
      and apt.ord_seq_in_codigo = vTAB_ORD.Ord_Seq_In_Codigo
      and apt.ord_in_codigo     = vTAB_ORD.Ord_In_Codigo
      and apt.apt_ch_status     = 'A';
   if v_existe > 0 then
      v_retorno := 'S';
   else
      v_retorno := 'N';
   end if;
   return(v_retorno);
end f_valida_apontamento;


function f_valida_sitordem(pFIL_IN_CODIGO in number,
                           pORD_IN_CODIGO in number) RETURN VARCHAR2 is
v_existe number;
v_retorno pro_ordens.ord_st_situacao%TYPE;
begin
   begin
     select ord.ord_st_situacao
       into v_retorno
       from IDP.pro_ordens ord
      where ord.org_tab_in_codigo = 53
        and ord.org_pad_in_codigo = 1
        and ord.fil_in_codigo     = pFIL_IN_CODIGO
        and ord.org_tau_st_codigo = 'G'
        and ord.ord_tab_in_codigo = 218
        and ord.ord_seq_in_codigo = pck_mega.ACHAPADRAODATABELA(pFIL_IN_CODIGO,218,sysdate)
        and ord.ord_in_codigo     = pORD_IN_CODIGO;
   exception when others then
      null;
   end; 
   if v_retorno is null then
      v_retorno := 'EN';
   end if;
   return(v_retorno);
end f_valida_sitordem;
-- Função para validar se existe demanda vinculada a operação 0;
function F_validaDemanda(pORG_IN_CODIGO in number,
                         pORD_SEQ_IN_CODIGO in number,
                         pORD_IN_CODIGO in number) return varchar2 is
vPermite char(1);
begin
   vPermite := 'S';
   for cDEP in(
      select *
        from pro_demanda_dep dep
       where dep.org_in_codigo = pORG_IN_CODIGO
         and dep.ord_in_codigo = pORD_IN_CODIGO
         and dep.dde_in_operacao = 0
      )
   loop
      vPermite := 'N';
      exit;
   end loop;
   return(vPermite);
end F_validaDemanda;
function f_valida_intdemanda RETURN CHAR is
v_existe number;
v_retorno char(1);
begin
   v_existe := 0;
   for cMVD in(  
      select mvd.*
        from IDP.apt_apontademanda_estoque mvd
       where mvd.org_tab_in_codigo = vAPT_DEM.Org_Tab_In_Codigo
         and mvd.org_pad_in_codigo = vAPT_DEM.Org_Pad_In_Codigo
         and mvd.org_in_codigo = vAPT_DEM.Org_In_Codigo
         and mvd.org_tau_st_codigo = vAPT_DEM.Org_Tau_St_Codigo
         and mvd.ord_tab_in_codigo = vAPT_DEM.Ord_Tab_In_Codigo
         and mvd.ord_seq_in_codigo = vAPT_DEM.Ord_Seq_In_Codigo
         and mvd.ord_in_codigo     = vAPT_DEM.Ord_In_Codigo
         and (
                 (mvd.apt_in_sequencia = vAPT_DEM.Apt_In_Sequencia and vAPT_DEM.Mvs_St_Loteforne = '*')                 
               or(mvd.mvs_st_loteforne = vAPT_DEM.Mvs_St_Loteforne and vAPT_DEM.Mvs_St_Loteforne <> '*')
             )             
         --and mvd.ctl_in_codigo     = &Ctl_In_Codigo
         and (mvd.mvd_in_sequencia  = vAPT_DEM.Mvd_In_Sequencia or vAPT_DEM.Mvd_In_Sequencia is null)
         and (mvd.com_in_codigo = vAPT_DEM.Com_In_Codigo or vAPT_DEM.Com_In_Codigo is null)
         order by mvd.mvd_in_sequencia 
         fetch first row only                  
         )
   loop
      vAPT_DEM := cMVD;
      v_existe := 1;
   end loop;        
   if v_existe > 0 then
      v_retorno := 'S';
      
   else
      v_retorno := 'N';
   end if;
   return(v_retorno);
end f_valida_intdemanda;
procedure p_cria_demanda is
begin
   for cDEM in (
      select dde.Org_Tab_In_Codigo,
             dde.Org_Pad_In_Codigo,
             dde.Org_In_Codigo,
             dde.Org_Tau_St_Codigo,
             dde.Ord_Tab_In_Codigo,
             dde.Ord_Seq_In_Codigo,
             dde.Ord_In_Codigo,
             dde.Com_Tab_In_Codigo,
             dde.Com_Pad_In_Codigo,
             dde.Com_In_Codigo,
             dde.plf_in_sqoperacao,
             dde.apt_in_sequencia,
             sum(dde.apt_re_qtdeselecionada) as mvs_re_quantidade
        from apt_apontademanda_estoque dde
       where dde.apt_in_sequencia = vTAB_APT.apt_in_sequencia
         and dde.dde_st_situacao <> 'C'
         and not exists(
             select 1
               from apt_apontademanda apd
              where apd.apt_in_sequencia   = dde.apt_in_sequencia
                and apd.com_tab_in_codigo  = dde.com_tab_in_codigo
                and apd.com_pad_in_codigo  = dde.com_pad_in_codigo
                and apd.com_in_codigo      = dde.com_in_codigo
                and apd.dde_in_operacao    = dde.dde_in_operacao
                and apd.plf_in_sqoperacao  = dde.plf_in_sqoperacao
                and apd.dde_dt_necessidade = dde.dde_dt_necessidade)
       group by dde.Org_Tab_In_Codigo,
             dde.Org_Pad_In_Codigo,
             dde.Org_In_Codigo,
             dde.Org_Tau_St_Codigo,
             dde.Ord_Tab_In_Codigo,
             dde.Ord_Seq_In_Codigo,
             dde.Ord_In_Codigo,
             dde.Com_Tab_In_Codigo,
             dde.Com_Pad_In_Codigo,
             dde.Com_In_Codigo,
             dde.plf_in_sqoperacao,
             dde.apt_in_sequencia
   )
   loop                    
      vTAB_DEP := null;
      if vTAB_DEP.Com_In_Codigo is null then
         for cDEP in (
            select dep.*
              from pro_demanda_dep dep
             where dep.org_tab_in_codigo = cDEM.Org_Tab_In_Codigo
               and dep.org_pad_in_codigo = cDEM.Org_Pad_In_Codigo
               and dep.org_in_codigo     = cDEM.Org_In_Codigo
               and dep.org_tau_st_codigo = cDEM.Org_Tau_St_Codigo
               and dep.ord_tab_in_codigo = cDEM.Ord_Tab_In_Codigo
               and dep.ord_seq_in_codigo = cDEM.Ord_Seq_In_Codigo
               and dep.ord_in_codigo     = cDEM.Ord_In_Codigo
               and dep.com_tab_in_codigo = cDEM.Com_Tab_In_Codigo
               and dep.com_pad_in_codigo = cDEM.Com_Pad_In_Codigo
               and (dep.com_in_codigo     = cDEM.Com_In_Codigo or cDEM.Com_In_Codigo is null)
               and dep.dde_in_operacao   = (select max(dde.dde_in_operacao)
                                             from pro_demanda_dep dde
                                            where dde.org_tab_in_codigo = dep.org_tab_in_codigo
                                              and dde.org_pad_in_codigo = dep.org_pad_in_codigo
                                              and dde.org_in_codigo     = dep.org_in_codigo
                                              and dde.org_tau_st_codigo = dep.org_tau_st_codigo
                                              and dde.ord_tab_in_codigo = dep.ord_tab_in_codigo
                                              and dde.ord_seq_in_codigo = dep.ord_seq_in_codigo
                                              and dde.ord_in_codigo     = dep.ord_in_codigo)
            and rownum < 2)
         loop
            vTAB_DEP := cDEP;        
         end loop;
      end if;
      if vTAB_DEP.Com_In_Codigo is null then
         -- Inserir o item na demanda;
         for cDEP in (
            select dep.*
              from pro_demanda_dep dep
             where dep.org_tab_in_codigo = cDEM.Org_Tab_In_Codigo
               and dep.org_pad_in_codigo = cDEM.Org_Pad_In_Codigo
               and dep.org_in_codigo     = cDEM.Org_In_Codigo
               and dep.org_tau_st_codigo = cDEM.Org_Tau_St_Codigo
               and dep.ord_tab_in_codigo = cDEM.Ord_Tab_In_Codigo
               and dep.ord_seq_in_codigo = cDEM.Ord_Seq_In_Codigo
               and dep.ord_in_codigo     = cDEM.Ord_In_Codigo
               and dep.com_tab_in_codigo = cDEM.Com_Tab_In_Codigo
               and dep.com_pad_in_codigo = cDEM.Com_Pad_In_Codigo               
               and dep.dde_in_operacao   = (select max(dde.dde_in_operacao)
                                             from pro_demanda_dep dde
                                            where dde.org_tab_in_codigo = dep.org_tab_in_codigo
                                              and dde.org_pad_in_codigo = dep.org_pad_in_codigo
                                              and dde.org_in_codigo     = dep.org_in_codigo
                                              and dde.org_tau_st_codigo = dep.org_tau_st_codigo
                                              and dde.ord_tab_in_codigo = dep.ord_tab_in_codigo
                                              and dde.ord_seq_in_codigo = dep.ord_seq_in_codigo
                                              and dde.ord_in_codigo     = dep.ord_in_codigo)
            and rownum < 2)
         loop
            vTAB_DEP := cDEP;
            vTAB_DEP.Com_In_Codigo := cDEM.Com_In_Codigo;
            vTAB_DEP.Dde_Re_Qtde_Requisitada := 0;
            vTAB_DEP.Dde_St_Situacao := 'AB';
            begin 
               select max(dde.lis_in_sequencia)+10
                 into vTAB_DEP.Lis_In_Sequencia
                 from pro_demanda_dep dde
                where dde.org_tab_in_codigo = cDEM.Org_Tab_In_Codigo
                  and dde.org_pad_in_codigo = cDEM.Org_Pad_In_Codigo
                  and dde.org_in_codigo     = cDEM.Org_In_Codigo
                  and dde.org_tau_st_codigo = cDEM.Org_Tau_St_Codigo
                  and dde.ord_tab_in_codigo = cDEM.Ord_Tab_In_Codigo
                  and dde.ord_seq_in_codigo = cDEM.Ord_Seq_In_Codigo
                  and dde.ord_in_codigo     = cDEM.Ord_In_Codigo;
            exception when others then
               null;
            end;               
            insert into pro_demanda_dep values vTAB_DEP;         
         end loop;
      end if;
      -- carrega tabela de demandas;     
      vTAB_DDE.Org_Tab_In_Codigo  := vTAB_DEP.Org_Tab_In_Codigo;
      vTAB_DDE.Org_Pad_In_Codigo  := vTAB_DEP.Org_Pad_In_Codigo;
      vTAB_DDE.Org_In_Codigo      := vTAB_DEP.Org_In_Codigo;
      vTAB_DDE.Org_Tau_St_Codigo  := vTAB_DEP.Org_Tau_St_Codigo;
      vTAB_DDE.Ord_Tab_In_Codigo  := vTAB_DEP.Ord_Tab_In_Codigo;
      vTAB_DDE.Ord_Seq_In_Codigo  := vTAB_DEP.Ord_Seq_In_Codigo;
      vTAB_DDE.Ord_In_Codigo      := vTAB_DEP.Ord_In_Codigo;
      vTAB_DDE.Com_Tab_In_Codigo  := vTAB_DEP.Com_Tab_In_Codigo;
      vTAB_DDE.Com_Pad_In_Codigo  := vTAB_DEP.Com_Pad_In_Codigo;
      vTAB_DDE.Com_In_Codigo      := vTAB_DEP.Com_In_Codigo;
      vTAB_DDE.Dde_In_Operacao    := vTAB_DEP.Dde_In_Operacao;
      vTAB_DDE.Dde_Dt_Necessidade := vTAB_DEP.Dde_Dt_Necessidade;
      vTAB_DDE.Dde_Re_Qtde_Padrao := cDEM.mvs_re_quantidade;
      vTAB_DDE.Plf_In_Sqoperacao  := cDEM.Plf_In_Sqoperacao;
      vTAB_DDE.Pro_St_Tipobaixa   :='M';
      vTAB_DDE.Dde_Bo_Atende      := 'S';
      vTAB_DDE.Dde_Re_Qtde_Disponivel :=cDEM.mvs_re_quantidade;
      vTAB_DDE.Dde_Bo_Reservado := 'N';
      vTAB_DDE.Dde_Re_Qtde_Padrao_Mov :=cDEM.mvs_re_quantidade;
      Begin
         update IDP.APT_APONTADEMANDA dde
            set row = vTAB_DDE
          where dde.Org_Tab_In_Codigo  = vTAB_DDE.Org_Tab_In_Codigo
            and dde.Org_Pad_In_Codigo  = vTAB_DDE.Org_Pad_In_Codigo
            and dde.Org_In_Codigo      = vTAB_DDE.Org_In_Codigo
            and dde.Org_Tau_St_Codigo  = vTAB_DDE.Org_Tau_St_Codigo
            and dde.Ord_Tab_In_Codigo  = vTAB_DDE.Ord_Tab_In_Codigo
            and dde.Ord_Seq_In_Codigo  = vTAB_DDE.Ord_Seq_In_Codigo
            and dde.Ord_In_Codigo      = vTAB_DDE.Ord_In_Codigo
            and dde.Com_Tab_In_Codigo  = vTAB_DDE.Com_Tab_In_Codigo
            and dde.Com_Pad_In_Codigo  = vTAB_DDE.Com_Pad_In_Codigo
            and dde.Com_In_Codigo      = vTAB_DDE.Com_In_Codigo
            and dde.Dde_In_Operacao    = vTAB_DDE.Dde_In_Operacao
            and dde.Dde_Dt_Necessidade = vTAB_DDE.Dde_Dt_Necessidade
            and dde.apt_in_sequencia   = vTAB_DDE.apt_in_sequencia;
         If Sql%Notfound Then
            Insert Into IDP.APT_APONTADEMANDA values vTAB_DDE;
         end if;
      end;
   end loop;      
end;

procedure p_RecalculaDemandaEmpenho(pAPT_IN_SEQUENCIA In IDP.APT_APONTAORDEM.APT_IN_SEQUENCIA%Type )is          
     v_achou char(1);
     begin        
        for cAPD in(
           select apd.*
             from APT_APONTADEMANDA apd
            where apd.apt_in_sequencia = pAPT_IN_SEQUENCIA
           )
        loop
           v_achou := 'N';
           for cDEP in(
              select dem.com_tab_in_codigo,
                     dem.com_pad_in_codigo,
                     dem.com_in_codigo, 
                     dem.apt_in_sequencia,
                    sum(dem.apt_re_qtdeselecionada) as DDE_QTDE 
                from APT_APONTADEMANDA_ESTOQUE dem
               where dem.apt_in_sequencia = pAPT_IN_SEQUENCIA
                 and dem.com_tab_in_codigo = cAPD.Com_Tab_In_Codigo
                 and dem.com_pad_in_codigo = cAPD.Com_Pad_In_Codigo
                 and dem.com_in_codigo     = cAPD.Com_In_Codigo
                 -- Somente demanda aberta;
                 and dem.dde_st_situacao <> 'C'
               group by dem.com_tab_in_codigo,
                     dem.com_pad_in_codigo,
                     dem.com_in_codigo,
                     dem.apt_in_sequencia             
             )
           loop
              v_achou := 'S';
              update APT_APONTADEMANDA dde
                 set dde.dde_re_qtde_padrao_mov = cDEP.Dde_Qtde,
                     dde.dde_re_qtde_padrao = cDEP.Dde_Qtde,
                     dde.dde_re_qtde_disponivel = cDEP.Dde_Qtde
               where dde.com_tab_in_codigo  = cDEP.Com_Tab_In_Codigo
                 and dde.com_pad_in_codigo  = cDEP.Com_Pad_In_Codigo
                 and dde.com_in_codigo      = cDEP.Com_In_Codigo
                 and dde.apt_in_sequencia   = cDEP.apt_in_sequencia;
           end loop;
           if v_achou = 'N' then
              delete APT_APONTADEMANDA dde
               where dde.com_tab_in_codigo  = cAPD.Com_Tab_In_Codigo
                 and dde.com_pad_in_codigo  = cAPD.Com_Pad_In_Codigo
                 and dde.com_in_codigo      = cAPD.Com_In_Codigo
                 and dde.apt_in_sequencia   = cAPD.apt_in_sequencia
                 --and dde.org_in_codigo      <> 301
                 ;
           end if;
        end loop;     
  end p_RecalculaDemandaEmpenho;
  procedure P_ReabreApontamento(pAPT_IN_SEQUENCIA In IDP.APT_APONTAORDEM.APT_IN_SEQUENCIA%Type) is 
  
  begin
     vTAB_DDE.Apt_In_Sequencia := pAPT_IN_SEQUENCIA;
     for cAPT in(
        select *
          from apt_apontaordem apt
         where apt.apt_in_sequencia = pAPT_IN_SEQUENCIA
           and apt.apt_ch_status <> 'A'
       )
     loop
        update apt_apontaordem_lote ape
           set ape.apt_ch_status = 'A'
         where ape.apt_in_sequencia = cAPT.Apt_In_Sequencia;                   
        update apt_apontaordem apt
           set apt.apt_ch_status = 'A'
         where apt.apt_in_sequencia = cAPT.Apt_In_Sequencia;
         p_cria_demanda;         
     end loop;     
  end P_ReabreApontamento;
  
    procedure p_programacaoordem is
    begin
       -- Carrega a programação da ordem;   
       for cPRG in(
         select * 
           from pro_prog_ordem po
          where po.org_tab_in_codigo = vTAB_ORD.org_tab_in_codigo
            and po.org_pad_in_codigo = vTAB_ORD.org_pad_in_codigo
            and po.org_in_codigo     = vTAB_ORD.org_in_codigo    
            and po.org_tau_st_codigo = vTAB_ORD.org_tau_st_codigo
            and po.ord_tab_in_codigo = vTAB_ORD.ord_tab_in_codigo
            and po.ord_seq_in_codigo = vTAB_ORD.ord_seq_in_codigo
            and po.ord_in_codigo     = vTAB_ORD.ord_in_codigo    
            and po.fil_in_codigo     = vTAB_ORD.fil_in_codigo
            and po.tmp_ch_aponta = 'S'
            --and po.tmp_ch_bxdemanda = 'S'
            and (po.plf_in_sqoperacao = vTAB_APT.Plf_In_Sqoperacao or vTAB_APT.Plf_In_Sqoperacao is null)
            )
       loop
          vTAB_PRG := cPRG;
          if vTAB_PRG.Tmp_Ch_Bxdemanda = 'N' then
             vTAB_PRG.Tmp_Ch_Bxdemanda := 'S';
          end if;
       end loop;
       -- Adicionado por JPC em 04/10/2022;
       -- Trata o código da máquina   
       -- Busca fixo na ordem
       if vTAB_PRG.Cmaq_In_Codigo is null or v_apontamento = 'N' or vTAB_APT.apt_cmaq_in_codigo is null then
          -- Carrega as configurações padrão de apontamento para a ordem
          for cCFM in(
             select cfm.*
               from IDP.apt_pro_maquina_config cfm
              where cfm.ctr_tab_in_codigo  = vTAB_PRG.maq_tab_in_codigo
                and cfm.ctr_pad_in_codigo  = vTAB_PRG.maq_pad_in_codigo
                and cfm.ctr_in_codigo      = vTAB_PRG.maq_in_codigo
                and cfm.opr_tab_in_codigo  = vTAB_PRG.opr_tab_in_codigo
                and cfm.opr_pad_in_codigo  = vTAB_PRG.opr_pad_in_codigo
                and cfm.opr_in_codigo      = vTAB_PRG.opr_in_codigo
                )
          loop
             vTAB_CFM := cCFM;
          end loop;
          if vTAB_APT.fil_in_codigo = 31 then
             if vTAB_ORD.Tpo_St_Codigo_Tipo = 'OT001' then
                if vTAB_PRG.Cmaq_In_Codigo is not null then
                   vTAB_APT.apt_cmaq_in_codigo := vTAB_PRG.Cmaq_In_Codigo;   
                else
                   vTAB_APT.apt_cmaq_in_codigo := 2;   
                end if;
             else
                vTAB_APT.apt_cmaq_in_codigo := 1;    
             end if;
          elsif vTAB_APT.fil_in_codigo = 3 then      
             case 
                when vTAB_PRG.Cmaq_In_Codigo is null then
                   -- Define a máquina padrão para o tipo de ordem
                   vTAB_PRG.cmaq_tab_in_codigo := vTAB_CFM.cmaq_tab_in_codigo;   
                   vTAB_PRG.cmaq_pad_in_codigo := vTAB_CFM.cmaq_pad_in_codigo;
                   vTAB_PRG.cmaq_in_codigo     := vTAB_CFM.cmaq_in_codigo;
                when vTAB_ORD.Tpo_St_Codigo_Tipo = 'OP001' then 
                   if vTAB_APT.apt_cmaq_in_codigo is null then
                      if vTAB_PRG.cmaq_in_codigo is not null then
                         vTAB_APT.apt_cmaq_in_codigo := vTAB_PRG.cmaq_in_codigo;
                      else
                         vTAB_APT.apt_cmaq_in_codigo := 1;        
                      end if;
                   end if;                                                             
                when vTAB_ORD.Tpo_St_Codigo_Tipo = 'OP002' then 
                   if vTAB_APT.apt_cmaq_in_codigo is null then
                      if vTAB_PRG.cmaq_in_codigo is not null then
                         vTAB_APT.apt_cmaq_in_codigo := vTAB_PRG.cmaq_in_codigo;
                      /*elsif pcmaq_st_id is not null and  vTAB_APT.apt_cmaq_in_codigo is null then
                         vTAB_APT.apt_cmaq_in_codigo := to_number(substr(pcmaq_st_id,-2));
                      else*/
                         vTAB_APT.apt_cmaq_in_codigo := 2;        
                      end if;
                   end if;                                                             
                when vTAB_ORD.Tpo_St_Codigo_Tipo = 'OP003' then 
                   vTAB_APT.apt_cmaq_in_codigo := 12;
                else 
                   vTAB_APT.apt_cmaq_in_codigo := 12;
             end case;            
          elsif vTAB_APT.fil_in_codigo in(302,312) then
             if vTAB_PRG.Cmaq_In_Codigo is null then
                -- Define a máquina padrão para o tipo de ordem
                vTAB_PRG.cmaq_tab_in_codigo := vTAB_CFM.cmaq_tab_in_codigo;   
                vTAB_PRG.cmaq_pad_in_codigo := vTAB_CFM.cmaq_pad_in_codigo;
                vTAB_PRG.cmaq_in_codigo     := vTAB_CFM.cmaq_in_codigo;
             end if;
             
             if vTAB_APT.apt_cmaq_in_codigo is null and vTAB_PRG.Cmaq_In_Codigo is not null then
                vTAB_APT.apt_cmaq_in_codigo := vTAB_PRG.Cmaq_In_Codigo;
             elsif v_apontamento = 'S' and vTAB_APT.apt_cmaq_in_codigo is null then
                vTAB_APT.apt_cmaq_in_codigo := vTAB_PRG.Cmaq_In_Codigo;
             elsif vTAB_APT.apt_cmaq_in_codigo <> vTAB_PRG.Cmaq_In_Codigo then
                vTAB_APT.apt_cmaq_in_codigo := vTAB_PRG.Cmaq_In_Codigo;
             end if;
          end if;                         
       end if;
       -- Atualiza programacão/operacão da ordem
       update pro_prog_ordem pod
          set pod.pod_st_situacao = 'AB',
              pod.cmaq_tab_in_codigo = vTAB_PRG.cmaq_tab_in_codigo,
              pod.cmaq_pad_in_codigo = vTAB_PRG.cmaq_pad_in_codigo,
              pod.cmaq_in_codigo     = vTAB_PRG.cmaq_in_codigo,
              pod.tmp_ch_bxdemanda   = vTAB_PRG.tmp_ch_bxdemanda
        where pod.org_tab_in_codigo  = vTAB_PRG.org_tab_in_codigo
          and pod.org_pad_in_codigo  = vTAB_PRG.org_pad_in_codigo
          and pod.org_in_codigo      = vTAB_PRG.org_in_codigo
          and pod.org_tau_st_codigo  = vTAB_PRG.org_tau_st_codigo
          and pod.fil_in_codigo      = vTAB_PRG.fil_in_codigo
          and pod.ord_tab_in_codigo  = vTAB_PRG.ord_tab_in_codigo
          and pod.ord_seq_in_codigo  = vTAB_PRG.ord_seq_in_codigo
          and pod.ord_in_codigo      = vTAB_PRG.ord_in_codigo
          and pod.plf_in_sqoperacao  = vTAB_PRG.plf_in_sqoperacao;
       -- Atualiza o apontamento
       if v_apontamento = 'S' and vTAB_APT.apt_cmaq_in_codigo is not null then
          update apt_apontaordem apt
             set apt.apt_cmaq_in_codigo = vTAB_APT.apt_cmaq_in_codigo       
           where apt.apt_in_sequencia   = vTAB_APT.Apt_In_Sequencia
             and (
                     (apt.apt_cmaq_in_codigo is null)
                   or(apt.apt_cmaq_in_codigo <> vTAB_APT.apt_cmaq_in_codigo)
                 );      
       end if;
    end;

procedure apt_inserir_apt(pfil_in_codigo in number,
                          pord_in_codigo in number,
                          pctl_in_codigo in number,
                          pplf_in_sqoperacao in number,
                          papt_dt_inclusao in date,
                          pcmaq_st_id varchar2,
                          pord_st_extenso varchar2,
                          --pusuario in varchar2,
                          presult in out sys_refcursor) as

--vapt_in_sequencia  IDP.apt_apontaordem.apt_in_sequencia%type;
--vplf_in_sqoperacao  IDP.apt_apontaordem.plf_in_sqoperacao%type;
--vapt_cmaq_in_codigo IDP.apt_apontaordem.apt_cmaq_in_codigo%type;

vexiste             char(1);
vctl_in_codigo      number;

begin
   vTAB_APT.Plf_In_Sqoperacao := pplf_in_sqoperacao;
   if vTAB_ORD.ord_in_codigo is null then
       for cORD in(
          select *
            from pro_ordens ord
           where ord.ord_in_codigo = pord_in_codigo
             and ord.fil_in_codigo = pfil_in_codigo
             and ord.ord_seq_in_codigo = pck_mega.achapadraodatabela(pfil_in_codigo,218, sysdate)
       )
       loop
          vTAB_ORD := cORD;
        end loop;
   end if;   
   p_programacaoordem;   
   vexiste := 'N';   
   if vTAB_APT.Plf_In_Sqoperacao is null then
      vTAB_APT.Plf_In_Sqoperacao := vTAB_PRG.Plf_In_Sqoperacao;
   end if;           
   if vexiste = 'S' then
      if vTAB_APT.apt_maq_in_codigo is null then
         vTAB_APT.apt_maq_in_codigo := vTAB_PRG.maq_in_codigo;
      end if;
      if vTAB_APT.ctl_in_codigo is null and pctl_in_codigo is not null then
         vTAB_APT.ctl_in_codigo := pctl_in_codigo;
      end if;
      if vTAB_APT.plf_in_sqoperacao is null and pplf_in_sqoperacao is not null then         
         vTAB_APT.Plf_In_Sqoperacao :=  pplf_in_sqoperacao;
       elsif vTAB_APT.plf_in_sqoperacao is null and pplf_in_sqoperacao is null and pord_st_extenso is not null then 
         vTAB_APT.Plf_In_Sqoperacao :=  substr(pord_st_extenso,11,13);
      end if;
      if vTAB_APT.Apt_Ord_St_Extenso is null and pord_st_extenso is not null then
         vTAB_APT.Apt_Ord_St_Extenso :=  pord_st_extenso;
      end if;
      begin
         update IDP.apt_apontaordem apt
            set apt.ctl_in_codigo = vTAB_APT.ctl_in_codigo,
                apt.apt_ord_st_extenso = vTAB_APT.apt_ord_st_extenso,
                apt.plf_in_sqoperacao = vTAB_APT.plf_in_sqoperacao,
                apt.apt_cmaq_in_codigo = vTAB_APT.apt_cmaq_in_codigo,
                apt.apt_maq_in_codigo = vTAB_APT.apt_maq_in_codigo
          where apt.apt_in_sequencia = vTAB_APT.apt_in_sequencia;         
      exception when others then
         null;
      end;
         
   Else
      vTAB_APT.org_tab_in_codigo := vTAB_ORD.org_tab_in_codigo;
      vTAB_APT.org_pad_in_codigo := vTAB_ORD.org_pad_in_codigo;
      vTAB_APT.org_in_codigo     := vTAB_ORD.org_in_codigo;
      vTAB_APT.org_tau_st_codigo := vTAB_ORD.org_tau_st_codigo;
      
      vTAB_APT.ord_tab_in_codigo := vTAB_ORD.ord_tab_in_codigo;
      vTAB_APT.ord_seq_in_codigo := vTAB_ORD.ord_seq_in_codigo;
      vTAB_APT.ord_in_codigo     := vTAB_ORD.ord_in_codigo;
      
      vTAB_APT.fil_in_codigo     := vTAB_ORD.fil_in_codigo;
      
      vTAB_APT.ctl_in_codigo     := pctl_in_codigo;
      vTAB_APT.apt_maq_in_codigo := vTAB_PRG.maq_in_codigo;
      if vTAB_APT.Plf_In_Sqoperacao is null and pord_st_extenso is not null then
         vTAB_APT.Plf_In_Sqoperacao :=  to_number(substr(pord_st_extenso,11,13));      
      end if;
      vTAB_APT.apt_dt_apontamento := papt_dt_inclusao;
      -- Busca nos parâmetros do tipo de ordem
      for cTPO in(
         select tpo.* 
           from pro_tipoordens tpo
          where tpo.tpo_tab_in_codigo  = vTAB_ORD.tpo_tab_in_codigo
            and tpo.tpo_pad_in_codigo  = vTAB_ORD.tpo_pad_in_codigo
            and tpo.tpo_st_codigo_tipo = vTAB_ORD.tpo_st_codigo_tipo     
         )
      loop
         vTAB_TPO := cTPO;
      end loop;   
      
      vTAB_APT.apt_ati_tab_in_codigo := 204;
      vTAB_APT.Apt_Ati_In_Codigo := vTAB_TPO.Ati_In_Codigoint;
      vTAB_APT.Apt_Maq_In_Codigo := vTAB_PRG.Maq_In_Codigo;
      vTAB_APT.apt_ch_status :=  'A';   
      vTAB_APT.apt_ord_st_extenso := pord_st_extenso;
      vTAB_APT.apt_ati_pad_in_codigo:= pck_mega.achapadraodatabela(vTAB_APT.Fil_In_Codigo,204,sysdate);            
      -- Busca o proxímo apontamento;
      begin
         select nvl(max(apt.apt_in_sequencia),0)+1
           into vTAB_APT.apt_in_sequencia
           from IDP.apt_apontaordem apt;
      exception when no_data_found then
         vTAB_APT.apt_in_sequencia := 1;
      end;      
      begin
         if vTAB_APT.org_in_codigo is not null then
            insert into IDP.apt_apontaordem values vTAB_APT;
         end if;
      exception when dup_val_on_index then
         null;
      end;      
      if (vTAB_ORD.ord_st_situacao <> 'AB') then
         -- abre ordem
         begin
            man_pck_ordem.p_abreordem(vTAB_ORD.org_pad_in_codigo
                                     ,vTAB_ORD.org_in_codigo
                                     ,vTAB_ORD.ord_seq_in_codigo
                                     ,vTAB_ORD.ord_in_codigo
                                     ,vTAB_ORD.fil_in_codigo
                                     ,vTAB_ORD.pro_pad_in_codigo
                                     ,vTAB_ORD.pro_in_codigo
                                     ,vTAB_ORD.cps_in_codigo
                                     ,vTAB_ORD.lis_in_revisao
                                     ,1
                                     ,'MEGA');
         end;
         -- atualiza status da demanda
         update pro_demanda_dep dde
            set dde.dde_st_situacao = man_pck_ordem.f_situacaodemanda('AB',dde.dde_re_qtde_necessaria,dde.dde_re_qtde_requisitada)
          where dde.org_tab_in_codigo  = vTAB_ORD.org_tab_in_codigo
            and dde.org_pad_in_codigo  = vTAB_ORD.org_pad_in_codigo
            and dde.org_in_codigo      = vTAB_ORD.org_in_codigo
            and dde.org_tau_st_codigo  = vTAB_ORD.org_tau_st_codigo
            and dde.ord_tab_in_codigo  = vTAB_ORD.ord_tab_in_codigo
            and dde.ord_seq_in_codigo  = vTAB_ORD.ord_seq_in_codigo
            and dde.ord_in_codigo      = vTAB_ORD.ord_in_codigo;
      end if;                     
   end if;
   commit;

  open presult for
     select apt.org_tab_in_codigo,
            apt.org_pad_in_codigo,
            apt.org_in_codigo,
            apt.org_tau_st_codigo,
            apt.ord_tab_in_codigo,
            apt.ord_seq_in_codigo,
            apt.ord_in_codigo,
            apt.apt_in_sequencia,
            apt.fil_in_codigo,
            apt.plf_in_sqoperacao
       from IDP.apt_apontaordem apt
      where apt.org_tab_in_codigo = 53
        and apt.org_pad_in_codigo = 1
        and apt.org_tau_st_codigo = 'G'
        and apt.fil_in_codigo     = vTAB_APT.fil_in_codigo
        and apt.apt_in_sequencia  = vTAB_APT.apt_in_sequencia
        and apt.ord_tab_in_codigo = 218
        and apt.ord_seq_in_codigo = vTAB_APT.ord_seq_in_codigo
        and apt.ord_in_codigo     = vTAB_APT.ord_in_codigo
        and (apt.ctl_in_codigo    = vTAB_APT.ctl_in_codigo or vTAB_APT.ctl_in_codigo is null);
end apt_inserir_apt;

procedure cli_p_lotes_ordem(pfil_in_codigo in number,
                            pord_in_codigo in number,
                            pctl_in_codigo in number,
                            pplf_in_sqoperacao in number,
                            papt_dt_inclusao in varchar2,
                            pmvp_in_sequencia in number,
                            pmvl_re_quantidade in number,
                            pmvl_re_quantmov in number,
                            pmvl_re_quantref in number,
                            ppro_in_codigo in number,
                            plote_obs varchar2,
                            pdoc_origem varchar2,
                            preferencia varchar2,
                            pusu_in_codigo number,
                            pdestino varchar2,
                            plote varchar2,
                            ppro_st_conversor varchar2,
                            plote_dt_inclusao varchar2,
                            pcmaq_st_id varchar2,
                            pord_st_id varchar2,
                            ppro_st_id varchar2,
                            pmvl_re_qtdeajustada in number,
                            pord_st_extenso varchar2,
                            plote_fornecedor varchar2,
                            presult in out sys_refcursor) as

vmvl_st_loteforne IDP.cus_lotes_temp.mvl_st_loteforne%type;
vlot_in_sequencia IDP.cus_lotes_temp.lot_in_sequencia%type;
vmvl_re_quantmov IDP.cus_lotes_temp.mvl_re_quantmov%type;
vmvl_st_referencia IDP.cus_lotes_temp.mvl_st_referencia%type;
vord_seq_in_codigo pro_ordemlotesub.ord_seq_in_codigo%type;
--vpro_pad_in_codigo IDP.apt_apontaordem_lote.pro_pad_in_codigo%type;
vexiste_apt char(1);
vlote_tipo  char(1);
vmensagem varchar2(200);
vmensagem_Sub varchar2(200);
vapt_in_sequencia   IDP.apt_apontaordem.apt_in_sequencia%type;
vplf_in_sqoperacao  IDP.apt_apontaordem.plf_in_sqoperacao%type;
vapt_cmaq_in_codigo IDP.apt_apontaordem.apt_cmaq_in_codigo%type;
vorl_st_slote  pro_ordemlotesub.orl_st_slotefabricacao%type;
vati_pad_in_codigo pro_atividade.ati_pad_in_codigo%type;
vorg_in_codigo  IDP.apt_apontaordem.org_in_codigo%type;
vcodreferencia est_produtos.rfc_in_codigo%type;
vQTDE_CONVERTIDA est_movsumarizado.mvs_re_quantidade%type;
vTPO_ST_CODIGO_TIPO pro_ordens.tpo_st_codigo_tipo%type;
vAPT_DT_INCLUSAO date;
vcmaq_st_id varchar2(13);
vloop number;
vAPT tAPT;
vFMT_ST_CODIGO est_prouni.fmt_st_codigo%type;
v_integrado char(1);

begin
   /*Raise_application_error(-20000,
                            pfil_in_codigo||';'||
                            pord_in_codigo||';'||
                            pctl_in_codigo||';'||
                            pplf_in_sqoperacao||';'||
                            papt_dt_inclusao||';'||
                            pmvp_in_sequencia||';'||
                            pmvl_re_quantidade||';'||
                            pmvl_re_quantmov||';'||
                            pmvl_re_quantref||';'||
                            ppro_in_codigo||';'||
                            plote_obs||';'||
                            pdoc_origem||';'||
                            preferencia||';'||
                            pusu_in_codigo||';'||
                            pdestino||';'||
                            plote||';'||
                            ppro_st_conversor||';'||
                            plote_dt_inclusao||';'||
                            pcmaq_st_id||';'||
                            pord_st_id||';'||
                            ppro_st_id||';'||
                            pmvl_re_qtdeajustada);*/
   vAPT_DT_INCLUSAO := to_date(papt_dt_inclusao,'yyyy/mm/dd');
   --vAPT_DT_INCLUSAO := to_date(papt_dt_inclusao,'dd/mm/yyyy');
   vmensagem := null;
   vmensagem_Sub := null;
   v_integrado := 'S';
   vpro_pad_in_codigo:=pck_mega.achapadraodatabela(pfil_in_codigo,100,sysdate);
   
   vlot_in_sequencia:=pord_in_codigo;
   if pfil_in_codigo = 312 then
      vcmaq_st_id := null;
   else
      vcmaq_st_id := pcmaq_st_id;
   end if;
   
   -- carrega dados iniciais da ordem    
   for cORD in(
      select *
        from pro_ordens ord
       where ord.ord_in_codigo = pord_in_codigo
         and ord.fil_in_codigo = pfil_in_codigo
         and ord.ord_seq_in_codigo = pck_mega.achapadraodatabela(pfil_in_codigo,218, sysdate)
        )
   loop
      vTAB_ORD := cORD;
   end loop;   
   -- Verifica se existe apontamento em aberto;   
   v_apontamento := f_valida_apontamento;
   if v_apontamento = 'S' then
      -- Busca o apontamento em aberto para a ordem;
      for cAPO in(
         select apt.*
           from IDP.apt_apontaordem apt
          where apt.fil_in_codigo = vTAB_ORD.fil_in_codigo
            and apt.ord_in_codigo = vTAB_ORD.ord_in_codigo
            and (apt.plf_in_sqoperacao = pplf_in_sqoperacao or pplf_in_sqoperacao is null)
            and apt.apt_ch_status = 'A')
      loop
         vTAB_APT := cAPO;         
         p_programacaoordem;
      end loop;
   else
      --Cria um novo apontamento; 
      apt_inserir_apt(pfil_in_codigo,
                      pord_in_codigo,
                      pctl_in_codigo,
                      pplf_in_sqoperacao,
                      vAPT_DT_INCLUSAO,
                      vcmaq_st_id,
                      pord_st_extenso,
                   --pusu_in_codigo,
                   vAPT);
      loop
         FETCH vAPT
          INTO vTAB_APT.org_tab_in_codigo,
               vTAB_APT.org_pad_in_codigo,
               vTAB_APT.org_in_codigo,
               vTAB_APT.org_tau_st_codigo,
               vTAB_APT.ord_tab_in_codigo,
               vTAB_APT.ord_seq_in_codigo,
               vTAB_APT.ord_in_codigo,
               vTAB_APT.apt_in_sequencia,
               vTAB_APT.fil_in_codigo,
               vTAB_APT.Plf_In_Sqoperacao;
         EXIT WHEN vAPT%NOTFOUND;
      end loop;
   end if;   
   vAPT_LOTE.apt_in_sequencia  := vTAB_APT.apt_in_sequencia;
   vAPT_LOTE.org_tab_in_codigo := vTAB_APT.org_tab_in_codigo;
   vAPT_LOTE.org_pad_in_codigo := vTAB_APT.org_pad_in_codigo;
   vAPT_LOTE.org_in_codigo     := vTAB_APT.org_in_codigo;
   vAPT_LOTE.org_tau_st_codigo := vTAB_APT.org_tau_st_codigo;
   vAPT_LOTE.ord_tab_in_codigo := vTAB_APT.ord_tab_in_codigo;
   vAPT_LOTE.ord_seq_in_codigo := vTAB_APT.ord_seq_in_codigo;
   vAPT_LOTE.ord_in_codigo     := vTAB_APT.ord_in_codigo;
   vAPT_LOTE.Fil_In_Codigo     := vTAB_APT.Fil_In_Codigo;
   vAPT_LOTE.Ctl_In_Codigo     := pctl_in_codigo;
   vAPT_LOTE.mvp_in_sequencia  := pmvp_in_sequencia;
   vAPT_LOTE.ord_st_id         := pord_st_id;
   vAPT_LOTE.pro_st_id         := ppro_st_id;
   vAPT_LOTE.cmaq_st_id        := pcmaq_st_id;
   vAPT_LOTE.Orl_St_Comprador := plote_fornecedor;
   if length(pdoc_origem) = 22 then
      vAPT_LOTE.orl_doc_origem := to_char(to_number(substr(pdoc_origem,9,8)));
   else
      vAPT_LOTE.orl_doc_origem := pdoc_origem;
   end if;
   if pmvl_re_quantref > 0 then
      vAPT_LOTE.orl_re_qtdref := pmvl_re_quantref;
      vAPT_LOTE.apt_ref_in_codigo := 2;
   else
      vAPT_LOTE.orl_re_qtdref := 0;
   end if;
   -- Valida integração de produção;
   v_integrado := f_valida_intproducao;
   --Raise_application_error(-20000, v_integrado);
   if  v_integrado = 'N' then
      --verifica se o item possui referência
      Begin
         Select nvl(pro.rfc_in_codigo,0)
           Into vcodreferencia
           From est_produtos pro
          Where pro.pro_tab_in_codigo = 100
            and pro.pro_pad_in_codigo = vpro_pad_in_codigo
            and pro.pro_in_codigo = ppro_in_codigo;
      Exception When NO_DATA_FOUND Then
         vcodreferencia:=0;
      End;
      If (vcodreferencia = 0) Then
         vmvl_st_referencia:='*';
      Else
         vmvl_st_referencia := preferencia;
      End if;

      if (preferencia is null and vcodreferencia <> 0) then
          raise_application_error(-20000, 'e obrigatorio informar as caracteristicas!');
      end if;
      if (preferencia ='null' and vcodreferencia <> 0) then
          raise_application_error(-20000, 'e obrigatorio informar as caracteristicas!');
      end if;

      for cAPT in (
         select *
           from IDP.apt_apontaordem apo
          where apo.ord_in_codigo = pord_in_codigo
            and apo.fil_in_codigo = pfil_in_codigo
            and apo.apt_in_sequencia = vTAB_APT.apt_in_sequencia)
      loop         

         vorg_in_codigo :=cAPT.org_in_codigo;
         vord_seq_in_codigo:=cAPT.ord_seq_in_codigo;
         vapt_in_sequencia:= cAPT.apt_in_sequencia;

         begin
            select 'P'
              into vlote_tipo
              from pro_ordens op
             where op.org_in_codigo = cAPT.org_in_codigo
               and op.fil_in_codigo = cAPT.fil_in_codigo
               and op.ord_in_codigo = cAPT.ord_in_codigo
               and op.pro_in_codigo = ppro_in_codigo;
         exception when no_data_found then
            vlote_tipo:='S';
         end;
         begin
            select OP.TPO_ST_CODIGO_TIPO
              into vTPO_ST_CODIGO_TIPO
              from pro_ordens op
             where op.org_in_codigo = cAPT.org_in_codigo
               and op.fil_in_codigo = cAPT.fil_in_codigo
               and op.ord_in_codigo = cAPT.ord_in_codigo;
         exception when no_data_found then
               vTPO_ST_CODIGO_TIPO:= NULL;
         end;         
         vmvl_re_quantmov :=pmvl_re_quantmov;
         if pmvp_in_sequencia is null then
            begin
               select count(1)+ 1
                 into vorl_st_slote
                 from IDP.apt_apontaordem_lote x
                where x.org_tau_st_codigo = 'G'
                  and x.org_tab_in_codigo = 53
                  and x.ord_seq_in_codigo = cAPT.ord_seq_in_codigo
                  and x.org_in_codigo     = cAPT.org_in_codigo
                  and x.ord_in_codigo     = cAPT.ord_in_codigo
                  and x.ord_tab_in_codigo = 218
                  and x.org_pad_in_codigo = 1;
            exception when no_data_found then
               vorl_st_slote:= 1;
            end;
         else
            vorl_st_slote:= pmvp_in_sequencia;
         end if;
         
         if plote is null then
            vMVL_ST_LOTEFORNE:=IDP.CLI_PCK_ESPECIFICOSMANUF.CUS_F_TABFILSEQLOTE(cAPT.ORG_IN_CODIGO,cAPT.FIL_IN_CODIGO,218,vLOT_IN_SEQUENCIA);
         else
            vMVL_ST_LOTEFORNE:=plote;
         end if;
         if vlote_tipo = 'P' then
            vAPT_SUB.org_tab_in_codigo      := cAPT.Org_Tab_In_Codigo;
            vAPT_SUB.org_pad_in_codigo      := cAPT.Org_Pad_In_Codigo;
            vAPT_SUB.org_in_codigo          := cAPT.org_in_codigo;
            vAPT_SUB.org_tau_st_codigo      := cAPT.Org_Tau_St_Codigo;
            vAPT_SUB.ord_tab_in_codigo      := cAPT.Ord_Tab_In_Codigo;
            vAPT_SUB.ord_seq_in_codigo      := cAPT.ord_seq_in_codigo;
            vAPT_SUB.ord_in_codigo          := cAPT.ord_in_codigo;
            vAPT_SUB.orl_st_lotefabricacao  := vmvl_st_loteforne;
            vAPT_SUB.orl_st_slotefabricacao := vorl_st_slote;
            vAPT_SUB.orl_st_referencia      := vmvl_st_referencia;
            vAPT_SUB.orl_re_qtdlote         := vmvl_re_quantmov;
            vAPT_SUB.orl_re_qtdrecebida     := 0;
            vAPT_SUB.orl_re_qtdrefugada     := 0;
            vAPT_SUB.orl_re_qtdinterditada  := 0;
            vAPT_SUB.orl_ch_origem          := 'O';
            begin
               insert into pro_ordemlotesub values vAPT_SUB;
               vmensagem_Sub := 'Ok';
            exception 
               when dup_val_on_index then 
                  vmensagem_Sub := 'Ok';
               when others then
                  vmensagem_Sub := 'Erro';
            end;
         else
            vmensagem_Sub := 'Ok';
         end if;
         vAPT_LOTE.orl_st_lotefabricacao  := vmvl_st_loteforne;
         vAPT_LOTE.orl_st_slotefabricacao := vorl_st_slote;
         vAPT_LOTE.orl_st_referencia      := vmvl_st_referencia;
         vAPT_LOTE.pro_tab_in_codigo      := 100;
         vAPT_LOTE.pro_pad_in_codigo      := vpro_pad_in_codigo;
         vAPT_LOTE.pro_in_codigo          := ppro_in_codigo;
         vAPT_LOTE.orl_re_qtdlote         := vmvl_re_quantmov;
         vAPT_LOTE.orl_re_unidade         := pmvl_re_quantidade;
         vAPT_LOTE.orl_st_tipolote        := vlote_tipo;
         vAPT_LOTE.Apt_Ch_Status          := 'A';
         vAPT_LOTE.orl_st_loteobs         := plote_obs;
         vAPT_LOTE.fil_in_codigo          := cAPT.fil_in_codigo;         
         vAPT_LOTE.ord_st_destino         := pdestino;
         vAPT_LOTE.apt_dt_inclusao        := to_date(plote_dt_inclusao,'yyyy-mm-dd');
         begin
            insert into IDP.apt_apontaordem_lote values vAPT_LOTE;
            vMENSAGEM:='Ok';
         exception 
            when dup_val_on_index then
               vMENSAGEM:='Ok';
            when others then
               vMENSAGEM:='Erro';
         end;
      end loop;
      if vMENSAGEM = 'Ok' and vmensagem_Sub = 'Ok' then
         --Raise_application_error(-20000, 'Passou aqui linha 1061');
         commit;
      else
         --Raise_application_error(-20000, 'APTO '||vMENSAGEM||' SUB '||vmensagem_Sub);
         rollback;
      end if;
   else
      vMENSAGEM := 'Ok';
      vmensagem_Sub := 'Ok';
   end if;
   p_SumarizaLotes(vTAB_APT.APT_IN_SEQUENCIA);   
open presult for
select apt.apt_in_sequencia,
       vMENSAGEM as MENSAGEM,
       vmensagem_Sub as MENSAGEM_SUB
  from IDP.apt_apontaordem_lote apt
 where apt.org_in_codigo = vTAB_APT.ORG_IN_CODIGO
   and apt.fil_in_codigo = vTAB_APT.FIL_IN_CODIGO
   and apt.apt_in_sequencia = vTAB_APT.APT_IN_SEQUENCIA
   and apt.ctl_in_codigo = pCTL_IN_CODIGO
   and apt.mvp_in_sequencia = pMVP_IN_SEQUENCIA;

end cli_p_lotes_ordem;

Procedure p_inseredemanda_lotes(pRESULT IN OUT SYS_REFCURSOR
                               ,pFIL_IN_CODIGO IN NUMBER
                               ,pORD_IN_CODIGO IN NUMBER
                               ,pCTL_IN_CODIGO IN NUMBER
                               ,pPLF_IN_SQOPERACAO in number
                               ,pAPT_DT_INCLUSAO IN VARCHAR2
                               ,pMVD_IN_SEQUENCIA IN NUMBER
                               ,pMVS_ST_LOTEFORNE In IDP.APT_APONTADEMANDA_ESTOQUE.MVS_ST_LOTEFORNE%Type
                               ,pAPT_RE_QUANTIDADE In IDP.APT_APONTAORDEM.APT_RE_QUANTIDADE%Type
                               ,pCMAQ_ST_ID varchar2
                               ,pORD_ST_ID varchar2
                               ,pORD_ST_EXTENSO varchar2) Is
    vAPT_RE_QTDESELECIONADA IDP.APT_APONTADEMANDA_ESTOQUE.APT_RE_QTDESELECIONADA%Type;
    vDDE_RE_DEMANDA         IDP.APT_APONTADEMANDA_ESTOQUE.APT_RE_QTDESELECIONADA%Type;
    vDDE_RE_QTDE_DISPONIVEL IDP.APT_APONTADEMANDA.DDE_RE_QTDE_DISPONIVEL%Type;
    vDDE_BO_RESERVADO       IDP.APT_APONTADEMANDA.DDE_BO_RESERVADO%TYPE;
    vAPT_IN_SEQUENCIA IDP.APT_APONTAORDEM.APT_IN_SEQUENCIA%TYPE;
    vORD_SEQ_IN_CODIGO PRO_ORDEMLOTESUB.ORD_SEQ_IN_CODIGO%TYPE;
    VATI_PAD_IN_CODIGO PRO_ATIVIDADE.ATI_PAD_IN_CODIGO%TYPE;
    vEXISTE_APT CHAR(1);
    vMENSAGEM varchar2(300);
    vDDE_IN_OPERACAO  pro_prog_ordem.plf_in_sqoperacao%type;
    vMAQ_IN_CODIGO    IDP.apt_apontaordem.apt_maq_in_codigo%type;
    vMVS_IN_SEQUENCIA IDP.apt_apontademanda_estoque.mvs_in_sequencia%type;
    vNAT_PAD_IN_CODIGO est_movsumarizado.nat_pad_in_codigo%type;
    vALM_TAB_IN_CODIGO est_produtolocaliza.alm_tab_in_codigo%type;
    vALM_PAD_IN_CODIGO est_produtolocaliza.alm_pad_in_codigo%type;
    vALM_IN_CODIGO     est_produtolocaliza.alm_in_codigo%type;
    vLOC_IN_CODIGO     est_produtolocaliza.loc_in_codigo%type;
    --vPRO_PAD_IN_CODIGO est_produtolocaliza.pro_pad_in_codigo%type;
    vPLF_IN_SQOPERACAO pro_prog_ordem.plf_in_sqoperacao%type;
    vAPT_DT_INCLUSAO date;
    vAPT tAPT;
    v_integrado char(1);
    vEXISTE_DEM CHAR(1);
    v_temlote CHAR(1);    
  Begin
     vDDE_RE_QTDE_DISPONIVEL := 0;
     vTAB_DEP := null;
     vMENSAGEM:=null;
     v_integrado := 'S';
     v_temlote := 'N'; 
        /* Raise_application_error(-20000,
                             vTAB_APT.fil_in_codigo||';'||
                             pFIL_IN_CODIGO||';'||
                             pORD_IN_CODIGO||';'||
                             pCTL_IN_CODIGO||';'||
                             pPLF_IN_SQOPERACAO||';'||
                             pAPT_DT_INCLUSAO||';'||
                             pMVD_IN_SEQUENCIA||';'||
                             pMVS_ST_LOTEFORNE||';'||
                             pAPT_RE_QUANTIDADE



     );*/
--     Raise_application_error(-20000, );


     vAPT_DT_INCLUSAO := to_date(papt_dt_inclusao,'yyyy/mm/dd');
     vORD_SEQ_IN_CODIGO:= PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,218,sysdate);
     VATI_PAD_IN_CODIGO:= PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,204,sysdate);
     -- carrega dados iniciais da ordem    
     for cORD in(
        select *
          from pro_ordens ord
         where ord.ord_in_codigo = pord_in_codigo
           and ord.fil_in_codigo = pfil_in_codigo
           and ord.ord_seq_in_codigo = pck_mega.achapadraodatabela(pfil_in_codigo,218, sysdate)
        )
     loop
        vTAB_ORD := cORD;
     end loop;
     v_apontamento := f_valida_apontamento;
     if v_apontamento = 'S' then     
        -- Busca o apontamento em aberto para a ordem;
        for cAPO in(
           select apt.*
             from IDP.apt_apontaordem apt
             where apt.fil_in_codigo = vTAB_ORD.fil_in_codigo
               and apt.ord_in_codigo = vTAB_ORD.ord_in_codigo
               and (apt.plf_in_sqoperacao = pplf_in_sqoperacao or pplf_in_sqoperacao is null)
               and apt.apt_ch_status = 'A')
        loop
           vTAB_APT := cAPO;
           p_programacaoordem;
        end loop;
     else
        apt_inserir_apt(pfil_in_codigo,
                        pord_in_codigo,
                        pctl_in_codigo,
                        pPLF_IN_SQOPERACAO,
                        vAPT_DT_INCLUSAO,
                        pCMAQ_ST_ID,
                        pord_st_extenso,
                        --pusu_in_codigo,
                        vAPT);
        LOOP
           FETCH vAPT
            INTO vTAB_APT.org_tab_in_codigo,
                 vTAB_APT.org_pad_in_codigo,
                 vTAB_APT.org_in_codigo,
                 vTAB_APT.org_tau_st_codigo,
                 vTAB_APT.ord_tab_in_codigo,
                 vTAB_APT.ord_seq_in_codigo,
                 vTAB_APT.ord_in_codigo,
                 vTAB_APT.apt_in_sequencia,
                 vTAB_APT.fil_in_codigo,
                 vTAB_APT.Plf_In_Sqoperacao;
           EXIT WHEN vAPT%NOTFOUND;
        END LOOP;
     end if;
        
     vAPT_DEM.org_tab_in_codigo  := vTAB_ORD.org_tab_in_codigo;
     vAPT_DEM.org_pad_in_codigo  := vTAB_ORD.org_pad_in_codigo;
     vAPT_DEM.org_in_codigo      := vTAB_ORD.org_in_codigo;
     vAPT_DEM.org_tau_st_codigo  := vTAB_ORD.org_tau_st_codigo;
     vAPT_DEM.ord_tab_in_codigo  := vTAB_ORD.ord_tab_in_codigo;
     vAPT_DEM.ord_seq_in_codigo  := vTAB_ORD.ord_seq_in_codigo;
     vAPT_DEM.ord_in_codigo      := vTAB_ORD.ord_in_codigo;
     vAPT_DEM.Fil_In_Codigo      := vTAB_ORD.Fil_In_Codigo;
     vAPT_DEM.Mvd_In_Sequencia   := pMVD_IN_SEQUENCIA;
     vAPT_DEM.mvs_st_loteforne   := pMVS_ST_LOTEFORNE;
     vAPT_DEM.Dde_St_Situacao    := 'A';
     v_integrado := f_valida_intdemanda;
     if v_integrado = 'N' then             
        vAPT_DEM.apt_in_sequencia   := vTAB_APT.Apt_In_Sequencia;     
        vAPT_DEM.com_tab_in_codigo  := 100;
        vAPT_DEM.com_pad_in_codigo  := PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,100,sysdate);
        vAPT_DEM.fil_in_codigo      := vTAB_APT.FIL_IN_CODIGO;
        vAPT_DEM.Ctl_In_Codigo      := pCTL_IN_CODIGO;     
        vAPT_DEM.mvs_in_reserva     := 0;
        vAPT_DEM.Alm_Tab_In_Codigo  := 105;
        vAPT_DEM.Alm_Pad_In_Codigo  := PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,105,sysdate);
        vAPT_DEM.nat_tab_in_codigo  := 143;
        vAPT_DEM.Nat_Pad_In_Codigo  := PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,143,sysdate);
        vAPT_DEM.nat_st_codigo      := 'DP';                
        vAPT_DEM.mvs_dt_entrada     := to_date('01/01/2000','dd/mm/yyyy');
        vAPT_DEM.mvs_dt_validade    := to_date('01/01/2000','dd/mm/yyyy');
        vAPT_DEM.Plf_In_Sqoperacao  := pPLF_IN_SQOPERACAO;
        vAPT_DEM.Apt_Re_Qtdeselecionada := pAPT_RE_QUANTIDADE;
        vAPT_DEM.Ord_St_Id              := pORD_ST_ID;
        vAPT_DEM.Cmaq_St_Id             := pCMAQ_ST_ID;
        vAPT_DEM.apt_re_qtdeaviso       := 0;
        vAPT_DEM.apt_bo_loteestoque     := 'S';
        vRCI := null;
        -- Valida lote do aviso de recebimento customizado
        if vAPT_DEM.Fil_In_Codigo = 3 then              
           for cRCI in(
              select *
                from cli_aviso_receb_item_lote rci
               where rci.mvl_st_loteforne = vAPT_DEM.Mvs_St_Loteforne
              )
           loop
              vRCI := cRCI;
              vAPT_DEM.apt_re_qtdeaviso := vRCI.Iar_Re_Quantconf;
              vAPT_DEM.apt_bo_loteestoque := 'N';
              for cIAR in(
                 select *
                   from cli_aviso_receb_item iar
                  where iar.org_tab_in_codigo = vRCI.org_tab_in_codigo
                    and iar.org_pad_in_codigo = vRCI.org_pad_in_codigo
                    and iar.org_in_codigo     = vRCI.org_in_codigo    
                    and iar.org_tau_st_codigo = vRCI.org_tau_st_codigo
                    and iar.avr_in_codigo     = vRCI.avr_in_codigo    
                    and iar.iar_in_sequencia  = vRCI.iar_in_sequencia 
                   
                 )
              loop
                 vAPT_DEM.Com_In_Codigo := cIAR.Pro_In_Codigo;
              end loop;
           end loop;
        end if;     
        BEGIN
           select nvl(max(t.mvs_in_sequencia),0)+1
             into vMVS_IN_SEQUENCIA
             from IDP.apt_apontademanda_estoque t
            where t.org_tab_in_codigo = vTAB_APT.Org_Tab_In_Codigo
              and t.org_pad_in_codigo = vTAB_APT.Org_Pad_In_Codigo
              and t.org_in_codigo     = vTAB_APT.Org_In_Codigo
              and t.ord_tab_in_codigo = vTAB_APT.Ord_Tab_In_Codigo
              and t.ord_seq_in_codigo = vTAB_APT.Ord_Seq_In_Codigo
              and t.ord_in_codigo     = vTAB_APT.Ord_In_Codigo
              and t.fil_in_codigo     = vTAB_APT.Fil_In_Codigo;
        EXCEPTION WHEN OTHERS THEN
           vMVS_IN_SEQUENCIA:=1;
        END;
        vAPT_DEM.mvs_in_sequencia   := vMVS_IN_SEQUENCIA;

        For cDEM in (
           Select m.org_tab_in_codigo,
                  m.org_pad_in_codigo,
                  m.org_in_codigo,
                  m.org_tau_st_codigo,
                  m.fil_in_codigo,
                  m.pro_tab_in_codigo,
                  m.pro_pad_in_codigo,
                  m.pro_in_codigo,
                  p.uni_st_unidade,
                  m.mvs_st_referencia,
                  m.alm_tab_in_codigo,
                  m.alm_pad_in_codigo,
                  m.alm_in_codigo,
                  m.loc_in_codigo,
                  m.mvs_in_reserva,
                  m.nat_tab_in_codigo,
                  m.nat_pad_in_codigo,
                  m.nat_st_codigo,
                  m.mvs_dt_entrada,
                  m.mvs_dt_validade,
              sum(m.mvs_re_quantidade) mvs_re_quantidade
             From est_movsumarizado m,
                  est_produtos p
            where m.pro_tab_in_codigo = p.pro_tab_in_codigo
              and m.pro_pad_in_codigo = p.pro_pad_in_codigo
              and m.pro_in_codigo     = p.pro_in_codigo
              and m.org_in_codigo     = vTAB_APT.ORG_IN_CODIGO
              and m.fil_in_codigo     = vTAB_APT.Fil_In_Codigo
              and m.mvs_st_loteforne  = pMVS_ST_LOTEFORNE
           group by
                  m.org_tab_in_codigo,
                  m.org_pad_in_codigo,
                  m.org_in_codigo,
                  m.org_tau_st_codigo,
                  m.fil_in_codigo,
                  m.pro_tab_in_codigo,
                  m.pro_pad_in_codigo,
                  m.pro_in_codigo,
                  p.uni_st_unidade,
                  m.mvs_st_referencia,
                  m.alm_tab_in_codigo,
                  m.alm_pad_in_codigo,
                  m.alm_in_codigo,
                  m.loc_in_codigo,
                  m.mvs_in_reserva,
                  m.nat_tab_in_codigo,
                  m.nat_pad_in_codigo,
                  m.nat_st_codigo,
                  m.mvs_dt_entrada,
                  m.mvs_dt_validade
           union all
           select lot.org_tab_in_codigo,
                  lot.org_pad_in_codigo,
                  lot.org_in_codigo,
                  lot.org_tau_st_codigo,
                  lot.fil_in_codigo,
                  lot.pro_tab_in_codigo,
                  lot.pro_pad_in_codigo,
                  lot.pro_in_codigo,
                  pro.uni_st_unidade,
                  lot.orl_st_referencia mvs_st_referencia,
                  0 alm_tab_in_codigo,
                  0 alm_pad_in_codigo,
                  0 alm_in_codigo,
                  0 loc_in_codigo,
                  0 mvs_in_reserva,
                  143 nat_tab_in_codigo,
                  PCK_MEGA.ACHAPADRAODATABELA(lot.Fil_In_Codigo,143,sysdate) as nat_pad_in_codigo,
                  'DP' nat_st_codigo,
                  to_date('01/01/2000','dd/mm/yyyy') mvs_dt_entrada,
                  to_date('01/01/2000','dd/mm/yyyy') mvs_dt_validade,
                  sum(lot.orl_re_qtdlote) mvs_re_quantidade
             from IDP.apt_apontaordem_lote lot,
                  IDP.apt_apontaordem apt,
                  est_produtos pro
            where lot.pro_tab_in_codigo = pro.pro_tab_in_codigo
              and lot.pro_pad_in_codigo = pro.pro_pad_in_codigo
              and lot.pro_in_codigo     = pro.pro_in_codigo
              and apt.apt_in_sequencia  = lot.apt_in_sequencia
              and apt.org_in_codigo     = vTAB_APT.Org_In_Codigo
              and apt.apt_ch_status = 'A'
              and lot.orl_st_lotefabricacao = pMVS_ST_LOTEFORNE
            group by lot.org_tab_in_codigo,
                  lot.org_pad_in_codigo,
                  lot.org_in_codigo,
                  lot.org_tau_st_codigo,
                  lot.fil_in_codigo,
                  lot.pro_tab_in_codigo,
                  lot.pro_pad_in_codigo,
                  lot.pro_in_codigo,
                  pro.uni_st_unidade,
                  lot.orl_st_referencia
         )
        loop           
           vAPT_DEM.mvs_dt_entrada     := cDEM.Mvs_Dt_Entrada;
           vAPT_DEM.mvs_dt_validade    := cDEM.Mvs_Dt_Validade;
           vAPT_DEM.Saldo_Estoque      := cDEM.Mvs_Re_Quantidade;
           IF cDEM.loc_in_codigo = 0 THEN
              begin
                 select distinct
                        pal.alm_tab_in_codigo,
                        pal.alm_pad_in_codigo,
                        pal.alm_in_codigo,
                        pal.loc_in_codigo
                   into vAPT_DEM.alm_tab_in_codigo,
                        vAPT_DEM.alm_pad_in_codigo,
                        vAPT_DEM.alm_in_codigo,
                        vAPT_DEM.loc_in_codigo
                   from est_produtolocaliza pal
                  where pal.pro_tab_in_codigo = cDEM.pro_tab_in_codigo
                    and pal.pro_pad_in_codigo = cDEM.pro_pad_in_codigo
                    and pal.pro_in_codigo     = cDEM.pro_in_codigo
                    and pal.org_in_codigo     = vTAB_APT.ORG_IN_CODIGO
                    and pal.fil_in_codigo     = vTAB_APT.FIL_IN_CODIGO
                    and pal.prl_in_prioridade = 1;
              exception when others then
                 null;
              end;
           else
              vAPT_DEM.ALM_TAB_IN_CODIGO:= cDEM.alm_tab_in_codigo;
              vAPT_DEM.ALM_PAD_IN_CODIGO:= cDEM.alm_pad_in_codigo;
              vAPT_DEM.ALM_IN_CODIGO    := cDEM.alm_in_codigo;
              vAPT_DEM.LOC_IN_CODIGO    := cDEM.loc_in_codigo;
           end if;
           vAPT_DEM.com_in_codigo      := cDEM.Pro_In_Codigo;           
           -- Dados da demanda dependente da Ordem;
           vEXISTE_APT := 'N';
           vEXISTE_DEM := 'N';
           for cDEE in (
              select *
                from pro_demanda_dep dep
               where dep.com_tab_in_codigo = cDEM.pro_tab_in_codigo
                 and dep.com_pad_in_codigo = cDEM.pro_pad_in_codigo
                 and dep.com_in_codigo     = cDEM.pro_in_codigo
                 and dep.org_tab_in_codigo = vAPT_DEM.Org_Tab_In_Codigo
                 and dep.org_pad_in_codigo = vAPT_DEM.Org_Pad_In_Codigo
                 and dep.org_in_codigo     = vAPT_DEM.Org_In_Codigo
                 and dep.org_tau_st_codigo = vAPT_DEM.Org_Tau_St_Codigo
                 and dep.ord_tab_in_codigo = vAPT_DEM.Ord_Tab_In_Codigo
                 and dep.ord_seq_in_codigo = vAPT_DEM.Ord_Seq_In_Codigo
                 and dep.ord_in_codigo     = vAPT_DEM.Ord_In_Codigo
                 and dep.com_tab_in_codigo = vAPT_DEM.Com_Tab_In_Codigo
                 and dep.com_pad_in_codigo = vAPT_DEM.Com_Pad_In_Codigo
                 and dep.com_in_codigo     = vAPT_DEM.Com_In_Codigo
                 order by dep.dde_in_operacao)
           loop
              vTAB_DEP := cDEE;
              vEXISTE_DEM := 'S';
           end loop;
           if vEXISTE_DEM = 'N' then
              for cDEP in (
                 select dep.*
                   from pro_demanda_dep dep
                  where dep.org_tab_in_codigo = vTAB_APT.Org_Tab_In_Codigo
                    and dep.org_pad_in_codigo = vTAB_APT.Org_Pad_In_Codigo
                    and dep.org_in_codigo     = vTAB_APT.Org_In_Codigo
                    and dep.org_tau_st_codigo = vTAB_APT.Org_Tau_St_Codigo
                    and dep.ord_tab_in_codigo = vTAB_APT.Ord_Tab_In_Codigo
                    and dep.ord_seq_in_codigo = vTAB_APT.Ord_Seq_In_Codigo
                    and dep.ord_in_codigo     = vTAB_APT.Ord_In_Codigo
                    and dep.dde_in_operacao   = (select max(dde.dde_in_operacao)
                                                   from pro_demanda_dep dde
                                                  where dde.org_tab_in_codigo = dep.org_tab_in_codigo
                                                    and dde.org_pad_in_codigo = dep.org_pad_in_codigo
                                                    and dde.org_in_codigo     = dep.org_in_codigo
                                                    and dde.org_tau_st_codigo = dep.org_tau_st_codigo
                                                    and dde.ord_tab_in_codigo = dep.ord_tab_in_codigo
                                                    and dde.ord_seq_in_codigo = dep.ord_seq_in_codigo
                                                    and dde.ord_in_codigo     = dep.ord_in_codigo)
                  and rownum < 2)
              loop
                 vTAB_DEP := cDEP;
                 vTAB_DEP.Dde_In_Operacao := vTAB_DEP.Dde_In_Operacao;
                 vTAB_DEP.Com_In_Codigo   := vAPT_DEM.Com_In_Codigo;
                 -- Inserir o registro na tabela de demanda dependente;
                 insert into pro_demanda_dep values vTAB_DEP;
              end loop;
           end if;
           -- Atualiza a sequencia da operação;
           vAPT_DEM.dde_in_operacao := vTAB_DEP.Dde_In_Operacao;
           vAPT_DEM.Dde_Dt_Necessidade := vTAB_DEP.Dde_Dt_Necessidade;

           vAPT_DEM.nat_pad_in_codigo  := cDEM.nat_pad_in_codigo;
           vAPT_DEM.mvs_st_referencia  := cDEM.mvs_st_referencia;           
           -- Atualiza a qtde do lote para a qtde do movimento;
           if vRCI.Iar_Re_Quantconf is not null then
              if vRCI.Iar_Re_Quantconf = vAPT_DEM.Apt_Re_Qtdeselecionada then             
                 vAPT_DEM.apt_re_qtdeselecionada := cDEM.mvs_re_quantidade;
              end if;
              vAPT_DEM.Apt_Bo_Loteestoque     := 'S';   
           elsif pAPT_RE_QUANTIDADE = 9999 then
              vAPT_DEM.apt_re_qtdeselecionada := cDEM.mvs_re_quantidade;
           else
              vAPT_DEM.apt_re_qtdeselecionada := pAPT_RE_QUANTIDADE;
           end if;
           vAPT_DEM.ctl_in_codigo          := pCTL_IN_CODIGO;
           vAPT_DEM.mvd_in_sequencia       := pMVD_IN_SEQUENCIA;
           -- carrega tabela de demandas;
           vTAB_DDE.Apt_In_Sequencia:= vAPT_DEM.Apt_In_Sequencia;           
           vAPT_DEM.DDE_ST_SITUACAO := 'A';
           begin
              insert into IDP.apt_apontademanda_estoque values vAPT_DEM;
              vMENSAGEM:='Ok';
              v_temlote := 'S';
           exception when others then
              vMENSAGEM:='Erro';
           end;
           Begin
              p_cria_demanda;
           Exception When others then 
              null;
           End;
           if vMENSAGEM ='Ok' then
              Commit;
           else
              rollback;
           end if;
        End Loop;        
        if v_temlote = 'N' then
           begin
              insert into IDP.apt_apontademanda_estoque values vAPT_DEM;
              vMENSAGEM:='Ok';           
           exception when others then
              vMENSAGEM:='Erro';
           end;
           if vMENSAGEM ='Ok' then
              Commit;
           else
              rollback;
           end if;
        end if;
     else
        if vAPT_DEM.Mvd_In_Sequencia is null then
           vAPT_DEM.Mvd_In_Sequencia := pMVD_IN_SEQUENCIA;
           vAPT_DEM.ctl_in_codigo := pCTL_IN_CODIGO;  
          update IDP.apt_apontademanda_estoque apd
             set apd.mvd_in_sequencia = pMVD_IN_SEQUENCIA,
                 apd.ctl_in_codigo    = pCTL_IN_CODIGO
           where apd.apt_in_sequencia = vAPT_DEM.apt_in_sequencia
             and apd.mvs_in_sequencia = vAPT_DEM.mvs_in_sequencia;          
        end if;
        vMENSAGEM := 'Ok';
     end if;

     OPEN pRESULT FOR
        SELECT vMENSAGEM MENSAGEM,
               decode(apd.com_in_codigo,null,'Não Encontrado!',apd.com_in_codigo) as PRO_IN_CODIGO,
               apd.apt_in_sequencia as APT_IN_SEQUENCIA,
               apd.mvs_in_sequencia as MVS_IN_SEQUENCIA
          FROM IDP.apt_apontademanda_estoque apd
         where apd.org_in_codigo    = vAPT_DEM.Org_In_Codigo
           and apd.ord_in_codigo    = vAPT_DEM.Ord_In_Codigo
           and apd.fil_in_codigo    = vAPT_DEM.Fil_In_Codigo
           and apd.apt_in_sequencia = vAPT_DEM.Apt_In_Sequencia
           and apd.ctl_in_codigo    = vAPT_DEM.Ctl_In_Codigo
           and apd.mvd_in_sequencia = vAPT_DEM.Mvd_In_Sequencia;

  End p_inseredemanda_lotes;
  Procedure p_inseredemanda_lotespro(pRESULT IN OUT SYS_REFCURSOR
                                    ,pFIL_IN_CODIGO IN NUMBER
                                    ,pORD_IN_CODIGO IN NUMBER
                                    ,pCTL_IN_CODIGO IN NUMBER
                                    ,pPLF_IN_SQOPERACAO in number
                                    ,pAPT_DT_INCLUSAO IN VARCHAR2
                                    ,pMVD_IN_SEQUENCIA IN NUMBER
                                    ,pMVS_ST_LOTEFORNE In IDP.APT_APONTADEMANDA_ESTOQUE.MVS_ST_LOTEFORNE%Type
                                    ,pAPT_RE_QUANTIDADE In IDP.APT_APONTAORDEM.APT_RE_QUANTIDADE%Type
                                    ,pCMAQ_ST_ID varchar2
                                    ,pORD_ST_ID varchar2
                                    ,pORD_ST_EXTENSO varchar2
                                    ,pPRO_IN_CODIGO in number) Is
    vAPT_RE_QTDESELECIONADA IDP.APT_APONTADEMANDA_ESTOQUE.APT_RE_QTDESELECIONADA%Type;
    vDDE_RE_DEMANDA         IDP.APT_APONTADEMANDA_ESTOQUE.APT_RE_QTDESELECIONADA%Type;
    vDDE_RE_QTDE_DISPONIVEL IDP.APT_APONTADEMANDA.DDE_RE_QTDE_DISPONIVEL%Type;
    vDDE_BO_RESERVADO       IDP.APT_APONTADEMANDA.DDE_BO_RESERVADO%TYPE;
    vAPT_IN_SEQUENCIA IDP.APT_APONTAORDEM.APT_IN_SEQUENCIA%TYPE;
    vORD_SEQ_IN_CODIGO PRO_ORDEMLOTESUB.ORD_SEQ_IN_CODIGO%TYPE;
    VATI_PAD_IN_CODIGO PRO_ATIVIDADE.ATI_PAD_IN_CODIGO%TYPE;
    vEXISTE_APT CHAR(1);
    vMENSAGEM varchar2(300);
    vDDE_IN_OPERACAO  pro_prog_ordem.plf_in_sqoperacao%type;
    vMAQ_IN_CODIGO    IDP.apt_apontaordem.apt_maq_in_codigo%type;
    vMVS_IN_SEQUENCIA IDP.apt_apontademanda_estoque.mvs_in_sequencia%type;
    vNAT_PAD_IN_CODIGO est_movsumarizado.nat_pad_in_codigo%type;
    vALM_TAB_IN_CODIGO est_produtolocaliza.alm_tab_in_codigo%type;
    vALM_PAD_IN_CODIGO est_produtolocaliza.alm_pad_in_codigo%type;
    vALM_IN_CODIGO     est_produtolocaliza.alm_in_codigo%type;
    vLOC_IN_CODIGO     est_produtolocaliza.loc_in_codigo%type;
    --vPRO_PAD_IN_CODIGO est_produtolocaliza.pro_pad_in_codigo%type;
    vPLF_IN_SQOPERACAO pro_prog_ordem.plf_in_sqoperacao%type;
    vAPT_DT_INCLUSAO date;
    vAPT tAPT;
    v_integrado char(1);
    vEXISTE_DEM CHAR(1);
    v_temlote CHAR(1);    
  Begin
     vDDE_RE_QTDE_DISPONIVEL := 0;
     vTAB_DEP := null;
     vMENSAGEM:=null;
     v_integrado := 'S';
     v_temlote := 'N'; 
         /*Raise_application_error(-20000,
                             vTAB_APT.fil_in_codigo||';'||
                             pFIL_IN_CODIGO||';'||
                             pORD_IN_CODIGO||';'||
                             pCTL_IN_CODIGO||';'||
                             pPLF_IN_SQOPERACAO||';'||
                             pAPT_DT_INCLUSAO||';'||
                             pMVD_IN_SEQUENCIA||';'||
                             pMVS_ST_LOTEFORNE||';'||
                             pAPT_RE_QUANTIDADE||';'||
                             pPRO_IN_CODIGO


     );*/
--     Raise_application_error(-20000, );
     vAPT_DT_INCLUSAO := to_date(papt_dt_inclusao,'yyyy/mm/dd');
     vORD_SEQ_IN_CODIGO:= PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,218,sysdate);
     VATI_PAD_IN_CODIGO:= PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,204,sysdate);
     -- carrega dados iniciais da ordem    
     for cORD in(
        select *
          from pro_ordens ord
         where ord.ord_in_codigo = pord_in_codigo
           and ord.fil_in_codigo = pfil_in_codigo
           and ord.ord_seq_in_codigo = pck_mega.achapadraodatabela(pfil_in_codigo,218, sysdate)
        )
     loop
        vTAB_ORD := cORD;
     end loop;
     v_apontamento := f_valida_apontamento;
     if v_apontamento = 'S' then     
        -- Busca o apontamento em aberto para a ordem;
        for cAPO in(
           select apt.*
             from IDP.apt_apontaordem apt
             where apt.fil_in_codigo = vTAB_ORD.fil_in_codigo
               and apt.ord_in_codigo = vTAB_ORD.ord_in_codigo
               and (apt.plf_in_sqoperacao = pplf_in_sqoperacao or pplf_in_sqoperacao is null)
               and apt.apt_ch_status = 'A')
        loop
           vTAB_APT := cAPO;
           p_programacaoordem;
        end loop;
     else
        apt_inserir_apt(pfil_in_codigo,
                        pord_in_codigo,
                        pctl_in_codigo,
                        pPLF_IN_SQOPERACAO,
                        vAPT_DT_INCLUSAO,
                        pCMAQ_ST_ID,
                        pord_st_extenso,
                        --pusu_in_codigo,
                        vAPT);
        LOOP
           FETCH vAPT
            INTO vTAB_APT.org_tab_in_codigo,
                 vTAB_APT.org_pad_in_codigo,
                 vTAB_APT.org_in_codigo,
                 vTAB_APT.org_tau_st_codigo,
                 vTAB_APT.ord_tab_in_codigo,
                 vTAB_APT.ord_seq_in_codigo,
                 vTAB_APT.ord_in_codigo,
                 vTAB_APT.apt_in_sequencia,
                 vTAB_APT.fil_in_codigo,
                 vTAB_APT.Plf_In_Sqoperacao;
           EXIT WHEN vAPT%NOTFOUND;
        END LOOP;
     end if;
        
     vAPT_DEM.org_tab_in_codigo  := vTAB_ORD.org_tab_in_codigo;
     vAPT_DEM.org_pad_in_codigo  := vTAB_ORD.org_pad_in_codigo;
     vAPT_DEM.org_in_codigo      := vTAB_ORD.org_in_codigo;
     vAPT_DEM.org_tau_st_codigo  := vTAB_ORD.org_tau_st_codigo;
     vAPT_DEM.ord_tab_in_codigo  := vTAB_ORD.ord_tab_in_codigo;
     vAPT_DEM.ord_seq_in_codigo  := vTAB_ORD.ord_seq_in_codigo;
     vAPT_DEM.ord_in_codigo      := vTAB_ORD.ord_in_codigo;
     vAPT_DEM.Fil_In_Codigo      := vTAB_ORD.fil_in_codigo;
     vAPT_DEM.mvd_in_sequencia   := pMVD_IN_SEQUENCIA;
     vAPT_DEM.mvs_st_loteforne   := pMVS_ST_LOTEFORNE;
     vAPT_DEM.apt_in_sequencia   := vTAB_APT.apt_in_sequencia;
     if pPRO_IN_CODIGO > 0 then
        vAPT_DEM.Com_In_Codigo := pPRO_IN_CODIGO;
     end if;
     v_integrado := f_valida_intdemanda;
     
     if v_integrado = 'N' then             
        vAPT_DEM.apt_in_sequencia   := vTAB_APT.apt_in_sequencia;     
        vAPT_DEM.com_tab_in_codigo  := 100;
        vAPT_DEM.com_pad_in_codigo  := PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,100,sysdate);
        vAPT_DEM.fil_in_codigo      := vTAB_APT.fil_in_codigo;
        vAPT_DEM.ctl_in_codigo      := pCTL_IN_CODIGO;     
        vAPT_DEM.mvs_in_reserva     := 0;
        vAPT_DEM.Alm_Tab_In_Codigo  := 105;
        vAPT_DEM.Alm_Pad_In_Codigo  := PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,105,sysdate);
        vAPT_DEM.nat_tab_in_codigo  := 143;
        vAPT_DEM.Nat_Pad_In_Codigo  := PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,143,sysdate);
        vAPT_DEM.nat_st_codigo      := 'DP';                
        vAPT_DEM.mvs_dt_entrada     := to_date('01/01/2000','dd/mm/yyyy');
        vAPT_DEM.mvs_dt_validade    := to_date('01/01/2000','dd/mm/yyyy');
        vAPT_DEM.Plf_In_Sqoperacao  := pPLF_IN_SQOPERACAO;
        vAPT_DEM.Apt_Re_Qtdeselecionada := pAPT_RE_QUANTIDADE;
        vAPT_DEM.Ord_St_Id              := pORD_ST_ID;
        vAPT_DEM.Cmaq_St_Id             := pCMAQ_ST_ID;
        vAPT_DEM.apt_re_qtdeaviso       := 0;
        vAPT_DEM.apt_bo_loteestoque     := 'S';
        vRCI := null;
        -- Valida lote do aviso de recebimento customizado
        if vAPT_DEM.Fil_In_Codigo = 3 then              
           for cRCI in(
              select *
                from cli_aviso_receb_item_lote rci
               where rci.mvl_st_loteforne = vAPT_DEM.Mvs_St_Loteforne
              )
           loop
              vRCI := cRCI;
              vAPT_DEM.apt_re_qtdeaviso := vRCI.Iar_Re_Quantconf;
              vAPT_DEM.apt_bo_loteestoque := 'N';
              for cIAR in(
                 select *
                   from cli_aviso_receb_item iar
                  where iar.org_tab_in_codigo = vRCI.org_tab_in_codigo
                    and iar.org_pad_in_codigo = vRCI.org_pad_in_codigo
                    and iar.org_in_codigo     = vRCI.org_in_codigo    
                    and iar.org_tau_st_codigo = vRCI.org_tau_st_codigo
                    and iar.avr_in_codigo     = vRCI.avr_in_codigo    
                    and iar.iar_in_sequencia  = vRCI.iar_in_sequencia 
                   
                 )
              loop
                 vAPT_DEM.Com_In_Codigo := cIAR.Pro_In_Codigo;
              end loop;
           end loop;
        end if;     
        BEGIN
           select nvl(max(t.mvs_in_sequencia),0)+1
             into vMVS_IN_SEQUENCIA
             from IDP.apt_apontademanda_estoque t
            where t.org_tab_in_codigo = vTAB_APT.Org_Tab_In_Codigo
              and t.org_pad_in_codigo = vTAB_APT.Org_Pad_In_Codigo
              and t.org_in_codigo     = vTAB_APT.Org_In_Codigo
              and t.ord_tab_in_codigo = vTAB_APT.Ord_Tab_In_Codigo
              and t.ord_seq_in_codigo = vTAB_APT.Ord_Seq_In_Codigo
              and t.ord_in_codigo     = vTAB_APT.Ord_In_Codigo
              and t.fil_in_codigo     = vTAB_APT.Fil_In_Codigo;
        EXCEPTION WHEN OTHERS THEN
           vMVS_IN_SEQUENCIA:=1;
        END;
        vAPT_DEM.mvs_in_sequencia   := vMVS_IN_SEQUENCIA;

        For cDEM in (
           Select m.org_tab_in_codigo,
                  m.org_pad_in_codigo,
                  m.org_in_codigo,
                  m.org_tau_st_codigo,
                  m.fil_in_codigo,
                  m.pro_tab_in_codigo,
                  m.pro_pad_in_codigo,
                  m.pro_in_codigo,
                  p.uni_st_unidade,
                  m.mvs_st_referencia,
                  m.alm_tab_in_codigo,
                  m.alm_pad_in_codigo,
                  m.alm_in_codigo,
                  m.loc_in_codigo,
                  m.mvs_in_reserva,
                  m.nat_tab_in_codigo,
                  m.nat_pad_in_codigo,
                  m.nat_st_codigo,
                  m.mvs_dt_entrada,
                  m.mvs_dt_validade,
              sum(m.mvs_re_quantidade) mvs_re_quantidade
             From est_movsumarizado m,
                  est_produtos p
            where m.pro_tab_in_codigo = p.pro_tab_in_codigo
              and m.pro_pad_in_codigo = p.pro_pad_in_codigo
              and m.pro_in_codigo     = p.pro_in_codigo
              and m.org_in_codigo     = vTAB_APT.ORG_IN_CODIGO
              and m.fil_in_codigo     = vTAB_APT.Fil_In_Codigo
              and (
                      (m.mvs_st_loteforne  = pMVS_ST_LOTEFORNE and pMVS_ST_LOTEFORNE <> '*')
                    or(m.pro_in_codigo  = pPRO_IN_CODIGO and pPRO_IN_CODIGO is not null)
                  )
           group by
                  m.org_tab_in_codigo,
                  m.org_pad_in_codigo,
                  m.org_in_codigo,
                  m.org_tau_st_codigo,
                  m.fil_in_codigo,
                  m.pro_tab_in_codigo,
                  m.pro_pad_in_codigo,
                  m.pro_in_codigo,
                  p.uni_st_unidade,
                  m.mvs_st_referencia,
                  m.alm_tab_in_codigo,
                  m.alm_pad_in_codigo,
                  m.alm_in_codigo,
                  m.loc_in_codigo,
                  m.mvs_in_reserva,
                  m.nat_tab_in_codigo,
                  m.nat_pad_in_codigo,
                  m.nat_st_codigo,
                  m.mvs_dt_entrada,
                  m.mvs_dt_validade
           union all
           select lot.org_tab_in_codigo,
                  lot.org_pad_in_codigo,
                  lot.org_in_codigo,
                  lot.org_tau_st_codigo,
                  lot.fil_in_codigo,
                  lot.pro_tab_in_codigo,
                  lot.pro_pad_in_codigo,
                  lot.pro_in_codigo,
                  pro.uni_st_unidade,
                  lot.orl_st_referencia mvs_st_referencia,
                  0 alm_tab_in_codigo,
                  0 alm_pad_in_codigo,
                  0 alm_in_codigo,
                  0 loc_in_codigo,
                  0 mvs_in_reserva,
                  143 nat_tab_in_codigo,
                  PCK_MEGA.ACHAPADRAODATABELA(lot.Fil_In_Codigo,143,sysdate) as nat_pad_in_codigo,
                  'DP' nat_st_codigo,
                  to_date('01/01/2000','dd/mm/yyyy') mvs_dt_entrada,
                  to_date('01/01/2000','dd/mm/yyyy') mvs_dt_validade,
                  sum(lot.orl_re_qtdlote) mvs_re_quantidade
             from IDP.apt_apontaordem_lote lot,
                  IDP.apt_apontaordem apt,
                  est_produtos pro
            where lot.pro_tab_in_codigo = pro.pro_tab_in_codigo
              and lot.pro_pad_in_codigo = pro.pro_pad_in_codigo
              and lot.pro_in_codigo     = pro.pro_in_codigo
              and apt.apt_in_sequencia  = lot.apt_in_sequencia
              and apt.org_in_codigo     = vTAB_APT.Org_In_Codigo
              and apt.apt_ch_status = 'A'
              and lot.orl_st_lotefabricacao = pMVS_ST_LOTEFORNE
            group by lot.org_tab_in_codigo,
                  lot.org_pad_in_codigo,
                  lot.org_in_codigo,
                  lot.org_tau_st_codigo,
                  lot.fil_in_codigo,
                  lot.pro_tab_in_codigo,
                  lot.pro_pad_in_codigo,
                  lot.pro_in_codigo,
                  pro.uni_st_unidade,
                  lot.orl_st_referencia
         )
        loop           
           vAPT_DEM.mvs_dt_entrada     := cDEM.Mvs_Dt_Entrada;
           vAPT_DEM.mvs_dt_validade    := cDEM.Mvs_Dt_Validade;
           vAPT_DEM.Saldo_Estoque      := cDEM.Mvs_Re_Quantidade;
           IF cDEM.loc_in_codigo = 0 THEN
              begin
                 select distinct
                        pal.alm_tab_in_codigo,
                        pal.alm_pad_in_codigo,
                        pal.alm_in_codigo,
                        pal.loc_in_codigo
                   into vAPT_DEM.alm_tab_in_codigo,
                        vAPT_DEM.alm_pad_in_codigo,
                        vAPT_DEM.alm_in_codigo,
                        vAPT_DEM.loc_in_codigo
                   from est_produtolocaliza pal
                  where pal.pro_tab_in_codigo = cDEM.pro_tab_in_codigo
                    and pal.pro_pad_in_codigo = cDEM.pro_pad_in_codigo
                    and pal.pro_in_codigo     = cDEM.pro_in_codigo
                    and pal.org_in_codigo     = vTAB_APT.ORG_IN_CODIGO
                    and pal.fil_in_codigo     = vTAB_APT.FIL_IN_CODIGO
                    and pal.prl_in_prioridade = 1;
              exception when others then
                 null;
              end;
           else
              vAPT_DEM.ALM_TAB_IN_CODIGO:= cDEM.alm_tab_in_codigo;
              vAPT_DEM.ALM_PAD_IN_CODIGO:= cDEM.alm_pad_in_codigo;
              vAPT_DEM.ALM_IN_CODIGO    := cDEM.alm_in_codigo;
              vAPT_DEM.LOC_IN_CODIGO    := cDEM.loc_in_codigo;
           end if;
           vAPT_DEM.com_in_codigo      := cDEM.Pro_In_Codigo;           
           -- Dados da demanda dependente da Ordem;
           vEXISTE_APT := 'N';
           vEXISTE_DEM := 'N';
           for cDEE in (
              select *
                from pro_demanda_dep dep
               where dep.com_tab_in_codigo = cDEM.pro_tab_in_codigo
                 and dep.com_pad_in_codigo = cDEM.pro_pad_in_codigo
                 and dep.com_in_codigo     = cDEM.pro_in_codigo
                 and dep.org_tab_in_codigo = vAPT_DEM.Org_Tab_In_Codigo
                 and dep.org_pad_in_codigo = vAPT_DEM.Org_Pad_In_Codigo
                 and dep.org_in_codigo     = vAPT_DEM.Org_In_Codigo
                 and dep.org_tau_st_codigo = vAPT_DEM.Org_Tau_St_Codigo
                 and dep.ord_tab_in_codigo = vAPT_DEM.Ord_Tab_In_Codigo
                 and dep.ord_seq_in_codigo = vAPT_DEM.Ord_Seq_In_Codigo
                 and dep.ord_in_codigo     = vAPT_DEM.Ord_In_Codigo
                 and dep.com_tab_in_codigo = vAPT_DEM.Com_Tab_In_Codigo
                 and dep.com_pad_in_codigo = vAPT_DEM.Com_Pad_In_Codigo
                 and dep.com_in_codigo     = vAPT_DEM.Com_In_Codigo
                 order by dep.dde_in_operacao)
           loop
              vTAB_DEP := cDEE;
              vEXISTE_DEM := 'S';
           end loop;
           if vEXISTE_DEM = 'N' then
              for cDEP in (
                 select dep.*
                   from pro_demanda_dep dep
                  where dep.org_tab_in_codigo = vTAB_APT.Org_Tab_In_Codigo
                    and dep.org_pad_in_codigo = vTAB_APT.Org_Pad_In_Codigo
                    and dep.org_in_codigo     = vTAB_APT.Org_In_Codigo
                    and dep.org_tau_st_codigo = vTAB_APT.Org_Tau_St_Codigo
                    and dep.ord_tab_in_codigo = vTAB_APT.Ord_Tab_In_Codigo
                    and dep.ord_seq_in_codigo = vTAB_APT.Ord_Seq_In_Codigo
                    and dep.ord_in_codigo     = vTAB_APT.Ord_In_Codigo
                    and dep.dde_in_operacao   = (select max(dde.dde_in_operacao)
                                                   from pro_demanda_dep dde
                                                  where dde.org_tab_in_codigo = dep.org_tab_in_codigo
                                                    and dde.org_pad_in_codigo = dep.org_pad_in_codigo
                                                    and dde.org_in_codigo     = dep.org_in_codigo
                                                    and dde.org_tau_st_codigo = dep.org_tau_st_codigo
                                                    and dde.ord_tab_in_codigo = dep.ord_tab_in_codigo
                                                    and dde.ord_seq_in_codigo = dep.ord_seq_in_codigo
                                                    and dde.ord_in_codigo     = dep.ord_in_codigo)
                  and rownum < 2)
              loop
                 vTAB_DEP := cDEP;
                 vTAB_DEP.Dde_In_Operacao := vTAB_DEP.Dde_In_Operacao;
                 vTAB_DEP.Com_In_Codigo   := vAPT_DEM.Com_In_Codigo;
                 -- Inserir o registro na tabela de demanda dependente;
                 insert into pro_demanda_dep values vTAB_DEP;
              end loop;
           end if;
           -- Atualiza a sequencia da operação;
           vAPT_DEM.dde_in_operacao := vTAB_DEP.Dde_In_Operacao;
           vAPT_DEM.Dde_Dt_Necessidade := vTAB_DEP.Dde_Dt_Necessidade;

           vAPT_DEM.nat_pad_in_codigo  := cDEM.nat_pad_in_codigo;
           vAPT_DEM.mvs_st_referencia  := cDEM.mvs_st_referencia;           
           -- Atualiza a qtde do lote para a qtde do movimento;
           if vRCI.Iar_Re_Quantconf is not null then
              if vRCI.Iar_Re_Quantconf = vAPT_DEM.Apt_Re_Qtdeselecionada then             
                 vAPT_DEM.apt_re_qtdeselecionada := cDEM.mvs_re_quantidade;
              end if;
              vAPT_DEM.Apt_Bo_Loteestoque     := 'S';   
           elsif pAPT_RE_QUANTIDADE = 9999 then
              vAPT_DEM.apt_re_qtdeselecionada := cDEM.mvs_re_quantidade;
           else
              vAPT_DEM.apt_re_qtdeselecionada := pAPT_RE_QUANTIDADE;
           end if;
           vAPT_DEM.ctl_in_codigo          := pCTL_IN_CODIGO;
           vAPT_DEM.mvd_in_sequencia       := pMVD_IN_SEQUENCIA;
           -- carrega tabela de demandas;
           vTAB_DDE.Apt_In_Sequencia:= vAPT_DEM.Apt_In_Sequencia;           
           begin
              insert into IDP.apt_apontademanda_estoque values vAPT_DEM;
              vMENSAGEM:='Ok';
              v_temlote := 'S';
           exception when others then
              vMENSAGEM:='Erro';
           end;
           Begin
              p_cria_demanda;
           Exception When others then 
              null;
           End;
           if vMENSAGEM ='Ok' then
              Commit;
           else
              rollback;
           end if;
        End Loop;        
        if v_temlote = 'N' then
           begin
              insert into IDP.apt_apontademanda_estoque values vAPT_DEM;
              vMENSAGEM:='Ok';           
           exception when others then
              vMENSAGEM:='Erro';
           end;
           if vMENSAGEM ='Ok' then
              Commit;
           else
              rollback;
           end if;
        end if;
     else
        if vAPT_DEM.Mvd_In_Sequencia is null then
           vAPT_DEM.Mvd_In_Sequencia := pMVD_IN_SEQUENCIA;
           vAPT_DEM.ctl_in_codigo := pCTL_IN_CODIGO;  
          update IDP.apt_apontademanda_estoque apd
             set apd.mvd_in_sequencia = pMVD_IN_SEQUENCIA,
                 apd.ctl_in_codigo    = pCTL_IN_CODIGO
           where apd.apt_in_sequencia = vAPT_DEM.apt_in_sequencia
             and apd.mvs_in_sequencia = vAPT_DEM.mvs_in_sequencia;          
        end if;
        vMENSAGEM := 'Ok';
     end if;

     OPEN pRESULT FOR
        SELECT vMENSAGEM MENSAGEM,
               decode(apd.com_in_codigo,null,'Não Encontrado!',apd.com_in_codigo) as PRO_IN_CODIGO,
               apd.apt_in_sequencia as APT_IN_SEQUENCIA,
               apd.mvs_in_sequencia as MVS_IN_SEQUENCIA
          FROM IDP.apt_apontademanda_estoque apd
         where apd.org_in_codigo    = vAPT_DEM.Org_In_Codigo
           and apd.ord_in_codigo    = vAPT_DEM.Ord_In_Codigo
           and apd.fil_in_codigo    = vAPT_DEM.Fil_In_Codigo
           and apd.apt_in_sequencia = vAPT_DEM.Apt_In_Sequencia
           and apd.ctl_in_codigo    = vAPT_DEM.Ctl_In_Codigo
           and apd.mvd_in_sequencia = vAPT_DEM.Mvd_In_Sequencia;

  End p_inseredemanda_lotespro;

  function F_ConverteUnidade(pro_pad est_produtos.pro_pad_in_codigo%type,
                             pro_in est_produtos.pro_in_codigo%type,
                             unidadepad est_produtos.uni_pad_in_codigo%type,
                             unidadecon est_produtos.uni_st_unidade%type,
                             unidademat est_produtos.uni_st_unidade%type,
                             formatopad est_produtos.fmt_pad_in_codigo%type,
                             formatost est_produtos.fmt_st_codigo%type,
                             qtdeaconv number) return number
 is


  Result           number;
  Dec_Qtde         Number;
  Dec_Valor        Number;
  ValorFator       Number;
  QtdeConvertida   Number;
  StFormula        Varchar2(200);
  StFator          Char(1);
  ChTipoConversao  Char(2);
  StCaracteristica Char(3);
begin
  if UnidadeCon <> UnidadeMat then
   begin
     begin
       SELECT F.UNI_ST_FORMULA, F.UNI_ST_FATOR,
              B.FMT_CH_TIPOCONVERSAO, B.FMT_ST_CARACTERISTICA
              into
              StFormula, StFator,
              ChTipoConversao, StCaracteristica
       FROM IDP.APT_FATORUNIDADE F, EST_FORMATOS B
       WHERE F.UNI_TAB_IN_CODIGO    = 103
       AND   F.UNI_PAD_IN_CODIGO    = UnidadePad
       AND   F.UN1_ST_UNIDADE       = UnidadeCon
       AND   F.UN2_ST_UNIDADE       = UnidadeMat
       AND   F.FMT_TAB_IN_CODIGO    = 112
       AND   F.FMT_PAD_IN_CODIGO    = FormatoPad
       AND   F.FMT_ST_CODIGO        = FormatoSt
       AND   B.FMT_TAB_IN_CODIGO    = F.FMT_TAB_IN_CODIGO
       AND   B.FMT_PAD_IN_CODIGO    = F.FMT_PAD_IN_CODIGO
       AND   B.FMT_ST_CODIGO        = F.FMT_ST_CODIGO;
     Exception
       When No_Data_Found then
         begin
          Raise_Application_Error(-20001,
             'Não definido Fator/Unidade para conversão da Unidade '||UnidadeMat||' para '||UnidadeCon||', c/o Conversor '||
             FormatoSt||', do Ítem '||PRO_IN||' assumido a unidade do produto');
          Result := QtdeAConv;
         end;
     End;

     adm_pck_util.p_decimaisunidade(Pro_Pad, Pro_IN, UnidadePad, UnidadeCon, Dec_Qtde, Dec_Valor);

     if ChTipoConversao = 'FC' then
      begin  /* Fator de Calculo    */
        ValorFator := StFormula;
        if StFator = '*' then
           QtdeConvertida := Round((QtdeAConv * ValorFator), Dec_Qtde);
        else
           QtdeConvertida := Round((QtdeAConv / ValorFator), Dec_Qtde);
        end if;
      end;
     end if;
     Result := QtdeConvertida;
   end;
  else
    Result := QtdeAConv;
  End If;

      return(Result);
 end F_ConverteUnidade;

 procedure apt_teste(pvalor varchar2, pretorno out sys_refcursor)  as

 begin

 open pretorno for
   select 'testar' teste from dual;

  end;

function funcout (y out varchar2) return varchar2 is

begin
   y := 'tested';
   return 'returned';
 end;

procedure p_GeraMovimentoEstoque_New is     
  CURSOR C_MOVESTOQUETAB IS
     SELECT * 
       FROM TABLE(CAST(ADM_PCK_MOVIMENTOESTOQUE.GETTABLEMOV AS EST_TYP_MOVESTOQUETAB));
 VTABMOV C_MOVESTOQUETAB%ROWTYPE;
 CURSOR C_LOTESTAB IS
        SELECT * 
          FROM TABLE(CAST(ADM_PCK_MOVIMENTOESTOQUE.GETTABLELOTES AS EST_TYP_LOTESMOVTAB));
 VTABITEM C_LOTESTAB%ROWTYPE;
 begin
    BEGIN
       ADM_PCK_MOVIMENTOESTOQUE.INICIALIZA;
    END;
    IF vTAB_MVT.first IS NOT NULL THEN
       FOR i IN vTAB_MVT.FIRST .. vTAB_MVT.LAST LOOP
          --IF VTABMOV.TPM_IN_CODIGO IS NOT NULL THEN
            VTABMOV.ORG_TAB_IN_CODIGO := vTAB_MVT(i).ORG_TAB_IN_CODIGO;
            VTABMOV.ORG_PAD_IN_CODIGO := vTAB_MVT(i).ORG_PAD_IN_CODIGO;
            VTABMOV.ORG_IN_CODIGO := vTAB_MVT(i).ORG_IN_CODIGO;
            VTABMOV.ORG_TAU_ST_CODIGO := vTAB_MVT(i).ORG_TAU_ST_CODIGO;
            VTABMOV.SER_TAB_IN_CODIGO := vTAB_MVT(i).SER_TAB_IN_CODIGO;
            VTABMOV.SER_IN_SEQUENCIA := vTAB_MVT(i).SER_IN_SEQUENCIA;
            VTABMOV.MVT_IN_LANCAM := vTAB_MVT(i).MVT_IN_LANCAM;
            VTABMOV.FIL_IN_CODIGO := vTAB_MVT(i).FIL_IN_CODIGO;
            VTABMOV.ACAO_TAB_IN_CODIGO := vTAB_MVT(i).ACAO_TAB_IN_CODIGO;
            VTABMOV.ACAO_PAD_IN_CODIGO := vTAB_MVT(i).ACAO_PAD_IN_CODIGO;
            VTABMOV.ACAO_IN_CODIGO := vTAB_MVT(i).ACAO_IN_CODIGO;
            VTABMOV.ACAOM_IN_SEQUENCIA := vTAB_MVT(i).ACAOM_IN_SEQUENCIA; -- null
            VTABMOV.MVT_CH_ORIGEM := vTAB_MVT(i).MVT_CH_ORIGEM;
            VTABMOV.TPM_TAB_IN_CODIGO := vTAB_MVT(i).TPM_TAB_IN_CODIGO;
            VTABMOV.TPM_PAD_IN_CODIGO := vTAB_MVT(i).TPM_PAD_IN_CODIGO;
            VTABMOV.TPM_IN_CODIGO := vTAB_MVT(i).TPM_IN_CODIGO;--
            VTABMOV.MVT_ST_ENTRSAIDA := vTAB_MVT(i).MVT_ST_ENTRSAIDA;--'ED';
            VTABMOV.MVT_ST_NUMDOC := vTAB_MVT(i).MVT_ST_NUMDOC;--'62154';
            VTABMOV.MVT_DT_DOCUMENTO := vTAB_MVT(i).MVT_DT_DOCUMENTO;--'29-nov-22';
            VTABMOV.MVT_DT_MOVIMENTO := vTAB_MVT(i).MVT_DT_MOVIMENTO;--'29-nov-22';
            VTABMOV.USU_IN_INCLUSAO := vTAB_MVT(i).USU_IN_INCLUSAO;--73;
            VTABMOV.MVT_DT_INCLUSAO := vTAB_MVT(i).MVT_DT_INCLUSAO;--'29-nov-22';
            VTABMOV.USU_IN_ALTERA := vTAB_MVT(i).USU_IN_ALTERA;--73;
            VTABMOV.MVT_DT_ALTERA := vTAB_MVT(i).MVT_DT_ALTERA;--'29-nov-22';
            VTABMOV.MVT_IN_VINCULO := vTAB_MVT(i).MVT_IN_VINCULO;--Null;
            VTABMOV.PRO_TAB_IN_CODIGO := vTAB_MVT(i).PRO_TAB_IN_CODIGO;--100;
            VTABMOV.PRO_PAD_IN_CODIGO := vTAB_MVT(i).PRO_PAD_IN_CODIGO;--1;
            VTABMOV.PRO_IN_CODIGO := vTAB_MVT(i).PRO_IN_CODIGO;--2775;
            VTABMOV.APL_TAB_IN_CODIGO := vTAB_MVT(i).APL_TAB_IN_CODIGO;--308;
            VTABMOV.APL_PAD_IN_CODIGO := vTAB_MVT(i).APL_PAD_IN_CODIGO;--1;
            VTABMOV.APL_IN_CODIGO := vTAB_MVT(i).APL_IN_CODIGO;--246;
            VTABMOV.MVT_RE_QUANTIDADE := vTAB_MVT(i).MVT_RE_QUANTIDADE;--51.84;
            VTABMOV.MVT_RE_AQUISICAO := vTAB_MVT(i).MVT_RE_AQUISICAO;--0;
            VTABMOV.MVT_RE_VLUNITARIO := vTAB_MVT(i).MVT_RE_VLUNITARIO;--0;
            VTABMOV.ALM_PAD_IN_CODIGO := vTAB_MVT(i).ALM_PAD_IN_CODIGO;--1;
            VTABMOV.ALM_IN_CODIGO := vTAB_MVT(i).ALM_IN_CODIGO;--5;
            VTABMOV.ALM_TAB_IN_CODIGO := vTAB_MVT(i).ALM_TAB_IN_CODIGO;--105;
            VTABMOV.LOC_IN_CODIGO := vTAB_MVT(i).LOC_IN_CODIGO;--1;
            VTABMOV.MVT_ST_DOCOFS := vTAB_MVT(i).MVT_ST_DOCOFS;--Null;
            VTABMOV.MVS_IN_RESERVA := vTAB_MVT(i).MVS_IN_RESERVA;--Null;
            VTABMOV.MVS_IN_RESERVADEST := vTAB_MVT(i).MVS_IN_RESERVADEST;--Null;
            VTABMOV.PRO_IN_CODIGODEST := vTAB_MVT(i).PRO_IN_CODIGODEST;--Null;
            VTABMOV.APL_IN_CODIGODEST := vTAB_MVT(i).APL_IN_CODIGODEST;--Null;
            VTABMOV.MVT_RE_QUANTIDADEDEST := vTAB_MVT(i).MVT_RE_QUANTIDADEDEST;--Null;
            VTABMOV.MVT_RE_QUANTIDADEMOV := vTAB_MVT(i).MVT_RE_QUANTIDADEMOV;--51.84;
            VTABMOV.MVT_RE_AQUISICAODEST := vTAB_MVT(i).MVT_RE_AQUISICAODEST;--Null;
            VTABMOV.MVT_BO_PENDENTE := vTAB_MVT(i).MVT_BO_PENDENTE;--Null;
            VTABMOV.NAT_TAB_IN_CODIGO := vTAB_MVT(i).NAT_TAB_IN_CODIGO;--Null;
            VTABMOV.NAT_PAD_IN_CODIGO := vTAB_MVT(i).NAT_PAD_IN_CODIGO;--Null;
            VTABMOV.NAT_ST_CODIGO := vTAB_MVT(i).NAT_ST_CODIGO;--Null;
            VTABMOV.NAT_ST_CODIGODEST := vTAB_MVT(i).NAT_ST_CODIGODEST;--Null;
            VTABMOV.ALM_IN_CODIGODEST := vTAB_MVT(i).ALM_IN_CODIGODEST;--Null;
            VTABMOV.LOC_IN_CODIGODEST := vTAB_MVT(i).LOC_IN_CODIGODEST;--Null;
            VTABMOV.TPM_IN_CODIGODEST := vTAB_MVT(i).TPM_IN_CODIGODEST;--Null;
            VTABMOV.IRE_CH_TIPORESERVA := vTAB_MVT(i).IRE_CH_TIPORESERVA;--Null;
            VTABMOV.CUS_TAB_IN_CODIGO  := vTAB_MVT(i).CUS_TAB_IN_CODIGO;--Null;
            VTABMOV.CUS_PAD_IN_CODIGO  := vTAB_MVT(i).CUS_PAD_IN_CODIGO;--Null;
            VTABMOV.CUS_IDE_ST_CODIGO  := vTAB_MVT(i).CUS_IDE_ST_CODIGO;--Null;
            VTABMOV.CUS_IN_REDUZIDO    := vTAB_MVT(i).CUS_IN_REDUZIDO;--Null;
            VTABMOV.PROJ_TAB_IN_CODIGO := vTAB_MVT(i).PROJ_TAB_IN_CODIGO;--Null;
            VTABMOV.PROJ_PAD_IN_CODIGO := vTAB_MVT(i).PROJ_PAD_IN_CODIGO;--Null;
            VTABMOV.PROJ_IDE_ST_CODIGO := vTAB_MVT(i).PROJ_IDE_ST_CODIGO;--Null;
            VTABMOV.PROJ_IN_REDUZIDO   := vTAB_MVT(i).PROJ_IN_REDUZIDO;--Null;
            VTABMOV.AGN_TAB_IN_CODIGO  := vTAB_MVT(i).AGN_TAB_IN_CODIGO;--Null; 
            VTABMOV.AGN_PAD_IN_CODIGO  := vTAB_MVT(i).AGN_PAD_IN_CODIGO;--Null; 
            VTABMOV.AGN_IN_CODIGO      := vTAB_MVT(i).AGN_IN_CODIGO;--Null;     
            VTABMOV.AGN_TAU_ST_CODIGO  := vTAB_MVT(i).AGN_TAU_ST_CODIGO;--Null; 
            VTABMOV.AGN_IN_CODIGODEST  := vTAB_MVT(i).AGN_IN_CODIGODEST;--Null; 
            VTABMOV.CFOP_TAB_IN_CODIGO := vTAB_MVT(i).CFOP_TAB_IN_CODIGO;--Null; 
            VTABMOV.CFOP_PAD_IN_CODIGO := vTAB_MVT(i).CFOP_PAD_IN_CODIGO;--Null; 
            VTABMOV.CFOP_IDE_ST_CODIGO := vTAB_MVT(i).CFOP_IDE_ST_CODIGO;--Null; 
            VTABMOV.CFOP_IN_CODIGO     := vTAB_MVT(i).CFOP_IN_CODIGO;--Null;     
            VTABMOV.MVT_BO_CONTROLATERCEIRO := vTAB_MVT(i).MVT_BO_CONTROLATERCEIRO;--Null;     
            VTABMOV.MVT_BO_SALDONEG    := vTAB_MVT(i).MVT_BO_SALDONEG;--'N'; 
            VTABMOV.MIE_IN_SEQMATTITDOC:= vTAB_MVT(i).MIE_IN_SEQMATTITDOC;--Null; 
            VTABMOV.MIE_IN_SEQMATTITDOCDEST:= vTAB_MVT(i).MIE_IN_SEQMATTITDOCDEST;--Null; 
            VTABMOV.FRO_SEQ_IN_CODIGO  := vTAB_MVT(i).FRO_SEQ_IN_CODIGO;--Null;
            VTABMOV.OSERV_IN_NUMERO    := vTAB_MVT(i).OSERV_IN_NUMERO;--Null;
            VTABMOV.ORF_TAB_IN_CODIGO  := vTAB_MVT(i).ORF_TAB_IN_CODIGO;--Null ;
            VTABMOV.ORF_PAD_IN_CODIGO  := vTAB_MVT(i).ORF_PAD_IN_CODIGO;--Null ;
            VTABMOV.ORF_IDE_ST_CODIGO  := vTAB_MVT(i).ORF_IDE_ST_CODIGO;--Null ;
            VTABMOV.ORF_IN_REDUZIDO    := vTAB_MVT(i).ORF_IN_REDUZIDO;--Null  ;
            VTABMOV.MVT_ST_ORIGEMPROCESSO := vTAB_MVT(i).MVT_ST_ORIGEMPROCESSO;--Null;
            VTABMOV.MVT_ST_OBSERVACAO := vTAB_MVT(i).MVT_ST_OBSERVACAO;--Null;
            VTABMOV.ROC_IN_SEQUENCIA := vTAB_MVT(i).ROC_IN_SEQUENCIA;--Null;
            VTABMOV.MVT_BO_VALIDAALMOXUSU := vTAB_MVT(i).MVT_BO_VALIDAALMOXUSU;--Null;
            VTABMOV.MVT_DT_MOVIMENTOOLD := vTAB_MVT(i).MVT_DT_MOVIMENTOOLD;--Null;
            VTABMOV.MVT_BO_ATUALIZAACAOMOV := vTAB_MVT(i).MVT_BO_ATUALIZAACAOMOV;--'N';
            /*dbms_output.put_line(VTABMOV.FIL_IN_CODIGO||chr(13)||
                                 VTABMOV.PRO_IN_CODIGO||chr(13)||
                                 VTABMOV.TPM_IN_CODIGO);*/
            ADM_PCK_MOVIMENTOESTOQUE.ADDRECORDMOV(VTABMOV);
          --END IF;               
       END LOOP;
    END IF;    
    -- Lotes  
    IF vTAB_MVL.first IS NOT NULL THEN
       FOR i IN vTAB_MVL.FIRST .. vTAB_MVL.LAST LOOP
          if vBXA.vmvt_in_lancam = vTAB_MVL(i).MVT_IN_LANCAM then
             vBXA.vgera_mvto := 'S';
          end if;
          VTABITEM.ORG_TAB_IN_CODIGO  := vTAB_MVL(i).ORG_TAB_IN_CODIGO;
          VTABITEM.ORG_PAD_IN_CODIGO  := vTAB_MVL(i).ORG_PAD_IN_CODIGO;
          VTABITEM.ORG_IN_CODIGO      := vTAB_MVL(i).ORG_IN_CODIGO;
          VTABITEM.ORG_TAU_ST_CODIGO  := vTAB_MVL(i).ORG_TAU_ST_CODIGO;
          VTABITEM.SER_TAB_IN_CODIGO  := vTAB_MVL(i).SER_TAB_IN_CODIGO;
          VTABITEM.SER_IN_SEQUENCIA   := vTAB_MVL(i).SER_IN_SEQUENCIA;
          VTABITEM.MVT_IN_LANCAM      := vTAB_MVL(i).MVT_IN_LANCAM;
          VTABITEM.FIL_IN_CODIGO      := vTAB_MVL(i).FIL_IN_CODIGO;
          VTABITEM.MVL_ST_LOTEFORNE   := vTAB_MVL(i).MVL_ST_LOTEFORNE;
          VTABITEM.MVT_DT_MOVIMENTO   := vTAB_MVL(i).MVT_DT_MOVIMENTO;
          VTABITEM.MVT_DT_VALIDADE    := vTAB_MVL(i).MVT_DT_VALIDADE;
          VTABITEM.PRO_TAB_IN_CODIGO  := vTAB_MVL(i).PRO_TAB_IN_CODIGO;
          VTABITEM.PRO_PAD_IN_CODIGO  := vTAB_MVL(i).PRO_PAD_IN_CODIGO;
          VTABITEM.PRO_IN_CODIGO      := vTAB_MVL(i).PRO_IN_CODIGO;
          VTABITEM.ALM_TAB_IN_CODIGO  := vTAB_MVL(i).ALM_TAB_IN_CODIGO;
          VTABITEM.ALM_PAD_IN_CODIGO  := vTAB_MVL(i).ALM_PAD_IN_CODIGO;
          VTABITEM.ALM_IN_CODIGO      := vTAB_MVL(i).ALM_IN_CODIGO;
          VTABITEM.LOC_IN_CODIGO      := vTAB_MVL(i).LOC_IN_CODIGO;
          VTABITEM.MVL_RE_QUANTIDADE  := vTAB_MVL(i).MVL_RE_QUANTIDADE;
          VTABITEM.MVL_RE_SALDO       := vTAB_MVL(i).MVL_RE_SALDO;
          VTABITEM.NAT_TAB_IN_CODIGO  := vTAB_MVL(i).NAT_TAB_IN_CODIGO;
          VTABITEM.NAT_PAD_IN_CODIGO  := vTAB_MVL(i).NAT_PAD_IN_CODIGO;
          VTABITEM.NAT_ST_CODIGO      := vTAB_MVL(i).NAT_ST_CODIGO;
          VTABITEM.MVL_DT_ENTRADA     := vTAB_MVL(i).MVL_DT_ENTRADA;
          VTABITEM.MVL_IN_RESERVA     := vTAB_MVL(i).MVL_IN_RESERVA;
          VTABITEM.MVL_ST_REFERENCIA  := TRIM(vTAB_MVL(i).MVL_ST_REFERENCIA);
          VTABITEM.MVL_RE_QTDERESERVA := vTAB_MVL(i).MVL_RE_QTDERESERVA;
          VTABITEM.PRO_IN_CODIGODEST  := vTAB_MVL(i).PRO_IN_CODIGODEST;
          VTABITEM.MVS_IN_RESERVADEST := vTAB_MVL(i).MVS_IN_RESERVADEST;
          VTABITEM.NAT_ST_CODIGODEST  := vTAB_MVL(i).NAT_ST_CODIGODEST;
          VTABITEM.NAT_CH_TIPO        := vTAB_MVL(i).NAT_CH_TIPO;
          VTABITEM.MIE_IN_SEQMATTITDOC:= vTAB_MVL(i).MIE_IN_SEQMATTITDOC;
          VTABITEM.MIE_IN_SEQMATTITDOCDEST:= vTAB_MVL(i).MIE_IN_SEQMATTITDOCDEST;
          ADM_PCK_MOVIMENTOESTOQUE.ADDRECORDLOTESMOV(VTABITEM => VTABITEM);
       END LOOP;
    END IF; 
    if vBXA.vreq_in_sequencia is not null then
       if vBXA.vgera_mvto = 'S' then
          --begin
             ADM_PCK_MOVIMENTOESTOQUE.ATUALIZAMOVESTQ(OPERACAO => 'I');
          /*exception when others then
             v_Encerra := 'N';    
          end;*/
       end if;
    else
       --begin
       ADM_PCK_MOVIMENTOESTOQUE.ATUALIZAMOVESTQ(OPERACAO => 'I');
       /*exception when others then
          v_Encerra := 'N';    
       end;*/
    end if;      
  end p_GeraMovimentoEstoque_New;

  procedure P_SincronizarBaixas is
  vFIL CUS_TB_FILIAL_DEPARA%rowtype;
  vMVT_IN_LANCAM est_movimento.mvt_in_lancam%type;
  vSALDO number;
  begin     
     -- Movimentos
     IF vTAB_MVT.first IS NOT NULL THEN
        FOR i IN vTAB_MVT.FIRST .. vTAB_MVT.LAST LOOP
           for cFIL in (
              select *
                from CUS_TB_FILIAL_DEPARA fil
               where fil.ori_org_in_codigo = vTAB_MVT(i).ORG_IN_CODIGO
                 and fil.ori_fil_in_codigo = vTAB_MVT(i).FIL_IN_CODIGO
                 and fil.cad_in_sequencial = 1
           )
           loop
              vFIL := cFIL;
           end loop;
           -- Carrega dados do movimento na nova filial
           vMVT_IN_LANCAM := vTAB_MVT(i).Mvt_In_Lancam;
           vTAB_MVT(i).org_in_codigo      := vFIL.Des_Org_In_Codigo;
           vTAB_MVT(i).fil_in_codigo      := vFIL.Des_fil_In_Codigo;
           vTAB_MVT(i).Acao_Pad_In_Codigo := Pck_Mega.AchaPadraoDaTabela(vFIL.Des_Fil_In_Codigo, 55, SYSDATE);
           vTAB_MVT(i).ser_in_sequencia   := Pck_Mega.AchaSequenciaDaTabela(vFIL.Des_Org_In_Codigo, vTAB_MVT(i).ser_tab_in_codigo, Sysdate); 
           vTAB_MVT(i).Mvt_In_Lancam      := Pck_Mega.ProximaSequenciaOrg(vFIL.Des_Org_In_Codigo, vTAB_MVT(i).ser_tab_in_codigo, vTAB_MVT(i).ser_in_sequencia);
           vTAB_MVT(i).mvt_in_vinculo    := vTAB_MVT(i).mvt_in_lancam;
           vTAB_MVT(i).tpm_pad_in_codigo  := Pck_Mega.AchaPadraoDaTabela(vFIL.Des_Fil_In_Codigo,vTAB_MVT(i).tpm_tab_in_codigo, SYSDATE);
           vTAB_MVT(i).pro_pad_in_codigo  := Pck_Mega.AchaPadraoDaTabela(vFIL.Des_Fil_In_Codigo,100, SYSDATE);
           vTAB_MVT(i).apl_pad_in_codigo  := Pck_Mega.AchaPadraoDaTabela(vFIL.Des_Fil_In_Codigo,vTAB_MVT(i).apl_tab_in_codigo, SYSDATE);
           vTAB_MVT(i).alm_pad_in_codigo  := Pck_Mega.AchaPadraoDaTabela(vFIL.Des_Fil_In_Codigo,vTAB_MVT(i).alm_tab_in_codigo, SYSDATE);
           vTAB_MVT(i).cus_pad_in_codigo  := Pck_Mega.AchaPadraoDaTabela(vFIL.Des_Fil_In_Codigo,vTAB_MVT(i).cus_tab_in_codigo, SYSDATE);
           -- Carrega localização do produto;
           vLOC.org_tab_in_codigo := vTAB_MVT(i).org_tab_in_codigo;
           vLOC.org_pad_in_codigo := vTAB_MVT(i).org_pad_in_codigo;
           vLOC.org_in_codigo     := vTAB_MVT(i).org_in_codigo;
           vLOC.org_tau_st_codigo := vTAB_MVT(i).org_tau_st_codigo;
           vLOC.fil_in_codigo     := vTAB_MVT(i).fil_in_codigo;
           vLOC.pro_tab_in_codigo := vTAB_MVT(i).pro_tab_in_codigo;
           vLOC.pro_pad_in_codigo := vTAB_MVT(i).pro_pad_in_codigo;
           vLOC.pro_in_codigo     := vTAB_MVT(i).pro_in_codigo;
           vLOC.mov_st_origem     := 'RE';
           p_DefineLocalizacaoItem;
           -- um movimento para cada baixa de requisição
           vSALDO:= ADM_PCK_ESTOQUE.F_SALDO_QTDE(vLOC.Org_In_Codigo,
                                                 vLOC.fil_in_codigo,
                                                 vLOC.Pro_Pad_In_Codigo,
                                                 vLOC.Pro_In_Codigo,
                                                 vTAB_MVT(i).MVT_DT_MOVIMENTO+1);
           if vSALDO >= vTAB_MVT(i).mvt_Re_Quantidade then
              vBXA.vbxi_ch_sinc := 'S';
              -- Busca saldo pro item na localização prioridade 1
              For cMVS In (
                 Select mvs.*
                   From est_movsumarizado mvs
                  Where mvs.pro_tab_in_codigo = vTAB_PRL.pro_tab_in_codigo
                    And mvs.pro_pad_in_codigo = vTAB_PRL.pro_pad_in_codigo
                    And mvs.pro_in_codigo     = vTAB_PRL.pro_in_codigo
                    And mvs.fil_in_codigo     = vTAB_PRL.fil_in_codigo
                    And mvs.alm_tab_in_codigo = vTAB_PRL.alm_tab_in_codigo
                    And mvs.alm_pad_in_codigo = vTAB_PRL.alm_pad_in_codigo
                    And mvs.alm_in_codigo     = vTAB_PRL.alm_in_codigo
                    and mvs.loc_in_codigo     = vTAB_PRL.loc_in_codigo
                    And mvs.nat_st_codigo     = 'DP')
              Loop
                 vTAB_MVS := cMVS;
              end loop;
              --Busca saldo em natureza disponível
              if vTAB_MVS.Org_In_Codigo is null then
                 for cMVS in (
                    Select mvs.*
                      From est_movsumarizado mvs
                     Where mvs.pro_tab_in_codigo = vTAB_PRL.pro_tab_in_codigo
                       And mvs.pro_pad_in_codigo = vTAB_PRL.pro_pad_in_codigo
                       And mvs.pro_in_codigo     = vTAB_PRL.pro_in_codigo
                       And mvs.fil_in_codigo     = vTAB_PRL.fil_in_codigo
                       And mvs.nat_st_codigo     = 'DP')
                 loop
                    vTAB_MVS := cMVS;
                 end loop;
              end if;
              vTAB_MVT(i).alm_in_codigo        := vTAB_MVS.alm_in_codigo;
              vTAB_MVT(i).loc_in_codigo        := vTAB_MVS.loc_in_codigo;
              -- Lotes       
              IF vTAB_MVL.first IS NOT NULL THEN
                 FOR j IN vTAB_MVL.FIRST .. vTAB_MVL.LAST LOOP
                    if vTAB_MVL(j).mvt_in_lancam = vMVT_IN_LANCAM then
                       vTAB_MVL(j).org_in_codigo      := vTAB_MVT(i).org_in_codigo;
                       vTAB_MVL(j).ser_tab_in_codigo  := vTAB_MVT(i).ser_tab_in_codigo;
                       vTAB_MVL(j).ser_in_sequencia   := vTAB_MVT(i).ser_in_sequencia;
                       vTAB_MVL(j).mvt_in_lancam      := vTAB_MVT(i).mvt_in_lancam;
                       vTAB_MVL(j).fil_in_codigo      := vTAB_MVT(i).fil_in_codigo;                    
                       vTAB_MVL(j).pro_pad_in_codigo  := vTAB_MVT(i).pro_pad_in_codigo;                    
                       vTAB_MVL(j).alm_pad_in_codigo  := vTAB_MVT(i).alm_pad_in_codigo;
                       vTAB_MVL(j).alm_in_codigo      := vTAB_MVT(i).alm_in_codigo;
                       vTAB_MVL(j).loc_in_codigo      := vTAB_MVT(i).loc_in_codigo;
                    end if;
                 END LOOP;
              END IF;
              -- Efetiva o movimento de Estoque
              p_GeraMovimentoEstoque_New;
           else
              vBXA.vbxi_ch_sinc := 'N';
           end if;          
        END LOOP;
        
     END IF;     
  end P_SincronizarBaixas;

  Procedure p_Insere_ItemRequisicao(pRESULT in out sys_refcursor,
                                  pFIL_IN_CODIGO in number,
                                  pREQ_IN_SEQUENCIA in IDP.apt_pro_requisicao.req_in_sequencia%type,
                                  pBXI_IN_SEQUENCIA  in IDP.apt_pro_itensrequisicao.bxi_in_sequencia%type,
                                  pBXA_IN_SEQUENCIA in IDP.apt_pro_itensrequisicao.bxa_in_sequencia%type,
                                  pBXI_ID_PRODUTO in IDP.apt_pro_itensrequisicao.bxi_id_produto%type,
                                  pBXI_RE_QUANTIDADE in IDP.apt_pro_itensrequisicao.bxi_re_quantidade%type,
                                  pBXI_CH_STATUS in IDP.apt_pro_itensrequisicao.bxi_ch_status%type,
                                  pBXI_ID_ALMOXA in IDP.apt_pro_itensrequisicao.bxi_id_almoxa%type) Is
  Begin
       /*if pFIL_IN_CODIGO = 302 then
       Raise_application_error(-20000,
       pFIL_IN_CODIGO||chr(13)||
       pREQ_IN_SEQUENCIA||chr(13)||
       pBXI_IN_SEQUENCIA||chr(13)||
       pBXA_IN_SEQUENCIA||chr(13)||
       pBXI_ID_PRODUTO||chr(13)||
       pBXI_RE_QUANTIDADE||chr(13)||
       pBXI_CH_STATUS
       );
       end if;*/
     vTAB_REI.fil_in_codigo := pFIL_IN_CODIGO;
     if pFIL_IN_CODIGO = 3 then
        vTAB_REI.Bxa_In_Sequencia := pBXA_IN_SEQUENCIA;
     else
        vTAB_REI.Bxa_In_Sequencia := pBXA_IN_SEQUENCIA;
     end if;
     vTAB_REI.Bxi_In_Sequencia := pBXI_IN_SEQUENCIA;
     vTAB_REI.Bxi_Id_Produto   := pBXI_ID_PRODUTO;
     vTAB_REI.Bxi_Re_Quantidade := pBXI_RE_QUANTIDADE;
     vTAB_REI.Bxi_Ch_Status := pBXI_CH_STATUS;
     vTAB_REI.Req_In_Sequencia := pREQ_IN_SEQUENCIA;
     vTAB_REI.Bxi_Id_Almoxa    := pBXI_ID_ALMOXA;
     vTAB_REI.Bxi_Ch_Baixa     := 'N';
     vTAB_REI.Bxi_Ch_Sinc      := 'N';
     Begin
        select req.rei_in_sequencia
          into vTAB_REI.Rei_In_Sequencia
          from IDP.apt_pro_itensrequisicao req
         where req.fil_in_codigo    = vTAB_REI.fil_in_codigo
           and req.bxa_in_sequencia = vTAB_REI.bxa_in_sequencia
           and req.bxi_in_sequencia = vTAB_REI.Bxi_In_Sequencia;
     exception when no_data_found then
        select nvl(max(rei.Rei_In_Sequencia),0)+1
          into vTAB_REI.Rei_In_Sequencia
          from IDP.apt_pro_itensrequisicao rei
         where rei.fil_in_codigo = vTAB_REI.fil_in_codigo
           and rei.req_in_sequencia = vTAB_REI.req_in_sequencia
           and rei.bxa_in_sequencia = vTAB_REI.bxa_in_sequencia
           --and rei.bxi_in_sequencia = vTAB_REI.bxi_in_sequencia
           ;
         Insert Into IDP.apt_pro_itensrequisicao values vTAB_REI;
     end;
     Commit;

      Open pRESULT For
          Select req.req_in_sequencia,
                 req.rei_in_sequencia,
                 req.bxa_in_sequencia,
                 req.bxi_in_sequencia
            From IDP.apt_pro_itensrequisicao req
           where req.bxa_in_sequencia = vTAB_REI.bxa_in_sequencia
             and req.bxi_in_sequencia = vTAB_REI.Bxi_In_Sequencia
             and req.fil_in_codigo    = vTAB_REI.Fil_In_Codigo;
  End p_Insere_ItemRequisicao;

  Procedure p_Insere_ItemInventario(pRESULT in out sys_refcursor,
                                    pFIL_IN_CODIGO in number,
                                    pINV_IN_SEQUENCIA in number,
                                    pITI_IN_SEQUENCIA in number,
                                    pITI_ID_PRODUTO in varchar2,
                                    pITI_RE_QUANTIDADE in number,
                                    pITI_CH_STATUS in varchar2,
                                    pMOV_IN_SEQUENCIA in number,
                                    pITI_ST_TIPOMOV in varchar2
                                    ) Is
  Begin
      /* if pINV_IN_SEQUENCIA = 1 then
       Raise_application_error(-20000,
       pFIL_IN_CODIGO||chr(13)||
       pINV_IN_SEQUENCIA||chr(13)||
       pITI_IN_SEQUENCIA||chr(13)||
       pITI_ID_PRODUTO||chr(13)||
       pITI_RE_QUANTIDADE||chr(13)||
       pITI_CH_STATUS||chr(13)||
       pMOV_IN_SEQUENCIA||chr(13)||
       pITI_ST_TIPOMOV
       );
       end if;*/
     -- Carrega a tabela de inventário;
     for cINV in(
        select inv.*
          from IDP.apt_pro_inventario inv
         where inv.fil_in_codigo = pFIL_IN_CODIGO
           and inv.inv_In_Sequencia = pINV_IN_SEQUENCIA
        )
     loop
        vTAB_INV := cINV;
     end loop;
     vTAB_IIT.fil_in_codigo := vTAB_INV.FIL_IN_CODIGO;
     vTAB_IIT.inv_In_Sequencia := vTAB_INV.INV_IN_SEQUENCIA;
     vTAB_IIT.Iti_In_Sequencia := pITI_IN_SEQUENCIA;
     vTAB_IIT.Iti_Id_Produto   := pITI_ID_PRODUTO;
     vTAB_IIT.iti_Re_Quantidade := pITI_RE_QUANTIDADE;
     vTAB_IIT.iti_Ch_Status := pITI_CH_STATUS;
     vTAB_IIT.Iti_St_Tipomov := pITI_ST_TIPOMOV;
     vTAB_IIT.Mov_In_Sequencia := pMOV_IN_SEQUENCIA;
     Begin
        select inv.moi_in_sequencia
          into vTAB_IIT.moi_in_sequencia
          from IDP.apt_pro_itensinventario inv
         where inv.fil_in_codigo = vTAB_IIT.fil_in_codigo
           and inv.inv_in_sequencia = vTAB_IIT.inv_in_sequencia
           and inv.iti_in_sequencia = vTAB_IIT.Iti_In_Sequencia;
     exception when no_data_found then
        select nvl(max(inv.Mov_In_Sequencia),0)+1
          into vTAB_IIT.moi_in_sequencia
          from IDP.apt_pro_itensinventario inv
         where inv.fil_in_codigo = vTAB_IIT.fil_in_codigo
           and inv.inv_in_sequencia = vTAB_IIT.inv_in_sequencia;
         Insert Into IDP.apt_pro_itensinventario values vTAB_IIT;
     end;     
     Open pRESULT For
          Select vTAB_IIT.inv_in_sequencia as inv_in_sequencia,
                 vTAB_IIT.iti_in_sequencia as iti_in_sequencia,
                 vTAB_IIT.mov_in_sequencia as mov_in_sequencia,
                 vTAB_IIT.moi_in_sequencia as moi_in_sequencia
            From DUAL;
      Commit;

  End p_Insere_ItemInventario;

  Procedure p_Insere_Inventario(pRESULT in out sys_refcursor,
                                pFIL_IN_CODIGO in number,
                                pINV_IN_SEQUENCIA in number,
                                pINV_ST_USUARIO   in varchar2,
                                pINV_DT_MOVIMENTO in varchar2,
                                PINV_CH_STATUS    in char) Is
  Begin
      /* if pINV_IN_SEQUENCIA = 2 then
       Raise_application_error(-20000,
       pFIL_IN_CODIGO||chr(13)||
       pINV_IN_SEQUENCIA||chr(13)||
       pINV_ST_USUARIO||chr(13)||
       pINV_DT_MOVIMENTO||chr(13)||
       PINV_CH_STATUS
       );
       end if;*/
     vTAB_INV.fil_in_codigo := pFIL_IN_CODIGO;
     vTAB_INV.inv_In_Sequencia := pINV_IN_SEQUENCIA;
     vTAB_INV.inv_Dt_Movimento := to_date(pINV_DT_MOVIMENTO,'yyyy/mm/dd');
     vTAB_INV.Inv_St_Usuario := pINV_ST_USUARIO;
     vTAB_INV.inv_Ch_Status := pINV_CH_STATUS;
     Begin
        select inv.Mov_In_Sequencia
          into vTAB_INV.Mov_In_Sequencia
          from IDP.apt_pro_inventario inv
         where inv.fil_in_codigo = vTAB_INV.fil_in_codigo
           and inv.inv_in_sequencia = vTAB_INV.inv_in_sequencia;
     exception when no_data_found then
        select nvl(max(inv.Mov_In_Sequencia),0)+1
          into vTAB_INV.Mov_In_Sequencia
          from IDP.apt_pro_inventario inv
         where inv.fil_in_codigo = vTAB_INV.fil_in_codigo
           ;
         Insert Into IDP.apt_pro_inventario values vTAB_INV;
     end;

     Open pRESULT For
        Select vTAB_INV.inv_In_Sequencia as inv_In_Sequencia,
               vTAB_INV.Mov_In_Sequencia as Mov_In_Sequencia
          From DUAL;
     Commit;
  End p_Insere_Inventario;

  Procedure p_Insere_Requisicao(pRESULT in out sys_refcursor,
                                pFIL_IN_CODIGO in IDP.apt_pro_requisicao.fil_in_codigo%Type,
                                pBXA_IN_SEQUENCIA in IDP.apt_pro_requisicao.bxa_in_sequencia%Type,
                                pBXA_DT_APONTAMENTO in varchar2,
                                pBXA_ST_USUARIO in IDP.apt_pro_requisicao.bxa_st_usuario%Type,
                                pCUS_ID_CCUSTO in IDP.apt_pro_requisicao.cus_id_ccusto%Type,
                                pBXA_CH_STATUS in IDP.apt_pro_requisicao.bxa_ch_status%Type,
                                pOS_ST_ID in IDP.apt_pro_requisicao.os_st_id%Type) Is
  Begin
      /* Raise_application_error(-20000,
       pBXA_IN_SEQUENCIA||chr(13)||
       pFIL_IN_CODIGO||chr(13)||
       pBXA_DT_APONTAMENTO||chr(13)||
       pBXA_ST_USUARIO||chr(13)||
       pCUS_ID_CCUSTO||chr(13)||
       pBXA_CH_STATUS
       ); */
     if pFIL_IN_CODIGO = 3 then
        vTAB_REQ.BXA_IN_SEQUENCIA := pBXA_IN_SEQUENCIA;
     else
        vTAB_REQ.BXA_IN_SEQUENCIA := pBXA_IN_SEQUENCIA;
     end if;
     vTAB_REQ.BXA_DT_APONTAMENTO := to_date(pBXA_DT_APONTAMENTO,'yyyy/mm/dd');
     vTAB_REQ.BXA_ST_USUARIO := pBXA_ST_USUARIO;
     vTAB_REQ.BXA_CH_STATUS := pBXA_CH_STATUS;
     vTAB_REQ.FIL_IN_CODIGO := pFIL_IN_CODIGO;
     vTAB_REQ.CUS_ID_CCUSTO := pCUS_ID_CCUSTO;
     vTAB_REQ.OS_ST_ID      := pOS_ST_ID;
     
     /*Raise_application_error(-20000,
       vTAB_REQ.BXA_DT_APONTAMENTO
       );*/

     -- Busca a sequência da requisição
     Begin
        select apt.req_in_sequencia
          into vTAB_REQ.req_in_sequencia
          from IDP.apt_pro_requisicao apt
         where apt.fil_in_codigo = vTAB_REQ.fil_in_codigo
           and apt.bxa_in_sequencia = vTAB_REQ.bxa_in_sequencia;
     exception when no_data_found then
        select nvl(max(apt.req_in_sequencia),0)+1
          into vTAB_REQ.req_in_sequencia
          from IDP.apt_pro_requisicao apt
          where apt.fil_in_codigo = vTAB_REQ.FIL_IN_CODIGO;
        -- cria nova requisição;
        Insert Into IDP.apt_pro_requisicao values vTAB_REQ;
     End;
     Commit;

     Open pRESULT For
         Select vTAB_REQ.req_in_sequencia as req_in_sequencia,
                vTAB_REQ.bxa_in_sequencia as bxa_in_sequencia
           From DUAL;
  End p_Insere_Requisicao;
  
  procedure p_ConsisteMovimento is   
  begin
     for cMVT in(
         select mvt.*
           from est_movimento mvt,
                est_produtos pro
          where mvt.pro_tab_in_codigo = pro.pro_tab_in_codigo
            and mvt.pro_pad_in_codigo = pro.pro_pad_in_codigo
            and mvt.pro_in_codigo     = pro.pro_in_codigo
            and pro.pro_st_cestoque   = 'S'
            and mvt.fil_in_codigo in (3,503)
            and mvt.tpm_in_codigo in (950,960)
            and trunc(mvt.mvt_dt_movimento) > (select trunc(est.sis_dt_encerramento)
                                                 from GLO_ENCERRASISTEMA est
                                                where est.fil_in_codigo = mvt.fil_in_codigo
                                                  and est.sis_in_codigo = 31)
            and not exists
                (select 1
                   from est_lotesmovimento l
                  where l.org_tab_in_codigo = mvt.org_tab_in_codigo
                    and l.org_pad_in_codigo = mvt.org_pad_in_codigo
                    and l.org_in_codigo     = mvt.org_in_codigo
                    and l.org_tau_st_codigo = mvt.org_tau_st_codigo
                    and l.ser_tab_in_codigo = mvt.ser_tab_in_codigo
                    and l.ser_in_sequencia  = mvt.ser_in_sequencia
                    and l.mvt_in_lancam     = mvt.mvt_in_lancam)
     )                
     loop
        -- Exclui o movimento de estoque
        idp.adm_pck_movimentoestoque.Excluirmovimento(cmvt.org_in_codigo,
                                                      cmvt.ser_in_sequencia,
                                                      cmvt.mvt_in_lancam);
        -- Busca o movimento de requisição vinculado e reabre caso esteja encerrado.
        for cREI in(
           select rei.*
             from apt_pro_itensrequisicao rei
            where rei.org_tab_in_codigo = cMVT.Org_Tab_In_Codigo
              and rei.org_pad_in_codigo = cMVT.Org_Pad_In_Codigo
              and rei.org_in_codigo     = cMVT.Org_In_Codigo
              and rei.org_tau_st_codigo = cMVT.Org_Tau_St_Codigo
              and rei.ser_tab_in_codigo = cMVT.Ser_Tab_In_Codigo
              and rei.ser_in_sequencia  = cMVT.Ser_In_Sequencia
              and rei.mvt_in_lancam     = cMVT.Mvt_In_Lancam)
        loop
           -- reabre o item da requisição;
           Update IDP.apt_pro_itensrequisicao rei
              Set rei.bxi_ch_status    = 'A',
                  -- Adicionado em 03/01/2024 por JPC
                  rei.org_tab_in_codigo = null,
                  rei.org_pad_in_codigo = null,
                  rei.org_in_codigo     = null,
                  rei.org_tau_st_codigo = null,
                  rei.ser_tab_in_codigo = null,
                  rei.ser_in_sequencia  = null,
                  rei.mvt_in_lancam     = null
            Where rei.Req_In_Sequencia = cREI.req_in_sequencia
              and rei.rei_in_sequencia = cREI.Rei_In_Sequencia
              And rei.fil_in_codigo    = cREI.fil_in_codigo
              And rei.bxi_ch_status    = 'B'
              And rei.bxi_ch_baixa     = 'N'
              And rei.bxi_ch_sinc      = 'S';
           -- reabre a requisição;
           -- Atualiza o Status da tabela de controle de baixa
          Update IDP.apt_pro_requisicao bxe
             Set bxe.bxa_ch_status = 'A'
           Where bxe.req_in_sequencia = cREI.req_in_sequencia
             And bxe.fil_in_codigo    = cREI.fil_in_codigo
             And bxe.bxa_ch_status <> 'A'
             And exists 
                 (select 1
                    from apt_pro_itensrequisicao bxi
                   Where bxi.Req_In_Sequencia = cREI.req_in_sequencia
                     And bxi.fil_in_codigo    = cREI.fil_in_codigo
                     And bxi.bxi_ch_status    = 'A');
        end loop;                                                        
     end loop;              
  end;   
  procedure p_Gera_BaixaRequisicao(pRESULT in out sys_refcursor,
                                   pFIL_IN_CODIGO in IDP.apt_pro_requisicao.fil_in_codigo%Type)is

  v_mov                        Number;
  v_lote                       Number;
  vMENSAGEM varchar2(300);
  vRETORNO CLOB;
  vSALDO number; 
  v_permite char(1); 
  v_dt_encerramento Date;

  Begin
     For cBXI in (
       Select *
         From IDP.apt_pro_requisicao bx
        Where bx.fil_in_codigo = pFIL_IN_CODIGO
          and (
                 (bx.bxa_ch_status = 'L' and bx.fil_in_codigo = 3)
               or
                 (bx.bxa_ch_status = 'L' and bx.fil_in_codigo = 302)
               or
                 (bx.bxa_ch_status = 'L' and bx.fil_in_codigo = 312)
               or
                 (bx.bxa_ch_status = 'L' and bx.fil_in_codigo = 31)
              )
         --and bx.bxa_in_sequencia = 12976
          /*and(
                 (bx.fil_in_codigo = 302 and BX.REQ_IN_SEQUENCIA <> 6)
               or
                 (bx.fil_in_codigo = 3 and BX.REQ_IN_SEQUENCIA <> 2)
              )*/
        order by bx.req_in_sequencia)
     Loop                
        v_permite := 'S';
        -- Valida encerramento do período do materiais;
        begin 
           select trunc(sis.sis_dt_encerramento)
             into v_dt_encerramento
             from glo_encerrasistema sis
            where sis.fil_in_codigo = pFIL_IN_CODIGO
              and sis.sis_in_codigo = 31;
        exception when others then
           v_dt_encerramento := trunc(sysdate);
        end;
        if v_dt_encerramento > trunc(cBXI.Bxa_Dt_Apontamento) then
           v_permite := 'N';
        else
           v_permite := 'S';
        end if;     
        
        if v_permite = 'S' then                      
           v_Encerra := 'S';             
           For cREQ in (
              Select req.req_in_sequencia,
                     rei.rei_in_sequencia,
                     req.fil_in_codigo,
                     req.bxa_dt_apontamento,
                     req.bxa_in_sequencia,
                     org.org_tab_in_codigo,
                     org.org_pad_in_codigo,
                     org.pai_org_in_codigo as org_in_codigo,
                     org.org_tau_st_codigo,
                     rei.bxi_id_produto,
                     rei.bxi_ch_baixa,
                     rei.bxi_ch_sinc,
                     rei.bxi_id_almoxa,
                     to_number(substr(req.cus_id_ccusto,1,3)) as cus_tab_in_codigo,
                     to_number(substr(req.cus_id_ccusto,4,3)) as cus_pad_in_codigo,
                     to_char(to_number(substr(req.cus_id_ccusto,7,5))) as cus_ide_st_codigo,
                     to_number(substr(req.cus_id_ccusto,13,7)) as cus_in_reduzido,
                     to_number(substr(rei.bxi_id_produto,1,3)) as pro_tab_in_codigo,
                     to_number(substr(rei.bxi_id_produto,4,3)) as pro_pad_in_codigo,
                     to_number(substr(rei.bxi_id_produto,7,7)) as pro_in_codigo,
                     to_number(substr(rei.bxi_id_almoxa,1,3)) as alm_tab_in_codigo,
                     to_number(substr(rei.bxi_id_almoxa,4,3)) as alm_pad_in_codigo,
                     to_number(substr(rei.bxi_id_almoxa,7,6)) as alm_in_codigo,
                     to_number(substr(rei.bxi_id_almoxa,13,6)) as loc_in_codigo,                                    
                     to_number(substr(req.os_st_id,8)) as Os_In_Numero,
                     sum(rei.bxi_re_quantidade) as bxi_re_quantidade
                From IDP.apt_pro_requisicao req,
                     IDP.apt_pro_itensrequisicao rei,
                     glo_vw_organizacao org
               Where req.fil_in_codigo = rei.fil_in_codigo
                 And req.req_in_sequencia = rei.req_in_sequencia
                 And org.org_in_codigo = req.fil_in_codigo
                 And org.org_bo_consolidador = 'F'
                 And req.fil_in_codigo = cBXI.fil_in_codigo
                 And req.req_in_sequencia = cBXI.req_in_sequencia
                 And req.bxa_ch_status    = cBXI.Bxa_Ch_Status
                 And rei.bxi_ch_status    = 'A'
                 --And rei.req_in_sequencia = 959
                 --And to_number(substr(rei.bxi_id_produto,7,7)) = 1804
               Group By
                     req.req_in_sequencia,
                     rei.rei_in_sequencia,
                     org.org_tab_in_codigo,
                     org.org_pad_in_codigo,
                     org.org_tau_st_codigo,
                     org.pai_org_in_codigo,
                     req.cus_id_ccusto,
                     req.os_st_id,
                     rei.bxi_id_produto,
                     req.fil_in_codigo,
                     req.bxa_dt_apontamento,
                     rei.bxi_id_almoxa,
                     rei.bxi_ch_baixa,
                     rei.bxi_ch_sinc,
                     req.bxa_in_sequencia
               order by req.req_in_sequencia
                 )
           Loop
              -- Carrega o item da requisição
              for cREI in(
                select rei.*
                  from apt_pro_itensrequisicao rei
                 where rei.req_in_sequencia = cREQ.req_in_sequencia
                   and rei.rei_in_sequencia = cREQ.rei_in_sequencia
                )
              loop
                 vTAB_REI := cREI; 
              end loop;
              -- Alimenta type global
              vBXA.vreq_in_sequencia := cREQ.Req_In_Sequencia;
              vBXA.vbxi_id_produto   := cREQ.Bxi_Id_Produto;
              vBXA.vfil_in_codigo    := cREQ.Fil_In_Codigo;
              vBXA.vbxi_ch_baixa     := 'N';
              vBXA.vbxi_ch_sinc      := 'N';
              vBXA.vgera_mvto        := 'N';
                 
              -- Inicializa o apontamento para cada produto;
              Inicializa;                                                                                                                  
              -- Limpa variáveis para cada item produzido gera um movimento de estoque;                  
              AddMov(vTAB_MVT);
              vM := vTAB_MVT.Last;                  
              AddlotesMov(vTAB_MVL);
              vL := vTAB_MVL.Last;
              vBXA.vbxi_ch_baixa := 'S';                                                       
              -- Busca configuração do tipo de movimento;           
              if cREQ.Loc_In_Codigo is not null then
                 -- Movimento de transferências
                 vTAB_MVT(vM).Acao_In_Codigo     := 950;
                 vTAB_MVT(vM).Acao_Pad_In_Codigo := Pck_Mega.AchaPadraoDaTabela(pFIL_IN_CODIGO, 55, SYSDATE);
                 For cCFG In (
                    Select *
                      From IDP.apt_baixatipomovto_config cfg
                     Where cfg.acao_in_codigo = vTAB_MVT(vM).Acao_In_Codigo
                       And cfg.acao_pad_in_codigo = vTAB_MVT(vM).Acao_Pad_In_Codigo
                       and cfg.tpm_bo_tipomovto = 'SDT')
                 Loop
                    vTAB_CFG:= cCFG;
                 End loop;
                 For cEDT In (
                    Select *
                      From IDP.apt_baixatipomovto_config edt
                     Where edt.acao_in_codigo = vTAB_MVT(vM).Acao_In_Codigo
                       And edt.acao_pad_in_codigo = vTAB_MVT(vM).Acao_Pad_In_Codigo
                       and edt.tpm_bo_tipomovto = 'EDT')
                 Loop
                    vTAB_SDT:= cEDT;
                 End loop; 
              else
                 vTAB_MVT(vM).Acao_In_Codigo     := 960;
                 vTAB_MVT(vM).Acao_Pad_In_Codigo := Pck_Mega.AchaPadraoDaTabela(pFIL_IN_CODIGO, 55, SYSDATE);
                 For cCFG In (
                    Select *
                      From IDP.apt_baixatipomovto_config cfg
                     Where cfg.acao_in_codigo = vTAB_MVT(vM).Acao_In_Codigo
                       And cfg.acao_pad_in_codigo = vTAB_MVT(vM).Acao_Pad_In_Codigo
                       and cfg.tpm_bo_tipomovto = 'SDR')
                 Loop
                    vTAB_CFG := cCFG;
                 End loop; 
              end if;            
              -- Carrega produto
              for cPRO in (
                 select pro.*
                   from est_produtos pro
                  where pro.pro_tab_in_codigo = cREQ.pro_tab_in_codigo
                    and pro.pro_pad_in_codigo = cREQ.pro_pad_in_codigo
                    and pro.pro_in_codigo     = cREQ.pro_in_codigo)
              loop
                 vTAB_PRO := cPRO;
              end loop;
                 
              -- Carrega localização do produto;
              vLOC.org_tab_in_codigo := cREQ.org_tab_in_codigo;
              vLOC.org_pad_in_codigo := cREQ.org_pad_in_codigo;
              vLOC.org_in_codigo := cREQ.org_in_codigo;
              vLOC.org_tau_st_codigo := cREQ.org_tau_st_codigo;
              vLOC.fil_in_codigo := cREQ.fil_in_codigo;
              vLOC.pro_tab_in_codigo := cREQ.pro_tab_in_codigo;
              vLOC.pro_pad_in_codigo := cREQ.pro_pad_in_codigo;
              vLOC.pro_in_codigo := cREQ.pro_in_codigo;
              vLOC.mvt_dt_movimento := cREQ.Bxa_Dt_Apontamento;
              vLOC.bxi_id_almoxa := cREQ.Bxi_Id_Almoxa;
              if vTAB_MVT(vM).Acao_In_Codigo = 960 then
                 vLOC.mov_st_origem := 'RE';
              else
                 vLOC.mov_st_origem := 'TR';
              end if;                    
              p_DefineLocalizacaoItem;
              -- um movimento para cada baixa de requisição
              vSALDO:= ADM_PCK_ESTOQUE.F_SALDO_QTDE(cREQ.Org_In_Codigo,
                                                    cREQ.fil_in_codigo,
                                                    cREQ.Pro_Pad_In_Codigo,
                                                    cREQ.Pro_In_Codigo,
                                                    vTAB_PRL.Alm_Pad_In_Codigo,
                                                    vTAB_PRL.Alm_In_Codigo,
                                                    vTAB_PRL.Loc_In_Codigo,
                                                    cBXI.Bxa_Dt_Apontamento+1,
                                                    'AN');
              if vSALDO >= cREQ.Bxi_Re_Quantidade then
                 -- Busca saldo pro item na localização prioridade 1
                 For cMVS In (
                    Select mvs.*
                      From est_movsumarizado mvs
                     Where mvs.pro_tab_in_codigo = vTAB_PRL.pro_tab_in_codigo
                       And mvs.pro_pad_in_codigo = vTAB_PRL.pro_pad_in_codigo
                       And mvs.pro_in_codigo     = vTAB_PRL.pro_in_codigo
                       And mvs.fil_in_codigo     = vTAB_PRL.fil_in_codigo
                       And mvs.alm_tab_in_codigo = vTAB_PRL.alm_tab_in_codigo
                       And mvs.alm_pad_in_codigo = vTAB_PRL.alm_pad_in_codigo
                       And mvs.alm_in_codigo     = vTAB_PRL.alm_in_codigo
                       and mvs.loc_in_codigo     = vTAB_PRL.loc_in_codigo
                       and (
                              (cREQ.Bxi_Id_Almoxa is null)
                            or(mvs.alm_in_codigo||mvs.loc_in_codigo <> cReq.alm_in_codigo||creq.loc_in_codigo)
                           )
                       And mvs.nat_st_codigo     = 'DP')
                 Loop
                    vTAB_MVS := cMVS;
                 end loop;
                 --Busca saldo em natureza disponível
                 if vTAB_MVS.Org_In_Codigo is null then
                    For cMVS In (
                       Select mvs.*
                         From est_movsumarizado mvs
                        Where mvs.pro_tab_in_codigo = vTAB_PRL.pro_tab_in_codigo
                          And mvs.pro_pad_in_codigo = vTAB_PRL.pro_pad_in_codigo
                          And mvs.pro_in_codigo     = vTAB_PRL.pro_in_codigo
                          And mvs.fil_in_codigo     = vTAB_PRL.fil_in_codigo
                          and (
                                  (cREQ.Bxi_Id_Almoxa is null)
                                or(mvs.alm_tab_in_codigo||
                                   mvs.alm_pad_in_codigo||
                                   mvs.alm_in_codigo||
                                   mvs.loc_in_codigo <> cREQ.Alm_Tab_In_Codigo||
                                                        cREQ.alm_pad_in_codigo||
                                                        cREQ.Alm_In_Codigo||
                                                        cREQ.Loc_In_Codigo))                                                   
                          And mvs.nat_st_codigo     = 'DP')
                    Loop
                       vTAB_MVS := cMVS;
                    end loop;
                 end if;
                 -- Busca Ordem de Serviço
                 if cREQ.Fil_In_Codigo = 3 then
                   vTAB_OS := null;
                   for cOS in(
                      select * 
                        from mti_os os
                       where os.org_tab_in_codigo = cREQ.Org_Tab_In_Codigo
                         and os.org_pad_in_codigo = cREQ.Org_Pad_In_Codigo
                         and os.org_in_codigo     = cREQ.Org_In_Codigo
                         and os.org_tau_st_codigo = cREQ.org_tau_st_codigo
                         and os.tab_in_codigo     = 522
                         and os.seq_in_codigo     = Pck_Mega.AchaPadraoDaTabela(cREQ.FIL_IN_CODIGO, 522, SYSDATE)
                         and os.os_in_numero      = cREQ.Os_In_Numero
                      )
                   loop
                      vTAB_OS.Org_Tab_In_Codigo := cOS.Org_Tab_In_Codigo;
                      vTAB_OS.Org_Pad_In_Codigo := cOS.Org_Pad_In_Codigo;
                      vTAB_OS.Org_In_Codigo     := cOS.Org_In_Codigo;
                      vTAB_OS.Org_Tau_St_Codigo := cOS.Org_Tau_St_Codigo;
                      vTAB_OS.Tab_In_Codigo     := cOS.Tab_In_Codigo;
                      vTAB_OS.Seq_In_Codigo     := cOS.Seq_In_Codigo;
                      vTAB_OS.Os_In_Numero      := cOS.Os_In_Numero;              
                   end loop;
                 end if;
                 if vTAB_MVS.Org_In_Codigo is not null and vTAB_MVS.Mvs_Re_Quantidade >=cREQ.Bxi_Re_Quantidade then              
                    -- Prepara movimento de estoque
                    vTAB_MVT(vM).mvt_st_numdoc:='BX ACB: '||cBXI.Bxa_In_Sequencia;           
                    vTAB_MVT(vM).ser_tab_in_codigo  := 102;
                    vTAB_MVT(vM).ser_in_sequencia   := Pck_Mega.AchaSequenciaDaTabela(cREQ.Org_In_Codigo, vTAB_MVT(vM).ser_tab_in_codigo, Sysdate);              
                    vTAB_MVT(vM).org_tab_in_codigo    := vTAB_MVS.org_tab_in_codigo;
                    vTAB_MVT(vM).org_pad_in_codigo    := vTAB_MVS.org_pad_in_codigo;
                    vTAB_MVT(vM).org_in_codigo        := vTAB_MVS.org_in_codigo;
                    vTAB_MVT(vM).org_tau_st_codigo    := vTAB_MVS.org_tau_st_codigo;
                    vTAB_MVT(vM).fil_in_codigo        := vTAB_MVS.fil_in_codigo;
                    vTAB_MVT(vM).acao_tab_in_codigo   := vTAB_CFG.acao_tab_in_codigo;
                    vTAB_MVT(vM).acao_pad_in_codigo   := vTAB_CFG.acao_pad_in_codigo;
                    vTAB_MVT(vM).acao_in_codigo       := vTAB_CFG.acao_in_codigo;
                    vTAB_MVT(vM).acaom_in_sequencia   := Null;
                    vTAB_MVT(vM).mvt_ch_origem        := 'M';
                    vTAB_MVT(vM).mvt_st_entrsaida     := 'SD';
                    vTAB_MVT(vM).tpm_tab_in_codigo    := vTAB_CFG.tpm_tab_in_codigo;
                    vTAB_MVT(vM).tpm_pad_in_codigo    := vTAB_CFG.tpm_pad_in_codigo;
                    vTAB_MVT(vM).tpm_in_codigo        := vTAB_CFG.tpm_in_codigo;
                    vTAB_MVT(vM).mvt_dt_documento     := cREQ.bxa_dt_apontamento;
                    vTAB_MVT(vM).mvt_dt_movimento     := cREQ.bxa_dt_apontamento;
                    vTAB_MVT(vM).usu_in_inclusao      := 1;
                    vTAB_MVT(vM).mvt_dt_inclusao      := SysDate;
                    vTAB_MVT(vM).usu_in_altera        := 1;
                    vTAB_MVT(vM).mvt_dt_altera        := SysDate;
                    if vTAB_MVS.fil_in_codigo = 312 then                 
                        if vTAB_MVS.Pro_In_Codigo = 106 then
                            vTAB_MVT(vM).mvt_st_observacao := 'Baixa por requisição de abastecimento Diesel';
                            if cREQ.Os_In_Numero is not null then
                               case when cREQ.Cus_In_Reduzido = '28' then
                                  vTAB_MVT(vM).mvt_st_observacao := vTAB_MVT(vM).mvt_st_observacao ||' horas da máquina: '|| cREQ.Os_In_Numero;
                               else 
                                 vTAB_MVT(vM).mvt_st_observacao := vTAB_MVT(vM).mvt_st_observacao ||' Km do veículo: '|| cREQ.Os_In_Numero;
                               end case;
                            end if;
                        end if;
                    else
                        vTAB_MVT(vM).mvt_st_observacao        := 'Baixa por requisição';
                    end if;
                    vTAB_MVT(vM).mvt_in_vinculo       := 0;
                    vTAB_MVT(vM).pro_tab_in_codigo    := vTAB_MVS.pro_tab_in_codigo;
                    vTAB_MVT(vM).pro_pad_in_codigo    := vTAB_MVS.pro_pad_in_codigo;
                    vTAB_MVT(vM).pro_in_codigo        := vTAB_MVS.pro_in_codigo;
                    vTAB_MVT(vM).apl_tab_in_codigo    := vTAB_CFG.apl_tab_in_codigo;
                    vTAB_MVT(vM).apl_pad_in_codigo    := vTAB_CFG.apl_pad_in_codigo;
                    vTAB_MVT(vM).apl_in_codigo        := vTAB_CFG.apl_in_codigo;
                    vTAB_MVT(vM).alm_tab_in_codigo    := vTAB_MVS.alm_tab_in_codigo;
                    vTAB_MVT(vM).alm_pad_in_codigo    := vTAB_MVS.alm_pad_in_codigo;
                    vTAB_MVT(vM).alm_in_codigo        := vTAB_MVS.alm_in_codigo;
                    vTAB_MVT(vM).loc_in_codigo        := vTAB_MVS.loc_in_codigo;
                    vTAB_MVT(vM).mvt_re_quantidade    := cREQ.Bxi_re_quantidade;
                    vTAB_MVT(vM).mvt_re_aquisicao     := 0;
                    vTAB_MVT(vM).mvt_re_vlunitario    := 0;
                    vTAB_MVT(vM).cus_tab_in_codigo    := cREQ.cus_tab_in_codigo;
                    vTAB_MVT(vM).cus_pad_in_codigo    := cREQ.cus_pad_in_codigo;
                    vTAB_MVT(vM).cus_ide_st_codigo    := cREQ.cus_ide_st_codigo;
                    vTAB_MVT(vM).cus_in_reduzido      := cREQ.cus_in_reduzido;
                    vTAB_MVT(vM).proj_tab_in_codigo   := Null;
                    vTAB_MVT(vM).proj_pad_in_codigo   := Null;
                    vTAB_MVT(vM).proj_ide_st_codigo   := Null;
                    vTAB_MVT(vM).proj_in_reduzido     := Null;
                    vTAB_MVT(vM).mvs_in_reserva       :=0;
                    vTAB_MVT(vM).Mvt_In_Lancam      := Pck_Mega.ProximaSequenciaOrg(cREQ.Org_In_Codigo, vTAB_MVT(vM).ser_tab_in_codigo, vTAB_MVT(vM).ser_in_sequencia);
                    vBXA.vmvt_in_lancam             := vTAB_MVT(vM).Mvt_In_Lancam;
                    if cREQ.Loc_In_Codigo is not null then
                       -- Gera movimento de transferência
                       vTAB_MVT(vM).MVT_IN_VINCULO    := Pck_Mega.ProximaSequenciaOrg(cREQ.Org_In_Codigo, vTAB_MVT(vM).ser_tab_in_codigo, vTAB_MVT(vM).ser_in_sequencia); 
                       vTAB_MVT(vM).NAT_ST_CODIGODEST := 'DP';
                       vTAB_MVT(vM).ALM_IN_CODIGODEST := cREQ.alm_in_codigo;
                       vTAB_MVT(vM).LOC_IN_CODIGODEST := cREQ.loc_in_codigo;
                       vTAB_MVT(vM).TPM_IN_CODIGODEST := vTAB_SDT.tpm_in_codigo;
                       vTAB_MVT(vM).MVT_RE_QUANTIDADEMOV := cREQ.Bxi_re_quantidade;
                    else
                       vTAB_MVT(vM).MVT_IN_VINCULO    := vTAB_MVT(vM).Mvt_In_Lancam;
                    end if;
                    if vTAB_OS.Os_In_Numero is not null then                 
                       vTAB_OS.Ser_Tab_In_Codigo := vTAB_MVT(vM).Ser_Tab_In_Codigo;
                       vTAB_OS.Ser_In_Sequencia  := vTAB_MVT(vM).Ser_In_Sequencia;
                       vTAB_OS.Mvt_In_Lancam     := vTAB_MVT(vM).Mvt_In_Lancam;
                    end if;                 
                    -- Prepara movimento dos lotes
                    vTAB_MVL(vL).org_tab_in_codigo  := vTAB_MVS.org_tab_in_codigo;
                    vTAB_MVL(vL).org_pad_in_codigo  := vTAB_MVS.org_pad_in_codigo;
                    vTAB_MVL(vL).org_in_codigo      := vTAB_MVS.org_in_codigo;
                    vTAB_MVL(vL).org_tau_st_codigo  := vTAB_MVS.org_tau_st_codigo;
                    vTAB_MVL(vL).ser_tab_in_codigo  := vTAB_MVT(vM).ser_tab_in_codigo;
                    vTAB_MVL(vL).ser_in_sequencia   := vTAB_MVT(vM).ser_in_sequencia;
                    vTAB_MVL(vL).mvt_in_lancam      := vTAB_MVT(vM).mvt_in_lancam;
                    vTAB_MVL(vL).fil_in_codigo      := vTAB_MVS.fil_in_codigo;
                    vTAB_MVL(vL).mvl_st_loteforne   := vTAB_MVS.mvs_st_loteforne;
                    vTAB_MVL(vL).mvt_dt_movimento   := cREQ.bxa_dt_apontamento;
                    vTAB_MVL(vL).mvt_dt_validade    := vTAB_MVS.mvs_dt_validade;
                    vTAB_MVL(vL).pro_tab_in_codigo  := vTAB_MVS.pro_tab_in_codigo;
                    vTAB_MVL(vL).pro_pad_in_codigo  := vTAB_MVS.pro_pad_in_codigo;
                    vTAB_MVL(vL).pro_in_codigo      := vTAB_MVS.pro_in_codigo;
                    vTAB_MVL(vL).alm_tab_in_codigo  := vTAB_MVS.alm_tab_in_codigo;
                    vTAB_MVL(vL).alm_pad_in_codigo  := vTAB_MVS.alm_pad_in_codigo;
                    vTAB_MVL(vL).alm_in_codigo      := vTAB_MVS.alm_in_codigo;
                    vTAB_MVL(vL).loc_in_codigo      := vTAB_MVS.loc_in_codigo;
                    vTAB_MVL(vL).mvl_re_quantidade  := cREQ.Bxi_re_quantidade;
                    vTAB_MVL(vL).nat_tab_in_codigo  := vTAB_MVS.nat_tab_in_codigo;
                    vTAB_MVL(vL).nat_pad_in_codigo  := vTAB_MVS.nat_pad_in_codigo;
                    vTAB_MVL(vL).nat_st_codigo      := vTAB_MVS.nat_st_codigo;
                    vTAB_MVL(vL).mvl_dt_entrada     := vTAB_MVS.mvs_dt_entrada;
                    vTAB_MVL(vL).mvl_st_referencia  := vTAB_MVS.mvs_st_referencia;
                    vTAB_MVL(vL).mvl_in_reserva     := vTAB_MVS.mvs_in_reserva;
                    -- Gera vinculo do movimento de estoque com o item da requisição;
                    -- Adicionado em 03/01/2024 por JPC
                    vTAB_REI.Org_Tab_In_Codigo := vTAB_MVL(vL).org_tab_in_codigo;
                    vTAB_REI.Org_Pad_In_Codigo := vTAB_MVL(vL).Org_Pad_In_Codigo;
                    vTAB_REI.Org_In_Codigo     := vTAB_MVL(vL).Org_In_Codigo    ;
                    vTAB_REI.Org_Tau_St_Codigo := vTAB_MVL(vL).Org_Tau_St_Codigo;
                    vTAB_REI.Ser_Tab_In_Codigo := vTAB_MVL(vL).Ser_Tab_In_Codigo;
                    vTAB_REI.Ser_In_Sequencia  := vTAB_MVL(vL).Ser_In_Sequencia ;
                    vTAB_REI.Mvt_In_Lancam     := vTAB_MVL(vL).Mvt_In_Lancam    ;
                    -- Efetiva o movimento de Estoque
                    if cREQ.Bxi_Ch_Baixa = 'N' then                      
                       begin
                          p_GeraMovimentoEstoque_New;                                     
                          Update IDP.apt_pro_itensrequisicao rei
                             Set rei.bxi_ch_baixa    = vBXA.vbxi_ch_baixa
                           Where rei.Req_In_Sequencia = cREQ.req_in_sequencia
                             And rei.rei_in_sequencia = cREQ.rei_in_sequencia
                             And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                             And rei.fil_in_codigo    = cREQ.fil_in_codigo
                             And rei.bxi_ch_status  = 'A'
                             And rei.bxi_ch_baixa     = 'N';
                           -- Grava o vinculo da tabela de OS;
                           if vTAB_OS.Os_In_Numero > 0 then   
                              insert into cus_tb_osmovimento values vTAB_OS;
                           end if;
                       exception when others then
                          vRETORNO := SQLERRM;
                          Update IDP.apt_pro_itensrequisicao rei
                             Set rei.BXI_CL_LOG    = vRETORNO
                           Where rei.Req_In_Sequencia = cREQ.req_in_sequencia
                             And rei.rei_in_sequencia = cREQ.rei_in_sequencia
                             And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                             And rei.fil_in_codigo    = cREQ.fil_in_codigo
                             And rei.bxi_ch_status    = 'A'
                             And rei.bxi_ch_baixa     = 'N';
                       end;
                    end if;
                    if vLOC.mvt_dt_movimento > '01/01/2023' then
                       if cREQ.bxi_ch_sinc = 'N' and vTAB_CFG.Acao_In_Codigo = 960 then  
                          begin
                             if pFIL_IN_CODIGO not in(31) then
                                P_SincronizarBaixas;
                             end if;
                             Update IDP.apt_pro_itensrequisicao rei
                                Set rei.bxi_ch_sinc = vBXA.vbxi_ch_sinc
                              Where rei.Req_In_Sequencia = cREQ.req_in_sequencia
                                And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                                And rei.fil_in_codigo    = cREQ.fil_in_codigo
                                And rei.bxi_ch_status  = 'A'
                                And rei.bxi_ch_sinc      = 'N';
                          exception when others then
                             vRETORNO := SQLERRM;
                             Update IDP.apt_pro_itensrequisicao rei
                             Set rei.BXI_CL_LOG    = vRETORNO
                           Where rei.Req_In_Sequencia = cREQ.req_in_sequencia
                             And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                             And rei.fil_in_codigo    = cREQ.fil_in_codigo
                             And rei.bxi_ch_status    = 'A'
                             And rei.bxi_ch_sinc     = 'N';
                          end;
                       elsif vTAB_MVT(vM).Acao_In_Codigo = 950 and cREQ.Loc_In_Codigo is not null then
                          begin
                             Update IDP.apt_pro_itensrequisicao rei
                                Set rei.bxi_ch_status = 'B'
                              Where rei.Req_In_Sequencia = cREQ.req_in_sequencia
                                And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                                And rei.fil_in_codigo    = cREQ.fil_in_codigo
                                And rei.bxi_ch_status    = 'A'
                                And rei.bxi_ch_sinc      = 'N';
                          exception when others then
                             vRETORNO := SQLERRM;
                             Update IDP.apt_pro_itensrequisicao rei
                             Set rei.BXI_CL_LOG    = vRETORNO
                           Where rei.Req_In_Sequencia = cREQ.req_in_sequencia
                             And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                             And rei.fil_in_codigo    = cREQ.fil_in_codigo
                             And rei.bxi_ch_status    = 'A'
                             And rei.bxi_ch_sinc      = 'N';
                          end;                                                                       
                       end if;                         
                     end if;
                     Update IDP.apt_pro_itensrequisicao rei
                        Set rei.bxi_ch_status    = 'B',
                            -- Adicionado em 03/01/2024 por JPC
                            rei.org_tab_in_codigo = vTAB_REI.org_tab_in_codigo,
                            rei.org_pad_in_codigo = vTAB_REI.org_pad_in_codigo,
                            rei.org_in_codigo     = vTAB_REI.org_in_codigo,
                            rei.org_tau_st_codigo = vTAB_REI.org_tau_st_codigo,
                            rei.ser_tab_in_codigo = vTAB_REI.ser_tab_in_codigo,
                            rei.ser_in_sequencia  = vTAB_REI.ser_in_sequencia,
                            rei.mvt_in_lancam     = vTAB_REI.mvt_in_lancam
                      Where rei.Req_In_Sequencia = cREQ.req_in_sequencia
                        And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                        And rei.fil_in_codigo    = cREQ.fil_in_codigo
                        And rei.bxi_ch_status    = 'A'
                        And rei.bxi_ch_baixa     = 'S'
                        And rei.bxi_ch_sinc      = 'S';
                 elsif vTAB_MVT(vM).Acao_In_Codigo = 950 and cREQ.Loc_In_Codigo is not null then
                    begin
                       Update IDP.apt_pro_itensrequisicao rei
                          Set rei.bxi_ch_status = 'B',
                              -- Adicionado em 03/01/2024 por JPC
                              rei.org_tab_in_codigo = vTAB_REI.org_tab_in_codigo,
                              rei.org_pad_in_codigo = vTAB_REI.org_pad_in_codigo,
                              rei.org_in_codigo     = vTAB_REI.org_in_codigo,
                              rei.org_tau_st_codigo = vTAB_REI.org_tau_st_codigo,
                              rei.ser_tab_in_codigo = vTAB_REI.ser_tab_in_codigo,
                              rei.ser_in_sequencia  = vTAB_REI.ser_in_sequencia,
                              rei.mvt_in_lancam     = vTAB_REI.mvt_in_lancam                           
                        Where rei.Req_In_Sequencia = cREQ.req_in_sequencia
                          And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                          And rei.fil_in_codigo    = cREQ.fil_in_codigo
                          And rei.bxi_ch_status    = 'A'
                          And rei.bxi_ch_baixa     = 'S'
                          And rei.bxi_ch_sinc      = 'N';
                    exception when others then
                       vRETORNO := SQLERRM;
                       Update IDP.apt_pro_itensrequisicao rei
                       Set rei.BXI_CL_LOG    = vRETORNO
                     Where rei.Req_In_Sequencia = cREQ.req_in_sequencia
                       And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                       And rei.fil_in_codigo    = cREQ.fil_in_codigo
                       And rei.bxi_ch_status    = 'A'
                       And rei.bxi_ch_sinc      = 'N';
                    end;                                                                                     
                 elsif vTAB_MVS.Mvs_Re_Quantidade < cREQ.Bxi_Re_Quantidade then
                    vRETORNO := 'Saldo insuficiente para baixa';
                    Update IDP.apt_pro_itensrequisicao rei
                       Set rei.BXI_CL_LOG    = vRETORNO
                     Where rei.Req_In_Sequencia = cREQ.req_in_sequencia
                       And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                       And rei.fil_in_codigo    = cREQ.fil_in_codigo
                       And rei.bxi_ch_status    = 'A'
                       And rei.bxi_ch_baixa     = 'N';
                    
                 end if;
              else
                 vRETORNO := 'Saldo insuficiente para baixa';
                 Update IDP.apt_pro_itensrequisicao rei
                    Set rei.BXI_CL_LOG    = vRETORNO
                  Where rei.req_in_sequencia = cREQ.req_in_sequencia
                    And rei.bxi_id_produto   = cREQ.Bxi_Id_Produto                    
                    And rei.fil_in_codigo    = cREQ.fil_in_codigo
                    And rei.bxi_ch_status    = 'A'
                    And rei.bxi_ch_baixa     = 'N';                                                                          
              end if;
           End Loop;
           -- Atualiza o Status da tabela de controle de baixa
           Update IDP.apt_pro_requisicao bxe
              Set bxe.bxa_ch_status = 'B'
            Where bxe.req_in_sequencia = cBXI.req_in_sequencia
              And bxe.fil_in_codigo    = cBXI.fil_in_codigo
              And bxe.bxa_ch_status = 'L'
              And not exists 
                  (select 1
                     from apt_pro_itensrequisicao bxi
                    Where bxi.Req_In_Sequencia = bxe.req_in_sequencia
                      And bxi.fil_in_codigo    = bxe.fil_in_codigo
                      And bxi.bxi_ch_status    = 'A');
           vMENSAGEM:='Baixa inserida com sucesso!';
           -- somente efetiva se não der erro na rotina;                
        else
           vMENSAGEM:='Movimentação não permitida! Período do Materiais Encerrado';      
        end if;
        update APT_PRO_REQUISICAO rq
           set rq.bxa_ch_status = 'C'
         where rq.bxa_dt_apontamento <= v_dt_encerramento
           and rq.fil_in_codigo = cBXI.FIL_IN_CODIGO
           and rq.req_in_sequencia = cBXI.Req_In_Sequencia;                 
     end loop;
     -- Consiste movimentos de requisição e transferência do almoxarifado;
     -- Adicionado em 03/01/2024 por JPC;
     --p_ConsisteMovimento;
     If vMENSAGEM IS NULL Then
        vMENSAGEM:='Não inserido nenhuma baixa!';
     End If;
     commit;
     Open pRESULT For
        Select vMENSAGEM as MSG From dual;
  End p_Gera_BaixaRequisicao;  
  
  procedure p_Gera_MovimentoInventario(pRESULT in out sys_refcursor,
                                       pFIL_IN_CODIGO in number,
                                       --'C' Contagem; 'R' Rotativo
                                       pPARAMETRO in char)is  

  v_mov                        Number;
  v_lote                       Number;
  vMENSAGEM varchar2(300);

  Begin
     if pPARAMETRO = 'C' then
        -- Carrega a Tabela de inventário;
        v_Encerra := 'N';        
        for cIVA in(
           select iva.* 
             from est_inventario iva        
            where iva.fil_in_codigo = pFil_In_Codigo
              and iva.inv_ch_status = 'N'
              and iva.inv_in_codigo = (select max(iv2.inv_in_codigo)
                                         from est_inventario iv2
                                        where iv2.fil_in_codigo = iva.fil_in_codigo)
            
           )
        loop
           vTAB_IVA := cIVA;
        end loop;
        for cINV in(
        select inv.*
          from IDP.apt_pro_inventario inv
         where inv.fil_in_codigo = vTAB_IVA.FIL_IN_CODIGO
           And inv.inv_ch_status    = 'A'
        )
        loop
           vTAB_INV := cINV;     
           -- Carrega dados de cabeçalho;
           vTAB_WS.organizacao      := vTAB_INV.Fil_In_Codigo;
           vTAB_WS.dispositivo      := sys.dbms_random.string('a',16);
           vTAB_WS.idatividade      := 1;
           vTAB_WS.idcabecalho      := sys.dbms_random.string('a',36);
           vTAB_WS.almoxarifado     := vTAB_IVA.Alm_In_Codigo;
           vTAB_WS.localizacao      := vTAB_IVA.Loc_In_Codigo;
           vTAB_WS.descricao        := 'Inventário Almoxarifado'; 
           vTAB_WS.altura           := 0;
           vTAB_WS.largura          := 0;
           vTAB_WS.comprimento      := 0;
           vTAB_WS.conversor        := 0;
           vTAB_WS.situacao         := 'A';
           vTAB_WS.usuario          := vTAB_INV.Inv_St_Usuario;
           vTAB_WS.ficha            := vTAB_IVA.Inv_In_Codigo;     
           vTAB_WS.inclusao         := vTAB_INV.Inv_Dt_Movimento;
           -- Carrega dados de detalhe;
           for cIT2 in(
              select iti.*
                from IDP.apt_pro_itensinventario iti
               where iti.fil_in_codigo = vTAB_INV.Fil_In_Codigo
                 and iti.inv_in_sequencia = vTAB_INV.Inv_In_Sequencia
                 and iti.iti_ch_status = 'A'
              )
           loop
              vTAB_WS.iddetalhe        := sys.dbms_random.string('a',36);
              vTAB_WS.lote             := cIT2.Iti_Id_Produto;
              vTAB_WS.quantidade       := cIT2.Iti_Re_Quantidade;                      
              insert into ws_coletor_app values vTAB_WS;
              v_Encerra := 'S';
              update IDP.apt_pro_itensinventario it2
                 set it2.iti_ch_status = 'B'
               where it2.inv_in_sequencia = cIT2.Inv_In_Sequencia
                 and it2.iti_in_sequencia = cIT2.Iti_In_Sequencia;               
          end loop;
          update IDP.apt_pro_inventario iv2
             set iv2.inv_ch_status = 'B'
           where iv2.inv_in_sequencia = cINV.Inv_In_Sequencia;          
          if v_Encerra = 'S' then
             vMENSAGEM:='inventário inserido com sucesso!';
             commit;
           else
              rollback;
           end if;                      
        end loop;
     else
     --Raise_application_error(-20000, pFIL_IN_CODIGO);
        For cINV in (
          Select inv.*
            From IDP.apt_pro_inventario inv
           Where inv.fil_in_codigo = pFIL_IN_CODIGO
             and inv.inv_ch_status = 'A')
        Loop
           v_Encerra := 'S';        
           For cITI in (
              Select inv.mov_in_sequencia,
                     inv.fil_in_codigo,
                     inv.inv_dt_movimento,
                     org.org_tab_in_codigo,
                     org.org_pad_in_codigo,
                     org.pai_org_in_codigo as org_in_codigo,
                     org.org_tau_st_codigo,
                     iti.iti_st_tipomov,
                     to_number(substr(inv.cus_id_ccusto,1,3)) as cus_tab_in_codigo,
                     to_number(substr(inv.cus_id_ccusto,4,3)) as cus_pad_in_codigo,
                     to_char(to_number(substr(inv.cus_id_ccusto,7,5))) as cus_ide_st_codigo,
                     to_number(substr(inv.cus_id_ccusto,13,7)) as cus_in_reduzido,
                     to_number(substr(iti.iti_id_produto,1,3)) as pro_tab_in_codigo,
                     to_number(substr(iti.iti_id_produto,4,3)) as pro_pad_in_codigo,
                     to_number(substr(iti.iti_id_produto,7,7)) as pro_in_codigo,
                     sum(iti.iti_re_quantidade) as bxi_re_quantidade
                From IDP.apt_pro_inventario inv,
                     IDP.apt_pro_itensinventario iti,
                     glo_vw_organizacao org
               Where inv.fil_in_codigo = iti.fil_in_codigo
                 And inv.mov_in_sequencia = iti.mov_in_sequencia
                 And org.org_in_codigo = inv.fil_in_codigo
                 And org.org_bo_consolidador = 'F'
                 And inv.fil_in_codigo = cINV.fil_in_codigo
                 And inv.mov_in_sequencia = cINV.mov_in_sequencia
                 And inv.inv_ch_status    = 'A'
                 And iti.iti_ch_status    = 'A'
               Group By
                     inv.mov_in_sequencia,
                     org.org_tab_in_codigo,
                     org.org_pad_in_codigo,
                     org.org_tau_st_codigo,
                     org.pai_org_in_codigo,
                     iti.iti_id_produto,
                     inv.fil_in_codigo,
                     inv.inv_dt_movimento,
                     iti.iti_st_tipomov,
                     inv.cus_id_ccusto
                 )
           Loop
              -- um movimento para cada baixa de requisição
              -- Inicializa o apontamento para cada produto;
              Inicializa;
              -- Limpa variáveis para cada item produzido gera um movimento de estoque;                  
              AddMov(vTAB_MVT);
              vM := vTAB_MVT.Last;                  
              AddlotesMov(vTAB_MVL);
              vL := vTAB_MVL.Last; 
                                    
              vLOC.org_tab_in_codigo := cITI.org_tab_in_codigo;
              vLOC.org_pad_in_codigo := cITI.org_pad_in_codigo;
              vLOC.org_in_codigo := cITI.org_in_codigo;
              vLOC.org_tau_st_codigo := cITI.org_tau_st_codigo;
              vLOC.fil_in_codigo := cITI.fil_in_codigo;
              vLOC.pro_tab_in_codigo := cITI.pro_tab_in_codigo;
              vLOC.pro_pad_in_codigo := cITI.pro_pad_in_codigo;
              vLOC.pro_in_codigo := cITI.pro_in_codigo;
              vLOC.mov_st_origem := 'IN';
              p_DefineLocalizacaoItem; 
              vTAB_MVT(vM).Acao_Pad_In_Codigo := Pck_Mega.AchaPadraoDaTabela(pFIL_IN_CODIGO, 55, SYSDATE);                                 
              -- Busca configuração do tipo de movimento;
              For cCFG In (
                 Select *
                   From IDP.apt_baixatipomovto_config cfg
                  Where cfg.acao_pad_in_codigo = vTAB_MVT(vM).Acao_Pad_In_Codigo
                    and cfg.tpm_bo_tipomovto = cITI.iti_st_tipomov)
              Loop
                 vTAB_CFG := cCFG;
              End loop;
              -- Carrega produto
              for cPRO in (
                 select pro.*
                   from est_produtos pro
                  where pro.pro_tab_in_codigo = cITI.pro_tab_in_codigo
                    and pro.pro_pad_in_codigo = cITI.pro_pad_in_codigo
                   and pro.pro_in_codigo     = cITI.pro_in_codigo)
              loop
                 vTAB_PRO := cPRO;           end loop;                      

              -- dados de movimento de estoque
              For cMVS In (
                 Select mvs.*
                   From est_movsumarizado mvs
                  Where mvs.pro_tab_in_codigo = cITI.pro_tab_in_codigo
                    And mvs.pro_pad_in_codigo = cITI.pro_pad_in_codigo
                    And mvs.pro_in_codigo     = cITI.pro_in_codigo
                    and mvs.fil_in_codigo     = cInv.Fil_In_Codigo
                    And mvs.nat_st_codigo     = 'DP')
              Loop
                 vTAB_MVS := cMVS;
              end loop;
              if vTAB_MVS.Org_In_Codigo is null then              
                 -- Carrega localização do produto;
                 vLOC.org_tab_in_codigo := cITI.org_tab_in_codigo;
                 vLOC.org_pad_in_codigo := cITI.org_pad_in_codigo;
                 vLOC.org_in_codigo := cITI.org_in_codigo;
                 vLOC.org_tau_st_codigo := cITI.org_tau_st_codigo;
                 vLOC.fil_in_codigo := cITI.fil_in_codigo;
                 vLOC.pro_tab_in_codigo := cITI.pro_tab_in_codigo;
                 vLOC.pro_pad_in_codigo := cITI.pro_pad_in_codigo;
                 vLOC.pro_in_codigo := cITI.pro_in_codigo;
                 vLOC.mov_st_origem := 'IN';
                 p_DefineLocalizacaoItem; 
                 vTAB_MVS.org_tab_in_codigo  := cITI.Org_Tab_In_Codigo;
                 vTAB_MVS.org_pad_in_codigo  := cITI.Org_Pad_In_Codigo;
                 vTAB_MVS.org_in_codigo      := cITI.Org_In_Codigo;
                 vTAB_MVS.org_tau_st_codigo  := cITI.Org_Tau_St_Codigo;
                 vTAB_MVS.fil_in_codigo      := cITI.Fil_In_Codigo;
                 vTAB_MVS.pro_tab_in_codigo  := cITI.Pro_Tab_In_Codigo;
                 vTAB_MVS.pro_pad_in_codigo  := cITI.Pro_Pad_In_Codigo;
                 vTAB_MVS.pro_in_codigo      := cITI.pro_in_codigo;
                 vTAB_MVS.alm_tab_in_codigo  := vTAB_PRL.Alm_Tab_In_Codigo;
                 vTAB_MVS.alm_pad_in_codigo  := vTAB_PRL.Alm_Pad_In_Codigo;
                 vTAB_MVS.alm_in_codigo      := vTAB_PRL.Alm_In_Codigo;
                 vTAB_MVS.loc_in_codigo      := vTAB_PRL.Loc_In_Codigo;
                 vTAB_MVS.mvs_in_reserva     := 0;
                 vTAB_MVS.nat_tab_in_codigo  := 143;
                 vTAB_MVS.nat_pad_in_codigo  := 1;
                 vTAB_MVS.nat_st_codigo      := 'DP';
                 vTAB_MVS.mvs_st_referencia  := '*';
                 vTAB_MVS.mvs_st_loteforne   := '*';
                 vTAB_MVS.mvs_dt_entrada     := '01/01/2000';
                 vTAB_MVS.mvs_dt_validade    := '01/01/2000';
              end if;
              -- Prepara movimento de estoque
              vTAB_MVT(vM).mvt_st_numdoc      :='INV ACB: '||cINV.Mov_In_Sequencia;           
              vTAB_MVT(vM).ser_tab_in_codigo  := 102;
              vTAB_MVT(vM).ser_in_sequencia   := Pck_Mega.AchaSequenciaDaTabela(cITI.Org_In_Codigo, vTAB_MVT(vM).ser_tab_in_codigo, Sysdate);
              vTAB_MVT(vM).Mvt_In_Lancam      := Pck_Mega.ProximaSequenciaOrg(cITI.Org_In_Codigo, vTAB_MVT(vM).ser_tab_in_codigo, vTAB_MVT(vM).ser_in_sequencia);
              vTAB_MVT(vM).org_tab_in_codigo  := vTAB_MVS.org_tab_in_codigo;
              vTAB_MVT(vM).org_pad_in_codigo  := vTAB_MVS.org_pad_in_codigo;
              vTAB_MVT(vM).org_in_codigo      := vTAB_MVS.org_in_codigo;
              vTAB_MVT(vM).org_tau_st_codigo  := vTAB_MVS.org_tau_st_codigo;
              vTAB_MVT(vM).fil_in_codigo      := vTAB_MVS.fil_in_codigo;           
              vTAB_MVT(vM).acao_tab_in_codigo := vTAB_CFG.acao_tab_in_codigo;
              vTAB_MVT(vM).acao_pad_in_codigo := vTAB_CFG.acao_pad_in_codigo;
              vTAB_MVT(vM).acao_in_codigo     := vTAB_CFG.acao_in_codigo;
              vTAB_MVT(vM).acaom_in_sequencia := Null;
              vTAB_MVT(vM).mvt_ch_origem      := 'M';
              if cITI.iti_st_tipomov like 'SD%' then
                 vTAB_MVT(vM).mvt_st_entrsaida := 'SD';
              else
                 vTAB_MVT(vM).mvt_st_entrsaida := 'ED';
              end if;
              vTAB_MVT(vM).tpm_tab_in_codigo    := vTAB_CFG.tpm_tab_in_codigo;
              vTAB_MVT(vM).tpm_pad_in_codigo    := vTAB_CFG.tpm_pad_in_codigo;
              vTAB_MVT(vM).tpm_in_codigo        := vTAB_CFG.tpm_in_codigo;
              vTAB_MVT(vM).mvt_dt_documento     := cINV.inv_dt_movimento;
              vTAB_MVT(vM).mvt_dt_movimento     := cINV.inv_dt_movimento;
              vTAB_MVT(vM).usu_in_inclusao      := 1;
              vTAB_MVT(vM).mvt_dt_inclusao      := SysDate;
              vTAB_MVT(vM).usu_in_altera        := 1;
              vTAB_MVT(vM).mvt_dt_altera        := SysDate;
              vTAB_MVT(vM).mvt_in_vinculo       := 0;
              vTAB_MVT(vM).pro_tab_in_codigo    := vTAB_MVS.pro_tab_in_codigo;
              vTAB_MVT(vM).pro_pad_in_codigo    := vTAB_MVS.pro_pad_in_codigo;
              vTAB_MVT(vM).pro_in_codigo        := vTAB_MVS.pro_in_codigo;
              vTAB_MVT(vM).apl_tab_in_codigo    := vTAB_CFG.apl_tab_in_codigo;
              vTAB_MVT(vM).apl_pad_in_codigo    := vTAB_CFG.apl_pad_in_codigo;
              vTAB_MVT(vM).apl_in_codigo        := vTAB_CFG.apl_in_codigo;
              vTAB_MVT(vM).alm_tab_in_codigo    := vTAB_MVS.alm_tab_in_codigo;
              vTAB_MVT(vM).alm_pad_in_codigo    := vTAB_MVS.alm_pad_in_codigo;
              vTAB_MVT(vM).alm_in_codigo        := vTAB_MVS.alm_in_codigo;
              vTAB_MVT(vM).loc_in_codigo        := vTAB_MVS.loc_in_codigo;
              vTAB_MVT(vM).mvt_re_quantidade    := cITI.bxi_re_quantidade;
              vTAB_MVT(vM).mvt_re_aquisicao     := 0;
              vTAB_MVT(vM).mvt_re_vlunitario    := 0;
              vTAB_MVT(vM).cus_tab_in_codigo    := cITI.cus_tab_in_codigo;
              vTAB_MVT(vM).cus_pad_in_codigo    := cITI.cus_pad_in_codigo;
              vTAB_MVT(vM).cus_ide_st_codigo    := cITI.cus_ide_st_codigo;
              vTAB_MVT(vM).cus_in_reduzido      := cITI.cus_in_reduzido;
              vTAB_MVT(vM).proj_tab_in_codigo   := Null;
              vTAB_MVT(vM).proj_pad_in_codigo   := Null;
              vTAB_MVT(vM).proj_ide_st_codigo   := Null;
              vTAB_MVT(vM).proj_in_reduzido     := Null;
              vTAB_MVT(vM).mvs_in_reserva       :=0;
              vTAB_MVT(vM).mvt_in_vinculo        := vTAB_MVT(vM).mvt_in_lancam;
              -- Prepara movimento dos lotes
              vTAB_MVL(vL).org_tab_in_codigo  := vTAB_MVS.org_tab_in_codigo;
              vTAB_MVL(vL).org_pad_in_codigo  := vTAB_MVS.org_pad_in_codigo;
              vTAB_MVL(vL).org_in_codigo      := vTAB_MVS.org_in_codigo;
              vTAB_MVL(vL).org_tau_st_codigo  := vTAB_MVS.org_tau_st_codigo;
              vTAB_MVL(vL).ser_tab_in_codigo  := vTAB_MVT(vM).ser_tab_in_codigo;
              vTAB_MVL(vL).ser_in_sequencia   := vTAB_MVT(vM).ser_in_sequencia;
              vTAB_MVL(vL).mvt_in_lancam      := vTAB_MVT(vM).mvt_in_lancam;
              vTAB_MVL(vL).fil_in_codigo      := vTAB_MVS.fil_in_codigo;
              vTAB_MVL(vL).mvt_dt_movimento   := cINV.inv_dt_movimento;
              vTAB_MVL(vL).mvt_dt_validade    := vTAB_MVS.mvs_dt_validade;
              vTAB_MVL(vL).pro_tab_in_codigo  := vTAB_MVS.pro_tab_in_codigo;
              vTAB_MVL(vL).pro_pad_in_codigo  := vTAB_MVS.pro_pad_in_codigo;
              vTAB_MVL(vL).pro_in_codigo      := vTAB_MVS.pro_in_codigo;
              vTAB_MVL(vL).alm_tab_in_codigo  := vTAB_MVS.alm_tab_in_codigo;
              vTAB_MVL(vL).alm_pad_in_codigo  := vTAB_MVS.alm_pad_in_codigo;
              vTAB_MVL(vL).alm_in_codigo      := vTAB_MVS.alm_in_codigo;
              vTAB_MVL(vL).loc_in_codigo      := vTAB_MVS.loc_in_codigo;
              vTAB_MVL(vL).mvl_re_quantidade  := cITI.bxi_re_quantidade;
              vTAB_MVL(vL).nat_tab_in_codigo  := vTAB_MVS.nat_tab_in_codigo;
              vTAB_MVL(vL).nat_pad_in_codigo  := vTAB_MVS.nat_pad_in_codigo;
              vTAB_MVL(vL).nat_st_codigo      := vTAB_MVS.nat_st_codigo;
              vTAB_MVL(vL).mvl_dt_entrada     := vTAB_MVS.mvs_dt_entrada;
              vTAB_MVL(vL).mvl_st_loteforne   := vTAB_MVS.mvs_st_loteforne;
              vTAB_MVL(vL).mvl_st_referencia  := vTAB_MVS.mvs_st_referencia;
              vTAB_MVL(vL).mvl_in_reserva     := vTAB_MVS.mvs_in_reserva;
              -- Efetiva o movimento de Estoque
              p_GeraMovimentoEstoque_New;
              Update IDP.apt_pro_itensinventario iti
                 Set iti.iti_ch_status     = 'B',
                     iti.mvt_in_lancam     = vTAB_MVT(vM).mvt_in_lancam,
                     iti.org_tab_in_codigo = vTAB_MVT(vM).org_tab_in_codigo,
                     iti.org_pad_in_codigo = vTAB_MVT(vM).org_pad_in_codigo,
                     iti.org_in_codigo     = vTAB_MVT(vM).org_in_codigo,
                     iti.org_tau_st_codigo = vTAB_MVT(vM).org_tau_st_codigo,
                     iti.ser_tab_in_codigo = vTAB_MVT(vM).ser_tab_in_codigo,
                     iti.ser_in_sequencia  = vTAB_MVT(vM).ser_in_sequencia
               Where iti.mov_In_Sequencia = cINV.mov_in_sequencia
                 And iti.fil_in_codigo    = cINV.fil_in_codigo
                 And iti.iti_ch_status    = 'A';
           End Loop;
           -- Atualiza o Status da tabela de controle de baixa
           Update IDP.apt_pro_inventario inv
              Set inv.inv_ch_status = 'B'
            Where inv.mov_in_sequencia = cINV.MOV_in_sequencia
              And inv.fil_in_codigo    = cINV.fil_in_codigo
              And inv.inv_ch_status = 'A';
           vMENSAGEM:='inventário inserido com sucesso!';
           -- somente efetiva se não der erro na rotina;
           if v_Encerra = 'S' then
              commit;
           else
              rollback;
           end if;
        end loop;
     end if;
     If vMENSAGEM IS NULL Then
        vMENSAGEM:='Não foi inserido nenhuma baixa!';
     End If;
     Open pRESULT For
        Select vMENSAGEM as MSG From dual;
  End p_Gera_MovimentoInventario;



  procedure apt_RetornaItensDisp(pFIL_IN_CODIGO NUMBER,
                                 pORG_IN_CODIGO NUMBER,
                                 pRESULT            IN OUT SYS_REFCURSOR) is
begin
   --Raise_application_error(-20000, pORG_IN_CODIGO);
   open pRESULT for
      select mvs.pro_in_codigo,
             pro.pro_st_descricao,
             mvs.mvs_re_quantidade,
             mvs.mvs_st_loteforne,
             substr(adm_pck_util.f_formatacaract(mvs.mvs_st_referencia),1,200) mvs_st_referenciadesc,
             mvs.mvs_st_referencia
        from est_movsumarizado mvs,
             est_produtos pro
       where pro.pro_tab_in_codigo = mvs.pro_tab_in_codigo
         and pro.pro_pad_in_codigo = mvs.pro_pad_in_codigo
         and pro.pro_in_codigo = mvs.pro_in_codigo
         and mvs.pro_pad_in_codigo = pck_mega.achapadraodatabela(pFIL_IN_CODIGO,100,sysdate)
         and mvs.org_in_codigo = pORG_IN_CODIGO
         and mvs.fil_in_codigo = pFIL_IN_CODIGO;
end apt_RetornaItensDisp;

procedure p_GeraMovimentoLotes is
  vLote number;
begin
   Adm_Pck_MovimentoEstoque.AddLotesMov(Adm_Pck_MovimentoEstoque.vTabLotes);
   vLote := Adm_Pck_MovimentoEstoque.vTabLotes.Last;

   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).org_tab_in_codigo  := vTAB_MVL(vL).ORG_TAB_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).org_pad_in_codigo  := vTAB_MVL(vL).ORG_PAD_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).org_in_codigo      := vTAB_MVL(vL).ORG_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).org_tau_st_codigo  := vTAB_MVL(vL).ORG_TAU_ST_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).ser_tab_in_codigo  := vTAB_MVL(vL).SER_TAB_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).ser_in_sequencia   := vTAB_MVL(vL).SER_IN_SEQUENCIA;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvt_in_lancam      := vTAB_MVL(vL).MVT_IN_LANCAM;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).fil_in_codigo      := vTAB_MVL(vL).FIL_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_st_loteforne   := vTAB_MVL(vL).mvl_st_loteforne;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvt_dt_movimento   := vTAB_MVL(vL).mvt_dt_movimento;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvt_dt_validade    := vTAB_MVL(vL).mvt_dt_validade;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).pro_tab_in_codigo  := vTAB_MVL(vL).PRO_TAB_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).pro_pad_in_codigo  := vTAB_MVL(vL).PRO_PAD_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).pro_in_codigo      := vTAB_MVL(vL).PRO_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).alm_tab_in_codigo  := vTAB_MVL(vL).ALM_TAB_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).alm_pad_in_codigo  := vTAB_MVL(vL).ALM_PAD_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).alm_in_codigo      := vTAB_MVL(vL).ALM_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).loc_in_codigo      := vTAB_MVL(vL).LOC_IN_CODIGO;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_re_quantidade  := vTAB_MVL(vL).mvl_re_quantidade;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).nat_tab_in_codigo  := vTAB_MVL(vL).nat_tab_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).nat_pad_in_codigo  := vTAB_MVL(vL).nat_pad_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).nat_st_codigo      := vTAB_MVL(vL).nat_st_codigo;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_dt_entrada     := vTAB_MVL(vL).mvl_dt_entrada;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_st_referencia  := vTAB_MVL(vL).mvl_st_referencia;
   Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_in_reserva     := vTAB_MVL(vL).mvl_in_reserva;
   --v_QTDE_PRODUTO := v_QTDE_PRODUTO + cLPROD.APT_RE_QUANTIDADE;
   If vTAB_PRO.pro_bo_controlalotes = 'S' Then
      Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_st_loteforne   := vTAB_MVL(vL).mvl_st_loteforne;
      Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_st_referencia  := vTAB_MVL(vL).mvl_st_referencia;
      Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_in_reserva     := vTAB_MVL(vL).mvl_in_reserva;
   elsIf vTAB_PRO.pro_bo_controlalotes = 'N' Then
      Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_st_loteforne   := '*';
      Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_st_referencia  := '*';
      Adm_Pck_MovimentoEstoque.vTabLotes(vLote).mvl_in_reserva     := 0;
   End If;
end p_GeraMovimentoLotes;

procedure p_GeraMovimentoEstoque is
vMov Number;
begin
   Adm_Pck_MovimentoEstoque.Inicializa;
   Adm_Pck_MovimentoEstoque.AddMov(Adm_Pck_MovimentoEstoque.vTabMovEstoque);
   vMov := Adm_Pck_MovimentoEstoque.vTabMovEstoque.Last;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).org_tab_in_codigo    := vTAB_MVT(vL).Org_Tab_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).org_pad_in_codigo    := vTAB_MVT(vL).Org_Pad_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).org_in_codigo        := vTAB_MVT(vL).Org_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).org_tau_st_codigo    := vTAB_MVT(vL).Org_Tau_St_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).ser_tab_in_codigo    := vTAB_MVT(vL).ser_tab_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).ser_in_sequencia     := vTAB_MVT(vL).ser_in_sequencia;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_in_lancam        := vTAB_MVT(vL).mvt_in_lancam;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).fil_in_codigo        := vTAB_MVT(vL).Fil_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).acao_tab_in_codigo   := vTAB_MVT(vL).acao_tab_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).acao_pad_in_codigo   := vTAB_MVT(vL).acao_pad_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).acao_in_codigo       := vTAB_MVT(vL).acao_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_ch_origem        := vTAB_MVT(vL).mvt_ch_origem;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_st_entrsaida     := vTAB_MVT(vL).mvt_st_entrsaida;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).tpm_tab_in_codigo    := vTAB_MVT(vL).tpm_tab_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).tpm_pad_in_codigo    := vTAB_MVT(vL).tpm_pad_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).tpm_in_codigo        := vTAB_MVT(vL).tpm_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_st_numdoc        := vTAB_MVT(vL).mvt_st_numdoc;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_dt_documento     := vTAB_MVT(vL).mvt_dt_documento;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_dt_movimento     := vTAB_MVT(vL).mvt_dt_movimento;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).usu_in_inclusao      := vTAB_MVT(vL).usu_in_inclusao;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_dt_inclusao      := vTAB_MVT(vL).mvt_dt_inclusao;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).usu_in_altera        := vTAB_MVT(vL).usu_in_altera;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_dt_altera        := vTAB_MVT(vL).mvt_dt_altera;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_in_vinculo       := vTAB_MVT(vL).Mvt_In_Vinculo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).pro_tab_in_codigo    := vTAB_MVT(vL).Pro_Tab_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).pro_pad_in_codigo    := vTAB_MVT(vL).Pro_Pad_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).pro_in_codigo        := vTAB_MVT(vL).Pro_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).apl_tab_in_codigo    := vTAB_MVT(vL).apl_tab_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).apl_pad_in_codigo    := vTAB_MVT(vL).apl_pad_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).apl_in_codigo        := vTAB_MVT(vL).apl_in_codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).alm_tab_in_codigo    := vTAB_MVT(vL).Alm_Tab_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).alm_pad_in_codigo    := vTAB_MVT(vL).Alm_Pad_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).alm_in_codigo        := vTAB_MVT(vL).Alm_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).loc_in_codigo        := vTAB_MVT(vL).Loc_In_Codigo;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_re_quantidade    := vTAB_MVT(vL).mvt_re_quantidade;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_re_aquisicao     := vTAB_MVT(vL).mvt_re_aquisicao;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvt_re_vlunitario    := vTAB_MVT(vL).mvt_re_vlunitario;
   Adm_Pck_MovimentoEstoque.vTabMovEstoque(vMov).mvs_in_reserva       := 0;
   p_GeraMovimentoLotes;
   begin
      Adm_Pck_MovimentoEstoque.AtualizaMovEstq('I');
   exception when others then
      null;
   end;
end p_GeraMovimentoEstoque;

procedure apt_retornaDemanda(pORG_IN_CODIGO NUMBER,
                             pORD_SEQ_IN_CODIGO NUMBER,
                             pORD_IN_CODIGO NUMBER,
                             pRESULT IN OUT SYS_REFCURSOR) is
begin
   --Raise_application_error(-20000, pFIL_IN_CODIGO ||'-'||pORD_IN_CODIGO);
   open pRESULT for
      select dep.org_tab_in_codigo,
             dep.org_pad_in_codigo,
             dep.org_in_codigo,
             dep.org_tau_st_codigo,
             dep.ord_tab_in_codigo,
             dep.ord_seq_in_codigo,
             dep.ord_in_codigo,
             dep.com_tab_in_codigo,
             dep.com_pad_in_codigo,
             dep.com_in_codigo,
             dep.dde_in_operacao,
             dep.dde_dt_necessidade,
             pro.pro_st_descricao,
             pro.uni_st_unidade,
             dep.dde_re_qtde_unitaria,
             pro.pro_in_criteriobusca,
             pro.pro_st_politicareposicao
        from pro_demanda_dep dep,
             est_produtos pro
       where dep.com_tab_in_codigo = pro.pro_tab_in_codigo
         and dep.com_pad_in_codigo = pro.pro_pad_in_codigo
         and dep.com_in_codigo     = pro.pro_in_codigo
         and dep.org_in_codigo     = pORG_IN_CODIGO
         and dep.ord_seq_in_codigo = pORD_SEQ_IN_CODIGO
         and dep.ord_in_codigo     = pORD_IN_CODIGO;
end apt_retornaDemanda;

function f_validademandaestoque(pAPT_IN_SEQUENCIA In number) return varchar2 is
  v_permite varchar2(1);
  v_temlote char(1);
  begin
    v_permite := 'S';
    for cDEM in (
        select dem.*
          from IDP.apt_apontademanda_estoque dem
         where dem.apt_in_sequencia = pAPT_IN_SEQUENCIA
           and dem.ctl_in_codigo is not null)
    loop
       v_temlote := 'N';
       -- Busca lotes no estoque
       for cMOV in(
          select *
            from est_movsumarizado mvs
           where mvs.org_in_codigo = cdem.org_in_codigo
             and mvs.fil_in_codigo = cdem.fil_in_codigo
             and mvs.pro_tab_in_codigo = cdem.com_tab_in_codigo
             and mvs.pro_pad_in_codigo = cdem.com_pad_in_codigo
             and mvs.pro_in_codigo = cdem.com_in_codigo
             and mvs.mvs_st_loteforne = cdem.mvs_st_loteforne
             and mvs.mvs_re_quantidade >= cdem.apt_re_qtdeselecionada
         )
       loop
          v_temlote := 'S';
       end loop;
       if v_temlote = 'N' then
          if v_permite = 'S' then
             v_permite := 'Lote de demanda :'||cDEm.Mvs_St_Loteforne;
          else
             v_permite := v_permite||' '|| cDEm.Mvs_St_Loteforne;
          end if;
       end if;
    end loop;
    if v_permite <> 'S' then
       v_permite := v_permite||' não disponível no estoque!';
    end if;
    Return(v_permite);
  end;
  
    
  
  procedure p_SumarizaApto is
  
  begin
     -- soma a qtde de produto principal
     vAPTO.ord_re_produto :=0;
     vAPTO.ord_re_subproduto :=0;
     vAPTO.ord_re_refugo :=0;
     begin
        select sum(lot.orl_re_qtdlote)
          into vAPTO.ord_re_produto
          from idp.apt_apontaordem_lote lot
         where lot.apt_in_sequencia = vTAB_APT.Apt_In_Sequencia
           and lot.orl_st_tipolote  = 'P'
           and lot.apt_ch_status    = 'A';
     exception when others then 
        null;
     end;
     if vAPTO.ord_re_produto is null then
        vAPTO.ord_re_produto :=0;     
     end if;
     -- Busca o tipo de Movimento;
     if vAPTO.ord_re_produto > 0 then 
        Begin
           Select a.tmo_in_codigo
             Into vAPTO.tmo_in_codigoprod
             From pro_tipomovto a
            Where a.pai_tmo_in_codigo = vTAB_APO.Tmo_In_Codigo
              And a.tmo_ch_tpdoc      = 'O'
              And a.tmo_ch_tpmovord   = 'ED'
              and a.tmo_in_codigo     = vTAB_APO.Tmo_In_Codigo;
        Exception When no_data_found then
           vAPTO.tmo_in_codigoref := Null;
           Raise_application_error(-20000, 'Não há tipo de movimento "ED - SubProduto" parametrizado para apontamento de ordens.');
        End;
     end if;  
     -- soma a qtde de subproduto
     begin
        select sum(lot.orl_re_qtdlote) 
          into vAPTO.ord_re_subproduto
          from idp.apt_apontaordem_lote lot
         where lot.apt_in_sequencia = vTAB_APT.Apt_In_Sequencia
           and lot.orl_st_tipolote  <> 'P'
           and lot.apt_ch_status    = 'A';
     exception when others then 
        null;
     end;
     -- Busca o tipo de Movimento de SubProduto;
     if vAPTO.ord_re_subproduto > 0 then 
        if nvl(vAPTO.ord_re_produto,0) = 0 then 
           Begin
              Select a.tmo_in_codigo
                Into vAPTO.tmo_in_codigoprod
                From pro_tipomovto a
               Where a.pai_tmo_in_codigo = vTAB_APO.Tmo_In_Codigo
                 And a.tmo_ch_tpdoc      = 'O'
                 And a.tmo_ch_tpmovord   = 'ED'
                 and a.tmo_in_codigo     = vTAB_APO.Tmo_In_Codigo;
           Exception When no_data_found then
              vAPTO.tmo_in_codigoref := Null;
              Raise_application_error(-20000, 'Não há tipo de movimento "ED - SubProduto" parametrizado para apontamento de ordens.');
           End;
        end if; 
        
        Begin
           Select a.tmo_in_codigo
             Into vAPTO.tmo_in_codigosub
             From pro_tipomovto a
            Where a.pai_tmo_in_codigo = vTAB_APO.Tmo_In_Codigo
              And a.tmo_ch_tpdoc      = 'P'
              And a.tmo_ch_tpmovord   = 'ED'
              and a.pai_tmo_in_codigo = vTAB_APO.Tmo_In_Codigo;
        Exception When no_data_found then
           vAPTO.tmo_in_codigoref := Null;
           Raise_application_error(-20000, 'Não há tipo de movimento "ED - SubProduto" parametrizado para apontamento de ordens.');
        End;             
     end if;     
     -- soma a qtde de refugo
     begin
        select sum(lot.orl_re_qtdref)
          into vAPTO.ord_re_refugo
          from idp.apt_apontaordem_lote lot
         where lot.apt_in_sequencia = vTAB_APT.Apt_In_Sequencia
           and lot.apt_ch_status    = 'A';
     exception when others then 
        null;
     end;
     -- Busca o tipo de Movimento de Refugo
     if vAPTO.ord_re_refugo > 0 then 
        Begin
           Select a.tmo_in_codigo
             Into vAPTO.tmo_in_codigoref
             From pro_tipomovto a
            Where a.pai_tmo_in_codigo = vTAB_APO.Tmo_In_Codigo
              And a.tmo_ch_tpdoc      = 'O'
              And a.tmo_ch_tpmovord   = 'RF';
        Exception When no_data_found then
           vAPTO.tmo_in_codigoref := Null;
           Raise_application_error(-20000, 'Não há tipo de movimento "RF - Refugo" parametrizado para apontamento de ordens.');
        End;
     end if;
     
     -- soma a qtde de Demandas
     begin
        select sum(dem.apt_re_qtdeselecionada)
          into vAPTO.ord_re_demanda
          from IDP.apt_apontademanda_estoque dem
         where dem.apt_in_sequencia = vTAB_APT.Apt_In_Sequencia
           and dem.dde_st_situacao  = 'A'
           ;
     exception when others then 
        null;
     end;
     -- Busca o tipo de Movimento de Demanda
     if vAPTO.ord_re_demanda > 0 then 
        Begin
           Select a.tmo_in_codigo
             Into vAPTO.tmo_in_codigodem
             From pro_tipomovto a
            Where a.pai_tmo_in_codigo = vTAB_APO.Tmo_In_Codigo
              And a.tmo_ch_tpdoc      = 'D'
              And a.tmo_ch_tpmovord   = 'SD' ;
        Exception When no_data_found then
           vAPTO.tmo_in_codigoref := Null;
           Raise_application_error(-20000, 'Não há tipo de movimento "SD - Demanda" parametrizado para apontamento de ordens.');
        End;
     end if;     
  end p_SumarizaApto;  
  procedure p_SumarizaDemanda is
  
  begin
     vAPTO.ord_re_demanda := 0;         
     -- soma a qtde de Demandas
     begin
        select sum(dem.apt_re_qtdeselecionada)
          into vAPTO.ord_re_demanda
          from IDP.apt_apontademanda_estoque dem
         where dem.apt_in_sequencia = vTAB_APT.Apt_In_Sequencia
           and dem.com_tab_in_codigo = vTAB_DEP.com_tab_in_codigo                         
           and dem.com_pad_in_codigo = vTAB_DEP.com_pad_in_codigo
           and dem.com_in_codigo     = vTAB_DEP.com_in_codigo
           and dem.Dde_St_Situacao   = 'A';
     exception when others then 
        null;
     end;
  end p_SumarizaDemanda;  
  procedure p_SumarizaLotes(pAPT_IN_SEQUENCIA in number) is
  
  begin
     -- soma a qtde de apontamentos;
     begin
        select sum(apt.orl_re_qtdlote)
          into vTAB_APT.apt_re_quantidade
          from IDP.Apt_Apontaordem_Lote apt
         where apt.apt_in_sequencia = pAPT_IN_SEQUENCIA;
     exception when others then 
        null;
     end;
     -- Atualiza total do apontamento;
     update apt_apontaordem apo
        set apo.apt_re_quantidade = vTAB_APT.apt_re_quantidade
      where apo.apt_in_sequencia = vTAB_APT.apt_in_sequencia;
  end p_SumarizaLotes;  
    
Procedure p_EfetivaApontamento
  ( pRESULT IN OUT SYS_REFCURSOR,
    pAPT_IN_SEQUENCIA In IDP.APT_APONTAORDEM.APT_IN_SEQUENCIA%Type,
    pCOMP_ST_NOME in varchar2,
    pUSU_IN_CODIGO in number
  ) Is
  PRAGMA AUTONOMOUS_TRANSACTION;
  v_QTDE_PRODUTO NUMBER;
  v_QTDE_SUBPRODUTO NUMBER;
  v_EFETIVAR CHAR(1);
  v_APONTA CHAR(1); 
  v_DEMANDA CHAR(1); 
  v_PRIORITEM CHAR(1);
  v_CORRECAO CHAR(1);
  -- 14/09/2020 - JPC  

  Cursor C_OrdLot Is
    Select a.*
    From PRO_ORDEMLOTESUB a
    Where a.org_tab_in_codigo  = vTAB_ORD.Org_Tab_In_Codigo
      And a.org_pad_in_codigo  = vTAB_ORD.Org_Pad_In_Codigo
      And a.org_tau_st_codigo  = vTAB_ORD.Org_Tau_St_Codigo
      And a.org_in_codigo      = vTAB_ORD.Org_In_Codigo
      And a.ord_tab_in_codigo  = vTAB_ORD.Ord_Tab_In_Codigo
      And a.ord_seq_in_codigo  = vTAB_ORD.Ord_Seq_In_Codigo
      And a.ord_in_codigo      = vTAB_ORD.Ord_In_Codigo
      And ( a.orl_re_qtdlote - a.orl_re_qtdrecebida - a.orl_re_qtdrefugada ) > 0
    Order By a.orl_st_slotefabricacao;
  V_OrdLot                     C_OrdLot%Rowtype;

  Cursor C_OrdDem Is
    --Select Distinct para não retornar várias linhas qdo vários lotes reservados para a mesma demanda
    SELECT a.*
      FROM IDP.APT_APONTADEMANDA a
     WHERE a.apt_in_sequencia   = vTAB_APT.Apt_In_Sequencia
       --and a.com_in_codigo = 188
       ;

  V_OrdDem                     C_OrdDem%Rowtype;


  vcont                        Number;  
  vMENSAGEM varchar2(200);
  vAPT tAPT;
  vCURSOR TCURSOR;

  Begin
     -- Corrige dados de apontamento;
     v_CORRECAO := 'N';
     for cAPT in (
        select apt.*
          from IDP.APT_APONTAORDEM apt
         where apt.apt_in_sequencia  = pAPT_IN_SEQUENCIA
           and apt.apt_ch_status = 'A')
     loop
        vTAB_APT := cAPT;
        -- Carrega programação da Ordem definida para apontamento;
        for cPRG in (
           select ppo.*
             from pro_prog_ordem ppo
            where ppo.org_tab_in_codigo = vTAB_APT.Org_Tab_In_Codigo
              and ppo.org_pad_in_codigo = vTAB_APT.Org_Pad_In_Codigo
              and ppo.org_in_codigo     = vTAB_APT.Org_In_Codigo
              and ppo.org_tau_st_codigo = vTAB_APT.Org_Tau_St_Codigo
              and ppo.ord_tab_in_codigo = vTAB_APT.Ord_Tab_In_Codigo
              and ppo.ord_seq_in_codigo = vTAB_APT.Ord_Seq_In_Codigo
              and ppo.ord_in_codigo     = vTAB_APT.Ord_In_Codigo
              and ppo.plf_in_sqoperacao = vTAB_APT.Plf_In_Sqoperacao
              and ppo.tmp_ch_aponta     = 'S'
              and ppo.tmp_ch_utilrecurso = 'A')
        loop
           vTAB_PRG := cPRG;
        end loop;        
        if vTAB_APT.Apt_Maq_In_Codigo is null then
           vTAB_APT.Apt_Maq_In_Codigo := vTAB_PRG.Maq_In_Codigo;
           v_CORRECAO := 'S';
        end if;
        if vTAB_APT.Apt_Cmaq_In_Codigo is null then
           if vTAB_PRG.cMaq_In_Codigo is not null then              
              vTAB_APT.Apt_Cmaq_In_Codigo := vTAB_PRG.cMaq_In_Codigo;
              v_CORRECAO := 'S';
           end if;
        elsif vTAB_APT.Apt_Cmaq_In_Codigo <> vTAB_PRG.cMaq_In_Codigo then
           if vTAB_PRG.cMaq_In_Codigo is not null then              
              vTAB_APT.Apt_Cmaq_In_Codigo := vTAB_PRG.cMaq_In_Codigo;
              v_CORRECAO := 'S';
           end if;                     
        end if;
        if v_CORRECAO = 'S' then
           update IDP.APT_APONTAORDEM apo
              set apo.Apt_Cmaq_In_Codigo = vTAB_APT.Apt_Cmaq_In_Codigo,
                  apo.apt_maq_in_codigo = vTAB_APT.Apt_maq_In_Codigo
            where apo.apt_in_sequencia = vTAB_APT.Apt_In_Sequencia;
            commit;
        end if;
     end loop;               
     
     for cAPT in (
        select apt.*
          from IDP.APT_APONTAORDEM apt
         where apt.apt_in_sequencia  = pAPT_IN_SEQUENCIA)
     loop
        if pAPT_IN_SEQUENCIA = 33982800 then
           v_APONTA := 'S';
           v_DEMANDA := 'N';
        else
           v_APONTA := 'S';
           v_DEMANDA := 'S';
        end if;
        vTAB_APT:= cAPT;        
        vTAB_APO.Org_Tab_In_Codigo := cAPT.Org_Tab_In_Codigo;
        vTAB_APO.Org_Pad_In_Codigo := cAPT.Org_Pad_In_Codigo;
        vTAB_APO.Org_In_Codigo     := cAPT.Org_In_Codigo;
        vTAB_APO.Org_Tau_St_Codigo := cAPT.Org_Tau_St_Codigo;
        vTAB_APO.Ord_Tab_In_Codigo := cAPT.Ord_Tab_In_Codigo;
        vTAB_APO.Ord_Seq_In_Codigo := cAPT.Ord_Seq_In_Codigo;
        vTAB_APO.Ord_In_Codigo     := cAPT.Ord_In_Codigo;
        vTAB_APO.Fil_In_Codigo     := cAPT.Fil_In_Codigo;
        vTAB_APO.Apo_In_Sequencia  := pck_mega.proximasequenciatab(226);
        vTAB_APO.Plf_In_Sqoperacao := cAPT.Plf_In_Sqoperacao;
        vTAB_APO.Apo_Re_Tempoinicial  := cAPT.Apt_Re_Tempoinicial;
        vTAB_APO.Apo_Re_Tempofinal  := cAPT.Apt_Re_Tempofinal;
        vTAB_APO.Apo_Re_Tempototal  := cAPT.Apt_Re_Tempototal;
        vTAB_APO.apo_dt_apontamento := cAPT.Apt_Dt_Encerramento;
        vTAB_APO.apo_st_documento  := cAPT.Apt_St_Documento;
        vTAB_APO.usu_in_aponta := pUSU_IN_CODIGO;
        vTAB_APO.Usu_In_Aponta := pUSU_IN_CODIGO;
        vTAB_APO.APO_CH_ORIGEM := 'M';
        vTAB_APO.apo_bo_encerra := 'N';
        vTAB_APO.Apo_Ch_Proc    := 'N';
        vTAB_APO.Usu_In_Digita := pUSU_IN_CODIGO;
        vTAB_APO.apo_in_nrpessoas := cAPT.Apt_In_Operadores;
        begin
           Select opd.opd_pad_in_codigo,
                  opd.opd_in_codigo,
                  opd.col_in_codigo
             Into vTAB_APO.opd_pad_in_codigo  ,
                  vTAB_APO.opd_in_codigo  ,
                  vTAB_APO.col_in_codigo
             From PRO_CADOPERADOR opd
            Where opd.opd_st_alternativo = cAPT.Apt_Adm_St_Chapeira;
        exception when no_data_found then
           vTAB_APO.opd_pad_in_codigo := 1;
           vTAB_APO.opd_in_codigo     := 1;
           vTAB_APO.col_in_codigo     := 0;
        end;
        -- Carrega ordem
        for cORD in (
           select ord.*
             from pro_ordens ord
            where ord.org_tab_in_codigo = vTAB_APO.Org_Tab_In_Codigo
              and ord.org_pad_in_codigo = vTAB_APO.Org_Pad_In_Codigo
              and ord.org_in_codigo     = vTAB_APO.Org_In_Codigo
              and ord.org_tau_st_codigo = vTAB_APO.Org_Tau_St_Codigo
              and ord.ord_tab_in_codigo = vTAB_APO.Ord_Tab_In_Codigo
              and ord.ord_seq_in_codigo = vTAB_APO.Ord_Seq_In_Codigo
              and ord.ord_in_codigo     = vTAB_APO.Ord_In_Codigo)
        loop
           vTAB_ORD := cORD;
        end loop;
        for cOCE in(
           select oce.* 
             from pro_ordenscmpesp oce
            where oce.org_tab_in_codigo = vTAB_APO.Org_Tab_In_Codigo
              and oce.org_pad_in_codigo = vTAB_APO.Org_Pad_In_Codigo
              and oce.org_in_codigo     = vTAB_APO.Org_In_Codigo
              and oce.org_tau_st_codigo = vTAB_APO.Org_Tau_St_Codigo
              and oce.ord_tab_in_codigo = vTAB_APO.Ord_Tab_In_Codigo
              and oce.ord_seq_in_codigo = vTAB_APO.Ord_Seq_In_Codigo
              and oce.ord_in_codigo     = vTAB_APO.Ord_In_Codigo
        )
        loop
           vOCE := cOCE;
        end loop;
        -- Carrega produto
        for cPRO in (
           select pro.*
             from est_produtos pro
            where pro.pro_tab_in_codigo = vTAB_ORD.pro_tab_in_codigo
              and pro.pro_pad_in_codigo = vTAB_ORD.pro_pad_in_codigo
              and pro.pro_in_codigo     = vTAB_ORD.pro_in_codigo)
        loop
           vTAB_PRO := cPRO;
        end loop;        
        
        vTAB_APO.Uni_Tab_In_Codigo := vTAB_PRG.Uni_Tab_In_Codigo;
        vTAB_APO.Uni_Pad_In_Codigo := vTAB_PRG.Uni_Pad_In_Codigo;
        vTAB_APO.Uni_St_Unidade    := vTAB_PRG.Uni_St_Unidade;
        
        vTAB_APO.Maq_Tab_In_Codigo := vTAB_PRG.Maq_Tab_In_Codigo;
        vTAB_APO.Maq_Pad_In_Codigo := vTAB_PRG.Maq_Pad_In_Codigo;
        vTAB_APO.Maq_In_Codigo     := vTAB_PRG.Maq_In_Codigo;
        -- Carrega tipo de Ordens;
        for cTPO in (
           select tmo.*
             from PRO_TIPOORDENS tmo
            where tmo.tpo_tab_in_codigo  = vTAB_ORD.Tpo_Tab_In_Codigo
              and tmo.tpo_pad_in_codigo  = vTAB_ORD.Tpo_Pad_In_Codigo
              and tmo.tpo_st_codigo_tipo = vTAB_ORD.Tpo_St_Codigo_Tipo)
        loop
          vTAB_TPO := cTPO;
        end loop;                
        -- sumariza os apontamentos;
        for cSUM in (
           select nvl(sum(apt.orl_re_qtdlote),0) as apo_Re_Quantidade,
                  nvl(sum(apt.orl_re_unidade),0) as apo_re_quantidadesec,
                  nvl(sum(apt.orl_re_qtdref),0) as apo_re_quantidaderef
             from IDP.apt_apontaordem_lote apt
            where apt.org_tab_in_codigo = vTAB_APO.Org_Tab_In_Codigo
              and apt.org_pad_in_codigo = vTAB_APO.Org_Pad_In_Codigo
              and apt.org_in_codigo     = vTAB_APO.Org_In_Codigo
              and apt.org_tau_st_codigo = vTAB_APO.Org_Tau_St_Codigo
              and apt.ord_tab_in_codigo = vTAB_APO.Ord_Tab_In_Codigo
              and apt.ord_seq_in_codigo = vTAB_APO.Ord_Seq_In_Codigo
              and apt.ord_in_codigo     = vTAB_APO.Ord_In_Codigo
              and apt.apt_in_sequencia  = pAPT_IN_SEQUENCIA
              and apt.orl_st_tipolote   = 'P'
              and apt.apt_ch_status     = 'A')
        loop
           vTAB_APO.Apo_Re_Quantidade := cSUM.apo_Re_Quantidade;
           vTAB_APO.Apo_Re_Quantidadesec := cSUM.apo_re_quantidadesec;
           vTAB_APO.apo_re_quantidaderef := cSUM.apo_re_quantidaderef;
           vTAB_APO.apo_re_quantidadesecref := 0;
        end loop;
        vTAB_APO.Ati_Tab_In_Codigo := vTAB_TPO.Ati_Tab_In_Codigoint;
        vTAB_APO.Ati_Pad_In_Codigo := vTAB_TPO.Ati_Pad_In_Codigoint;
        vTAB_APO.Ati_In_Codigo     := vTAB_TPO.Ati_In_Codigoint;
        vTAB_APO.Tmo_In_Codigo     := vTAB_TPO.Tmo_In_Codigoint;
        p_SumarizaApto;
        vAPTO.atualiza_prog := 'N';
        if vTAB_PRG.tmp_ch_bxdemanda <> 'S' then
           vTAB_PRG.tmp_ch_bxdemanda := 'S';
           vAPTO.atualiza_prog := 'S';
        end if;
        if vTAB_PRG.Tmp_Ch_Aponta <> 'S' then
           vTAB_PRG.Tmp_Ch_Aponta := 'S';
           vAPTO.atualiza_prog := 'S';
        end if;
        if vAPTO.atualiza_prog = 'S' then
           Begin
              Update PRO_PROG_ORDEM a
                 Set a.tmp_ch_bxdemanda = vTAB_PRG.tmp_ch_bxdemanda,
                     a.tmp_ch_aponta    = vTAB_PRG.tmp_ch_aponta
               Where a.org_tab_in_codigo = vTAB_PRG.Org_Tab_In_Codigo
                 And a.org_pad_in_codigo = vTAB_PRG.Org_Pad_In_Codigo
                 And a.org_in_codigo     = vTAB_PRG.Org_In_Codigo
                 And a.org_tau_st_codigo = vTAB_PRG.Org_Tau_St_Codigo
                 And a.fil_in_codigo     = vTAB_PRG.Fil_In_Codigo
                 And a.ord_tab_in_codigo = vTAB_PRG.Ord_Tab_In_Codigo
                 And a.ord_seq_in_codigo = vTAB_PRG.Ord_Seq_In_Codigo
                 And a.ord_in_codigo     = vTAB_PRG.Ord_In_Codigo
                 And a.plf_in_sqoperacao = vTAB_PRG.Plf_In_Sqoperacao;
           End;
        end if;
        Update PRO_ORDENS
           Set ord_ch_travaprog    = 'S'
         Where org_tab_in_codigo = vTAB_APO.Org_Tab_In_Codigo
           And org_pad_in_codigo = vTAB_APO.Org_Pad_In_Codigo
           And org_in_codigo     = vTAB_APO.Org_In_Codigo
           And org_tau_st_codigo = vTAB_APO.Org_Tau_St_Codigo
           And ord_tab_in_codigo = vTAB_APO.Ord_Tab_In_Codigo
           And ord_seq_in_codigo = vTAB_APO.Ord_Seq_In_Codigo
           And ord_in_codigo     = vTAB_APO.Ord_In_Codigo;
        -- Inicia o apontamento da ordem;
        Insert Into PRO_APONTAORDEM values vTAB_APO;
     end loop;

     v_EFETIVAR := 'S';
     vAPTO.ser_tab_in_codigo := 102;
     vAPTO.ser_in_sequencia  := Pck_Mega.AchaSequenciaDaTabela(vTAB_APO.org_in_codigo, 
                                                               vAPTO.ser_tab_in_codigo, 
                                                               Sysdate);
     --Executa o processo pendente do apontamento
     Begin
        p_processopendenteapontamento(vTAB_APO.apo_in_sequencia,
                                      vTAB_APO.org_in_codigo,
                                      vTAB_APO.fil_in_codigo,
                                      vTAB_APO.ord_seq_in_codigo,
                                      vTAB_APO.ord_in_codigo);
     End;

     if vTAB_APO.apo_re_quantidade > 0 or vAPTO.ord_re_subproduto > 0 then     
        Select Min (apo.apo_dt_apontamento)
              ,Max(apo.apo_dt_apontamento)
              ,Sum(nvl(apo.apo_re_quantidade,0))
              ,Sum(nvl(apo.apo_re_quantidaderef,0))
              ,nvl(Sum(decode(ati.ati_ch_tipotempo     ,'S',apo.apo_re_tempototal,0)),0)
              ,nvl(Sum(decode(ati.ati_ch_tipotempo     ,'F',apo.apo_re_tempototal,0)),0)
              ,nvl(Sum(decode(ati.ati_ch_tipotempo     ,'M',apo.apo_re_tempototal,0)),0)
              ,nvl(Sum(decode(ati.ati_ch_tipotempo||ati.ati_ch_produtiva,'EP',apo.apo_re_tempototal,0)),0)
              --,nvl(Sum(decode(ati.ati_ch_tipotempo||ati.ati_ch_produtiva,'EI',apo.apo_re_tempototal,0)),0)
         Into vTAB_PRG.Pod_Dt_Inicioreal,
              vTAB_PRG.Pod_dt_terminoreal,
              vTAB_PRG.Pod_re_qtdereal,
              vTAB_PRG.Pod_Re_Qtderefugada,
              vTAB_PRG.pod_re_tempo_setu_real,
              vTAB_PRG.pod_re_tempo_fila_real,
              vTAB_PRG.pod_re_tempo_mov_real,
              vTAB_PRG.pod_re_tempo_exec_real
         From PRO_APONTAORDEM apo,
              PRO_ATIVIDADE   ati
        Where apo.org_tab_in_codigo = vTAB_APO.Org_Tab_In_Codigo
          And apo.org_pad_in_codigo = vTAB_APO.Org_Pad_In_Codigo
          And apo.org_in_codigo     = vTAB_APO.Org_In_Codigo
          And apo.org_tau_st_codigo = vTAB_APO.Org_Tau_St_Codigo
          And apo.fil_in_codigo     = vTAB_APO.Fil_In_Codigo
          And apo.ord_tab_in_codigo = vTAB_APO.Ord_Tab_In_Codigo
          And apo.ord_seq_in_codigo = vTAB_APO.Ord_Seq_In_Codigo
          And apo.ord_in_codigo     = vTAB_APO.Ord_In_Codigo
          And apo.plf_in_sqoperacao = vTAB_APO.Plf_In_Sqoperacao
          And ati.ati_tab_in_codigo = apo.ati_tab_in_codigo
          And ati.ati_pad_in_codigo = apo.ati_pad_in_codigo
          And ati.ati_in_codigo     = apo.ati_in_codigo;
          
        if vAPTO.ord_re_subproduto is null then
           vAPTO.ord_re_subproduto := 0;
        end if;
        if vAPTO.ord_re_refugo is null then
           vAPTO.ord_re_refugo := 0;
        end if;
        vTAB_ORD.Ord_Re_Qtde_Recebida := NVL(vTAB_ORD.Ord_Re_Qtde_Recebida,0)+nvl(vAPTO.ord_re_produto,0)+nvl(vAPTO.ord_re_subproduto,0)+nvl(vAPTO.ord_re_refugo,0);
        vTAB_ORD.Ord_Re_Qtde_Refugada := NVL(vTAB_ORD.Ord_Re_Qtde_Refugada,0)+nvl(vAPTO.ord_re_refugo,0);
          

        If (
              (nvl(vTAB_PRG.Pod_re_qtdereal,0) + nvl(vTAB_PRG.Pod_Re_Qtderefugada,0)) > 0) and nvl(vAPTO.ord_re_produto,0) > 0           
           Then
           --Roda processo de alteração da ordem           
           Begin
              man_pck_ordem.P_ALTERAORDEM(vTAB_ORD.Org_Pad_In_Codigo,
                                          vTAB_ORD.Org_In_Codigo,
                                          vTAB_ORD.Ord_Seq_In_Codigo,
                                          vTAB_ORD.Ord_In_Codigo,
                                          vTAB_ORD.Fil_In_Codigo,
                                          vTAB_ORD.Pro_Pad_In_Codigo,
                                          vTAB_ORD.Pro_In_Codigo,
                                          vTAB_ORD.Cps_In_Codigo,
                                          vTAB_ORD.Lis_In_Revisao,
                                          pUSU_IN_CODIGO,
                                          pCOMP_ST_NOME,
                                          'A',
                                          0,
                                          vTAB_ORD.Ord_Re_Qtde_Recebida,
                                          vTAB_ORD.Ord_Dt_Abertura_Pl,
                                          vTAB_ORD.Ord_Dt_Recebimento);
           End;           
        End if;

        update pro_prog_ordem a
           set a.pod_dt_inicioreal      = vTAB_PRG.pod_dt_inicioreal
              ,a.pod_dt_terminoreal     = vTAB_PRG.pod_dt_terminoreal
              ,a.pod_re_qtdereal        = vTAB_PRG.pod_re_qtdereal
              ,a.pod_re_tempo_setu_real = vTAB_PRG.pod_re_tempo_setu_real
              ,a.pod_re_tempo_exec_real = vTAB_PRG.pod_re_tempo_exec_real
              ,a.pod_re_tempo_fila_real = vTAB_PRG.pod_re_tempo_fila_real
              ,a.pod_re_tempo_mov_real  = vTAB_PRG.pod_re_tempo_mov_real
              ,a.pod_st_situacao        = decode(a.pod_re_qtdenecessaria,vTAB_PRG.pod_re_qtdereal + vTAB_PRG.Pod_Re_Qtderefugada,'EN','AB')
        Where a.org_tab_in_codigo = vTAB_PRG.Org_Tab_In_Codigo
          And a.org_pad_in_codigo = vTAB_PRG.Org_Pad_In_Codigo
          And a.org_in_codigo     = vTAB_PRG.Org_In_Codigo
          And a.org_tau_st_codigo = vTAB_PRG.Org_Tau_St_Codigo
          And a.fil_in_codigo     = vTAB_PRG.Fil_In_Codigo
          And a.ord_tab_in_codigo = vTAB_PRG.Ord_Tab_In_Codigo
          And a.ord_seq_in_codigo = vTAB_PRG.Ord_Seq_In_Codigo
          And a.ord_in_codigo     = vTAB_PRG.Ord_In_Codigo
          And a.plf_in_sqoperacao = vTAB_PRG.Plf_In_Sqoperacao
          And a.tmp_ch_aponta     = 'S';
          
        -- Processo de Recebimento - MOV. ESTOQUE
        -- Última Operação e item com controle de estoque
        If vTAB_PRO.pro_st_cestoque = 'S' Then           
           If ((vTAB_APO.Apo_Re_Quantidade) > 0 or vAPTO.ord_re_subproduto > 0) Then
               v_QTDE_PRODUTO :=0;
               v_QTDE_SUBPRODUTO :=0;               
               -- Totaliza a qtde a ser produzida por item;
               For cLPROD In ( 
                  select lot.pro_tab_in_codigo
                         ,lot.pro_pad_in_codigo
                         ,lot.pro_in_codigo
                         ,lot.orl_st_tipolote
                         ,lot.loc_st_id                                   
                         ,sum(lot.orl_re_qtdlote) apt_re_quantidade
                         ,max(apt_ref_in_codigo) apt_ref_in_codigo
                         ,sum(lot.orl_re_qtdref) apt_re_quantrefugo
                    from idp.apt_apontaordem_lote lot
                   where lot.apt_in_sequencia = vTAB_APT.Apt_In_Sequencia
                     and lot.apt_ch_status    = 'A'
                group by lot.pro_tab_in_codigo
                     ,lot.pro_pad_in_codigo
                     ,lot.pro_in_codigo
                     ,lot.orl_st_tipolote
                     ,lot.loc_st_id
                 order by decode (lot.orl_st_tipolote,'P',1,2)
                    )
               Loop
                  -- Inicializa o apontamento para cada produto;
                  Inicializa;
                  -- Limpa variáveis para cada item produzido gera um movimento de estoque;                  
                  AddMov(vTAB_MVT);
                  vM := vTAB_MVT.Last;                  
                  -- Carrega os dados do produto para apontamento
                  for cPRO in (
                     select pro.*
                       from est_produtos pro
                      where pro.pro_tab_in_codigo = cLPROD.pro_tab_in_codigo
                        and pro.pro_pad_in_codigo = cLPROD.pro_pad_in_codigo
                        and pro.pro_in_codigo     = cLPROD.pro_in_codigo)
                  loop
                     vTAB_PRO := cPRO;
                  end loop;                  

                  vTAB_MVT(vM).mvt_in_lancam := Pck_Mega.ProximaSequenciaOrg(vTAB_APO.Org_In_Codigo, vAPTO.ser_tab_in_codigo, vAPTO.ser_in_sequencia);
                  
                  Begin
                     Update pro_ordens ord
                        set row = vTAB_ORD
                      Where ord.org_tab_in_codigo = vTAB_ORD.Org_Tab_In_Codigo
                        And ord.org_pad_in_codigo = vTAB_ORD.Org_Pad_In_Codigo
                        And ord.org_in_codigo     = vTAB_ORD.Org_In_Codigo
                        And ord.org_tau_st_codigo = vTAB_ORD.Org_Tau_St_Codigo
                        And ord.ord_tab_in_codigo = vTAB_ORD.Ord_Tab_In_Codigo
                        And ord.ord_seq_in_codigo = vTAB_ORD.Ord_Seq_In_Codigo
                        And ord.ord_in_codigo     = vTAB_ORD.Ord_In_Codigo;
                  End;                                                                                            
                  -- Carrega localização do produto;
                  vLOC.org_tab_in_codigo := vTAB_APT.org_tab_in_codigo;
                  vLOC.org_pad_in_codigo := vTAB_APT.org_pad_in_codigo;
                  vLOC.org_in_codigo := vTAB_APT.org_in_codigo;
                  vLOC.org_tau_st_codigo := vTAB_APT.org_tau_st_codigo;
                  vLOC.fil_in_codigo := vTAB_APT.fil_in_codigo;
                  vLOC.pro_tab_in_codigo := cLPROD.pro_tab_in_codigo;
                  vLOC.pro_pad_in_codigo := cLPROD.pro_pad_in_codigo;
                  vLOC.pro_in_codigo := cLPROD.pro_in_codigo;
                  vLOC.tpo_st_codigo_tipo := vTAB_ORD.tpo_st_codigo_tipo;
                  vLOC.apt_maq_in_codigo := vTAB_APT.apt_maq_in_codigo;
                  vLOC.cmaq_in_codigo := vTAB_APT.apt_cmaq_in_codigo;
                  vLOC.opr_in_codigo := vTAB_PRG.opr_in_codigo;
                  vLOC.mov_st_origem := 'PR';
                  p_DefineLocalizacaoItem;
                  if vTAB_APO.Fil_In_Codigo = 31 then
                     if vTAB_TPO.Tpo_St_Codigo_Tipo = 'OT001' and vOCE.Loc_In_Codigo <> 2407 then
                        vTAB_PRL.Alm_In_Codigo := 3;
                        vTAB_PRL.loc_In_Codigo := vOCE.Loc_In_Codigo;
                     end if;
                  end if;
                  if vTAB_APT.Fil_In_Codigo = 312 then
                     if cLPROD.loc_st_id is not null then
                        vTAB_PRL.alm_in_codigo := substr(cLPROD.loc_st_id,1,6);
                        vTAB_PRL.loc_in_codigo := substr(cLPROD.loc_st_id,7,6);
                     end if;
                  end if;                   
                  if cLPROD.Orl_St_Tipolote = 'P' then
                     -- Carrega tipo de Movto da Ordem
                     for cTMO in(
                        select tmo.* 
                          from pro_tipomovto tmo
                         where tmo.tmo_in_codigo = vAPTO.tmo_in_codigoprod)
                     loop
                        vTAB_TMO := cTMO;
                     end loop;
                  else
                     for cTMO in(
                        select tmo.* 
                          from pro_tipomovto tmo
                         where tmO.Pai_Tmo_In_Codigo = vAPTO.tmo_in_codigoprod)
                     loop
                        vTAB_TMO := cTMO;
                     end loop;                     
                  end if;
                  -- Gera movimento de estoque
                  vTAB_MVT(vM).org_tab_in_codigo    := vTAB_APO.Org_Tab_In_Codigo;
                  vTAB_MVT(vM).org_pad_in_codigo    := vTAB_APO.Org_Pad_In_Codigo;
                  vTAB_MVT(vM).org_in_codigo        := vTAB_APO.Org_In_Codigo;
                  vTAB_MVT(vM).org_tau_st_codigo    := vTAB_APO.Org_Tau_St_Codigo;
                  vTAB_MVT(vM).ser_tab_in_codigo    := vAPTO.ser_tab_in_codigo;
                  vTAB_MVT(vM).ser_in_sequencia     := vAPTO.ser_in_sequencia;
                  vTAB_MVT(vM).fil_in_codigo        := vTAB_APO.Fil_In_Codigo;
                  vTAB_MVT(vM).acao_tab_in_codigo   := vTAB_TMO.acao_tab_in_codigo;
                  vTAB_MVT(vM).acao_pad_in_codigo   := vTAB_TMO.acao_pad_in_codigo;
                  vTAB_MVT(vM).acao_in_codigo       := vTAB_TMO.acao_in_codigo;
                  vTAB_MVT(vM).mvt_ch_origem        := 'P';
                  vTAB_MVT(vM).mvt_st_entrsaida     := 'ED';
                  vTAB_MVT(vM).tpm_tab_in_codigo    := vTAB_TMO.tpm_tab_in_codigo;
                  vTAB_MVT(vM).tpm_pad_in_codigo    := vTAB_TMO.tpm_pad_in_codigo;
                  vTAB_MVT(vM).tpm_in_codigo        := vTAB_TMO.tpm_in_codigo;
                  vTAB_MVT(vM).mvt_st_numdoc        := vTAB_APO.ord_in_codigo;
                  vTAB_MVT(vM).mvt_dt_documento     := vTAB_APO.apo_dt_apontamento;
                  vTAB_MVT(vM).mvt_dt_movimento     := vTAB_APO.apo_dt_apontamento;
                  vTAB_MVT(vM).usu_in_inclusao      := 1;
                  vTAB_MVT(vM).mvt_dt_inclusao      := SysDate;
                  vTAB_MVT(vM).usu_in_altera        := 1;
                  vTAB_MVT(vM).mvt_dt_altera        := SysDate;
                  vTAB_MVT(vM).mvt_in_vinculo       := 0;
                  vTAB_MVT(vM).pro_tab_in_codigo    := vTAB_PRO.Pro_Tab_In_Codigo;
                  vTAB_MVT(vM).pro_pad_in_codigo    := vTAB_PRO.Pro_Pad_In_Codigo;
                  vTAB_MVT(vM).pro_in_codigo        := vTAB_PRO.Pro_In_Codigo;
                  vTAB_MVT(vM).apl_tab_in_codigo    := vTAB_TMO.apl_tab_in_codigo;
                  vTAB_MVT(vM).apl_pad_in_codigo    := vTAB_TMO.apl_pad_in_codigo;
                  vTAB_MVT(vM).apl_in_codigo        := vTAB_TMO.apl_in_codigo;
                  vTAB_MVT(vM).alm_tab_in_codigo    := vTAB_PRL.Alm_Tab_In_Codigo;
                  vTAB_MVT(vM).alm_pad_in_codigo    := vTAB_PRL.Alm_Pad_In_Codigo;
                  vTAB_MVT(vM).alm_in_codigo        := vTAB_PRL.Alm_In_Codigo;
                  vTAB_MVT(vM).loc_in_codigo        := vTAB_PRL.Loc_In_Codigo;
                  vTAB_MVT(vM).mvt_re_quantidade    := cLPROD.Apt_Re_Quantidade;
                  vTAB_MVT(vM).mvt_re_aquisicao     := 0;
                  vTAB_MVT(vM).mvt_re_vlunitario    := 0;            
                  if cLPROD.Orl_St_Tipolote = 'P' then
                        Select S_MovtoManuf.Nextval
                          Into vAPTO.int_in_sequencia
                          From DUAL;
                        Begin
                           Man_Pck_Ordem.P_MovimentaOrdem(vTAB_APO.Org_Pad_In_Codigo,
                                                          vTAB_APO.Org_In_Codigo,
                                                          vTAB_APO.Fil_In_Codigo,
                                                          vTAB_APO.Ord_Seq_In_Codigo,
                                                          vTAB_APO.Ord_In_Codigo,
                                                          cLPROD.Pro_Pad_In_Codigo,
                                                          cLPROD.Apt_Re_Quantidade,
                                                          Null,
                                                          Null,
                                                          Null,
                                                          Null,
                                                          1,
                                                          vTAB_MVT(vM).mvt_in_lancam,
                                                          vTAB_APO.tmo_in_codigo,
                                                          vTAB_APO.Apo_Dt_Apontamento,
                                                          vTAB_APO.Apo_Dt_Apontamento,
                                                          0,
                                                          Null,
                                                          Null,
                                                          vTAB_APO.apo_in_sequencia,
                                                          vAPTO.int_in_sequencia,
                                                          vAPTO.int_in_sequencia);
                        End;                     
                     end if;
                  -- Busca os lotes
                  for cLOT in(
                     select lot.*
                       from idp.apt_apontaordem_lote lot
                      where lot.apt_in_sequencia = vTAB_APT.Apt_In_Sequencia
                        and lot.apt_ch_status    = 'A'
                        and lot.pro_tab_in_codigo = cLPROD.Pro_Tab_In_Codigo
                        and lot.pro_pad_in_codigo = cLPROD.Pro_Pad_In_Codigo
                        and lot.pro_in_codigo     = cLPROD.Pro_In_Codigo)
                  loop 
                     Addlotesmov(vTAB_MVL);
                     vL := vTAB_MVL.Last;
                     --vL := vL+1;                                      
                     if vTAB_PRO.Pro_Bo_Controladtentrada = 'S' then
                        vTAB_MVL(vL).mvl_dt_entrada := trunc(sysdate);
                     else
                        vTAB_MVL(vL).mvl_dt_entrada := To_Date('01/01/2000','dd/mm/yyyy');
                     end if;

                     if vTAB_PRO.Pro_Bo_Controlavalidade = 'S' then
                        select case vTAB_PRO.Pro_St_Calcvaltpper
                               when 'D' then Trunc(sysdate + vTAB_PRO.Pro_Re_Calcvalqtdref)
                               when 'M' then Trunc(Add_Months(sysdate,vTAB_PRO.Pro_Re_Calcvalqtdref))
                               when 'A' then Trunc(Add_Months(sysdate,12 * vTAB_PRO.Pro_Re_Calcvalqtdref))
                               else To_Date('01/01/2000','dd/mm/yyyy') end                        
                           into vTAB_MVL(vL).mvt_dt_validade
                           From DUAL;
                     else
                       vTAB_MVL(vL).mvt_dt_validade := To_Date('01/01/2000','dd/mm/yyyy');
                     end if;              
                     
                     vTAB_MVL(vL).org_tab_in_codigo  := cLOT.ORG_TAB_IN_CODIGO;
                     vTAB_MVL(vL).org_pad_in_codigo  := cLOT.ORG_PAD_IN_CODIGO;
                     vTAB_MVL(vL).org_in_codigo      := cLOT.ORG_IN_CODIGO;
                     vTAB_MVL(vL).org_tau_st_codigo  := cLOT.ORG_TAU_ST_CODIGO;
                     vTAB_MVL(vL).ser_tab_in_codigo  := vAPTO.SER_TAB_IN_CODIGO;
                     vTAB_MVL(vL).ser_in_sequencia   := vAPTO.SER_IN_SEQUENCIA;
                     vTAB_MVL(vL).fil_in_codigo      := cLOT.FIL_IN_CODIGO;
                     vTAB_MVL(vL).mvt_in_lancam      := vTAB_MVT(vM).mvt_in_lancam;
                     vTAB_MVL(vL).mvt_dt_movimento   := vTAB_APO.apo_dt_apontamento;
                     vTAB_MVL(vL).pro_tab_in_codigo  := cLOT.PRO_TAB_IN_CODIGO;
                     vTAB_MVL(vL).pro_pad_in_codigo  := cLOT.PRO_PAD_IN_CODIGO;
                     vTAB_MVL(vL).pro_in_codigo      := cLOT.PRO_IN_CODIGO;
                     vTAB_MVL(vL).alm_tab_in_codigo  := vTAB_PRL.ALM_TAB_IN_CODIGO;
                     vTAB_MVL(vL).alm_pad_in_codigo  := vTAB_PRL.ALM_PAD_IN_CODIGO;
                     vTAB_MVL(vL).alm_in_codigo      := vTAB_PRL.ALM_IN_CODIGO;
                     vTAB_MVL(vL).loc_in_codigo      := vTAB_PRL.LOC_IN_CODIGO;
                     vTAB_MVL(vL).mvl_re_quantidade  := cLOT.Orl_Re_Qtdlote;
                     vTAB_MVL(vL).nat_tab_in_codigo  := 143;
                     vTAB_MVL(vL).nat_pad_in_codigo  := 1;
                     vTAB_MVL(vL).nat_st_codigo      := 'DP';
                     vTAB_MVL(vL).mvl_in_reserva     := 0;
                     If vTAB_PRO.pro_bo_controlalotes = 'S' Then
                        vTAB_MVL(vL).mvl_st_loteforne   := cLOT.ORL_ST_LOTEFABRICACAO;
                        vTAB_MVL(vL).mvl_st_referencia  := cLOT.Orl_St_Referencia;
                     ElsIf vTAB_PRO.pro_bo_controlalotes = 'N' Then
                        vTAB_MVL(vL).mvl_st_loteforne   := '*';
                        vTAB_MVL(vL).mvl_st_referencia := '*';
                     End If;                                          
                     if cLPROD.Orl_St_Tipolote <> 'P' then
                        SELECT Nvl(MAX(OSP_IN_SEQUENCIA),0)+1
                          Into vTAB_SUP.osp_in_sequencia
                        FROM PRO_ORDEMSUBPROD;
                        -- Busca a composição do subproduto
                        begin
                           Select Max(CPS_IN_CODIGO) 
                             Into vTAB_SUP.cps_in_codigo
                             From EST_LISTAMATERIAIS
                            Where PRO_TAB_IN_CODIGO = cLOT.PRO_TAB_IN_CODIGO
                              And PRO_PAD_IN_CODIGO = cLOT.PRO_PAD_IN_CODIGO
                              And PRO_IN_CODIGO     = cLOT.PRO_IN_CODIGO;
                        exception when others then
                           null;
                        end;                                                                              
                        vTAB_SUP.apo_in_sequencia   := vTAB_APO.apo_in_sequencia; 
                        vTAB_SUP.org_tab_in_codigo  := vTAB_APO.org_tab_in_codigo; 
                        vTAB_SUP.org_pad_in_codigo  := vTAB_APO.org_pad_in_codigo;  
                        vTAB_SUP.org_in_codigo      := vTAB_APO.org_in_codigo; 
                        vTAB_SUP.org_tau_st_codigo  := vTAB_APO.org_tau_st_codigo; 
                        vTAB_SUP.ord_tab_in_codigo  := vTAB_APO.ord_tab_in_codigo; 
                        vTAB_SUP.ord_seq_in_codigo  := vTAB_APO.ord_seq_in_codigo; 
                        vTAB_SUP.ord_in_codigo      := vTAB_APO.ord_in_codigo;  
                        vTAB_SUP.pro_tab_in_codigo  := vTAB_MVL(vL).pro_tab_in_codigo; 
                        vTAB_SUP.pro_pad_in_codigo  := vTAB_MVL(vL).pro_pad_in_codigo; 
                        vTAB_SUP.pro_in_codigo      := vTAB_MVL(vL).pro_in_codigo;  
                        vTAB_SUP.tpm_tab_in_codigo  := vTAB_TMO.tpm_tab_in_codigo; 
                        vTAB_SUP.tpm_pad_in_codigo  := vTAB_TMO.tpm_pad_in_codigo; 
                        vTAB_SUP.tpm_in_codigo      := vTAB_TMO.tpm_in_codigo; 
                        vTAB_SUP.alm_tab_in_codigo  := vTAB_MVL(vL).alm_tab_in_codigo; 
                        vTAB_SUP.alm_pad_in_codigo  := vTAB_MVL(vL).alm_pad_in_codigo; 
                        vTAB_SUP.alm_in_codigo      := vTAB_MVL(vL).alm_in_codigo; 
                        vTAB_SUP.loc_in_codigo      := vTAB_MVL(vL).loc_in_codigo; 
                        vTAB_SUP.mvl_st_loteforne   := vTAB_MVL(vL).mvl_st_loteforne; 
                        vTAB_SUP.mvt_dt_movimento   := vTAB_MVL(vL).mvt_dt_movimento; 
                        vTAB_SUP.mvt_dt_validade    := vTAB_MVL(vL).mvt_dt_validade; 
                        vTAB_SUP.mvl_st_referencia  := vTAB_MVL(vL).mvl_st_referencia; 
                        vTAB_SUP.osp_re_qtde        := vTAB_MVL(vL).mvl_re_quantidade; 
                        vTAB_SUP.osp_ch_partcalcdde := 'S';  
                        vTAB_SUP.ser_tab_in_codigo  := vTAB_MVL(vL).ser_tab_in_codigo; 
                        vTAB_SUP.ser_in_sequencia   := vTAB_MVL(vL).ser_in_sequencia; 
                        vTAB_SUP.mvt_in_lancam      := vTAB_MVL(vL).mvt_in_lancam; 
                        vTAB_SUP.nat_tab_in_codigo  := vTAB_MVL(vL).nat_tab_in_codigo;  
                        vTAB_SUP.nat_pad_in_codigo  := vTAB_MVL(vL).nat_pad_in_codigo; 
                        vTAB_SUP.nat_st_codigo      := vTAB_MVL(vL).nat_st_codigo; 
                        vTAB_SUP.osp_re_qtdesec     := 0;
                        vTAB_SUP.Osp_St_Tipo        :='SUB';
                        -- Grava na tabela de Subproduto;                
                        INSERT INTO PRO_ORDEMSUBPROD values vTAB_SUP;                 
                     end if;                                                         
                     -- p_GeraMovimentoEstoque;                                          
                     
                     vAPT_SUB.org_tab_in_codigo      := vTAB_APO.Org_Tab_In_Codigo;
                     vAPT_SUB.org_pad_in_codigo      := vTAB_APO.Org_Pad_In_Codigo;
                     vAPT_SUB.org_in_codigo          := vTAB_APO.org_in_codigo;
                     vAPT_SUB.org_tau_st_codigo      := vTAB_APO.Org_Tau_St_Codigo;
                     vAPT_SUB.ord_tab_in_codigo      := vTAB_APO.Ord_Tab_In_Codigo;
                     vAPT_SUB.ord_seq_in_codigo      := vTAB_APO.ord_seq_in_codigo;
                     vAPT_SUB.ord_in_codigo          := vTAB_APO.ord_in_codigo;
                     vAPT_SUB.orl_st_lotefabricacao  := cLOT.Orl_St_Lotefabricacao;
                     vAPT_SUB.orl_st_slotefabricacao := cLOT.Orl_St_Slotefabricacao;
                     vAPT_SUB.orl_st_referencia      := cLOT.Orl_St_Referencia;
                     vAPT_SUB.orl_re_qtdlote         := cLOT.Orl_Re_Qtdlote;
                     vAPT_SUB.orl_re_qtdrecebida     := cLOT.Orl_Re_Qtdlote;
                     vAPT_SUB.orl_re_qtdrefugada     := CLOT.ORL_RE_QTDREF;
                     vAPT_SUB.orl_re_qtdinterditada  := 0;
                     vAPT_SUB.orl_ch_origem          := 'O';
                     begin
                        update pro_ordemlotesub s
                           set s.orl_re_qtdrecebida = vAPT_SUB.orl_re_qtdrecebida,
                               s.orl_re_qtdrefugada = vAPT_SUB.orl_re_qtdrefugada
                         where s.org_tab_in_codigo  = vAPT_SUB.org_tab_in_codigo
                           and s.org_pad_in_codigo  = vAPT_SUB.org_pad_in_codigo
                           and s.org_in_codigo      = vAPT_SUB.org_in_codigo
                           and s.org_tau_st_codigo  = vAPT_SUB.org_tau_st_codigo
                           and s.ord_tab_in_codigo  = vAPT_SUB.ord_tab_in_codigo                      
                           and s.ord_seq_in_codigo  = vAPT_SUB.ord_seq_in_codigo                       
                           and s.ord_in_codigo      = vAPT_SUB.ord_in_codigo                      
                           and s.orl_st_lotefabricacao  = vAPT_SUB.orl_st_lotefabricacao
                           and s.orl_st_slotefabricacao = vAPT_SUB.orl_st_slotefabricacao;
                        If Sql%Notfound Then
                           insert into pro_ordemlotesub values vAPT_SUB;
                        End if;                   
                     end;                                                                                                                    

                     UPDATE IDP.APT_APONTAORDEM_LOTE L
                        SET L.APT_CH_STATUS = 'B'
                      WHERE L.ORG_TAU_ST_CODIGO      = cLOT.Org_Tau_St_Codigo
                        AND L.ORG_TAB_IN_CODIGO      = cLOT.Org_Tab_In_Codigo
                        AND L.ORD_SEQ_IN_CODIGO      = cLOT.Ord_Seq_In_Codigo
                        AND L.ORG_IN_CODIGO          = cLOT.Org_In_Codigo
                        AND L.ORD_IN_CODIGO          = cLOT.Ord_In_Codigo
                        AND L.ORD_TAB_IN_CODIGO      = cLOT.Ord_Tab_In_Codigo
                        AND L.ORG_PAD_IN_CODIGO      = cLOT.Org_Pad_In_Codigo
                        AND L.ORL_ST_LOTEFABRICACAO  = cLOT.Orl_St_Lotefabricacao
                        AND L.APT_CH_STATUS          <> 'C';               
                  end loop;
                  Begin
                     Update EST_VALORIZAPRODUTOS
                        Set vpro_dt_movto       = vTAB_APT.apt_dt_apontamento,
                            vpro_ch_estatistica = 'S',
                            vpro_in_metodocmd   = 'S',
                            vpro_in_metodocmm   = 'S',
                            vpro_in_metodopep   = 'S',
                            vpro_in_metodouep   = 'S',
                            vpro_in_metodopme   = 'N',
                            org_in_codigo       = vTAB_APT.org_in_codigo
                      Where pro_tab_in_codigo = vTAB_PRO.pro_tab_in_codigo
                        And pro_pad_in_codigo = vTAB_PRO.pro_pad_in_codigo
                        And pro_in_codigo     = vTAB_PRO.pro_in_codigo
                        And org_tab_in_codigo = vTAB_APT.org_tab_in_codigo
                        And org_pad_in_codigo = vTAB_APT.org_pad_in_codigo
                        And fil_in_codigo     = vTAB_APT.fil_in_codigo
                        And org_tau_st_codigo = vTAB_APT.org_tau_st_codigo;
                      If Sql%Notfound Then
                        Insert Into EST_VALORIZAPRODUTOS
                        ( pro_tab_in_codigo, pro_pad_in_codigo, pro_in_codigo    , org_in_codigo    ,
                          org_tab_in_codigo, org_pad_in_codigo, fil_in_codigo    , org_tau_st_codigo,
                          vpro_in_metodocmd, vpro_in_metodocmm, vpro_in_metodopep, vpro_in_metodouep,
                          vpro_in_metodopme, vpro_dt_movto    , vpro_ch_estatistica )
                        Values
                        ( vTAB_PRO.pro_tab_in_codigo, vTAB_PRO.pro_pad_in_codigo , vTAB_PRO.pro_in_codigo, vTAB_APT.org_in_codigo,
                          vTAB_APT.org_tab_in_codigo, vTAB_APT.org_pad_in_codigo , vTAB_APT.fil_in_codigo, vTAB_APT.org_tau_st_codigo,
                          'S'                    , 'S'                     , 'S'                , 'S',
                          'N'                    , vTAB_APT.apt_dt_apontamento, 'S' );
                      End If;
                  End;
                  If cLPROD.Orl_St_Tipolote = 'P' Then
                     v_QTDE_PRODUTO := v_QTDE_PRODUTO + cLPROD.APT_RE_QUANTIDADE;
                  Else
                     v_QTDE_SUBPRODUTO := v_QTDE_SUBPRODUTO + cLPROD.APT_RE_QUANTIDADE;
                  End If;  
                  -- Processo de Refugo
                  If ((Nvl(vTAB_APO.Apo_Re_Quantidaderef,0) > 0) And (cLPROD.Apt_Ref_In_Codigo Is Not Null)) Then      
                     vTAB_REF.ref_re_quantidade := vTAB_APO.apo_re_quantidaderef;
                     vTAB_REF.apo_in_sequencia  := vTAB_APO.apo_in_sequencia;
                     vTAB_REF.ref_tab_in_codigo := 137;
                     vTAB_REF.ref_pad_in_codigo := pck_mega.achapadraodatabela(vTAB_APO.fil_in_codigo, 137, sysdate);
                     vTAB_REF.ref_in_codigo     := cLPROD.apt_ref_in_codigo;               
                     -- Atualiza refugo na ordem
                     Begin
                        Update pro_apontarefugo rf
                           set rf.ref_re_quantidade = vTAB_REF.ref_re_quantidade
                         where apo_in_sequencia = vTAB_REF.apo_in_sequencia
                           and ref_tab_in_codigo = vTAB_REF.ref_tab_in_codigo
                           and ref_pad_in_codigo = vTAB_REF.ref_pad_in_codigo
                           and ref_in_codigo = vTAB_REF.ref_in_codigo;
                        If Sql%Notfound Then
                           INSERT INTO pro_apontarefugo values vTAB_REF;
                        end if;
                     End;               

                     Select s_movtomanuf.Nextval
                       Into vAPTO.int_in_sequenciaref
                       From DUAL;

                     Begin
                        Man_Pck_Ordem.P_MovimentaOrdem(vTAB_APO.Org_Pad_In_Codigo,
                                                        vTAB_APO.Org_In_Codigo,
                                                        vTAB_APO.Fil_In_Codigo,
                                                        vTAB_APO.Ord_Seq_In_Codigo,
                                                        vTAB_APO.Ord_In_Codigo,
                                                        vTAB_PRO.Pro_Pad_In_Codigo,
                                                        vTAB_REF.ref_re_quantidade, -- Verificar
                                                        vTAB_REF.Ref_In_Codigo,
                                                        vTAB_REF.Ref_Pad_In_Codigo,
                                                        Null,
                                                        Null,
                                                        1,
                                                        Null,
                                                        vAPTO.tmo_in_codigoref,
                                                        vTAB_APO.apo_dt_apontamento,
                                                        vTAB_APO.apo_dt_apontamento,
                                                        0,
                                                        Null,
                                                        Null,
                                                        vTAB_APO.Apo_In_Sequencia,
                                                        vAPTO.int_in_sequenciaref,
                                                        Nvl(vAPTO.int_in_sequencia,vAPTO.int_in_sequenciaref));
                     End;                   
                  End If;
                  p_GeraMovimentoEstoque_New;               
               end loop;                       
            End If;
         End If;
     end if;
     if (vAPTO.ord_re_demanda > 0) Then
        if vTAB_DDE.Apt_In_Sequencia is null then
           vTAB_DDE.Apt_In_Sequencia := vTAB_APT.apt_in_sequencia;
           p_cria_demanda;
        end if;
         -- Processo de Baixa da Demanda
         if v_DEMANDA = 'S' then            
            p_RecalculaDemandaEmpenho(vTAB_APT.apt_in_sequencia);
            --If ((V_Apt.apt_re_quantidade + V_Apt.Apt_Re_Quantidaderef + V_Apt.Apt_Re_Quantidadeint) > 0) Then            
               --If V_Apt.Plf_In_Sqoperacao = v_ultoperacao Then
               --Abre cursor de demandas
               Open C_OrdDem;
               Loop
                  Fetch C_OrdDem 
                  Into V_OrdDem;
                  Exit When C_OrdDem%Notfound;
                  -- Inicializa o apontamento para cada produto;
                  Inicializa;
                  -- Limpa variáveis para cada item;                  
                  AddMov(vTAB_MVT);
                  vM := vTAB_MVT.Last;                  
                  --Identificação do tipo de movimento a ser utilizado                      
                  for cTMO in(
                     select tmo.* 
                       from pro_tipomovto tmo
                      where tmo.tmo_in_codigo = vAPTO.tmo_in_codigodem)
                  loop
                     vTAB_TMO := cTMO;
                  end loop;
                  for cDEP in(
                     select dep.* 
                       from pro_demanda_dep dep
                      where dep.org_tab_in_codigo  = V_OrdDem.org_tab_in_codigo
                        and dep.org_pad_in_codigo  = V_OrdDem.org_pad_in_codigo                    
                        and dep.org_in_codigo      = V_OrdDem.org_in_codigo
                        and dep.org_tau_st_codigo  = V_OrdDem.org_tau_st_codigo
                        and dep.ord_tab_in_codigo  = V_OrdDem.ord_tab_in_codigo
                        and dep.ord_seq_in_codigo  = V_OrdDem.ord_seq_in_codigo
                        and dep.ord_in_codigo      = V_OrdDem.ord_in_codigo
                        and dep.com_tab_in_codigo  = V_OrdDem.com_tab_in_codigo                         
                        and dep.com_pad_in_codigo  = V_OrdDem.com_pad_in_codigo
                        and dep.com_in_codigo      = V_OrdDem.com_in_codigo
                        and dep.dde_in_operacao    = V_OrdDem.dde_in_operacao
                        and dep.dde_dt_necessidade = V_OrdDem.dde_dt_necessidade)
                  loop
                     vTAB_DEP := cDEP;
                  end loop;                                                                           
                  vTAB_MVT(vM).mvt_in_lancam:= Pck_Mega.ProximaSequenciaOrg(vTAB_APO.Org_In_Codigo, vAPTO.ser_tab_in_codigo, vAPTO.ser_in_sequencia);                            
                  -- CAPA DO MOVIMENTO
                  vTAB_MVT(vM).org_tab_in_codigo    := vTAB_APT.org_tab_in_codigo;
                  vTAB_MVT(vM).org_pad_in_codigo    := vTAB_APT.org_pad_in_codigo;
                  vTAB_MVT(vM).org_in_codigo        := vTAB_APT.org_in_codigo;
                  vTAB_MVT(vM).org_tau_st_codigo    := vTAB_APT.org_tau_st_codigo;
                  vTAB_MVT(vM).ser_tab_in_codigo    := vAPTO.ser_tab_in_codigo;
                  vTAB_MVT(vM).ser_in_sequencia     := vAPTO.ser_in_sequencia;
                  vTAB_MVT(vM).fil_in_codigo        := vTAB_APT.fil_in_codigo;
                  vTAB_MVT(vM).acao_tab_in_codigo   := vTAB_TMO.acao_tab_in_codigo;
                  vTAB_MVT(vM).acao_pad_in_codigo   := vTAB_TMO.acao_pad_in_codigo;
                  vTAB_MVT(vM).acao_in_codigo       := vTAB_TMO.acao_in_codigo;
                  vTAB_MVT(vM).acaom_in_sequencia   := Null;
                  vTAB_MVT(vM).mvt_ch_origem        := 'P';
                  vTAB_MVT(vM).mvt_st_entrsaida     := 'SD';
                  vTAB_MVT(vM).tpm_tab_in_codigo    := vTAB_TMO.tpm_tab_in_codigo;
                  vTAB_MVT(vM).tpm_pad_in_codigo    := vTAB_TMO.tpm_pad_in_codigo;
                  vTAB_MVT(vM).tpm_in_codigo        := vTAB_TMO.tpm_in_codigo;
                  vTAB_MVT(vM).mvt_st_numdoc        := vTAB_APT.ord_in_codigo;
                  vTAB_MVT(vM).mvt_dt_documento     := vTAB_APO.apo_dt_apontamento;
                  vTAB_MVT(vM).mvt_dt_movimento     := vTAB_APO.apo_dt_apontamento;
                  vTAB_MVT(vM).usu_in_inclusao      := 1;
                  vTAB_MVT(vM).mvt_dt_inclusao      := vTAB_APO.apo_dt_apontamento;
                  vTAB_MVT(vM).usu_in_altera        := 1;
                  vTAB_MVT(vM).mvt_dt_altera        := vTAB_APO.apo_dt_apontamento;
                  vTAB_MVT(vM).mvt_in_vinculo       := 0;
                  vTAB_MVT(vM).pro_tab_in_codigo    := V_OrdDem.com_tab_in_codigo;
                  vTAB_MVT(vM).pro_pad_in_codigo    := V_OrdDem.com_pad_in_codigo;
                  vTAB_MVT(vM).pro_in_codigo        := V_OrdDem.com_in_codigo;
                  vTAB_MVT(vM).apl_tab_in_codigo    := vTAB_TMO.apl_tab_in_codigo;
                  vTAB_MVT(vM).apl_pad_in_codigo    := vTAB_TMO.apl_pad_in_codigo;
                  vTAB_MVT(vM).apl_in_codigo        := vTAB_TMO.apl_in_codigo;
                  if vTAB_APT.fil_in_codigo IN(312,302) then 
                     p_SumarizaDemanda;
                  end if;
                  if vTAB_APT.fil_in_codigo <> 31 then
                     vTAB_MVT(vM).mvt_re_quantidade    := vAPTO.ord_re_demanda;                  
                  Else
                    p_SumarizaDemanda;
                    vTAB_MVT(vM).mvt_re_quantidade    := vAPTO.ord_re_demanda;                  
                    --vTAB_MVT(vM).mvt_re_quantidade    := V_OrdDem.dde_re_qtde_disponivel;
                  end if;
                  vTAB_MVT(vM).mvt_re_aquisicao     := 0;
                  vTAB_MVT(vM).mvt_re_vlunitario    := 0;
                  vTAB_MVT(vM).cus_tab_in_codigo    := Null;
                  vTAB_MVT(vM).cus_pad_in_codigo    := Null;
                  vTAB_MVT(vM).cus_ide_st_codigo    := Null;
                  vTAB_MVT(vM).cus_in_reduzido      := Null;
                  vTAB_MVT(vM).proj_tab_in_codigo   := Null;
                  vTAB_MVT(vM).proj_pad_in_codigo   := Null;
                  vTAB_MVT(vM).proj_ide_st_codigo   := Null;
                  vTAB_MVT(vM).proj_in_reduzido     := Null;
                  vTAB_MVT(vM).mvs_in_reserva       := 0;                                    
                  vAPTO.dde_st_atende := 'S';
                  --Se saldo atende total ou parcial demanda, baixa estoque automaticamente
                  If vAPTO.dde_st_atende in ('S','P') then
                     --Cursor utilizado para identificar estoque reservado para a ordem
                     For C_DemMvs in (
                        SELECT LOT.*                                            
                          FROM IDP.APT_APONTADEMANDA_ESTOQUE LOT,
                               IDP.APT_APONTADEMANDA         DEM,
                               EST_PRODUTOS                 PRO
                         WHERE LOT.APT_IN_SEQUENCIA   = DEM.APT_IN_SEQUENCIA
                           AND LOT.ORG_IN_CODIGO      = DEM.ORG_IN_CODIGO
                           AND LOT.ORD_SEQ_IN_CODIGO  = DEM.ORD_SEQ_IN_CODIGO
                           AND LOT.ORD_IN_CODIGO      = DEM.ORD_IN_CODIGO
                           AND LOT.COM_PAD_IN_CODIGO  = DEM.COM_PAD_IN_CODIGO
                           AND LOT.COM_IN_CODIGO      = DEM.COM_IN_CODIGO
                           AND LOT.DDE_IN_OPERACAO    = DEM.DDE_IN_OPERACAO
                           AND LOT.DDE_DT_NECESSIDADE = DEM.DDE_DT_NECESSIDADE
                           AND LOT.PLF_IN_SQOPERACAO  = DEM.PLF_IN_SQOPERACAO

                           AND DEM.COM_TAB_IN_CODIGO  = PRO.PRO_TAB_IN_CODIGO
                           AND DEM.COM_PAD_IN_CODIGO  = PRO.PRO_PAD_IN_CODIGO
                           AND DEM.COM_IN_CODIGO      = PRO.PRO_IN_CODIGO
                           
                           AND LOT.DDE_ST_SITUACAO    = 'A'

                           AND LOT.APT_IN_SEQUENCIA   = V_OrdDem.APT_IN_SEQUENCIA
                           AND LOT.ORG_IN_CODIGO      = V_OrdDem.ORG_IN_CODIGO
                           AND LOT.ORD_SEQ_IN_CODIGO  = V_OrdDem.ORD_SEQ_IN_CODIGO
                           AND LOT.ORD_IN_CODIGO      = V_OrdDem.ORD_IN_CODIGO
                           AND LOT.COM_PAD_IN_CODIGO  = V_OrdDem.COM_PAD_IN_CODIGO
                           AND LOT.COM_IN_CODIGO      = V_OrdDem.COM_IN_CODIGO
                           AND LOT.DDE_IN_OPERACAO    = V_OrdDem.DDE_IN_OPERACAO
                           AND LOT.DDE_DT_NECESSIDADE = V_OrdDem.DDE_DT_NECESSIDADE
                           AND LOT.PLF_IN_SQOPERACAO  = V_OrdDem.PLF_IN_SQOPERACAO)
                                           
                     Loop                     
                        Addlotesmov(vTAB_MVL);
                        vL := vTAB_MVL.Last;
                        -- LOTE DO MOVIMENTO
                        vTAB_MVL(vL).org_tab_in_codigo        := C_DemMvs.Org_Tab_In_Codigo;
                        vTAB_MVL(vL).org_pad_in_codigo        := C_DemMvs.Org_Pad_In_Codigo;
                        vTAB_MVL(vL).org_in_codigo            := C_DemMvs.Org_In_Codigo;
                        vTAB_MVL(vL).org_tau_st_codigo        := C_DemMvs.Org_Tau_St_Codigo;
                        vTAB_MVL(vL).ser_tab_in_codigo        := 102;
                        vTAB_MVL(vL).ser_in_sequencia         := 1;
                        vTAB_MVL(vL).mvt_in_lancam            := vTAB_MVT(vM).mvt_in_lancam;
                        vTAB_MVL(vL).fil_in_codigo            := C_DemMvs.Fil_In_Codigo;
                        vTAB_MVL(vL).mvl_st_loteforne         := C_DemMvs.Mvs_St_Loteforne;
                        vTAB_MVL(vL).mvt_dt_movimento         := vTAB_MVT(vM).mvt_dt_movimento;
                        vTAB_MVL(vL).mvt_dt_validade          := to_date(to_char(C_DemMvs.Mvs_Dt_Validade),'dd/mm/yy');
                        vTAB_MVL(vL).pro_tab_in_codigo        := C_DemMvs.COM_Tab_In_Codigo;
                        vTAB_MVL(vL).pro_pad_in_codigo        := C_DemMvs.COM_Pad_In_Codigo;
                        vTAB_MVL(vL).pro_in_codigo            := C_DemMvs.COM_In_Codigo;
                        vTAB_MVL(vL).alm_tab_in_codigo        := C_DemMvs.Alm_Tab_In_Codigo;
                        vTAB_MVL(vL).alm_pad_in_codigo        := C_DemMvs.Alm_Pad_In_Codigo;
                        vTAB_MVL(vL).alm_in_codigo            := C_DemMvs.Alm_In_Codigo;
                        vTAB_MVL(vL).loc_in_codigo            := C_DemMvs.Loc_In_Codigo;
                        vTAB_MVL(vL).mvl_re_quantidade        := C_DemMvs.Apt_Re_Qtdeselecionada;
                        vTAB_MVL(vL).nat_tab_in_codigo        := C_DemMvs.Nat_Tab_In_Codigo;
                        vTAB_MVL(vL).nat_pad_in_codigo        := C_DemMvs.Nat_Pad_In_Codigo;
                        vTAB_MVL(vL).nat_st_codigo            := C_DemMvs.Nat_St_Codigo;
                        vTAB_MVL(vL).mvl_dt_entrada           := to_date(to_char(C_DemMvs.Mvs_Dt_Entrada),'dd/mm/yy');
                        vTAB_MVL(vL).mvl_st_referencia        := C_DemMvs.Mvs_St_Referencia;
                        vTAB_MVL(vL).mvl_in_reserva           := C_DemMvs.Mvs_In_Reserva;
                        --vTAB_MVL(vL).mie_in_seqmattitdoc      := C_DemMvs.mie_in_seqmattitdoco;
                        vTAB_MVL(vL).mie_in_seqmattitdocdest  := Null;                     

                        Select man_seq_proestmovtomanuf.Nextval
                          Into vTAB_EMM.emm_in_sequencia
                          From dual;                                                
                        vTAB_EMM.org_tab_in_codigo  := V_OrdDem.org_tab_in_codigo ;           
                        vTAB_EMM.org_pad_in_codigo  := V_OrdDem.org_pad_in_codigo ;       
                        vTAB_EMM.org_in_codigo      := V_OrdDem.org_in_codigo     ;        
                        vTAB_EMM.org_tau_st_codigo  := V_OrdDem.org_tau_st_codigo ; 
                        vTAB_EMM.ord_tab_in_codigo  := V_OrdDem.ord_tab_in_codigo ;            
                        vTAB_EMM.ord_seq_in_codigo  := V_OrdDem.ord_seq_in_codigo ;        
                        vTAB_EMM.ord_in_codigo      := V_OrdDem.ord_in_codigo     ;        
                        vTAB_EMM.com_tab_in_codigo  := V_OrdDem.com_tab_in_codigo ; 
                        vTAB_EMM.com_pad_in_codigo  := V_OrdDem.com_pad_in_codigo ;           
                        vTAB_EMM.com_in_codigo      := V_OrdDem.com_in_codigo     ;       
                        vTAB_EMM.dde_in_operacao    := V_OrdDem.dde_in_operacao   ;        
                        vTAB_EMM.dde_dt_necessidade := V_OrdDem.dde_dt_necessidade;
                        vTAB_EMM.alm_tab_in_codigo  := C_DemMvs.alm_tab_in_codigo ;       
                        vTAB_EMM.alm_pad_in_codigo  := C_DemMvs.alm_pad_in_codigo ;        
                        vTAB_EMM.alm_in_codigoo     := C_DemMvs.alm_in_codigo     ;    
                        vTAB_EMM.loc_in_codigoo     := C_DemMvs.loc_in_codigo     ;              
                        vTAB_EMM.mvl_st_loteforneo  := C_DemMvs.mvs_st_loteforne  ;         
                        vTAB_EMM.mvt_dt_movimentoo  := C_DemMvs.Mvs_Dt_Entrada    ;          
                        vTAB_EMM.mvt_dt_validadeo   := C_DemMvs.mvs_dt_validade   ;
                        vTAB_EMM.mvl_st_referenciao := C_DemMvs.mvs_st_referencia ;          
                        vTAB_EMM.alm_in_codigod     := C_DemMvs.alm_in_codigo     ;            
                        vTAB_EMM.loc_in_codigod     := C_DemMvs.loc_in_codigo     ;             
                        vTAB_EMM.mvl_st_loteforned  := C_DemMvs.mvs_st_loteforne  ;
                        vTAB_EMM.mvt_dt_movimentod  := C_DemMvs.Mvs_Dt_Entrada    ;           
                        vTAB_EMM.mvt_dt_validaded   := C_DemMvs.mvs_dt_validade   ;         
                        vTAB_EMM.mvl_st_referenciad := C_DemMvs.mvs_st_referencia ;         
                        vTAB_EMM.emm_re_qtd         := C_DemMvs.Apt_Re_Qtdeselecionada;        
                        vTAB_EMM.emm_re_saldo       := C_DemMvs.Apt_Re_Qtdeselecionada;                
                        vTAB_EMM.emm_ch_tipomov     := 'M'                        ;            
                        vTAB_EMM.nat_tab_in_codigo  := C_DemMvs.nat_tab_in_codigo ;          
                        vTAB_EMM.nat_st_codigo      := C_DemMvs.nat_st_codigo     ;     
                        vTAB_EMM.nat_pad_in_codigo  := C_DemMvs.nat_pad_in_codigo ;           
                        vTAB_EMM.nat_st_codigod     := C_DemMvs.nat_st_codigo     ;
                        vTAB_EMM.Apo_In_Sequencia   := vTAB_APO.apo_in_sequencia  ;                                                                                                                                                                  

                       Begin
                          Insert Into pro_estmovtomanuf values vTAB_EMM;     
                       End;                     
      
                       -- ATUALIZA DEMANDA/LOTE COM SEQUENCIA DA ESTMOVTOMANUF
                       UPDATE IDP.APT_APONTADEMANDA_ESTOQUE A
                          SET A.EMM_IN_SEQUENCIA = vTAB_EMM.emm_in_sequencia,
                              --Adicionado por João Paulo em 02/09/2016 para atualizar vinculo com movimento de estoque;
                              A.MVT_IN_LANCAM    = vTAB_MVT(vM).mvt_in_lancam,
                              A.DDE_ST_SITUACAO  = 'B'
                        WHERE A.APT_IN_SEQUENCIA = C_DemMvs.Apt_In_Sequencia
                          AND A.MVS_IN_SEQUENCIA = C_DemMvs.Mvs_In_Sequencia;
                     End Loop;
                     Select s_movtomanuf.Nextval
                          Into vAPTO.int_in_sequenciadem
                          From dual;
                          man_pck_ordem.P_MOVIMENTADEMANDA(vTAB_DEP.Org_Pad_In_Codigo,
                                                         vTAB_DEP.Org_In_Codigo,
                                                         vTAB_MVT(vM).fil_in_codigo,
                                                         vTAB_DEP.Ord_Seq_In_Codigo,
                                                         vTAB_DEP.Ord_In_Codigo,
                                                         vTAB_DEP.Com_Pad_In_Codigo,
                                                         vTAB_DEP.Com_In_Codigo,
                                                         vTAB_DEP.Dde_In_Operacao,
                                                         vTAB_DEP.Dde_Dt_Necessidade,
                                                         0,
                                                         vTAB_MVT(vM).mvt_re_quantidade,
                                                         'MAN',
                                                         Null,
                                                         Null,
                                                         vTAB_APO.MAQ_PAD_IN_CODIGO,
                                                         vTAB_APO.MAQ_IN_CODIGO,
                                                         1,
                                                         vTAB_MVT(vM).mvt_in_lancam,
                                                         vTAB_TMO.tmo_in_codigo,
                                                         vTAB_APO.Apo_Dt_Apontamento,
                                                         vTAB_APO.Apo_Dt_Apontamento,
                                                         Null,
                                                         Null,
                                                         Null,
                                                         vTAB_APO.apo_in_sequencia,
                                                         vAPTO.int_in_sequenciadem,
                                                         Nvl(vAPTO.int_in_sequencia,vAPTO.int_in_sequenciadem),
                                                         'N');

                     vTAB_DEP.Dde_Re_Qtde_Requisitada := NVL(vTAB_DEP.Dde_Re_Qtde_Requisitada,0)+NVL(vTAB_MVT(vM).mvt_re_quantidade,0);
                     Update pro_demanda_dep
                        Set dde_st_situacao      = man_pck_ordem.f_situacaodemanda(vTAB_ORD.Ord_St_Situacao,
                                                                                   vTAB_DEP.dde_re_qtde_necessaria,
                                                                                   vTAB_DEP.dde_re_qtde_requisitada)
                      Where org_tab_in_codigo  = V_OrdDem.org_tab_in_codigo
                        and org_pad_in_codigo  = V_OrdDem.org_pad_in_codigo
                        and org_in_codigo      = V_OrdDem.org_in_codigo
                        and org_tau_st_codigo  = V_OrdDem.org_tau_st_codigo
                        and ord_tab_in_codigo  = V_OrdDem.ord_tab_in_codigo
                        and ord_seq_in_codigo  = V_OrdDem.ord_seq_in_codigo
                        and ord_in_codigo      = V_OrdDem.ord_in_codigo
                        and com_tab_in_codigo  = V_OrdDem.com_tab_in_codigo
                        and com_pad_in_codigo  = V_OrdDem.com_pad_in_codigo
                        and com_in_codigo      = V_OrdDem.com_in_codigo
                        and dde_in_operacao    = V_OrdDem.dde_in_operacao
                        and dde_dt_necessidade = V_OrdDem.dde_dt_necessidade;

                  End if;
                  if vTAB_TPO.Tpo_Pad_In_Codigo = 31 and vTAB_TPO.Tpo_St_Codigo_Tipo = 'OT001' then
                     for cPAR in(
                        select * from est_parametros par
                         where par.org_in_codigo = vTAB_EMM.Org_In_Codigo 
                     )
                     loop
                        vTAB_PAR := cPAR;  
                        vTAB_PAR.Par_Ch_Estqnegativo :='A';
                        update est_parametros p1
                           set p1.Par_Ch_Estqnegativo = vTAB_PAR.Par_Ch_Estqnegativo
                         where p1.org_in_codigo = vTAB_PAR.Org_In_Codigo;
                     end loop;
                  end if;
                  p_GeraMovimentoEstoque_New;
                  if vTAB_TPO.Tpo_Pad_In_Codigo = 31 and vTAB_TPO.Tpo_St_Codigo_Tipo = 'OT001' then
                     vTAB_PAR.Par_Ch_Estqnegativo :='N';
                     update est_parametros p1
                        set p1.Par_Ch_Estqnegativo = vTAB_PAR.Par_Ch_Estqnegativo
                      where p1.org_in_codigo = vTAB_PAR.Org_In_Codigo;
                  end if;
               End Loop;            
               Close C_OrdDem;
               --Fecha cursor de demandas
               --End if;
            --End if;
         end if;
         --Fim do processo de baixa de demandas na primeira operação
         
         Begin
            Man_Pck_Ordem.P_VerificaEncOrdem(vTAB_ORD.Org_Pad_In_Codigo,
                                             vTAB_ORD.Org_In_Codigo,
                                             vTAB_ORD.Ord_Seq_In_Codigo,
                                             vTAB_ORD.Ord_In_Codigo,
                                             vTAB_ORD.Pro_Pad_In_Codigo,
                                             vTAB_APT.Apt_Re_Quantidade);
         End;

         /*Begin
            Man_Pck_CRP.P_SincrinizaApontOrdem(vTAB_ORD.Org_Pad_In_Codigo,
                                               vTAB_ORD.Org_In_Codigo,
                                               vTAB_ORD.Ord_Seq_In_Codigo,
                                               vTAB_ORD.Ord_In_Codigo,
                                               vTAB_ORD.Ord_In_Codigo,
                                               vTAB_ORD.Fil_In_Codigo);
         End;       */ 
        

         --atualiza situação da ordem
         if vTAB_APO.Org_In_Codigo = 2 Then
            Update PRO_ORDENS a
               Set a.ord_st_situacao = 'EN'
             Where org_tab_in_codigo = vTAB_ORD.Org_Tab_In_Codigo
               And org_pad_in_codigo = vTAB_ORD.Org_Pad_In_Codigo
               And org_in_codigo     = vTAB_ORD.Org_In_Codigo
               And org_tau_st_codigo = vTAB_ORD.Org_Tau_St_Codigo
               And ord_tab_in_codigo = vTAB_ORD.Ord_Tab_In_Codigo
               And ord_seq_in_codigo = vTAB_ORD.Ord_Seq_In_Codigo
               And ord_in_codigo     = vTAB_ORD.Ord_In_Codigo
               And ( nvl(vTAB_ORD.ord_re_qtde_recebida,0) + nvl(vTAB_ORD.ord_re_qtde_refugada,0) + nvl(a.ord_re_qtde_interditada,0) ) >= vTAB_ORD.ord_re_qtde_ordem
               And IDP.apt_pck.F_CHECA_ENCERRAMENTO_ORD(vTAB_ORD.Org_In_Codigo,
                                                       vTAB_ORD.Fil_In_Codigo,
                                                       vTAB_ORD.Ord_Seq_In_Codigo,
                                                       vTAB_ORD.Ord_In_Codigo) = 'S';

         End if;
      End If;
      for cAPL in(
         select sum(apo.orl_re_qtdlote) orl_re_qtdlote
           from apt_apontaordem_lote apo
          where APO.APT_IN_SEQUENCIA = vTAB_APT.apt_in_sequencia 
         )
      loop
         Update IDP.APT_APONTAORDEM
            Set apt_apo_in_sequencia = vTAB_APO.apo_in_sequencia,
                apt_re_quantidade    = cAPL.orl_re_qtdlote,
                apt_ch_status        = 'E' -- Apontamento Encerrado
          Where apt_in_sequencia     = vTAB_APT.apt_in_sequencia;
      end loop;
      
      Begin
         Man_Pck_Ordem.P_VerificaEncOrdem(vTAB_ORD.Org_Pad_In_Codigo,
                                          vTAB_ORD.Org_In_Codigo,
                                          vTAB_ORD.Ord_Seq_In_Codigo,
                                          vTAB_ORD.Ord_In_Codigo,
                                          vTAB_ORD.Pro_Pad_In_Codigo,
                                          vTAB_APO.Apo_Re_Quantidade);
      End;

      /*Begin
         Man_Pck_CRP.P_SincrinizaApontOrdem(vTAB_APO.Org_Pad_In_Codigo,
                                            vTAB_APO.Org_In_Codigo,
                                            vTAB_APO.Ord_Seq_In_Codigo,
                                            vTAB_APO.Ord_In_Codigo,
                                            vTAB_APO.Ord_In_Codigo,
                                            vTAB_APO.Fil_In_Codigo);
      End;*/
        /*if V_Apt.Org_In_Codigo = 2 Then
        BEGIN
           MAN_PCK_ORDEM.P_CANCELAORDEM(V_Apt.Org_Pad_In_Codigo,
                                              V_Apt.Org_In_Codigo,
                                              V_Apt.Ord_Seq_In_Codigo,
                                              V_Apt.Ord_In_Codigo,
                                              V_Apt.Fil_In_Codigo,
                                              pUSU_IN_CODIGO,
                                              pCOMP_ST_NOME);
         END;*/





    If v_QTDE_PRODUTO > 0 then
       vMENSAGEM:='Ordem apontada sucesso!'|| chr(13)||
       'Qtde Produzida do Item: '||v_QTDE_PRODUTO;
       If v_QTDE_SUBPRODUTO > 0 then
          vMENSAGEM:=vMENSAGEM ||chr(13)||'Qtde Produzida de Subproduto: '||v_QTDE_SUBPRODUTO;
       end If;
    elsif vAPTO.ord_re_demanda > 0 then
       vMENSAGEM:='Qtde demandas: '||vAPTO.ord_re_demanda;
    Else
    vMENSAGEM:='Não foi encontrado lote em aberto para fazer apontamento!';
    End If;
    begin
       cus_pck_man_utilidades.p_recalculatotaordem(vCURSOR,
                                                   vTAB_APT.ORG_IN_CODIGO,
                                                   vTAB_APT.ORD_SEQ_IN_CODIGO,
                                                   vTAB_APT.ORD_IN_CODIGO);
    end;

    OPEN pRESULT FOR
        SELECT vMENSAGEM MENSAGEM
          FROM DUAL;
    Commit;

  end; -- P_ATUAPONTA_ESTOQUE_LOTE
  procedure p_carimbaimpressao(pFIL_IN_CODIGO in number,
                               pORG_IN_CODIGO in number,
                               pORD_IN_CODIGO in number,
                               pAPT_IN_SEQUENCIA in number,
                               pORL_ST_LOTEFABRICACAO in varchar2,
                               pORL_ST_SLOTEFABRICACAO in varchar2
                              ) is
  begin
     update IDP.apt_apontaordem_lote lot
        set lot.apt_re_qtdeetiqueta = nvl(lot.apt_re_qtdeetiqueta,0)+1
      where lot.apt_in_sequencia = pAPT_IN_SEQUENCIA
        and lot.org_in_codigo    = pORG_IN_CODIGO
        and lot.fil_in_codigo    = pFIL_IN_CODIGO
        and lot.ord_in_codigo    = pORD_IN_CODIGO
        and lot.orl_st_lotefabricacao = pORL_ST_LOTEFABRICACAO
        and lot.orl_st_slotefabricacao = pORL_ST_SLOTEFABRICACAO;
  end;
  procedure apt_GetDadosMaquina(pRESULT IN OUT SYS_REFCURSOR,
                                pFIL_IN_CODIGO in number) is
  begin
   --Raise_application_error(-20000, pPRO_IN_CODIGO);
   open pRESULT for
      select lpad(cfg.ctr_tab_in_codigo,3,0)||
             lpad(cfg.ctr_pad_in_codigo,3,0)||
             lpad(cfg.ctr_in_codigo,7,0) as ctr_st_id,
             lpad(cfg.cmaq_tab_in_codigo,3,0)||
             lpad(cfg.cmaq_pad_in_codigo,3,0)||
             lpad(cfg.cmaq_in_codigo,7,0) as cmaq_st_id,
             ctr.maq_st_nome,
             cmaq.cmaq_st_descricao,
             cmaq.cmaq_st_alternativo
        from IDP.apt_pro_maquina_config cfg,
             pro_maquina ctr,
             pro_cadmaquinas cmaq
       where cfg.ctr_tab_in_codigo = ctr.maq_tab_in_codigo
         and cfg.ctr_pad_in_codigo = ctr.maq_pad_in_codigo
         and cfg.ctr_in_codigo     = ctr.maq_in_codigo
         and cfg.cmaq_tab_in_codigo  = cmaq.cmaq_tab_in_codigo
         and cfg.cmaq_pad_in_codigo  = cmaq.cmaq_pad_in_codigo
         and cfg.cmaq_in_codigo      = cmaq.cmaq_in_codigo
--         and nvl(cfg.cus_bo_integraacb,'N')   = 'N'
         ;
  end apt_GetDadosMaquina;
  procedure apt_PutDadosMaquina(pRESULT in out sys_refcursor,
                                pCTR_ST_ID in varchar2,
                                pCMAQ_ST_ID in varchar2) is
  vMENSAGEM varchar2(300);
  begin
     --Raise_application_error(-20000, pCTR_ST_ID||chr(13)||pCMAQ_ST_ID);
     update IDP.apt_pro_maquina_config cfg
        set cfg.cus_bo_integraacb = 'S'
      where lpad(cfg.ctr_tab_in_codigo,3,0)||
            lpad(cfg.ctr_pad_in_codigo,3,0)||
            lpad(cfg.ctr_in_codigo,7,0) = pCTR_ST_ID
        and lpad(cfg.cmaq_tab_in_codigo,3,0)||
            lpad(cfg.cmaq_pad_in_codigo,3,0)||
            lpad(cfg.cmaq_in_codigo,7,0) = pCMAQ_ST_ID
        and cfg.cus_bo_integraacb   = 'N';
     commit;
     vMENSAGEM := 'Ok';
     open pRESULT for
        select vMENSAGEM as MSG
          from dual;
  end apt_PutDadosMaquina;
  procedure apt_PutItens(pPRO_ST_ID in varchar2,
                         pPRO_CH_ACB in varchar2,
                         PPRO_CH_ALMOXA in varchar2,
                         pPRO_CH_ACBOLD in varchar2,
                         PPRO_CH_ALMOXAOLD in varchar2,
                         pRESULT in out sys_refcursor) is
  vMENSAGEM varchar2(300);
  vTAB est_produtoscmpesp%rowtype;
  begin
     --dbms_output.put_line(substr(pPRO_ST_ID,1,3));
     --dbms_output.put_line(substr(pPRO_ST_ID,4,3));
     --dbms_output.put_line(substr(pPRO_ST_ID,7,7));
     --Raise_application_error(-20000, pPRO_ST_ID||chr(13)||PPRO_CH_ALMOXA);
     vTAB.Pro_Tab_In_Codigo := substr(pPRO_ST_ID,1,3);
     vTAB.Pro_Pad_In_Codigo := substr(pPRO_ST_ID,4,3);
     vTAB.Pro_In_Codigo := substr(pPRO_ST_ID,7,7);
     vTAB.Pro_Ch_Acb := pPRO_CH_ACB;
     vTAB.Pro_Ch_Almoxarifado := PPRO_CH_ALMOXA;
     vTAB.pro_st_orialteracao := 'A';
     begin
        insert into est_produtoscmpesp values vTAB;
     exception when others then
        update est_produtoscmpesp cpe
           set cpe.pro_ch_acb = pPRO_CH_ACB,
               cpe.pro_ch_almoxarifado = PPRO_CH_ALMOXA,
               cpe.pro_st_orialteracao = vTAB.PRO_ST_ORIALTERACAO
         where lpad(cpe.pro_tab_in_codigo,3,0)||
               lpad(cpe.pro_pad_in_codigo,3,0)||
               lpad(cpe.pro_in_codigo,7,0) = pPRO_ST_ID
           and nvl(cpe.pro_ch_acb,'N') = pPRO_CH_ACBOLD
           and nvl(cpe.pro_ch_almoxarifado,'N') = PPRO_CH_ALMOXAOLD;
     end;
     commit;
     vMENSAGEM := 'Ok';
     open pRESULT for
        select vMENSAGEM as MSG
          from dual;
  end apt_PutItens;
  procedure apt_put_itemalmoxa(pLOC_ID_PROALMFIL varchar2,
                               pSTATUS CHAR,
                               pRESULT in out sys_refcursor) is
  vMENSAGEM varchar2(300);
  begin 
     vTAB_CAL.Loc_Id_Proalmfil := pLOC_ID_PROALMFIL;
     vTAB_CAL.Pro_Ch_Almoxarifado := pSTATUS;
     begin
        insert into cus_tb_api_almoxloc values vTAB_CAL; 
     exception when DUP_VAL_ON_INDEX then
        update cus_tb_api_almoxloc loc
           set loc.pro_ch_almoxarifado = vTAB_CAL.Pro_Ch_Almoxarifado
         where loc.loc_id_proalmfil = vTAB_CAL.Loc_Id_Proalmfil;
     end;
     commit;
     vMENSAGEM := 'Ok';
     open pRESULT for
        select vMENSAGEM as MSG
          from dual;       
  end apt_put_itemalmoxa;
  procedure apt_getConfigAponta(pRESULT IN OUT SYS_REFCURSOR,
                                pFIL_IN_CODIGO in number) is
  begin
   --Raise_application_error(-20000, pPRO_IN_CODIGO);
   open pRESULT for
      select lpad(cfg.ctr_tab_in_codigo,3,0)||
             lpad(cfg.ctr_pad_in_codigo,3,0)||
             lpad(cfg.ctr_in_codigo,7,0) as ctr_st_id,
             lpad(cfg.cmaq_tab_in_codigo,3,0)||
             lpad(cfg.cmaq_pad_in_codigo,3,0)||
             lpad(cfg.cmaq_in_codigo,7,0) as cmaq_st_id,
             lpad(cfg.opr_tab_in_codigo,3,0)||
             lpad(cfg.opr_pad_in_codigo,3,0)||
             lpad(cfg.opr_in_codigo,7,0) as opr_st_id,
             cfg.cus_bo_naobaixademanda,
             cfg.cus_bo_geraseqpallet,
             cfg.cus_bo_conversor,
             cfg.cus_bo_lotes
        from IDP.apt_pro_maquina_config cfg
       where cfg.ctr_tab_in_codigo = 207
         and cfg.ctr_pad_in_codigo = pck_mega.achapadraodatabela(pFIL_IN_CODIGO, 207, sysdate)
         --and cfg.cus_bo_integraacb   = 'N'
         ;
  end apt_getConfigAponta;
  procedure p_excluirapontamento(pORG_IN_CODIGO in number,
                                 pFIL_IN_CODIGO in number,                                 
                                 pAPT_IN_SEQUENCIA in number) is 
  
  CURSOR C_APONTAMENTO IS
    SELECT * FROM TABLE(CAST(MAN_PCK_APONTAMENTO.GETTABLEAPONTA AS MAN_TYP_APONTAMENTOTAB));
  VTABAPONTA C_APONTAMENTO%ROWTYPE;  
  v_DEBUG char(1);
  my_code NUMBER;
  my_errm VARCHAR2(32000);
  begin
     v_DEBUG := 'N';     
     IF v_DEBUG = 'S' THEN
        Raise_application_error(-20000, 
            pORG_IN_CODIGO||CHR(13)||
            pFIL_IN_CODIGO||CHR(13)||
            --pOPD_IN_CODIGO||CHR(13)||
            pAPT_IN_SEQUENCIA);
     END IF;
     
     for cAPT in(
        select apt.*
          from apt_apontaordem apt
         where apt.apt_in_sequencia = pAPT_IN_SEQUENCIA
     )
     loop
        vTAB_APT := cAPT;
     end loop;
             
        for cAPO in(
           select * 
             from pro_apontaordem apo
            where apo.apo_in_sequencia = vTAB_APT.Apt_Apo_In_Sequencia
              and apo.org_in_codigo = vTAB_APT.ORG_IN_CODIGO
              and apo.fil_in_codigo = vTAB_APT.FIL_IN_CODIGO)
        loop
           begin
              man_pck_apontamento.Inicializa;          
           end;
           begin
              VTABAPONTA.APO_IN_SEQUENCIA        := cAPO.Apo_In_Sequencia;
              VTABAPONTA.ORG_TAB_IN_CODIGO       := cAPO.Org_Tab_In_Codigo;
              VTABAPONTA.ORG_PAD_IN_CODIGO       := cAPO.Org_Pad_In_Codigo;
              VTABAPONTA.ORG_IN_CODIGO           := cAPO.Org_In_Codigo;
              VTABAPONTA.ORG_TAU_ST_CODIGO       := cAPO.Org_Tau_St_Codigo;
              VTABAPONTA.FIL_IN_CODIGO           := cAPO.Fil_In_Codigo;
              VTABAPONTA.ORD_TAB_IN_CODIGO       := cAPO.Org_Tab_In_Codigo;
              VTABAPONTA.ORD_SEQ_IN_CODIGO       := cAPO.Ord_Seq_In_Codigo;
              VTABAPONTA.ORD_IN_CODIGO           := cAPO.Ord_In_Codigo;          
              VTABAPONTA.PLF_IN_SQOPERACAO       := cAPO.Plf_In_Sqoperacao;
              VTABAPONTA.COL_IN_CODIGO           := Null;
              VTABAPONTA.ATI_TAB_IN_CODIGO       := cAPO.Ati_Tab_In_Codigo;
              VTABAPONTA.ATI_PAD_IN_CODIGO       := cAPO.Ati_Pad_In_Codigo;
              VTABAPONTA.ATI_IN_CODIGO           := cAPO.Ati_In_Codigo;
              VTABAPONTA.APO_RE_QUANTIDADE       := cAPO.Apo_Re_Quantidade;
              VTABAPONTA.APO_DT_APONTAMENTO      := cAPO.Apo_Dt_Apontamento;
              VTABAPONTA.MAQ_TAB_IN_CODIGO       := cAPO.Maq_Tab_In_Codigo;
              VTABAPONTA.MAQ_PAD_IN_CODIGO       := cAPO.Maq_Pad_In_Codigo;
              VTABAPONTA.MAQ_IN_CODIGO           := cAPO.Maq_In_Codigo;
              VTABAPONTA.APO_ST_TIPOTERC         := 'ORD';
              VTABAPONTA.TMO_IN_CODIGO           := cAPO.Tmo_In_Codigo;  
              man_pck_apontamento.addrecordaponta(VTABAPONTA);
           end;
                  
           begin
              man_pck_apontamento.GeraApontamento('E');
           exception when others then
              my_code := my_code||SQLCODE;
              my_errm := my_errm||SQLERRM;
           end;       
           for cMVF in(
              select *
                from pro_movtomanuf mvf
               where mvf.apo_in_sequencia = cAPO.Apo_In_Sequencia)          
           loop
              delete pro_movtomanuf mv
               where mv.int_in_sequencia = cMVF.Int_In_Sequencia;
              delete PRO_ESTMOVTOMANUF me
               where me.apo_in_sequencia = cMVF.Apo_In_Sequencia;
              begin
                 adm_pck_movimentoestoque.Excluirmovimento(cMVF.Org_In_Codigo,cMVF.Ser_In_Sequencia, cMVF.Mvt_In_Lancam);
              exception when others then
                 my_code := my_code||SQLCODE;
                 my_errm := my_errm||SQLERRM;
              end;          
           end loop;                    
           begin
              commit;                    
           exception when others then
              my_code := SQLCODE;
              my_errm := SQLERRM;
              rollback;
           end;                                      
        end loop;                      
        commit;           
  end P_EXCLUIRAPONTAMENTO;
  procedure p_inseredemanda(pRESULT IN OUT SYS_REFCURSOR
                           ,pORG_IN_CODIGO IN NUMBER
                           ,pFIL_IN_CODIGO IN NUMBER                           
                           ,pORD_IN_CODIGO IN NUMBER                           
                           ,pMVS_ST_LOTEFORNE In IDP.APT_APONTADEMANDA_ESTOQUE.MVS_ST_LOTEFORNE%Type
                           ,pAPT_RE_QUANTIDADE In IDP.APT_APONTAORDEM.APT_RE_QUANTIDADE%Type
                           ) Is
    vAPT_RE_QTDESELECIONADA IDP.APT_APONTADEMANDA_ESTOQUE.APT_RE_QTDESELECIONADA%Type;
    
    vDDE_BO_RESERVADO       IDP.APT_APONTADEMANDA.DDE_BO_RESERVADO%TYPE;        
    vEXISTE_APT CHAR(1);
    
    vDDE_IN_OPERACAO  pro_prog_ordem.plf_in_sqoperacao%type;
    vMAQ_IN_CODIGO    IDP.apt_apontaordem.apt_maq_in_codigo%type;
    vMVS_IN_SEQUENCIA IDP.apt_apontademanda_estoque.mvs_in_sequencia%type;
    vNAT_PAD_IN_CODIGO est_movsumarizado.nat_pad_in_codigo%type;
    vALM_TAB_IN_CODIGO est_produtolocaliza.alm_tab_in_codigo%type;
    vALM_PAD_IN_CODIGO est_produtolocaliza.alm_pad_in_codigo%type;
    vALM_IN_CODIGO     est_produtolocaliza.alm_in_codigo%type;
    vLOC_IN_CODIGO     est_produtolocaliza.loc_in_codigo%type;
    --vPRO_PAD_IN_CODIGO est_produtolocaliza.pro_pad_in_codigo%type;
    VATI_PAD_IN_CODIGO PRO_ATIVIDADE.ATI_PAD_IN_CODIGO%TYPE;
    vAPT_IN_SEQUENCIA IDP.APT_APONTAORDEM.APT_IN_SEQUENCIA%TYPE;
    vORD_SEQ_IN_CODIGO PRO_ORDEMLOTESUB.ORD_SEQ_IN_CODIGO%TYPE;
    vPLF_IN_SQOPERACAO pro_prog_ordem.plf_in_sqoperacao%type;
    vAPT_DT_INCLUSAO date;
    vMENSAGEM varchar2(300);
    vAPT tAPT;
    v_integrado char(1);
    vEXISTE_DEM CHAR(1);
    v_temlote CHAR(1);
    vDDE_RE_DEMANDA         IDP.APT_APONTADEMANDA_ESTOQUE.APT_RE_QTDESELECIONADA%Type;
    vDDE_RE_QTDE_DISPONIVEL IDP.APT_APONTADEMANDA.DDE_RE_QTDE_DISPONIVEL%Type;
    vDEBUG  char(1);
  Begin
     vDDE_RE_QTDE_DISPONIVEL := 0;
     vMENSAGEM:=null;
     v_integrado := 'S';
     v_temlote := 'N'; 
     vDEBUG := 'N';
     if vDEBUG = 'S' then
         Raise_application_error(-20000,
                             pFIL_IN_CODIGO||';'||
                             pORD_IN_CODIGO||';'||
                             pORG_IN_CODIGO||';'||
                             pMVS_ST_LOTEFORNE||';'||
                             pAPT_RE_QUANTIDADE

        );
     end if;
--     Raise_application_error(-20000, );
     vAPT_DT_INCLUSAO := trunc(sysdate);
     vORD_SEQ_IN_CODIGO:= PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,218,sysdate);
     VATI_PAD_IN_CODIGO:= PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,204,sysdate);
     for cORD in(
        select *
          from pro_ordens ord
         where ord.ord_in_codigo = pord_in_codigo
           and ord.fil_in_codigo = pfil_in_codigo
           and ord.ord_seq_in_codigo = pck_mega.achapadraodatabela(pfil_in_codigo,218, sysdate)
        )
     loop
        vTAB_ORD := cORD;
     end loop;
     if pFIL_IN_CODIGO = 312 then        
        if length(pMVS_ST_LOTEFORNE) = 6 then
           vAPT_DEM.Mvs_St_Loteforne := pMVS_ST_LOTEFORNE;
        elsif length(pMVS_ST_LOTEFORNE) <6 then
           vAPT_DEM.Com_In_Codigo := to_number(pMVS_ST_LOTEFORNE);
           vAPT_DEM.Mvs_St_Loteforne := '*';
        elsif length(pMVS_ST_LOTEFORNE) <22 then
           vAPT_DEM.Mvs_St_Loteforne := pMVS_ST_LOTEFORNE;
        else 
           vAPT_DEM.Mvs_St_Loteforne := pMVS_ST_LOTEFORNE;
        end if;
     else 
        vAPT_DEM.Mvs_St_Loteforne := pMVS_ST_LOTEFORNE;
     end if;
     -- busca no Mov_sumarizado;
     for cMVS in(
        select mvs.*
          from est_movsumarizado mvs
         where mvs.fil_in_codigo = pFIL_IN_CODIGO
           and mvs.nat_st_codigo = 'DP'
           and (
                  (vAPT_DEM.Mvs_St_Loteforne = '*' and
                   mvs.pro_in_codigo = vAPT_DEM.Com_In_Codigo)
                or(mvs.mvs_st_loteforne = vAPT_DEM.Mvs_St_Loteforne and mvs.mvs_st_loteforne <> '*')
               )
           
        )
     loop
        vMVS := cMVS;
     end loop;
     -- Carrega demanda do item
     vTAB_DEP := null;
     for cDEP in(
        select dep.* 
          from pro_demanda_dep dep
         where dep.org_in_codigo = pORG_IN_CODIGO
           and dep.ord_seq_in_codigo = vORD_SEQ_IN_CODIGO
           and dep.ord_in_codigo = pORD_IN_CODIGO
           and dep.com_tab_in_codigo = vMVS.Pro_Tab_In_Codigo
           and dep.com_pad_in_codigo = vMVS.Pro_Pad_In_Codigo
           and dep.com_in_codigo     = vMVS.Pro_In_Codigo
       )
     loop
        vTAB_DEP := cDEP;
     end loop;
     if vTAB_DEP.Com_In_Codigo is null then
        OPEN pRESULT FOR
        Select 'O Item : '||vMVS.Pro_In_Codigo||' Lote: '||vMVS.Mvs_St_Loteforne||chr(13)||' Não faz parte das demandas dessa ordem!'||chr(13)||'Favor inserir nos itens da ordem, da tela de ordem.' MENSAGEM
          from dual;
        return;
     end if;        
     v_apontamento := f_valida_apontamento;
     if v_apontamento = 'S' then     
        -- Busca o apontamento em aberto para a ordem;
        for cAPO in(
           select apt.*
             from IDP.apt_apontaordem apt
             where apt.fil_in_codigo = vTAB_ORD.fil_in_codigo
               and apt.ord_in_codigo = vTAB_ORD.ord_in_codigo
               --and (apt.plf_in_sqoperacao = pplf_in_sqoperacao or pplf_in_sqoperacao is null)
               and apt.apt_ch_status = 'A')
        loop
           vTAB_APT := cAPO;
           p_programacaoordem;
        end loop;
     else
        apt_inserir_apt(pfil_in_codigo,
                        pord_in_codigo,
                        null,
                        null,
                        vAPT_DT_INCLUSAO,
                        null,
                        null,
                        --pusu_in_codigo,
                        vAPT);
        loop
           fetch vAPT
            INTO vTAB_APT.org_tab_in_codigo,
                 vTAB_APT.org_pad_in_codigo,
                 vTAB_APT.org_in_codigo,
                 vTAB_APT.org_tau_st_codigo,
                 vTAB_APT.ord_tab_in_codigo,
                 vTAB_APT.ord_seq_in_codigo,
                 vTAB_APT.ord_in_codigo,
                 vTAB_APT.apt_in_sequencia,
                 vTAB_APT.fil_in_codigo,
                 vTAB_APT.Plf_In_Sqoperacao;
           EXIT WHEN vAPT%NOTFOUND;
        end loop;
     end if;
     
     vAPT_DEM.apt_in_sequencia   := vTAB_APT.Apt_In_Sequencia;
     vAPT_DEM.org_tab_in_codigo  := vTAB_APT.org_tab_in_codigo;
     vAPT_DEM.org_pad_in_codigo  := vTAB_APT.org_pad_in_codigo;
     vAPT_DEM.org_in_codigo      := vTAB_APT.org_in_codigo;
     vAPT_DEM.org_tau_st_codigo  := vTAB_APT.org_tau_st_codigo;
     vAPT_DEM.ord_tab_in_codigo  := vTAB_APT.ord_tab_in_codigo;
     vAPT_DEM.ord_seq_in_codigo  := vTAB_APT.ord_seq_in_codigo;
     vAPT_DEM.ord_in_codigo      := vTAB_APT.ord_in_codigo;
     vAPT_DEM.com_tab_in_codigo  := 100;
     vAPT_DEM.com_pad_in_codigo  := PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,100,sysdate);
     vAPT_DEM.fil_in_codigo      := vTAB_APT.FIL_IN_CODIGO;
     vAPT_DEM.Ctl_In_Codigo      := null;
     vAPT_DEM.Mvd_In_Sequencia   := null;
     vAPT_DEM.mvs_in_reserva     := 0;
     vAPT_DEM.Alm_Tab_In_Codigo  := 105;
     vAPT_DEM.Alm_Pad_In_Codigo  := PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,105,sysdate);
     vAPT_DEM.nat_tab_in_codigo  := 143;
     vAPT_DEM.Nat_Pad_In_Codigo  := PCK_MEGA.ACHAPADRAODATABELA(pFIL_IN_CODIGO,143,sysdate);
     vAPT_DEM.nat_st_codigo      := 'DP';     
     vAPT_DEM.mvs_dt_entrada     := to_date('01/01/2000','dd/mm/yyyy');
     vAPT_DEM.mvs_dt_validade    := to_date('01/01/2000','dd/mm/yyyy');
     vAPT_DEM.Plf_In_Sqoperacao  := vTAB_APT.Plf_In_Sqoperacao;
     vAPT_DEM.Apt_Re_Qtdeselecionada := pAPT_RE_QUANTIDADE;
     vAPT_DEM.Ord_St_Id              := null;
     vAPT_DEM.Cmaq_St_Id             := null;
     -- Carrega localização do produto;
     vLOC.org_tab_in_codigo := vTAB_APT.org_tab_in_codigo;
     vLOC.org_pad_in_codigo := vTAB_APT.org_pad_in_codigo;
     vLOC.org_in_codigo := vTAB_APT.org_in_codigo;
     vLOC.org_tau_st_codigo := vTAB_APT.org_tau_st_codigo;
     vLOC.fil_in_codigo := vTAB_APT.fil_in_codigo;
     vLOC.pro_tab_in_codigo := vTAB_DEP.com_tab_in_codigo;
     vLOC.pro_pad_in_codigo := vTAB_DEP.com_pad_in_codigo;
     vLOC.pro_in_codigo := vTAB_DEP.com_in_codigo;
     vLOC.tpo_st_codigo_tipo := vTAB_ORD.tpo_st_codigo_tipo;
     vLOC.apt_maq_in_codigo := vTAB_APT.apt_maq_in_codigo;
     vLOC.cmaq_in_codigo := vTAB_APT.apt_cmaq_in_codigo;
     vLOC.opr_in_codigo := vTAB_PRG.opr_in_codigo;
     vLOC.mov_st_origem := 'D';
     p_DefineLocalizacaoItem;     
     v_integrado := f_valida_intdemanda;          
     if v_integrado = 'N' then
        BEGIN
           select nvl(max(t.mvs_in_sequencia),0)+1
             into vAPT_DEM.mvs_in_sequencia
             from IDP.apt_apontademanda_estoque t
            where t.org_tab_in_codigo = vTAB_APT.Org_Tab_In_Codigo
              and t.org_pad_in_codigo = vTAB_APT.Org_Pad_In_Codigo
              and t.org_in_codigo = vTAB_APT.Org_In_Codigo
              and t.ord_tab_in_codigo = vTAB_APT.Ord_Tab_In_Codigo
              and t.ord_seq_in_codigo = vTAB_APT.Ord_Seq_In_Codigo
              and t.ord_in_codigo = vTAB_APT.Ord_In_Codigo
              and t.fil_in_codigo = vTAB_APT.Fil_In_Codigo;
        EXCEPTION WHEN OTHERS THEN
           vAPT_DEM.mvs_in_sequencia:=1;
        END;        

        For cDEM in (
           Select m.org_tab_in_codigo,
                  m.org_pad_in_codigo,
                  m.org_in_codigo,
                  m.org_tau_st_codigo,
                  m.fil_in_codigo,
                  m.pro_tab_in_codigo,
                  m.pro_pad_in_codigo,
                  m.pro_in_codigo,
                  p.uni_st_unidade,
                  m.mvs_st_referencia,
                  m.alm_tab_in_codigo,
                  m.alm_pad_in_codigo,
                  m.alm_in_codigo,
                  m.loc_in_codigo,
                  m.mvs_in_reserva,
                  m.nat_tab_in_codigo,
                  m.nat_pad_in_codigo,
                  m.nat_st_codigo,
                  m.mvs_dt_entrada,
                  m.mvs_dt_validade,
              sum(m.mvs_re_quantidade) mvs_re_quantidade
             From est_movsumarizado m,
                  est_produtos p
            where m.pro_tab_in_codigo = p.pro_tab_in_codigo
              and m.pro_pad_in_codigo = p.pro_pad_in_codigo
              and m.pro_in_codigo     = p.pro_in_codigo
              and m.org_in_codigo     = vTAB_APT.ORG_IN_CODIGO
              and m.fil_in_codigo     = vTAB_APT.Fil_In_Codigo
              and m.mvs_st_loteforne  = vAPT_DEM.mvs_st_loteforne
              and m.pro_tab_in_codigo = vTAB_DEP.Com_Tab_In_Codigo
              and m.pro_pad_in_codigo = vTAB_DEP.Com_Pad_In_Codigo
              and m.pro_in_codigo     = vTAB_DEP.Com_In_Codigo    
              and m.alm_tab_in_codigo = vTAB_PRL.Alm_Tab_In_Codigo
              and m.alm_pad_in_codigo = vTAB_PRL.Alm_Pad_In_Codigo
              and m.alm_in_codigo     = vTAB_PRL.Alm_In_Codigo
              and m.loc_in_codigo     = vTAB_PRL.Loc_In_Codigo
              and m.nat_st_codigo     = 'DP'
           group by
                  m.org_tab_in_codigo,
                  m.org_pad_in_codigo,
                  m.org_in_codigo,
                  m.org_tau_st_codigo,
                  m.fil_in_codigo,
                  m.pro_tab_in_codigo,
                  m.pro_pad_in_codigo,
                  m.pro_in_codigo,
                  p.uni_st_unidade,
                  m.mvs_st_referencia,
                  m.alm_tab_in_codigo,
                  m.alm_pad_in_codigo,
                  m.alm_in_codigo,
                  m.loc_in_codigo,
                  m.mvs_in_reserva,
                  m.nat_tab_in_codigo,
                  m.nat_pad_in_codigo,
                  m.nat_st_codigo,
                  m.mvs_dt_entrada,
                  m.mvs_dt_validade           
         )
        loop
           IF cDEM.loc_in_codigo = 0 THEN
              begin
                 select distinct
                        pal.alm_tab_in_codigo,
                        pal.alm_pad_in_codigo,
                        pal.alm_in_codigo,
                        pal.loc_in_codigo
                   into vAPT_DEM.alm_tab_in_codigo,
                        vAPT_DEM.alm_pad_in_codigo,
                        vAPT_DEM.alm_in_codigo,
                        vAPT_DEM.loc_in_codigo
                   from est_produtolocaliza pal
                  where pal.pro_tab_in_codigo = cDEM.pro_tab_in_codigo
                    and pal.pro_pad_in_codigo = cDEM.pro_pad_in_codigo
                    and pal.pro_in_codigo     = cDEM.pro_in_codigo
                    and pal.org_in_codigo     = vTAB_APT.ORG_IN_CODIGO
                    and pal.fil_in_codigo     = vTAB_APT.FIL_IN_CODIGO
                    and pal.prl_in_prioridade = 1;
              exception when others then
                 null;
              end;
           else
              vAPT_DEM.ALM_TAB_IN_CODIGO:= cDEM.alm_tab_in_codigo;
              vAPT_DEM.ALM_PAD_IN_CODIGO:= cDEM.alm_pad_in_codigo;
              vAPT_DEM.ALM_IN_CODIGO    := cDEM.alm_in_codigo;
              vAPT_DEM.LOC_IN_CODIGO    := cDEM.loc_in_codigo;
           end if;
           vAPT_DEM.com_in_codigo      := cDEM.Pro_In_Codigo;           
           -- Dados da demanda dependente da Ordem;
           vEXISTE_APT := 'N';           
           -- Atualiza a sequencia da operação;
           vAPT_DEM.dde_in_operacao := vTAB_DEP.Dde_In_Operacao;
           vAPT_DEM.Dde_Dt_Necessidade := vTAB_DEP.Dde_Dt_Necessidade;

           vAPT_DEM.nat_pad_in_codigo  := cDEM.nat_pad_in_codigo;
           vAPT_DEM.mvs_st_referencia  := cDEM.mvs_st_referencia;
           if nvl(pAPT_RE_QUANTIDADE,0) = 0 then
              vAPT_DEM.apt_re_qtdeselecionada := vTAB_DEP.Dde_Re_Qtde_Necessaria;
           else
              vAPT_DEM.apt_re_qtdeselecionada := pAPT_RE_QUANTIDADE;
           end if;
           vAPT_DEM.ctl_in_codigo          := null;
           vAPT_DEM.mvd_in_sequencia       := null;
           -- carrega tabela de demandas;
           vTAB_DDE.Apt_In_Sequencia:= vAPT_DEM.Apt_In_Sequencia;
           vTAB_DDE.Org_Tab_In_Codigo := vTAB_DEP.Org_Tab_In_Codigo;
           vTAB_DDE.Org_Pad_In_Codigo := vTAB_DEP.Org_Pad_In_Codigo;
           vTAB_DDE.Org_In_Codigo := vTAB_DEP.Org_In_Codigo;
           vTAB_DDE.Org_Tau_St_Codigo := vTAB_DEP.Org_Tau_St_Codigo;
           vTAB_DDE.Ord_Tab_In_Codigo := vTAB_DEP.Ord_Tab_In_Codigo;
           vTAB_DDE.Ord_Seq_In_Codigo := vTAB_DEP.Ord_Seq_In_Codigo;
           vTAB_DDE.Ord_In_Codigo := vTAB_DEP.Ord_In_Codigo;
           vTAB_DDE.Com_Tab_In_Codigo := vTAB_DEP.Com_Tab_In_Codigo;
           vTAB_DDE.Com_Pad_In_Codigo := vTAB_DEP.Com_Pad_In_Codigo;
           vTAB_DDE.Com_In_Codigo := vTAB_DEP.Com_In_Codigo;
           vTAB_DDE.Dde_In_Operacao := vTAB_DEP.Dde_In_Operacao;
           vTAB_DDE.Dde_Dt_Necessidade := vTAB_DEP.Dde_Dt_Necessidade;
           vTAB_DDE.Dde_Re_Qtde_Padrao :=vAPT_DEM.Apt_Re_Qtdeselecionada;
           vTAB_DDE.Plf_In_Sqoperacao := vTAB_APT.Plf_In_Sqoperacao;
           vTAB_DDE.Pro_St_Tipobaixa :='M';
           vTAB_DDE.Dde_Bo_Atende := 'S';
           vTAB_DDE.Dde_Re_Qtde_Disponivel :=cDEM.mvs_re_quantidade;
           vTAB_DDE.Dde_Bo_Reservado := 'N';
           vTAB_DDE.Dde_Re_Qtde_Padrao_Mov :=vAPT_DEM.Apt_Re_Qtdeselecionada;
           begin
              insert into IDP.apt_apontademanda_estoque values vAPT_DEM;
              vMENSAGEM:='Ok';
              v_temlote := 'S';
           exception when others then
              vMENSAGEM:='Erro';
           end;
           Begin
              Insert Into IDP.APT_APONTADEMANDA values vTAB_DDE;
           Exception When DUP_VAL_ON_INDEX Then
                p_RecalculaDemandaEmpenho(vTAB_APT.APT_IN_SEQUENCIA);
           End;
           if vMENSAGEM ='Ok' then
              Commit;
           else
              rollback;
           end if;
        End Loop;        
        if v_temlote = 'N' then
           begin
              insert into IDP.apt_apontademanda_estoque values vAPT_DEM;
              vMENSAGEM:='Ok';           
           exception when others then
              vMENSAGEM:='Erro';
           end;
           if vMENSAGEM ='Ok' then
              Commit;
           else
              rollback;
           end if;
        end if;
     else
        vMENSAGEM := 'Ok';
     end if;

     OPEN pRESULT FOR
        SELECT vMENSAGEM MENSAGEM,
               decode(apd.com_in_codigo,null,'Não Encontrado!',apd.com_in_codigo) as PRO_IN_CODIGO,
               apd.apt_in_sequencia as APT_IN_SEQUENCIA,
               apd.mvs_in_sequencia as MVS_IN_SEQUENCIA
          FROM IDP.apt_apontademanda_estoque apd
         where apd.org_in_codigo    = vAPT_DEM.Org_In_Codigo
           and apd.ord_in_codigo    = vAPT_DEM.Ord_In_Codigo
           and apd.fil_in_codigo    = vAPT_DEM.Fil_In_Codigo
           and apd.apt_in_sequencia = vAPT_DEM.Apt_In_Sequencia
           and apd.ctl_in_codigo    = vAPT_DEM.Ctl_In_Codigo
           and apd.mvd_in_sequencia = vAPT_DEM.Mvd_In_Sequencia;

  End p_inseredemanda;
  procedure p_geraresiduos_nmv(pRESULT IN OUT SYS_REFCURSOR
                              ,pORG_IN_CODIGO IN NUMBER
                              ,pFIL_IN_CODIGO IN NUMBER                           
                              ,pORD_IN_CODIGO IN NUMBER) is
     begin
        for cRES in(       
               select apl.*
                 from IDP.apt_apontaordem_lote apl
                where apl.org_tab_in_codigo = 53
                  and apl.org_pad_in_codigo = 1
                  and apl.org_in_codigo     = pORG_IN_CODIGO
                  and apl.org_tau_st_codigo = 'G'                  
                  and apl.ord_tab_in_codigo = 218
                  and apl.ord_seq_in_codigo = pck_mega.achapadraodatabela(pFIL_IN_CODIGO,218,sysdate)                  
                  and apl.ord_in_codigo     = pORD_IN_CODIGO                  
                  and apl.orl_st_slotefabricacao = (select max(to_number(l.orl_st_slotefabricacao))
                                                      from apt_apontaordem_lote l
                                                     where l.org_tab_in_codigo = apl.org_tab_in_codigo
                                                       and l.org_pad_in_codigo = apl.org_pad_in_codigo
                                                       and l.org_in_codigo     = apl.org_in_codigo
                                                       and l.org_tau_st_codigo = apl.org_tau_st_codigo
                                                       and l.ord_tab_in_codigo = apl.ord_tab_in_codigo
                                                       and l.ord_seq_in_codigo = apl.ord_seq_in_codigo
                                                       and l.ord_in_codigo     = apl.ord_in_codigo
                                                        )
                  )
        loop
           vAPT_LOTE := cRES;
        end loop;
  end p_geraresiduos_nmv;
  procedure p_atualizaDemandaLote (pAPT_IN_SEQUENCIA in number) is
    vLOT apt_apontademanda_estoque%rowtype;
    begin
       vTAB_DDE.Apt_In_Sequencia:= pAPT_IN_SEQUENCIA; 
       for cAPT in(
          select apt.*
            from apt_apontaordem apt
           where apt.apt_in_sequencia = pAPT_IN_SEQUENCIA
          )
       loop
          vTAB_APT := cAPT;
       end loop;
       -- nova rotina de validação de demanda do aviso de recebimento;
       if vTAB_APT.fil_in_codigo = 3 then
          -- Busca o lote na tabela de apontamento
          for cITD in(
             select * 
               from apt_apontademanda_estoque itd
              where itd.apt_in_sequencia = vTAB_APT.APT_IN_SEQUENCIA
                and itd.apt_bo_loteestoque = 'N')
          loop
             vLOT := cITD;
             -- busca o item no aviso
             -- Valida lote do aviso de recebimento customizado        
             for cRCI in(
                select rci.*
                  from cli_aviso_receb_item_lote rci
                 where rci.mvl_st_loteforne = vLOT.mvs_st_loteforne)
             loop
                vRCI := cRCI;
             end loop;             
             vTAB_MVS := null;                   
             -- Busca as informações da tabela de saldos
             for cSLD in(
                 select * 
                 from est_movsumarizado mvs
                where mvs.org_tab_in_codigo = vLOT.Org_Tab_In_Codigo
                  and mvs.org_pad_in_codigo = vLOT.Org_Pad_In_Codigo
                  and mvs.org_in_codigo     = vLOT.Org_In_Codigo
                  and mvs.org_tau_st_codigo = vLOT.Org_Tau_St_Codigo
                  and mvs.fil_in_codigo     = vLOT.Fil_In_Codigo
                  and mvs.mvs_st_loteforne  = vLOT.Mvs_St_Loteforne
                  and mvs.nat_st_codigo      = 'DP'
                  and rownum < 2
             )
             loop
                vTAB_MVS := cSLD;
             end loop;
             if  vTAB_MVS.org_in_codigo is not null then                            
                vLOT.com_in_codigo      := vTAB_MVS.pro_in_codigo;
                vLOT.apt_bo_loteestoque := 'S';
                vLOT.alm_in_codigo      := vTAB_MVS.Alm_In_Codigo;
                vLOT.loc_in_codigo      := vTAB_MVS.Loc_In_Codigo;
                vLOT.Mvs_St_Referencia  := vTAB_MVS.Mvs_St_Referencia;
                vLOT.Ire_Ch_Tiporeserva := vTAB_MVS.Ire_Ch_Tiporeserva;
                vLOT.Saldo_Estoque      := vTAB_MVS.Mvs_Re_Quantidade;
                if vRCI.Iar_Re_Quantconf = vLOT.Apt_Re_Qtdeselecionada then             
                   vLOT.apt_re_qtdeselecionada := vTAB_MVS.mvs_re_quantidade;
                end if;
                for cDDE in(
                   select * 
                     from pro_demanda_dep dde
                    where dde.org_tab_in_codigo = vLOT.Org_Tab_In_Codigo
                      and dde.org_pad_in_codigo = vLOT.Org_Pad_In_Codigo
                      and dde.org_in_codigo     = vLOT.Org_In_Codigo
                      and dde.org_tau_st_codigo = vLOT.Org_Tau_St_Codigo
                      and dde.ord_tab_in_codigo = vLOT.Ord_Tab_In_Codigo
                      and dde.ord_seq_in_codigo = vLOT.Ord_Seq_In_Codigo
                      and dde.ord_in_codigo     = vLOT.Ord_In_Codigo
                      and dde.com_tab_in_codigo = vLOT.Com_Tab_In_Codigo
                      and dde.com_pad_in_codigo = vLOT.Com_Pad_In_Codigo
                      and dde.com_in_codigo     = vLOT.Com_In_Codigo)                                                   
                loop
                   vTAB_DEP := cDDE;
                end loop;
                if vLOT.Dde_Dt_Necessidade is null then                  
                   vLOT.Dde_In_Operacao := vTAB_DEP.Dde_In_Operacao;
                   vLOT.Dde_Dt_Necessidade := vTAB_DEP.Dde_Dt_Necessidade;                   
                end if;
                
                update apt_apontademanda_estoque upd
                   set upd.com_in_codigo          = vLOT.com_in_codigo,
                       upd.alm_in_codigo          = vLOT.Alm_In_Codigo,
                       upd.loc_in_codigo          = vLOT.Loc_In_Codigo,
                       upd.Mvs_St_Referencia      = vLOT.Mvs_St_Referencia,
                       upd.Ire_Ch_Tiporeserva     = vLOT.Ire_Ch_Tiporeserva,
                       upd.apt_re_qtdeselecionada = vLOT.apt_re_qtdeselecionada,
                       upd.dde_in_operacao        = VLOT.Dde_In_Operacao,
                       upd.dde_dt_necessidade     = vLOT.dde_dt_necessidade,
                       upd.mvl_st_log             = null,
                       upd.apt_bo_loteestoque     = vLOT.apt_bo_loteestoque,
                       upd.saldo_estoque          = vLOT.Saldo_Estoque
                    where upd.Apt_In_Sequencia    = vLOT.apt_in_sequencia
                      and upd.Mvs_In_Sequencia    = vLOT.mvs_in_sequencia;                         
             end if;
          end loop;
          commit;
       end if;                
       vTAB_DEP := null;          
       for cLOT in(
         select * 
           from apt_apontademanda_estoque lot
          where lot.apt_in_sequencia = pAPT_IN_SEQUENCIA
            
            and (
                 (lot.apt_re_qtdeselecionada = 0) or 
                 (lot.apt_re_qtdeselecionada = 9999) or 
                 (lot.com_in_codigo is null) or
                 (lot.dde_dt_necessidade is null) or
                 (lot.mvl_st_log is not null) or
                 (nvl(lot.saldo_estoque,0) = 0))
            --and lot.com_in_codigo is null
            and exists
                (select 1 
                   from apt_apontaordem apt
                  where apt.apt_in_sequencia = lot.apt_in_sequencia
                    and apt.apt_ch_status = 'A')
            )
       loop
          vLOT := cLOT;
          vTAB_MVS := null;
          if vLOT.Mvs_St_Loteforne = '*' then
             return;
          end if;          
          -- Busca as informações da tabela de saldos
          for cSLD in(
              select * 
              from est_movsumarizado mvs
             where mvs.org_tab_in_codigo = vLOT.Org_Tab_In_Codigo
               and mvs.org_pad_in_codigo = vLOT.Org_Pad_In_Codigo
               and mvs.org_in_codigo     = vLOT.Org_In_Codigo
               and mvs.org_tau_st_codigo = vLOT.Org_Tau_St_Codigo
               and mvs.fil_in_codigo     = vLOT.Fil_In_Codigo
               and mvs.mvs_st_loteforne  = vLOT.Mvs_St_Loteforne
               and (mvs.alm_in_codigo     = vLOT.Alm_In_Codigo or vLOT.Alm_In_Codigo is null)
               and (mvs.loc_in_codigo     = vLOT.loc_in_codigo or vLOT.loc_in_codigo is null)
               and mvs.nat_st_codigo      = 'DP'
               and rownum < 2
          )
          loop
             vTAB_MVS := cSLD;             
             if cLOT.Fil_In_Codigo in(312,31,3) then
                vLOT.com_in_codigo := cSLD.Pro_In_Codigo;
                vLOT.alm_in_codigo := cSLD.Alm_In_Codigo;
                vLOT.loc_in_codigo := cSLD.Loc_In_Codigo;
                vLOT.Mvs_St_Referencia := cSLD.Mvs_St_Referencia;
                vLOT.Ire_Ch_Tiporeserva := cSLD.Ire_Ch_Tiporeserva;
                vLOT.Saldo_Estoque := cSLD.Mvs_Re_Quantidade;
                if vLOT.Apt_Re_Qtdeselecionada = 9999 then
                   vLOT.Apt_Re_Qtdeselecionada := cSLD.Mvs_Re_Quantidade;
                elsif vLOT.Apt_Re_Qtdeselecionada = 0 then
                   vLOT.Apt_Re_Qtdeselecionada := cSLD.Mvs_Re_Quantidade;
                elsif vLOT.Apt_Re_Qtdeselecionada > cSLD.Mvs_Re_Quantidade then
                   vLOT.Apt_Re_Qtdeselecionada := cSLD.Mvs_Re_Quantidade;
                /*elsif (vLOT.Apt_Re_Qtdeselecionada < cSLD.Mvs_Re_Quantidade) 
                   and (cSLD.Fil_In_Codigo = 312) then                 
                   vLOT.Apt_Re_Qtdeselecionada := cSLD.Mvs_Re_Quantidade;*/
                end if;                                
                -- Busca dados da demanda da ordem
                for cDDE in(
                   select * 
                     from pro_demanda_dep dde
                    where dde.org_tab_in_codigo = vLOT.Org_Tab_In_Codigo
                      and dde.org_pad_in_codigo = vLOT.Org_Pad_In_Codigo
                      and dde.org_in_codigo     = vLOT.Org_In_Codigo
                      and dde.org_tau_st_codigo = vLOT.Org_Tau_St_Codigo
                      and dde.ord_tab_in_codigo = vLOT.Ord_Tab_In_Codigo
                      and dde.ord_seq_in_codigo = vLOT.Ord_Seq_In_Codigo
                      and dde.ord_in_codigo     = vLOT.Ord_In_Codigo
                      and dde.com_tab_in_codigo = vLOT.Com_Tab_In_Codigo
                      and dde.com_pad_in_codigo = vLOT.Com_Pad_In_Codigo
                      and dde.com_in_codigo     = vLOT.Com_In_Codigo)                                                   
                loop
                   vTAB_DEP := cDDE;
                end loop;
                if vLOT.Dde_Dt_Necessidade is null then                  
                   vLOT.Dde_In_Operacao := vTAB_DEP.Dde_In_Operacao;
                   vLOT.Dde_Dt_Necessidade := vTAB_DEP.Dde_Dt_Necessidade;                   
                end if;
                if (vTAB_DEP.Com_In_Codigo <> vLOT.Com_In_Codigo) and vLOT.Com_In_Codigo is not null then
                   null;
                   Raise_application_error(-20000, 'O Lote: '||vTAB_MVS.Mvs_St_Loteforne||chr(13)||
                                                   ' do item: '||vTAB_MVS.Pro_In_Codigo||chr(13)||
                                                   ' Não faz parte da demanda dessa ordem! '||chr(13)||
                                                   'Favor inserir como item da ordem para prosseguir.'||chr(13)||
                                                   ' Analisar qual ação será tomada em relação a essa divergência!');
                   -- Gera erro de demanda para o usuário;
                end if;                  
                update apt_apontademanda_estoque upd
                   set upd.com_in_codigo = vLOT.com_in_codigo,
                       upd.alm_in_codigo = vLOT.Alm_In_Codigo,
                       upd.loc_in_codigo = vLOT.Loc_In_Codigo,
                       upd.Mvs_St_Referencia = vLOT.Mvs_St_Referencia,
                       upd.Ire_Ch_Tiporeserva = vLOT.Ire_Ch_Tiporeserva,
                       upd.apt_re_qtdeselecionada = vLOT.apt_re_qtdeselecionada,
                       upd.dde_in_operacao = VLOT.Dde_In_Operacao,
                       upd.dde_dt_necessidade     = vLOT.dde_dt_necessidade,
                       upd.mvl_st_log             = null,
                       upd.saldo_estoque          = vLOT.Saldo_Estoque
                 where upd.Apt_In_Sequencia = vLOT.apt_in_sequencia
                   and upd.Mvs_In_Sequencia = vLOT.mvs_in_sequencia;
               -- atualiza o total da semana;
             end if;
          end loop;
          if VLOT.dde_dt_necessidade <> vTAB_DEP.dde_dt_necessidade then
             update apt_apontademanda_estoque upd
                set upd.dde_dt_necessidade = vTAB_DEP.dde_dt_necessidade
              where upd.Apt_In_Sequencia = vLOT.apt_in_sequencia
                and upd.Mvs_In_Sequencia = vLOT.mvs_in_sequencia;
          end if;
          if vLOT.Mvs_St_Loteforne is not null then
             if vTAB_MVS.Mvs_St_Loteforne is not null then
                p_cria_demanda;                        
             else
                vLOT.Mvl_St_Log := 'O Lote:............. '||vLOT.Mvs_St_Loteforne||chr(13)||
                                            'Vinculado na demanda dessa ordem, '||chr(13)||
                                                'Não existe no estoque, favor verificar!';
                update apt_apontademanda_estoque upd
                      set upd.mvl_st_log = vLOT.Mvl_St_Log
                    where upd.Apt_In_Sequencia = vLOT.apt_in_sequencia
                      and upd.Mvs_In_Sequencia = vLOT.mvs_in_sequencia;
             end if;
          end if;
       end loop;
       begin
          for cAPT in(
             select d.*,
                    m.mvs_dt_entrada as mvs_dt_entrada_new
               from APT_APONTADEMANDA_ESTOQUE d,
                    est_movsumarizado m
              where m.pro_tab_in_codigo = d.com_tab_in_codigo
                and m.pro_pad_in_codigo = d.com_pad_in_codigo
                and m.pro_in_codigo     = d.com_in_codigo
                and m.mvs_st_loteforne  = d.mvs_st_loteforne
                and d.apt_in_sequencia  = pAPT_IN_SEQUENCIA
                and m.mvs_dt_entrada <> d.mvs_dt_entrada)
          loop
             update APT_APONTADEMANDA_ESTOQUE e
                set e.mvs_dt_entrada = cAPT.mvs_dt_entrada_new
              where e.APT_IN_SEQUENCIA = cAPT.APT_IN_SEQUENCIA
                and e.MVS_IN_SEQUENCIA = cAPT.MVS_IN_SEQUENCIA;
          end loop;
       exception when others then
          null;
       end;      
       begin
          for cAPT in(
             select d.*,
                    m.dde_dt_necessidade as new_dde_dt_necessidade
               from APT_APONTADEMANDA_ESTOQUE d,
                    PRO_DEMANDA_DEP m
              where m.com_tab_in_codigo = d.com_tab_in_codigo
                and m.com_pad_in_codigo = d.com_pad_in_codigo
                and m.com_in_codigo     = d.com_in_codigo
                and m.org_tab_in_codigo = d.org_tab_in_codigo
                and m.org_pad_in_codigo = d.org_pad_in_codigo
                and m.org_in_codigo     = d.org_in_codigo
                and m.org_tau_st_codigo = d.org_tau_st_codigo
                and m.ord_tab_in_codigo = d.ord_tab_in_codigo
                and m.ord_seq_in_codigo = d.ord_seq_in_codigo
                and m.ord_in_codigo     = d.ord_in_codigo                
                and d.apt_in_sequencia  = pAPT_IN_SEQUENCIA
                and m.dde_dt_necessidade <> d.dde_dt_necessidade)
          loop
             update APT_APONTADEMANDA_ESTOQUE e
                set e.dde_dt_necessidade = cAPT.new_dde_dt_necessidade
              where e.APT_IN_SEQUENCIA = cAPT.APT_IN_SEQUENCIA
                and e.MVS_IN_SEQUENCIA = cAPT.MVS_IN_SEQUENCIA;
             update APT_APONTADEMANDA d
                set d.dde_dt_necessidade = cAPT.new_dde_dt_necessidade
              where d.apt_in_sequencia = cAPT.apt_in_sequencia
                and d.com_tab_in_codigo = cAPT.com_tab_in_codigo
                and d.com_pad_in_codigo = cAPT.com_pad_in_codigo
                and d.com_in_codigo     = cAPT.com_in_codigo
                and d.org_tab_in_codigo = cAPT.org_tab_in_codigo
                and d.org_pad_in_codigo = cAPT.org_pad_in_codigo
                and d.org_in_codigo     = cAPT.org_in_codigo
                and d.org_tau_st_codigo = cAPT.org_tau_st_codigo
                and d.ord_tab_in_codigo = cAPT.ord_tab_in_codigo
                and d.ord_seq_in_codigo = cAPT.ord_seq_in_codigo
                and d.ord_in_codigo     = cAPT.ord_in_codigo;
          end loop;
       exception when others then
          null;
       end;      
       p_RecalculaDemandaEmpenho(pAPT_IN_SEQUENCIA);
       p_SumarizaLotes(pAPT_IN_SEQUENCIA);
       commit;                                   
  end p_atualizaDemandaLote;
  
  procedure p_atualizaprog(Org_In_Codigo in number,
                           Fil_In_Codigo in number,
                           Ord_In_Codigo in number,
                           pplf_in_sqoperacao in number) is
  v_apontamento char(1);    
  begin
     vTAB_APT.Org_In_Codigo := Org_In_Codigo;
     vTAB_APT.Fil_In_Codigo := Fil_In_Codigo;
     vTAB_APT.ord_In_Codigo := Ord_In_Codigo;
     vTAB_APT.Plf_In_Sqoperacao := pplf_in_sqoperacao;     
     for cORD in(
        select *
          from pro_ordens ord
          where ord.ord_in_codigo = vTAB_APT.ord_In_Codigo
            and ord.fil_in_codigo = vTAB_APT.Fil_In_Codigo
            and ord.ord_seq_in_codigo = pck_mega.achapadraodatabela(vTAB_APT.Fil_In_Codigo,218, sysdate)
           )
     loop
        vTAB_ORD := cORD;
     end loop;   
     -- Verifica se existe apontamento em aberto;   
     v_apontamento := f_valida_apontamento;
     if v_apontamento = 'S' then
        -- Busca o apontamento em aberto para a ordem;
        for cAPO in(
           select apt.*
             from IDP.apt_apontaordem apt
            where apt.fil_in_codigo = vTAB_ORD.fil_in_codigo
              and apt.ord_in_codigo = vTAB_ORD.ord_in_codigo
              and (apt.plf_in_sqoperacao =  vTAB_APT.Plf_In_Sqoperacao or  vTAB_APT.Plf_In_Sqoperacao is null)
              and apt.apt_ch_status = 'A')
         loop
            vTAB_APT := cAPO;
         end loop;
         p_programacaoordem;
         commit;
     end if;
  end;
  
  procedure apt_retornaitensReceb(pFIL_IN_CODIGO NUMBER,
                                  pPRO_ST_ID VARCHAR2,
                                  pRESULT IN OUT SYS_REFCURSOR) is

  begin
      --Raise_application_error(-20000, pPRO_IN_CODIGO);
      open pRESULT for
         select lpad(p.pro_tab_in_codigo,3,'0')||
                lpad(p.pro_pad_in_codigo,3,'0')||
                lpad(p.pro_in_codigo,7,'0') as pro_st_id,
                p.pro_in_codigo,
                p.pro_st_descricao,
                p.uni_st_unidade,
                nvl(p.rfc_in_codigo,0) rfc_in_codigo,                                
                (select pai.gru_st_nome
                   from est_grupos gru,
                        est_grupos pai
                  where gru.gru_tab_in_codigo = p.gru_tab_in_codigo
                    and gru.gru_pad_in_codigo = p.gru_pad_in_codigo
                    and gru.gru_ide_st_codigo = p.gru_ide_st_codigo
                    and gru.gru_in_codigo     = p.gru_in_codigo                          
                    and gru.pai_gru_tab_in_codigo = pai.gru_tab_in_codigo
                    and gru.pai_gru_pad_in_codigo = pai.gru_pad_in_codigo
                    and gru.pai_gru_ide_st_codigo = pai.gru_ide_st_codigo
                    and gru.pai_gru_in_codigo     = pai.gru_in_codigo) as gru_st_nome
           from est_produtos p,
                IDP.cus_tb_estprodutoreferencia r
          where p.pro_st_cestoque   = 'S'
            and p.pro_tab_in_codigo = r.pro_tab_in_codigo (+)
            and p.pro_pad_in_codigo = r.pro_pad_in_codigo (+)
            and p.pro_in_codigo     = r.pro_in_codigo     (+)
            and (
                    (lpad(p.pro_tab_in_codigo,3,'0')||
                     lpad(p.pro_pad_in_codigo,3,'0')||
                     lpad(p.pro_in_codigo,7,'0') = pPRO_ST_ID)                  
                  or(p.pro_in_codigo = pPRO_ST_ID and p.pro_pad_in_codigo = pck_mega.achapadraodatabela(pFIL_IN_CODIGO, 100, sysdate))
                )
            and p.pro_st_defitem    = 'MP';         
  end apt_retornaitensReceb;

  procedure p_carregaAviso is
  begin
     for cAVR in(
        select avr.*
          from cus_tb_api_avisoreceb avr
         where avr.org_tab_in_codigo = vTAB_AVR.Org_Tab_In_Codigo
           and avr.org_pad_in_codigo = vTAB_AVR.Org_Pad_In_Codigo
           and avr.org_in_codigo     = vTAB_AVR.Org_In_Codigo
           and avr.org_tau_st_codigo = vTAB_AVR.Org_Tau_St_Codigo
           and avr.fil_in_codigo     = vTAB_AVR.Fil_In_Codigo
           and avr.avr_in_sequencia   = vTAB_AVR.Avr_In_Sequencia
        )
     loop
        vAVR := cAVR;
     end loop;
  end;
  procedure p_geraavisoRecebimento(pXML clob,
                                 presult in out sys_refcursor) is
vSEQITN NUMBER;
vSEQITNL NUMBER;
vSEQLOT NUMBER;
begin
   vSEQITN := 0;
   vSEQLOT := 0;
   vSEQITNL := 0;
   --Raise_application_error(-20000, pXML);
   for cAVR in (
      select DECODE(EXISTSNODE(VALUE(A),'AVISO/FIL_IN_CODIGO'),1,EXTRACTVALUE(VALUE(A), 'AVISO/FIL_IN_CODIGO'),NULL) FIL_IN_CODIGO,
             DECODE(EXISTSNODE(VALUE(A),'AVISO/AVR_IN_SEQUENCIA'),1,EXTRACTVALUE(VALUE(A), 'AVISO/AVR_IN_SEQUENCIA'),NULL) AVR_IN_SEQUENCIA,
             DECODE(EXISTSNODE(VALUE(A),'AVISO/AVR_ST_USUARIO'),1,EXTRACTVALUE(VALUE(A), 'AVISO/AVR_ST_USUARIO'),NULL) AVR_ST_USUARIO,
             TO_DATE(DECODE(EXISTSNODE(VALUE(A),'AVISO/AVR_DT_INCLUSAO'),1,EXTRACTVALUE(VALUE(A), 'AVISO/AVR_DT_INCLUSAO'),NULL),'YYYY-MM-DD HH24:MI:SS') AVR_DT_INCLUSAO,
             DECODE(EXISTSNODE(VALUE(A),'AVISO/AVR_CH_STATUS'),1,EXTRACTVALUE(VALUE(A), 'AVISO/AVR_CH_STATUS'),NULL) AVR_CH_STATUS
        from TABLE(xmlsequence(extract(xmltype(pXML),'PARAMS/AVISO'))) A
   )
   loop
      p_carregaorg(cAVR.Fil_In_Codigo);
      vTAB_AVR.org_tab_in_codigo := vTAB_ORG.org_tab_in_codigo;
      vTAB_AVR.org_pad_in_codigo := vTAB_ORG.org_pad_in_codigo;
      vTAB_AVR.org_in_codigo     := vTAB_ORG.pai_org_in_codigo;
      vTAB_AVR.org_tau_st_codigo := vTAB_ORG.org_tau_st_codigo;
      vTAB_AVR.avr_in_sequencia  := cAVR.Avr_In_Sequencia;
      vTAB_AVR.fil_in_codigo     := cAVR.fil_in_codigo;
      vTAB_AVR.avr_dt_inclusao   := cAVR.avr_dt_inclusao;
      vTAB_AVR.avr_ch_status     := cAVR.Avr_Ch_Status;   
      vTAB_AVR.avr_st_usuario    := cAVR.avr_st_usuario;
      -- verificar se existe aviso
      insert into cus_tb_api_avisoreceb values vTAB_AVR;
      --Raise_application_error(-20000, pXML);
      for cRCI in(
         select TO_NUMBER(DECODE(EXISTSNODE(VALUE(I),'ITENS/AVR_IN_SEQUENCIA'),1,EXTRACTVALUE(VALUE(I), 'ITENS/AVR_IN_SEQUENCIA'),NULL)) AVR_IN_SEQUENCIA,
                DECODE(EXISTSNODE(VALUE(I),'ITENS/RCI_ID_PRODUTO'),1,EXTRACTVALUE(VALUE(I), 'ITENS/RCI_ID_PRODUTO'),NULL) RCI_ID_PRODUTO,
                --TO_NUMBER(replace(DECODE(EXISTSNODE(VALUE(I),'ITENS/TOTAL_AVR'),1,EXTRACTVALUE(VALUE(I), 'ITENS/TOTAL_AVR'),NULL),'.',',')) TOTAL_AVR
                TO_NUMBER(DECODE(EXISTSNODE(VALUE(I),'ITENS/TOTAL_AVR'),1,EXTRACTVALUE(VALUE(I), 'ITENS/TOTAL_AVR'),NULL)) TOTAL_AVR
           from TABLE(xmlsequence(extract(xmltype(pXML),'PARAMS/ITENS'))) I         
      )
      loop
         vTAB_AVI.org_tab_in_codigo := vTAB_AVR.Org_Tab_In_Codigo;
         vTAB_AVI.org_pad_in_codigo := vTAB_AVR.Org_Pad_In_Codigo;
         vTAB_AVI.org_in_codigo     := vTAB_AVR.Org_In_Codigo;
         vTAB_AVI.org_tau_st_codigo := vTAB_AVR.org_tau_st_codigo;
         vTAB_AVI.fil_in_codigo     := vTAB_AVR.Fil_In_Codigo;
         vTAB_AVI.avr_in_sequencia  := vTAB_AVR.Avr_In_Sequencia;
         vTAB_AVI.pro_tab_in_codigo := to_number(substr(cRCI.Rci_Id_Produto,1,3));
         vTAB_AVI.pro_pad_in_codigo := to_number(substr(cRCI.Rci_Id_Produto,4,3));
         vTAB_AVI.pro_in_codigo     := to_number(substr(cRCI.Rci_Id_Produto,7));
         vTAB_AVI.rci_re_qtdecom    := to_number(cRCI.Total_Avr);                  
         vSEQITN := vSEQITN+1;
         vTAB_AVI.iar_in_sequencial := vSEQITN;
         vTAB_AVI.rci_st_status     := 'A';         
         insert into cus_tb_api_itensavisoreceb values vTAB_AVI;         
         for cRCL in(
            select DECODE(EXISTSNODE(VALUE(L),'LOTE/RCI_ID_LOTE'),1,EXTRACTVALUE(VALUE(L), 'LOTE/RCI_ID_LOTE'),NULL) RCI_ID_LOTE,
                   TO_NUMBER(DECODE(EXISTSNODE(VALUE(L),'LOTE/FIL_IN_CODIGO'),1,EXTRACTVALUE(VALUE(L), 'LOTE/FIL_IN_CODIGO'),NULL)) FIL_IN_CODIGO,
                   TO_NUMBER(DECODE(EXISTSNODE(VALUE(L),'LOTE/AVR_IN_SEQUENCIA'),1,EXTRACTVALUE(VALUE(L), 'LOTE/AVR_IN_SEQUENCIA'),NULL)) AVR_IN_SEQUENCIA,
                   TO_NUMBER(DECODE(EXISTSNODE(VALUE(L),'LOTE/RCI_IN_SEQUENCIA'),1,EXTRACTVALUE(VALUE(L), 'LOTE/RCI_IN_SEQUENCIA'),NULL)) RCI_IN_SEQUENCIA,
                   DECODE(EXISTSNODE(VALUE(L),'LOTE/RCI_ID_PRODUTO'),1,EXTRACTVALUE(VALUE(L), 'LOTE/RCI_ID_PRODUTO'),NULL) RCI_ID_PRODUTO,
                   TO_NUMBER(DECODE(EXISTSNODE(VALUE(L),'LOTE/RCI_RE_QUANTIDADE'),1,EXTRACTVALUE(VALUE(L), 'LOTE/RCI_RE_QUANTIDADE'),NULL)) RCI_RE_QUANTIDADE,
                   DECODE(EXISTSNODE(VALUE(L),'LOTE/RCI_CH_STATUS'),1,EXTRACTVALUE(VALUE(L), 'LOTE/RCI_CH_STATUS'),NULL) RCI_CH_STATUS,
                   DECODE(EXISTSNODE(VALUE(L),'LOTE/RCI_ST_LOTE'),1,EXTRACTVALUE(VALUE(L), 'LOTE/RCI_ST_LOTE'),NULL) RCI_ST_LOTE,
                   DECODE(EXISTSNODE(VALUE(L),'LOTE/RCI_ST_REFERENCIA'),1,EXTRACTVALUE(VALUE(L), 'LOTE/RCI_ST_REFERENCIA'),NULL) RCI_ST_REFERENCIA,
                   DECODE(EXISTSNODE(VALUE(L),'LOTE/RCI_ST_DESCRICAO'),1,EXTRACTVALUE(VALUE(L), 'LOTE/RCI_ST_DESCRICAO'),NULL) RCI_ST_DESCRICAO
              from TABLE(xmlsequence(extract(xmltype(pXML),'PARAMS/LOTE'))) L
             where EXTRACTVALUE(VALUE(L), 'LOTE/RCI_ID_PRODUTO') = cRCI.Rci_Id_Produto
         )
         loop
            vSEQLOT := vSEQLOT+1;
            vTAB_AVL.org_tab_in_codigo := vTAB_AVI.Org_Tab_In_Codigo;
            vTAB_AVL.org_pad_in_codigo := vTAB_AVI.Org_Pad_In_Codigo;    
            vTAB_AVL.org_in_codigo     := vTAB_AVI.Org_In_Codigo;    
            vTAB_AVL.org_tau_st_codigo := vTAB_AVI.Org_Tau_St_Codigo;    
            vTAB_AVL.fil_in_codigo     := vTAB_AVI.Fil_In_Codigo;    
            vTAB_AVL.avr_in_sequencia  := vTAB_AVI.Avr_In_Sequencia;    
            vTAB_AVL.iar_in_sequencial := vTAB_AVI.Iar_In_Sequencial;    
            vTAB_AVL.lot_in_sequencia  := vSEQLOT;
            vTAB_AVL.mvl_st_loteforne  := cRCL.Rci_St_Lote;
            vTAB_AVL.mvl_st_referencia := cRCL.rci_st_referencia;    
            vTAB_AVL.lot_re_qtdecom    := cRCL.Rci_Re_Quantidade;        
            vTAB_AVL.lot_re_qtdeibm    := (to_number(adm_pck_utilidades.f_formatacaract(vTAB_AVL.mvl_st_referencia,'Comprimento_I'))*
                                           to_number(adm_pck_utilidades.f_formatacaract(vTAB_AVL.mvl_st_referencia,'Ponta_I'))*
                                           to_number(adm_pck_utilidades.f_formatacaract(vTAB_AVL.mvl_st_referencia,'Pé_I'))* 0.0000007854);            
            vTAB_AVL.lot_re_qtdebaixada := 0;
            vTAB_AVL.lot_ch_status := 'A';         
            insert into cus_tb_api_lotesavisoreceb values vTAB_AVL;            
         end loop;
         --sumariza itens do aviso
         for cSUM in(
            select sum(la.lot_re_qtdeibm) sum_re_qtdeibm 
              from cus_tb_api_lotesavisoreceb la
             where la.org_tab_in_codigo = vTAB_AVI.org_tab_in_codigo
               and la.org_pad_in_codigo = vTAB_AVI.org_pad_in_codigo
               and la.org_in_codigo     = vTAB_AVI.org_in_codigo    
               and la.org_tau_st_codigo = vTAB_AVI.org_tau_st_codigo
               and la.fil_in_codigo     = vTAB_AVI.fil_in_codigo    
               and la.avr_in_sequencia  = vTAB_AVI.avr_in_sequencia 
               and la.iar_in_sequencial = vTAB_AVI.iar_in_sequencial
            )
         loop
            vTAB_AVI.Rci_Re_Qtdeibm := cSUM.Sum_Re_Qtdeibm;
            update cus_tb_api_itensavisoreceb li
               set li.rci_re_qtdeibm = vTAB_AVI.rci_re_qtdeibm
             where li.org_tab_in_codigo = vTAB_AVI.org_tab_in_codigo
               and li.org_pad_in_codigo = vTAB_AVI.org_pad_in_codigo
               and li.org_in_codigo     = vTAB_AVI.org_in_codigo    
               and li.org_tau_st_codigo = vTAB_AVI.org_tau_st_codigo
               and li.fil_in_codigo     = vTAB_AVI.fil_in_codigo    
               and li.avr_in_sequencia  = vTAB_AVI.avr_in_sequencia 
               and li.iar_in_sequencial = vTAB_AVI.iar_in_sequencial;                
         end loop;
      end loop;
   end loop;
   commit;
   Open pRESULT For
        Select vTAB_AVR.Avr_In_Codigo as Avr_In_Codigo
          From DUAL;
end;
procedure P_testaxml is
v_XML clob;
v_RES TCURSOR;
begin
   v_XML:= '<PARAMS><AVISO><AVR_IN_SEQUENCIA>1</AVR_IN_SEQUENCIA><AVR_ST_USUARIO>0000041873</AVR_ST_USUARIO><AVR_DT_INCLUSAO>2024-08-25</AVR_DT_INCLUSAO><AVR_CH_STATUS>A</AVR_CH_STATUS><FIL_IN_CODIGO>31</FIL_IN_CODIGO><AVR_ST_ID></AVR_ST_ID></AVISO><ITENS><AVR_IN_SEQUENCIA>1</AVR_IN_SEQUENCIA><RCI_ID_PRODUTO>1000310000001</RCI_ID_PRODUTO><TOTAL_AVR>6.817</TOTAL_AVR></ITENS><LOTE><RCI_ID_LOTE>11</RCI_ID_LOTE><FIL_IN_CODIGO>31</FIL_IN_CODIGO><AVR_IN_SEQUENCIA>1</AVR_IN_SEQUENCIA><RCI_IN_SEQUENCIA>1</RCI_IN_SEQUENCIA><RCI_ID_PRODUTO>1000310000001</RCI_ID_PRODUTO><RCI_RE_QUANTIDADE>1.571</RCI_RE_QUANTIDADE><RCI_CH_STATUS>A</RCI_CH_STATUS><RCI_ST_LOTE>2024382400002001002002</RCI_ST_LOTE><RCI_ST_REFERENCIA>0000730=1822;0001750=1751;0000703=704;0001741=3808/2023;0001604=2000;0001605=2001;0001606=2002;0001600=60;0001601=50;0000019=800;0001746=60;0001747=50;0001749=800;</RCI_ST_REFERENCIA><RCI_ST_DESCRICAO>Cumaru em Toras</RCI_ST_DESCRICAO></LOTE><LOTE><RCI_ID_LOTE>12</RCI_ID_LOTE><FIL_IN_CODIGO>31</FIL_IN_CODIGO><AVR_IN_SEQUENCIA>1</AVR_IN_SEQUENCIA><RCI_IN_SEQUENCIA>2</RCI_IN_SEQUENCIA><RCI_ID_PRODUTO>1000310000001</RCI_ID_PRODUTO><RCI_RE_QUANTIDADE>1.571</RCI_RE_QUANTIDADE><RCI_CH_STATUS>A</RCI_CH_STATUS><RCI_ST_LOTE>2024382400002001002002</RCI_ST_LOTE><RCI_ST_REFERENCIA>0000730=1822;0001750=1751;0000703=704;0001741=3808/2023;0001604=2000;0001605=2001;0001606=2002;0001600=60;0001601=50;0000019=800;0001746=60;0001747=50;0001749=800;</RCI_ST_REFERENCIA><RCI_ST_DESCRICAO>Cumaru em Toras</RCI_ST_DESCRICAO></LOTE><LOTE><RCI_ID_LOTE>13</RCI_ID_LOTE><FIL_IN_CODIGO>31</FIL_IN_CODIGO><AVR_IN_SEQUENCIA>1</AVR_IN_SEQUENCIA><RCI_IN_SEQUENCIA>3</RCI_IN_SEQUENCIA><RCI_ID_PRODUTO>1000310000001</RCI_ID_PRODUTO><RCI_RE_QUANTIDADE>1.979</RCI_RE_QUANTIDADE><RCI_CH_STATUS>A</RCI_CH_STATUS><RCI_ST_LOTE>2024390100002003002004</RCI_ST_LOTE><RCI_ST_REFERENCIA>0000730=1822;0001750=1751;0000703=704;0001741=3808/2023;0001604=2002;0001605=2003;0001606=2004;0001600=70;0001601=60;0000019=700;0001746=70;0001747=60;0001749=700;</RCI_ST_REFERENCIA><RCI_ST_DESCRICAO>Cumaru em Toras</RCI_ST_DESCRICAO></LOTE><LOTE><RCI_ID_LOTE>14</RCI_ID_LOTE><FIL_IN_CODIGO>31</FIL_IN_CODIGO><AVR_IN_SEQUENCIA>1</AVR_IN_SEQUENCIA><RCI_IN_SEQUENCIA>4</RCI_IN_SEQUENCIA><RCI_ID_PRODUTO>1000310000001</RCI_ID_PRODUTO><RCI_RE_QUANTIDADE>1.696</RCI_RE_QUANTIDADE><RCI_CH_STATUS>A</RCI_CH_STATUS><RCI_ST_LOTE>2024390100002005002006</RCI_ST_LOTE><RCI_ST_REFERENCIA>0000730=1822;0001750=1751;0000703=704;0001741=3808/2023;0001604=2004;0001605=2005;0001606=2006;0001600=65;0001601=60;0000019=600;0001746=65;0001747=60;0001749=600;</RCI_ST_REFERENCIA><RCI_ST_DESCRICAO>Cumaru em Toras</RCI_ST_DESCRICAO></LOTE></PARAMS>';
   begin
      -- Call the procedure
      apt_intprod2.p_geraavisorecebimento(v_XML,
                                          v_RES);
   end;    
end;
procedure p_cria_demandamanual is
begin
   vTAB_APT.Apt_In_Sequencia := 441682;
   p_cria_demanda;
end;
procedure p_atualizatotalapto is
begin
   vTAB_APT.Apt_In_Sequencia := 394771;
   p_SumarizaLotes(vTAB_APT.Apt_In_Sequencia);
end;

  procedure p_gerademandaslotesmanual is
    vDADOS TCURSOR;
  begin
     for cAPT in(
        select apt.*
          from apt_apontaordem apt
         where apt.org_in_codigo = 301
           and apt.ord_in_codigo = 66476)
     loop
        for cMVD in(
           select ord.*
             from cus_tb_66476 ord
            where ord.org_in_codigo = cAPT.org_in_codigo
              and ord.ord_in_codigo = cAPT.ord_in_codigo
              and not exists
                  (select 1
                     from apt_apontademanda_estoque mvo
                    where mvo.org_in_codigo = ord.org_in_codigo
                      and mvo.ord_in_codigo = ord.ord_in_codigo
                      and mvo.com_in_codigo = ord.com_in_codigo
                      and mvo.mvs_st_loteforne = ord.mvl_st_loteforneo)
        )
        loop
           begin
              -- Call the procedure
              apt_intprod2.p_inseredemanda_lotespro(vDADOS,
                                        cAPT.Fil_In_Codigo,
                                        cAPT.Ord_In_Codigo,
                                        cAPT.Ctl_In_Codigo,
                                        cAPT.Plf_In_Sqoperacao,
                                        TRUNC(SYSDATE),
                                        NULL,
                                        cMVD.Mvl_St_Loteforneo,
                                        cMVD.Emm_Re_Qtd,
                                        null,
                                        null,
                                        '30200664760500',
                                        cMVD.Com_In_Codigo);
           end;
        end loop;
     end loop;
  end;

/*
  -- Initialization
  <Statement>;*/
end apt_intprod2;
