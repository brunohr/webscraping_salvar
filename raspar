import pandas as pd
import numpy as np
from pathlib import Path
from collections import deque

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options

import requests
from requests.exceptions import ReadTimeout, Timeout, RequestException, ConnectTimeout

from lxml import html

from datetime import datetime, date, time, timezone, timedelta
import time as time_aux

import os, glob, warnings
import zipfile
import pyodbc
import tempfile

import folium
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.colors as mcolors
import geopandas as gpd

from concurrent.futures import ThreadPoolExecutor

from IPython.display import clear_output

global CAMINHO
global OUTPUT_DIR

global LOGIN_SALVAR
global SENHA_SALVAR

CAMINHO = Path(r"")
OUTPUT_DIR = Path(r'')


def raspar(LOGIN, SENHA, CAMINHO, headless = False):
    
    edge_service = Service(executable_path=r'C:/Users/x20597602/selenium/msedgedriver.exe')
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Edge(service=edge_service, options=options)

    while True:
        
        driver.get('https://salvar.cemaden.gov.br/salvar/restrito/meteorologia/index.jsf?c=3&o=asc&nets=1-11-3&uf=MG')
        # time_aux.sleep(1)   
            
        try:
            driver.find_element("id", "j_username").send_keys(LOGIN)
            driver.find_element("id", "j_password").send_keys(SENHA)
            driver.find_element("id", "j_password").send_keys(Keys.RETURN)
            time_aux.sleep(1)
        except NoSuchElementException:
            pass
        
        try:
            WebDriverWait(driver, 10).until(lambda d: d.find_element('id', 'tituloAtualizacao').text != '')

            listaLink = set()
            auxInfo = []
            codigos_vistos = set()
            auxTam = -1
            break
        
        except TimeoutException:
            pass

    while len(set(codigos_vistos)) > auxTam:
        auxTam = len(set(codigos_vistos))
        page = driver.page_source
        tree = html.fromstring(page)

        rows = tree.xpath("//table[@id='infopcds']//tbody/tr")

        for row in rows:
            cells = [c.text_content().strip() for c in row.xpath(".//td")]

            rede   = cells[0]
            cidade = cells[3]
            nome   = cells[4]
            link   = cells[-2]
            codigo = cells[-1]
            link   = row.xpath(".//a[@name='linkPeriodo']/@href")[0].split("&")[0]
            
            try:
                data = datetime.strptime(cells[5], "%d/%m/%Y %H:%M")
            except Exception:
                data = None

            if codigo in codigos_vistos:
                # print("duplicado")
                continue

            codigos_vistos.add(codigo)

            auxInfo.append([
                codigo,
                nome,
                cidade,
                rede,
                data,
                link
            ])
        
        # print(auxTam, len(codigos_vistos))
        
        ActionChains(driver).move_to_element(driver.find_elements("xpath", "//a[@name='linkPeriodo']")[-1]).perform()
        
    df_info = pd.DataFrame(auxInfo, columns=["codigo_estacao", "nome", "municipio", "rede", "data", "link"]).reset_index(drop=True)
    # df_info.to_excel(CAMINHO / f"dados_estacoes_salvar_{datetime.today().strftime('%Y%m%d_%H%M%S')}.xlsx", index=False)
    # df_info

    links = df_info[df_info["data"] >= pd.to_datetime(date.today()) + pd.Timedelta(hours=3)]["link"].to_list() ###df_info.query("data >= @date.today()")["link"].to_list()
    I = len(links)
    # links

    i = 0
    auxDf = []

    # link_datainicial = int(datetime.combine(date.today(), time(3, 0)).timestamp() * 1000)
    # link_datafinal = int(datetime.combine(date.today()+timedelta(days=1), time(2, 59)).timestamp() * 1000)
    
    link_datainicial = round((datetime.now() - timedelta(hours=24-3)).timestamp()*1000)
    link_datafinal = round((datetime.now() + timedelta(hours=3)).timestamp()*1000)
            
    # link_datainicial = round((datetime.strptime('2026-06-26 03:00', "%Y-%m-%d %H:%M")).timestamp()*1000)
    # link_datafinal = round((datetime.strptime('2026-05-01 02:59', "%Y-%m-%d %H:%M")).timestamp()*1000)
    
    print(f"SALVAR: {I} estações válidas")        
            
    while len(links):
    # for i in range(1):
        link = links[0]#.split("&")[0]
        if True:
            # link_datafinal = link.split("dh=")[1].split("&")[0]
            # link_datainicial = int(link_datafinal) - 432000000 ##### 5 DIAS

            ##### SITE É UTC
            # link_datainicial = int(datetime(2025, 10, 1, 3, 0, 0).timestamp() * 1000) ##### 2025/10/01 03:00:00
            # link_datafinal = int(datetime(2026, 4, 1, 2, 59, 59).timestamp() * 1000) #2026/04/01 02:59:59
            
            # driver.get(link+"&idh="+str(link_datainicial)+"&dh="+str(link_datafinal)+"&pe=1&es=1")

            url = ("https://salvar.cemaden.gov.br"
                f"{link}"
                f"&idh={link_datainicial}"
                f"&dh={link_datafinal}"
                f"&pe=1"
                f"&es=1"
            )
                        
            driver.get(url)
            
            MAX_RETRY = 5
            for tentativa in range(MAX_RETRY):
                try:
                    # =====================================================
                    # espera tabela carregar
                    # =====================================================

                    wait = WebDriverWait(driver, 30)
                    wait.until(EC.presence_of_element_located((By.ID, "periodoTable")))
                    wait.until_not(EC.text_to_be_present_in_element((By.CLASS_NAME, "dataTables_empty"), "Carregando"))

                    # =====================================================
                    # id estação
                    # =====================================================

                    # =====================================================
                    # parse HTML
                    # =====================================================

                    tree = html.fromstring(driver.page_source)

                    # =====================================================
                    # verifica vazio
                    # =====================================================

                    mensagem = tree.xpath("//td[contains(@class,'dataTables_empty')]/text()")

                    if mensagem and "Nenhum" in mensagem[0]:
                        break
                    
                    else:
                        rows = tree.xpath("//table[@id='periodoTable']//tbody/tr")

                        for row in rows:

                            tds = row.xpath('./td')

                            datahora = tds[0].xpath('string(.)').strip()
                            chuva = tds[1].xpath('string(.)').strip()
                            status = tds[2].xpath('string(.)').replace('\xa0', '').strip()

                            valores = [datahora, chuva, status]

                            # =============================================
                            # data
                            # =============================================

                            try:
                                datahora = datetime.strptime(valores[0], "%d/%m/%Y %H:%M")
                            except:
                                continue #### PRA REMOVER LINHA EM BRANCO OU DE TOTAL

                            # =============================================
                            # chuva
                            # =============================================

                            chuva_mm = float(valores[1].replace(",", "."))
                            qualificacao = valores[2]

                            auxDf.append([
                                # estacao_id,
                                link,
                                datahora,
                                chuva_mm,
                                qualificacao if qualificacao != '' else None,
                            ])

                    print(f"SALVAR: {link}: {i+1}/{I}")
                    
                    break

                except TimeoutException:
                    print(f"SALVAR: Tentativa {tentativa+1}/{MAX_RETRY}")
                    driver.refresh()

            else:
                print(f"SALVAR: {link} falhou após {MAX_RETRY} tentativas")
        
            links.pop(0)
            i += 1
        
    try:
        driver.find_element('xpath', '//*[@id="expandmenu"]/ul/li[1]/div/a/input').click()
    except ElementNotInteractableException:
        pass
    driver.quit()    
    
    
    df_info["coleta"] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    # ##### BAIXAR INVENTARIO EM https://www.snirh.gov.br/hidroweb/download
    # with zipfile.ZipFile(CAMINHO / fr"Inventario.zip", 'r') as z:

    #     # encontra o .mdb dentro do zip
    #     mdb_name = [f for f in z.namelist() if f.endswith(".mdb")][0]

    #     # extrai para arquivo temporário
    #     with tempfile.NamedTemporaryFile(delete=False, suffix=".mdb") as tmp:
    #         tmp.write(z.read(mdb_name))
    #         mdb_path = tmp.name

    # # conexão Access
    # conn = pyodbc.connect(
    #     rf"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_path};"
    # )

    # # leitura via SQL
    # query = "SELECT codigo AS codigo_estacao, latitude, longitude FROM Estacao"

    # df = pd.read_sql(query, conn)

    # conn.close()
    # os.remove(mdb_path)
    
    df_dados_24h = (pd.DataFrame(auxDf, columns=["link", "datahora_utc", "chuva_mm", "qualificacao"])
                    .merge(df_info[["link", "codigo_estacao"]], how="left", on="link")
                    [["codigo_estacao", "datahora_utc", "chuva_mm", "qualificacao"]]
                )
    try:
        base = pd.read_parquet(CAMINHO / "medicoes_salvar.parquet")
        print(CAMINHO / "medicoes_salvar.parquet")
        df = (pd.concat(
            [base, df_dados_24h],
            ignore_index=True
        ))
        auxFlag = True
    except FileNotFoundError as e:
        print(e)
        df = df_dados_24h.copy()
        
    df_dados = (df
                # .fillna(None).replace("", None)
                .sort_values(["codigo_estacao", "datahora_utc"])
                .drop_duplicates()
                .reset_index(drop=True))
        
    df_info = df_info.merge(pd.read_excel(CAMINHO / r"CODIGOS_SALVAR_MG_v2.xlsx"), on="codigo_estacao", how="left")
    df_info.to_parquet(CAMINHO / f"estacoes_salvar_{datetime.today().strftime('%Y%m%d%H%M%S')}.parquet", index=False)
    (pd.concat([df_info, pd.read_parquet(CAMINHO / "estacoes_salvar.parquet")], ignore_index=True)
     .sort_values(['codigo_estacao', 'coleta'])
     .drop_duplicates(subset="codigo_estacao", keep="last")
     .to_parquet(CAMINHO / "estacoes_salvar.parquet", index=False)
    )
    # df_dados   
    df_dados_24h.to_parquet(CAMINHO / f"medicoes_salvar_{datetime.today().strftime('%Y%m%d%H%M%S')}.parquet", index=False)
    print(CAMINHO / f"medicoes_salvar_{datetime.today().strftime('%Y%m%d%H%M%S')}.parquet")
    if auxFlag:
        df_dados.to_parquet(CAMINHO / f"medicoes_salvar.parquet", index=False)
    
    return df_dados_24h, df_dados, df_info

