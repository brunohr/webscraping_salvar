import pandas as pd
import requests
from datetime import datetime
from requests.exceptions import ConnectTimeout
from pathlib import Path

global proxies
proxies = {"http": PROXY_URL, "https": PROXY_URL}

def medicoes_salvar(LOGIN, SENHA, CAMINHO, horainic = 72):
        
    # ============================================================
    # CONFIGURAÇÃO
    # ============================================================
    BASE = "https://salvar.cemaden.gov.br"


    HORAS_JANELA = horainic
    PAUSA        = 0.25   # segundos entre chamadas

    session = requests.Session()

    # ============================================================
    # 1. LOGIN (j_security_check + meta-refresh)
    # ============================================================
    def login():
        r = session.post(f"{BASE}/salvar/j_security_check",
                        data={"j_username": LOGIN, "j_password": SENHA},
                        proxies=proxies, timeout=10)
        m = re.search(r'URL=([^"]+)"', r.text)
        if m:
            session.get(f"{BASE}/salvar/{m.group(1).lstrip('./')}",
                        proxies=proxies, timeout=10)
        if "JSESSIONID" not in session.cookies.get_dict():
            raise RuntimeError("Login falhou — sem JSESSIONID")
        return r

    def obter_token():
        r = session.get(f"{BASE}/salvar/tokenize", proxies=proxies, timeout=10)
        t = r.text.strip()
        if t in ("", "FAIL"):
            raise RuntimeError("Sessão inválida — refaça o login")
        return t

    login()
    token = obter_token()

    # ============================================================
    # 2. JANELA TEMPORAL (UTC — o SALVAR opera em UTC)
    # ============================================================
    agora  = datetime.now(timezone.utc)
    inicio = agora - timedelta(hours=HORAS_JANELA)

    ts_fim       = int(agora.timestamp() * 1000)
    ts_inicio    = int(inicio.timestamp() * 1000)
    data_final   = agora.strftime("%Y-%m-%d %H:%M")
    data_inicial = inicio.strftime("%Y-%m-%d %H:%M")

    # ============================================================
    # 3. LISTA DE ESTAÇÕES + ACUMULADOS
    # ============================================================
    url_painel = (f"{BASE}/salvar/restrito/meteorologia/index.jsf"
                "?susp=1&inv=1&fut=1&A4H=1&c=6&o=desc"
                f"&uf=MG&ci=&A120H=1&A30D=1&nets=1")

    r_tab = session.get(f"{BASE}/SalvarWS/rest/table-meteoro/dados",
                        params={"_": int(time_aux.time() * 1000)},
                        headers={"Accept": "application/json, text/javascript, */*; q=0.01",
                                "X-Requested-With": "XMLHttpRequest",
                                "Referer": url_painel,
                                "Token": token},
                        proxies=proxies, timeout=30)
    r_tab.raise_for_status()
    payload = r_tab.json()

    df_estacoes = pd.json_normalize(payload["estacoes"])
    df_estacoes["atualizado"] = pd.to_datetime(payload["atualizado"].replace(" UTC", ""))
    df_estacoes["datahora"]   = pd.to_datetime(df_estacoes["datahora"])
    df_estacoes["data_monit"] = pd.to_datetime(df_estacoes["data_monit"], errors="coerce")

    REDES = {
        1: "ANA", 3: "INMET", 9: "INEA", 11: "CEMADEN", 12: "SIMEPAR",
        13: "CEMADEN-RJ", 14: "PCJ", 15: "CODESAL", 16: "SJC", 18: "CEPDEC-ES",
    }

    df_estacoes["rede"] = df_estacoes["id_rede"].map(REDES)

    print(f"Painel: {len(df_estacoes)} estações | atualizado {payload['atualizado']}")

    # ============================================================
    # 4. SÉRIE HORÁRIA POR ESTAÇÃO
    # ============================================================
    sel = df_estacoes.query("uf == 'MG' and rede == ['ANA', 'CEMADEN', 'INMET'] and datahora.notna()")
    mapa_cod = dict(zip(sel["id_estacao"], sel["codestacao"]))
    ids = sel["id_estacao"].tolist()

    dups = sel["codestacao"].duplicated().sum()
    if dups:
        print(f"Atenção: {dups} codestacao duplicados na seleção")

    def buscar_periodo(id_estacao, tok):
        headers = {
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": (f"{BASE}/salvar/restrito/meteorologia/ana/index.jsf"
                        f"?id={id_estacao}&pe=1&dh={ts_fim}&idh={ts_inicio}"),
            "Token": tok,
        }
        return session.get(
            f"{BASE}/SalvarWS/rest/periodo/{id_estacao}/{data_inicial}/{data_final}",
            params={"_": int(time_aux.time() * 1000)},
            headers=headers, proxies=proxies, timeout=30
        )

    frames, falhas = [], []

    for n, i in enumerate(ids, 1):
        cod = mapa_cod[i]
        try:
            r = buscar_periodo(i, token)

            if r.status_code == 204:                 # token expira a cada ~10 min
                token = obter_token()
                r = buscar_periodo(i, token)

            if r.status_code != 200 or not r.content:
                falhas.append((cod, r.status_code)); continue

            registros = r.json().get("data", [])
            if not registros:
                falhas.append((cod, "vazio")); continue

            frames.append(pd.DataFrame(registros).assign(codigo_estacao=cod))

        except Exception as e:
            falhas.append((cod, repr(e)))

        if n % 25 == 0:
            print(f"  {n}/{len(ids)} — {len(falhas)} falhas")
        time_aux.sleep(PAUSA)

    # ============================================================
    # 5. CONSOLIDAÇÃO E TIPAGEM
    # ============================================================
    df_estacoes = (df_estacoes.query("uf == 'MG' and rede == ['ANA', 'CEMADEN', 'INMET'] and datahora.notna()")
                .rename(columns = {'codestacao': 'codigo_estacao', 'atualizado': 'coleta', 'cidade': 'municipio', 'id_estacao': 'link', 'datahora': 'data'})
                .merge(pd.read_excel(CAMINHO / "CODIGOS_SALVAR_MG_v2.xlsx"), how='left', on='codigo_estacao'))[
                    ['codigo_estacao', 'nome', 'municipio', 'rede', 'data', 'link', 'coleta', 'latitude', 'longitude']]

    df_estacoes.to_parquet(CAMINHO / 'medicoes_salvar' / f'estacoes_salvar_{datetime.today().strftime('%Y%m%d%H%M%S')}.parquet', index=False)
    df_estacoes.to_parquet(CAMINHO / 'estacoes_salvar.parquet', index=False)

    df_chuva = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    if not df_chuva.empty:
        # descarta linhas de rodapé ('Total', vazias) — data inválida
        datas = pd.to_datetime(df_chuva["data"], format="%d/%m/%Y %H:%M",
                            errors="coerce"
                            #    , utc=True
                            )
        df_chuva = df_chuva[datas.notna()].copy()
        df_chuva["data"]     = datas[datas.notna()]
        # df_chuva["data_brt"] = df_chuva["data"].dt.tz_convert("America/Sao_Paulo")

        df_chuva["valor"] = pd.to_numeric(
            df_chuva["valor"].str.replace(".", "", regex=False)
                            .str.replace(",", ".", regex=False),
            errors="coerce")

        df_chuva = (df_chuva[["codigo_estacao", "data",
        # "data_brt",
        "valor", "qualificacao"]]
                    .sort_values(["codigo_estacao", "data"])
                    .reset_index(drop=True)).rename(columns = {'data': 'datahora_utc', 'valor': 'chuva_mm'}).assign(datacoleta = datetime.now())

        df_chuva.to_parquet(CAMINHO / "medicoes_salvar" / f"medicoes_salvar_{datetime.today().strftime('%Y%m%d%H%M%S')}.parquet", index=False)

        (pd.concat([df_chuva,
        pd.read_parquet(CAMINHO / "medicoes_salvar.parquet")],
        ignore_index=True
        ).sort_values(['codigo_estacao', 'datahora_utc', 'datacoleta']).drop_duplicates(subset = ['codigo_estacao', 'datahora_utc'], keep='last')
        .to_parquet(CAMINHO / "medicoes_salvar.parquet", index=False))
        
    print(f"fim coleta salvar: {datetime.today().strftime('%Y%m%d%H%M%S')}")