def calculos(PATH, OUTPUT_DIR, IMPRIME = False):
        ######################################################################################################################
    ##############                                                                                          ##############
    ##############   SCRIPT CRIADO PARA PLOTAR ACUMULADO MENSAL DE CHUVA DOS PLUVIOMETROS INMET E CEMADEN   ##############
    ##############      DESENVOLVIDO POR: ROMERO WANZELER E CAROLINE DE SA (METEOROLOGISTAS DO CINDEC)      ##############
    ##############      ADAPTADO POR: BRUNO H RODRIGUES, MSC. (ANALSITA DE DADOS DO CINDEC)                 ##############
    ##############                                    EM: 26/05/2026                                        ##############
    ##############                                                                                          ##############
    ######################################################################################################################
    # --------------------------------------------------------------------------------------------------------------------
    # CÉLULA 1
    # --------------------------------------------------------------------------------------------------------------------
    # %pip install -q scipy pykrige descartes contextily rasterio
    # --------------------------------------------------------------------------------------------------------------------
    # CÉLULA 2
    # --------------------------------------------------------------------------------------------------------------------
    # import pandas as pd
    # import numpy as np
    # import os, glob, warnings
    # import folium
    # from matplotlib.colors import ListedColormap, BoundaryNorm
    # import matplotlib.colors as mcolors
    # import geopandas as gpd
    # from pathlib import Path

    warnings.filterwarnings('ignore')
    # print('Bibliotecas carregadas.')
    # --------------------------------------------------------------------------------------------------------------------
    # CÉLULA 3
    # --------------------------------------------------------------------------------------------------------------------
    # # Arquivos
    # CEMADEN_PATH    = r'C:\Users\x20597602\Downloads\ideia_final\dados\cemaden\cemaden_*.csv'
    # INMET_PATH      = r'C:\Users\x20597602\Downloads\ideia_final\dados\inmet\*.csv'
    # # PATH = r'C:\Users\x20597602\Downloads\dados_salvar'

    # # Shapefiles (faça upload do .shp e arquivos auxiliares no /content/)
    # shape_mg     = r'C:\Users\x20597602\Downloads\ideia_final\QGIS_projeto_e_shapes\MG_Mesorregioes_2022.shp'
    # SHAPE_MICRO  = r'C:\Users\x20597602\Downloads\ideia_final\QGIS_projeto_e_shapes\MG_Microrregioes_2022.shp'
    # SHAPE_BRASIL = r'C:\Users\x20597602\Downloads\ideia_final\QGIS_projeto_e_shapes\BR_UF_2022.shp'
    shape_mg     = OUTPUT_DIR.parent / "QGIS_projeto_e_shapes" / "MG_Mesorregioes_2022.shp"
    SHAPE_MICRO  = OUTPUT_DIR.parent / "QGIS_projeto_e_shapes" / "MG_Microrregioes_2022.shp"
    SHAPE_BRASIL = OUTPUT_DIR.parent / "QGIS_projeto_e_shapes" / "BR_UF_2022.shp"

    # Método de interpolação: 'idw' (rápido) ou 'kriging' (mais preciso)
    METODO_INTERP   = 'idw'

    # Resolução da grade em graus (0.05 ≈ 5 km | 0.1 ≈ 10 km)
    RESOLUCAO_GRADE = 0.05

    # Expoente IDW
    IDW_POWER = 2

    # Limite superior fixo da escala de cor (None = automático por mês)
    VMAX_FIXO = None

    # Estações excluídas manualmente (dados não confiáveis)
    # Formato: {codigo_estacao: "motivo"}
    ESTACOES_EXCLUIDAS = {
        "314390608A": "Estação Barra/Muriaé — leituras inconsistentes",
        "314390604A": "Estação Centro/Muriaé — leituras inconsistentes",
        "58652000": "Estação UHE ILHA DOS POMBOS BARRAMENTO — leituras inconsistentes",
        "56651000": "Estação Pch São Gonçalo Montante 1 — leituras inconsistentes",
        "61268700": "Estação PCH NINHO DA ÁGUIA MONTANTE — leituras inconsistentes",
        "55566000": "Estação Pch Mucuri Barramento — leituras inconsistentes",
        
    }

    MES_ATUAL = [datetime.now().strftime(format = '%Y-%m')]
    # MES_ATUAL = ['2026-04', '2026-05', '2026-06']
    # MES_ATUAL = ['2026-06', '2026-07']

    # OUTPUT_DIR = r'C:\Users\x20597602\Downloads\ideia_final\saidas'
    os.makedirs(OUTPUT_DIR / 'mapas', exist_ok=True)
    if IMPRIME:
        print('Configuração OK.')
    # --------------------------------------------------------------------------------------------------------------------
    # CÉLULA 4 (AJUSTADA)
    # --------------------------------------------------------------------------------------------------------------------

    BRT_OFFSET = pd.DateOffset(hours=-3)

    # --------------------------
    # utilidades
    # --------------------------
    def _float_br(s):
        return pd.to_numeric(
            s.astype(str)
            .str.strip()
            .str.replace('.', '', regex=False)   # remove separador milhar
            .str.replace(',', '.', regex=False),
            errors='coerce'
        )

    def _safe_float(x):
        try:
            return float(str(x).replace(',', '.'))
        except:
            return np.nan

    def _add_brt(df):
        df['datahora_brt'] = df['datahora_utc'] + BRT_OFFSET
        df['ano_mes_brt']  = df['datahora_brt'].dt.to_period('M').astype(str)
        df['data_brt']     = df['datahora_brt'].dt.date
        return df

    def ler_salvar(path):
        
        ##### BAIXAR INVENTARIO EM https://www.snirh.gov.br/hidroweb/download
        # with zipfile.ZipFile(Path(path) / fr"Inventario.zip", 'r') as z:

        #     # encontra o .mdb dentro do zip
        #     mdb_name = [f for f in z.namelist() if f.endswith(".mdb")][0]

        #     # extrai para arquivo temporário
        #     with tempfile.NamedTemporaryFile(delete=False, suffix=".mdb") as tmp:
        #         tmp.write(z.read(mdb_name))
        #         mdb_path = tmp.name

        # # conexão Access
        # conn = pyodbc.connect(
        #     rf"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_path};"
        # )
        # # leitura via SQL
        # query = """
        #     SELECT
        #         e.Codigo AS codigo_estacao,
        #         e.CodigoAdicional,
        #         e.Nome AS nome_estacao,
        #         m.CodigoIBGE,
        #         m.Nome AS nome_municipio,
        #         est.Sigla AS nome_estado,
        #         e.Latitude,
        #         e.Longitude,
        #         e.Altitude
        #     FROM
        #         (Estacao e
        #         LEFT JOIN Municipio m
        #             ON m.Codigo = e.MunicipioCodigo)
        #         LEFT JOIN Estado est
        #             ON m.EstadoCodigo = est.Codigo
        #     WHERE
        #         m.CodigoIBGE IS NOT NULL
        #         AND est.CodigoIBGE >= 1;
        #     """

        # df_info = pd.read_sql(query, conn)

        # conn.close()
        # os.remove(mdb_path)
        
        df_info = pd.concat(
            pd.read_parquet(parquet_file) for parquet_file in Path(path).glob("estacoes_salvar_*.parquet")
        ).sort_values(["codigo_estacao", "coleta"]).drop_duplicates(subset="codigo_estacao", keep="last")
        
        df_dados = pd.read_parquet(Path(path) / "medicoes_salvar.parquet").drop_duplicates(subset=["codigo_estacao", "datahora_utc"], keep="last")
        
        return df_info, _add_brt(df_dados)

    if IMPRIME:
        print('✅ Funções definidas (ajustadas e robustas)')


    # --------------------------------------------------------------------------------------------------------------------
    # CÉLULA 5
    # --------------------------------------------------------------------------------------------------------------------
    
    df_info, df = ler_salvar(PATH)

    # Remove estações da lista de exclusão manual
    if ESTACOES_EXCLUIDAS:
        mask_excl = df["codigo_estacao"].isin(ESTACOES_EXCLUIDAS.keys())
        n_excl    = mask_excl.sum()
        df        = df[~mask_excl].reset_index(drop=True)
        # df        = (df
        #              .query('not (codigo_estacao == ["314390608A", "314390604A"] or (ano_mes_brt == "2026-04" and codigo_estacao == ["58652000", "56651000", "61268700", "55566000"]))')  
        #     .reset_index(drop=True))
        
        if IMPRIME:
            print(f"Estações excluídas manualmente: {list(ESTACOES_EXCLUIDAS.keys())} → {n_excl:,} registros removidos")

    if IMPRIME:
        print(f'\nTotal: {len(df):,} registros')
        print(f'Período BRT: {df["datahora_brt"].min()} → {df["datahora_brt"].max()}')
        print(f'Meses (BRT): {sorted(df["ano_mes_brt"].unique())}')
    
    # --------------------------------------------------------------------------------------------------------------------
    # CÉLULA 5B
    # --------------------------------------------------------------------------------------------------------------------
    # ─── PARÂMETROS DE QC ────────────────────────────────────────────────────────

    # CEMADEN mede a cada ~10 min, INMET a cada 1 hora
    CHUVA_MAX_CEMADEN = 100   # mm por leitura (~10 min)
    CHUVA_MAX_INMET   = 150   # mm por hora
    CHUVA_MAX_ANA = 100   # mm por leitura (~15 min) — mesmo critério do CEMADEN

    # ─────────────────────────────────────────────────────────────────────────────

    df_qc = df.copy().query("ano_mes_brt == @MES_ATUAL")
    n_inicial = len(df_qc)

    codigos_cemaden = df_info.query("rede == 'CEMADEN'")["codigo_estacao"].to_list()
    codigos_inmet = df_info.query("rede == 'INMET'")["codigo_estacao"].to_list()
    codigos_ana = df_info.query("rede == 'ANA'")["codigo_estacao"].to_list()

    # Remove registros acima do limite físico por fonte
    # mask_cemaden = (df_qc['fonte'] == 'CEMADEN') & (df_qc['chuva_mm'] > CHUVA_MAX_CEMADEN)
    # mask_inmet   = (df_qc['fonte'] == 'INMET')   & (df_qc['chuva_mm'] > CHUVA_MAX_INMET)

    # mask_cemaden = (df_qc.query("codigo_estacao == @codigos_cemaden and chuva_mm > @CHUVA_MAX_CEMADEN"))
    # mask_inmet   = (df_qc.query("codigo_estacao == @codigos_cemaden and chuva_mm > @CHUVA_MAX_INMET"))
    # removidos    = df_qc[mask_cemaden | mask_inmet].copy()
    removidos = df_qc.query("(codigo_estacao == @codigos_cemaden and chuva_mm > @CHUVA_MAX_INMET) or (codigo_estacao == @codigos_inmet and chuva_mm > @CHUVA_MAX_INMET) or (codigo_estacao == @codigos_ana and chuva_mm > @CHUVA_MAX_ANA)").copy()
    df_qc = df_qc.query("not (codigo_estacao == @codigos_cemaden and chuva_mm > @CHUVA_MAX_INMET) and not (codigo_estacao == @codigos_inmet and chuva_mm > @CHUVA_MAX_INMET) and not (codigo_estacao == @codigos_ana and chuva_mm > @CHUVA_MAX_ANA)")

    n_removidos = len(removidos)
    pct = n_removidos / n_inicial * 100

    # ─── Relatório ────────────────────────────────────────────────────────────────
    linhas = []
    linhas.append('RELATÓRIO DE QUALIDADE (QC) — LIMITE FÍSICO')
    linhas.append('=' * 60)
    linhas.append(f'Gerado em: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}')
    linhas.append(f'Limite CEMADEN: {CHUVA_MAX_CEMADEN} mm/leitura')
    linhas.append(f'Limite INMET:   {CHUVA_MAX_INMET} mm/hora')
    linhas.append('=' * 60)
    linhas.append(f'Registros analisados: {n_inicial:,}')
    linhas.append(f'Registros removidos:  {n_removidos:,} ({pct:.1f}%)')
    linhas.append(f'Registros aprovados:  {len(df_qc):,}')
    linhas.append('\n--- REGISTROS REMOVIDOS ---')

    if len(removidos) == 0:
        linhas.append('Nenhum registro removido.')
    else:
        removidos = removidos.merge(df_info[["codigo_estacao", "rede", "nome"]], how="left", on="codigo_estacao")
        for _, r in removidos.iterrows():
            linhas.append(
                f"  [{r['rede']}] {r['codigo_estacao']} | {r['nome']} | "
                f"UTC={r['datahora_utc']} | BRT={r['datahora_brt']} | {r['chuva_mm']} mm"
            )

    relatorio_path = f'{OUTPUT_DIR}/relatorio_qc.txt'
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linhas))

    if IMPRIME:
        print('\n'.join(linhas))
        print(f'\nRelatório salvo em: {relatorio_path}')

    # Substitui df pelo df filtrado para as células seguintes
    df = df_qc

    # # --------------------------------------------------------------------------------------------------------------------
    # # CÉLULA 6
    # # --------------------------------------------------------------------------------------------------------------------
    # df[['fonte','codigo_estacao','datahora_utc','datahora_brt','ano_mes_brt','data_brt','chuva_mm']].head(6)

    # --------------------------------------------------------------------------------------------------------------------
    # CÉLULA 7  —  Agrega: mensal  +  diário (com janelas móveis)
    # --------------------------------------------------------------------------------------------------------------------
    # ── Acumulado mensal (inalterado) ─────────────────────────────────────────────
    df_mensal = (
        # df.groupby(['ano_mes_brt','fonte','codigo_estacao','nome_estacao',
                    #'municipio','uf','latitude','longitude'
        df.groupby(['ano_mes_brt','codigo_estacao',])
        .agg(chuva_acum_mm=('chuva_mm','sum'),
            chuva_max_mm =('chuva_mm','max'),
            n_medicoes   =('chuva_mm','count'))
        .reset_index()
    )
    if IMPRIME:
        print(f'df_mensal → {len(df_mensal):,} linhas | {df_mensal["ano_mes_brt"].nunique()} meses')

    # ── Janelas móveis por estação (sobre datahora_brt) ─────────────────────────────
    # Ordena por estação e horário, define o índice temporal para o rolling
    df_sorted = (df.dropna(subset=['chuva_mm','datahora_brt'])
                .sort_values(['codigo_estacao','datahora_brt'])
                .copy())
    df_sorted = df_sorted.set_index('datahora_brt')

    def _max_rolling_com_periodo(grupo, janela_str, duracao):
        """
        Soma rolante de `janela_str` sobre o grupo.
        Retorna valor_maximo, horario_inicio e horario_fim, onde:
        - horario_fim    = indice (datahora_brt) do ponto com soma maxima
        - horario_inicio = horario_fim - duracao
        """
        serie   = grupo['chuva_mm'].rolling(janela_str, min_periods=1).sum()
        idx_max = serie.idxmax()
        return pd.Series({
            'valor': serie[idx_max],
            't_ini': idx_max - duracao + pd.Timedelta('60min'),
            't_fim': idx_max + pd.Timedelta('60min'),
        })

    def _fmt_hm(ts):
        """Formata Timestamp como 'XXhYYmin'."""
        return ts.strftime('%Hh%Mmin')

    def _calcular_janela(grupos, janela_str, duracao, prefixo):
        """
        Aplica _max_rolling_com_periodo e devolve DataFrame com:
        {prefixo}_mm      -> valor acumulado maximo
        {prefixo}_periodo -> string 'entre XXhYYmin e XXhYYmin'
        """
        res = grupos.apply(lambda g: _max_rolling_com_periodo(g, janela_str, duracao))
        res = res.reset_index()
        
        #### GARANTIR QUE É NÚMERO
        res['valor'] = pd.to_numeric(res['valor'], errors='coerce')

        res[f'{prefixo}_mm']      = res['valor'].round(1)
        res[f'{prefixo}_periodo'] = (
            'entre ' + res['t_ini'].apply(_fmt_hm) +
            ' e '    + res['t_fim'].apply(_fmt_hm)
        )
        return res[['codigo_estacao', 'data_brt', f'{prefixo}_mm', f'{prefixo}_periodo']]

    # Calcula as três janelas agrupadas por estação + dia
    grupos = df_sorted.groupby(['codigo_estacao', 'data_brt'])

    df_j30 = _calcular_janela(grupos, '30min',  pd.Timedelta('30min'),  'acum_max_30min')
    df_j1h = _calcular_janela(grupos, '60min',  pd.Timedelta('60min'),  'acum_max_1h')
    df_j2h = _calcular_janela(grupos, '120min', pd.Timedelta('120min'), 'acum_max_2h')

    df_janelas = (df_j30
                .merge(df_j1h, on=['codigo_estacao','data_brt'], how='outer')
                .merge(df_j2h, on=['codigo_estacao','data_brt'], how='outer'))

    # ── Acumulado diário (soma total) ─────────────────────────────────────────────
    df_diario = (
        # df.groupby(['data_brt','ano_mes_brt','fonte','codigo_estacao','nome_estacao',
                    #'municipio','uf','latitude','longitude'
                    df.groupby(['codigo_estacao', 'data_brt','ano_mes_brt'])
        .agg(chuva_acum_mm=('chuva_mm','sum'))
        .reset_index()
    )

    # Junta as janelas móveis
    df_diario = df_diario.merge(df_janelas, on=['codigo_estacao','data_brt'], how='left')

    # Converte data_brt para string (yyyy-mm-dd) para facilitar filtragem no dashboard
    df_diario['data_brt'] = df_diario['data_brt'].astype(str)

    # ── QC diário: remove acumulados acima do limite físico (300 mm/dia) ─────────────
    CHUVA_MAX_DIA = 300  # mm/dia

    mask_dia_invalida = df_diario['chuva_acum_mm'] > CHUVA_MAX_DIA
    removidos_dia     = df_diario[mask_dia_invalida].copy()
    df_diario         = df_diario[~mask_dia_invalida].reset_index(drop=True)

    # Registra no relatório de QC
    if len(removidos_dia) > 0:
        linhas_qc = ['\n--- QC DIÁRIO: ACUMULADO > 300 mm/dia ---']
        removidos_dia = removidos_dia.merge(df_info[["codigo_estacao", "rede", "nome"]], how="left", on="codigo_estacao")
        for _, r in removidos_dia.iterrows():
            linhas_qc.append(
                f"  [{r['rede']}] {r['codigo_estacao']} | {r['nome']} | "
                f"data={r['data_brt']} | {r['chuva_acum_mm']:.1f} mm"
            )
        with open(relatorio_path, 'a', encoding='utf-8') as f:
            f.write('\n'.join(linhas_qc))
        if IMPRIME:
            print(f'QC diário: {len(removidos_dia)} registro(s) removido(s) (acumulado > {CHUVA_MAX_DIA} mm/dia)')
    else:
        if IMPRIME:
            print('QC diário: nenhum registro removido.')
    if IMPRIME:
        print(f'df_diario → {len(df_diario):,} linhas | {df_diario["data_brt"].nunique()} dias únicos')
        # print(df_diario.head())

    # ── Série horária BRT (acumulado por hora) ─────────────────────────────
    # Trunca datahora_brt na hora e soma leituras — unifica CEMADEN (~10min) e INMET (1h).
    _df_h = df.copy()
    _df_h['hora_brt'] = _df_h['datahora_brt'].dt.floor('h') + pd.Timedelta('60min')
    _df_h['data_brt'] = _df_h['datahora_brt'].dt.date.astype(str)

    serie_horaria = (
        # _df_h.groupby(['data_brt','codigo_estacao','nome_estacao', 'fonte',
        #                #'municipio','fonte','latitude','longitude',
        #                'hora_brt'])
        _df_h.groupby(['codigo_estacao', 'data_brt', 'hora_brt'])
        .agg(chuva_mm=('chuva_mm','sum'))
        .reset_index()
    )
    serie_horaria['hora_brt'] = serie_horaria['hora_brt'].dt.strftime('%H:%M')
    serie_horaria['ano_mes_brt'] = serie_horaria['data_brt'].str[:7]
    if IMPRIME:
        print(f'serie_horaria → {len(serie_horaria):,} linhas')

    # CÉLULA 8
    # --------------------------------------------------------------------------------------------------------------------
    def idw(lon, lat, vals, lon_g, lat_g, power=2):
        from scipy.spatial import cKDTree
        tree = cKDTree(np.c_[lon, lat])
        glon, glat = np.meshgrid(lon_g, lat_g)
        d, ix = tree.query(np.c_[glon.ravel(), glat.ravel()], k=min(12, len(lon)))
        d = np.where(d == 0, 1e-10, d)
        w = 1 / d**power
        z = (w * vals[ix]).sum(1) / w.sum(1)
        return z.reshape(glat.shape)

    def kriging(lon, lat, vals, lon_g, lat_g):
        from pykrige.ok import OrdinaryKriging
        ok = OrdinaryKriging(lon, lat, vals, variogram_model='spherical',
                            verbose=False, enable_plotting=False)
        z, _ = ok.execute('grid', lon_g, lat_g)
        return np.array(z)

    if IMPRIME:
        print('Funções de interpolação definidas.')
    # --------------------------------------------------------------------------------------------------------------------
    # CÉLULA 9
    # --------------------------------------------------------------------------------------------------------------------
    from scipy.ndimage import distance_transform_edt, gaussian_filter
    from shapely.geometry import Point

    # Carrega shapefile (definido como string na Célula 3)
    shape_mg     = gpd.read_file(shape_mg).to_crs(epsg=4326)
    shape_brasil = gpd.read_file(SHAPE_BRASIL).to_crs(epsg=4326)
    shape_micro = gpd.read_file(SHAPE_MICRO).to_crs(epsg=4326)

    # ── Spatial join: associa cada estação à sua Mesorregião ─────────────────────
    # Detecta a coluna de NOME da mesorregião no shapefile (ex: NM_MESO do IBGE)
    # Prioriza colunas que contenham "nm_" + "meso", depois "nome" + "meso", depois qualquer "meso"
    _col_meso = next(
        (c for c in shape_mg.columns if c.lower().startswith("nm_") and "meso" in c.lower()),
        next(
            (c for c in shape_mg.columns if "nome" in c.lower() and "meso" in c.lower()),
            next(
                (c for c in shape_mg.columns if "meso" in c.lower() and not c.lower().startswith("cd_")),
                shape_mg.columns[0]
            )
        )
    )
    if IMPRIME:
        print(f'Coluna de mesorregião detectada: {_col_meso} | Valores únicos: {shape_mg[_col_meso].unique()[:5]}')

    # Cria GeoDataFrame com as coordenadas únicas de cada estação
    _est_coords = (
        # df[['codigo_estacao','latitude','longitude']]
        df_info[['codigo_estacao','latitude','longitude']]
        .drop_duplicates(subset='codigo_estacao')
        .dropna(subset=['latitude','longitude'])
    )
    _gdf_est = gpd.GeoDataFrame(
        _est_coords,
        geometry=gpd.points_from_xy(_est_coords['longitude'], _est_coords['latitude']),
        crs='EPSG:4326'
    )

    # Spatial join: cada ponto recebe o atributo da mesorregião que o contém
    _join = gpd.sjoin(
        _gdf_est,
        shape_mg[['geometry', _col_meso]],
        how='left',
        predicate='within'
    )[['codigo_estacao', _col_meso]].rename(columns={_col_meso: 'mesorregiao'})

    # Propaga mesorregiao para df_mensal e df_diario
    df_mensal = df_mensal.merge(_join, on='codigo_estacao', how='left')
    df_diario = df_diario.merge(_join, on='codigo_estacao', how='left')
    if IMPRIME:
        print(f'Mesorregioes atribuidas: {_join["mesorregiao"].notna().sum()} / {len(_join)} estacoes')

    NIVEIS = [0, 10, 20, 30, 40, 60, 80, 100, 140, 180, 220, 260, 300, 340, 380, 420, 460, 500]
    CORES  = [
        '#ffffff', '#e3f2fd', '#bbdefb', '#90caf9', '#64b5f6',
        '#42a5f5', '#2196f3', '#1e88e5', '#1565c0', '#0d47a1',
        '#0a3880', '#082d66', '#06224d', '#041833', '#030f20',
        '#020a16', '#01060e', '#000000', '#000000',
    ]
    CMAP_FIXO = mcolors.ListedColormap(CORES)
    NORM_FIXO = BoundaryNorm(NIVEIS + [9999], ncolors=len(CORES))
    mg_uniao  = shape_mg.geometry.unary_union


    def mapa_mes(sub, mes, metodo='idw', res=0.05, power=2):
        sub = sub.dropna(subset=['latitude', 'longitude', 'chuva_acum_mm'])
        sub = sub[sub['chuva_acum_mm'] >= 0]
        if len(sub) < 4:
            if IMPRIME:
                print(f'  [{mes}] poucas estações ({len(sub)}), ignorado.')
            return

        lons = sub['longitude'].values
        lats = sub['latitude'].values
        vals = sub['chuva_acum_mm'].values

        mg_bounds = shape_mg.total_bounds
        lon_g = np.arange(mg_bounds[0] - 0.5, mg_bounds[2] + 0.51, res)
        lat_g = np.arange(mg_bounds[1] - 0.5, mg_bounds[3] + 0.51, res)

        # ── Interpolação na grade base ────────────────────────────────────────────
        grade = idw(lons, lats, vals, lon_g, lat_g, power) if metodo != 'kriging' \
                else kriging(lons, lats, vals, lon_g, lat_g)
        grade = np.clip(grade, 0, None)

        # Preenche NaN por vizinho mais próximo
        mask_valida = ~np.isnan(grade)
        if not mask_valida.all():
            _, ix = distance_transform_edt(~mask_valida, return_indices=True)
            grade = grade[ix[0], ix[1]]

        # ── Suavização gaussiana ───────────────────────────────────────────────
        grade_suave = gaussian_filter(grade, sigma=4)

        # ── HTML interativo (Folium) ──────────────────────────────────────────────
        glon, glat = np.meshgrid(lon_g, lat_g)
        pontos = gpd.GeoSeries(
            [Point(x, y) for x, y in zip(glon.ravel(), glat.ravel())],
            crs='EPSG:4326'
        )
        dentro     = pontos.within(mg_uniao).values.reshape(glon.shape)
        grade_html = np.where(dentro, grade_suave, np.nan)
        grade_html = grade_html[::-1]

        rgba = CMAP_FIXO(NORM_FIXO(grade_html))
        rgba[np.isnan(grade_html)] = [0, 0, 0, 0]
        img8 = (rgba * 255).astype(np.uint8)

        m = folium.Map(location=[lats.mean(), lons.mean()], zoom_start=7,
                    tiles='Esri.WorldImagery')
        folium.GeoJson(shape_mg, name='Limite MG',
                    style_function=lambda _: {
                        'fillColor': 'none', 'color': 'white', 'weight': 1.2
                    }).add_to(m)
        folium.raster_layers.ImageOverlay(
            image=img8,
            bounds=[[lat_g.min(), lon_g.min()], [lat_g.max(), lon_g.max()]],
            opacity=0.70, name='Interpolação'
        ).add_to(m)
        # ── Barra de cores (legenda) ───────────────────────────────────────
        # Gera HTML da barra de cores com os níveis e cores da escala
        barra_items = []
        for i, (nivel, cor) in enumerate(zip(NIVEIS, CORES)):
            proximo = NIVEIS[i + 1] if i + 1 < len(NIVEIS) else 500
            rotulo  = f"{nivel}–{proximo}" if i < len(NIVEIS) - 1 else f"≥{nivel}"
            txt_cor = "#000" if i < 6 else "#fff"
            barra_items.append(
                f'<div style="background:{cor};color:{txt_cor};padding:2px 4px;'
                f'font-size:10px;text-align:center;min-width:36px">{rotulo}</div>'
            )
        barra_html = (
            '<div style="position:fixed;bottom:20px;left:50%;transform:translateX(-50%);'
            'background:rgba(255,255,255,0.85);border:1px solid #aaa;'
            'border-radius:6px;padding:6px 10px;z-index:9999">'
            '<div style="font-size:11px;font-weight:bold;text-align:center;'
            'margin-bottom:4px;color:#333">Precipitação acumulada (mm)</div>'
            '<div style="display:flex;flex-wrap:wrap;gap:2px;justify-content:center">'
            + "".join(barra_items)
            + '</div></div>'
        )
        m.get_root().html.add_child(folium.Element(barra_html))

        folium.LayerControl().add_to(m)
        m.save(f'{OUTPUT_DIR}/mapas/chuva_{mes}.html')
        if IMPRIME:
            print(f'  HTML → {OUTPUT_DIR}/mapas/chuva_{mes}.html')

    # Roda para todos os meses
    for mes in sorted(df_mensal['ano_mes_brt'].unique()):
        if IMPRIME:
            print(f'\n── {mes} ──')
        # mapa_mes(df_mensal[df_mensal['ano_mes_brt'] == mes],
        mapa_mes(df_mensal.merge(df_info, on='codigo_estacao', how='left').query('ano_mes_brt == @mes'),
                mes, metodo=METODO_INTERP,
                res=RESOLUCAO_GRADE, power=IDW_POWER)

    # --------------------------------------------------------------------------------------------------------------------
    # CÉLULA 10
    # --------------------------------------------------------------------------------------------------------------------
    # Exporta dados padronizados, acumulado mensal e acumulado diário
    # df.to_csv(fr'{OUTPUT_DIR}\dados_padronizados.csv', index=False, encoding='utf-8-sig')
    # df_mensal.to_csv(fr'{OUTPUT_DIR}\acumulado_mensal.csv', index=False, encoding='utf-8-sig')
    # df_diario.to_csv(fr'{OUTPUT_DIR}\acumulado_diario.csv', index=False, encoding='utf-8-sig')  # <-- NOVO
    # serie_horaria.to_csv(fr'{OUTPUT_DIR}\serie_horaria.csv', index=False, encoding='utf-8-sig')

    # df.to_parquet(fr'{OUTPUT_DIR}\dados_padronizados.parquet', index=False)
    # df_mensal.to_parquet(fr'{OUTPUT_DIR}\acumulado_mensal.parquet', index=False)
    # df_diario.to_parquet(fr'{OUTPUT_DIR}\acumulado_diario.parquet', index=False)
    # serie_horaria.to_parquet(fr'{OUTPUT_DIR}\serie_horaria.parquet', index=False)

    for nome in MES_ATUAL:
        df.query('ano_mes_brt == @nome').to_parquet(fr'{OUTPUT_DIR}\dados_padronizados_{nome}.parquet', index=False)
        df_mensal.query('ano_mes_brt == @nome').to_parquet(fr'{OUTPUT_DIR}\acumulado_mensal_{nome}.parquet', index=False)
        df_diario.query('ano_mes_brt == @nome').to_parquet(fr'{OUTPUT_DIR}\acumulado_diario_{nome}.parquet', index=False)
        serie_horaria.query('ano_mes_brt == @nome').to_parquet(fr'{OUTPUT_DIR}\serie_horaria_{nome}.parquet', index=False)

        # Relatório municipal: média e máximo mensal por município, ordem alfabética
        relatorio_municipal = (
            # df_mensal.groupby(['ano_mes_brt', 'municipio', 'uf'])
            df_mensal.query('ano_mes_brt == @nome').merge(df_info[["codigo_estacao", "municipio"]], on="codigo_estacao", how="left").groupby(['ano_mes_brt', 'municipio'])
                    .agg(
                        chuva_media_mm = ('chuva_acum_mm', 'mean'),
                        chuva_max_mm   = ('chuva_acum_mm', 'max'),
                        n_estacoes     = ('codigo_estacao', 'count'),
                    )
                    .reset_index()
                    .sort_values(['ano_mes_brt', 'municipio'])
                    .round(2)
        )
        relatorio_municipal.to_parquet(fr'{OUTPUT_DIR}\relatorio_municipal_{nome}.parquet', index=False)
    
    df_info.to_parquet(fr'{OUTPUT_DIR}\estacoes_salvar.parquet', index=False)
    
    if IMPRIME:
        print('Arquivos salvos em', OUTPUT_DIR)
        print('Mapas gerados:', sorted(os.listdir(fr'{OUTPUT_DIR}\mapas')))
        print(fr'\nRelatório municipal: {len(relatorio_municipal)} linhas')
        print(relatorio_municipal.head(10).to_string(index=False))
        print(fr'\ndf_diario: {len(df_diario):,} linhas exportadas → {OUTPUT_DIR}\acumulado_diario.parquet')

        # fim = datetime.now()
        # print(fim-inicio)
    
    return df, df_mensal, df_diario, serie_horaria, relatorio_municipal

def salvar():
    
    while True:
        inicio = datetime.now()
        # os.system("taskkill /f /im msedgedriver.exe /T") ###### FECHA TODOS OS WEBDRIVERS ATIVOS PRA EVITAR SOBRECARREGAR A MAQUINA. DESATIVAR SE TIVER RODANDO MAIS COISA
        
        print(f"INICIANDO LOOP EM {inicio.strftime(format = '%Y/%m/%d %H:%M')}")

        df_dados_24h, df_dados, df_info = raspar(LOGIN_SALVAR, SENHA_SALVAR, CAMINHO, 1)
        fim1 = datetime.now()
        
        # clear_output(wait=True)
        # print(f"RASPAGEM INICIADA EM {inicio.strftime(format = '%Y/%m/%d %H:%M')}, FINALIZADA EM {fim.strftime(format = '%Y/%m/%d %H:%M')}")

        df_padr, df_mensal, df_diario, serie_horaria, relatorio_municipal = calculos(CAMINHO, OUTPUT_DIR, 0)
        fim2 = datetime.now()

        # clear_output(wait=True)
        # print(f"RASPAGEM INICIADA EM {inicio.strftime(format = '%Y/%m/%d %H:%M')}, FINALIZADA EM {fim1.strftime(format = '%Y/%m/%d %H:%M')}")
        # print(f"CÁLCULOS INICIADOS EM {fim1.strftime(format = '%Y/%m/%d %H:%M')}, FINALIZADOS EM {fim2.strftime(format = '%Y/%m/%d %H:%M')}")

        # espera = max(0, 10*60 - (fim2 - inicio).total_seconds())
        # print(f"Aguardando {round(espera)} segundos para completar 10 minutos")
        # time_aux.sleep(max(0, espera))
        
        print(f"{(fim2 - inicio).total_seconds()} segundos para executar script salvar.")
        
        # return df_dados_24h, df_dados, df_info, df_padr, df_mensal, df_diario, serie_horaria, relatorio_municipal
        # return espera
