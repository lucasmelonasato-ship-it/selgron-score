#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  SELGRON · GERADOR DE FECHAMENTO MENSAL
#  Cruza PRAZO DE ENTREGA + INSPEÇÃO DE RECEBIMENTO e gera o arquivo AAAA-MM.xlsx
#  pronto para upload na pasta dados/ do GitHub.
#
#  USO:
#    python gerar_mes.py --prazo PRAZO_MAIO.xlsx --qualidade Inspecao.xlsx --mes 2026-05
#
#  O arquivo de saída (ex: 2026-05.xlsx) vai para a pasta atual.
#  Basta subir esse arquivo na pasta dados/ do repositório GitHub.
# ─────────────────────────────────────────────────────────────────────────────

import argparse
import re
import sys
import unicodedata
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

PESO_PRAZO = 0.60
PESO_QUAL  = 0.40

# Reatribuições de carteira (compradores antigos → comprador atual)
REASSIGN = {
    "Paulo Cesar Siberino da Silva": "Jair Wermuth",
    "Ricardo Krause":                "Jair Wermuth",
    "Matheus Veloso Vasconcelos":    "Nithael Alexandre Krepsky Silveira",
}
# Compradores removidos (carteira não é de Suprimentos)
REMOVER = {"Anelize dos Santos"}

MESES_PT = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
            7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def classify(s: float) -> str:
    if s >= 0.90: return "A - EXCELENTE"
    if s >= 0.80: return "B - BOM"
    if s >= 0.70: return "C - REGULAR"
    if s >= 0.60: return "D - ATENCAO"
    return "E - CRITICO"

def normalize_name(name) -> str:
    """Normaliza nome de fornecedor para cruzamento robusto (acento + sufixo)."""
    if pd.isna(name):
        return ""
    s = str(name).upper().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    for suf in [" LTDA", " S/A", " S.A", " SA", " EIRELI", " EPP", " ME",
                " - ME", " - EPP", "."]:
        s = s.replace(suf, " ")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_excel_date(v):
    """Converte serial Excel OU string para datetime, tolerando lixo."""
    try:
        n = float(v)
        if 40000 < n < 55000:      # range plausível de datas 2009–2050
            return pd.Timestamp("1899-12-30") + pd.Timedelta(days=n)
    except (ValueError, TypeError):
        pass
    try:
        d = pd.to_datetime(v, dayfirst=True, errors="coerce")
        if pd.notna(d) and 2020 <= d.year <= 2050:
            return d
    except Exception:
        pass
    return pd.NaT


# ─── LEITURA: PRAZO ──────────────────────────────────────────────────────────

def ler_prazo(path: str, ano: int, mes: int):
    """Lê a aba BASE e retorna entregas do mês alvo, com nome de exibição."""
    df = pd.read_excel(path, sheet_name="BASE")

    # Filtra status válido
    df = df[df["ATRASO ?"].astype(str).str.upper().str.strip().isin(["NO PRAZO", "ATRASO"])].copy()

    # Filtra mês/ano pela DATA PREVISÃO (fonte mais confiável que MÊS PREVISÃO textual)
    df["dt"] = df["DATA PREVISÃO"].apply(parse_excel_date)
    # fallback para MÊS PREVISÃO textual quando data inválida
    mask_dt = (df["dt"].dt.year == ano) & (df["dt"].dt.month == mes)

    # também aceita pela coluna textual MÊS PREVISÃO (ex '05-mai') + ANO PREVISÃO
    mes_txt = df["MÊS PREVISÃO"].astype(str)
    mask_txt = mes_txt.str.startswith(f"{mes:02d}") & (df.get("ANO PREVISÃO", 0) == ano)

    df = df[mask_dt | mask_txt].copy()

    df["COMPRADOR"] = df["COMPRADOR"].replace(REASSIGN)
    df = df[~df["COMPRADOR"].isin(REMOVER)].copy()
    df = df.dropna(subset=["FORNECEDOR"])

    df["norm"]    = df["FORNECEDOR"].apply(normalize_name)
    df["no_prazo"] = (df["ATRASO ?"].astype(str).str.upper().str.strip() == "NO PRAZO").astype(int)
    df["valor"]    = pd.to_numeric(df.get("VALOR NOTA FISCAL", 0), errors="coerce").fillna(0)

    # Nome de exibição: o mais completo/frequente por chave normalizada
    nome_display = (df.groupby("norm")["FORNECEDOR"]
                      .agg(lambda s: s.value_counts().index[0]))
    comprador_pred = (df.groupby("norm")["COMPRADOR"]
                        .agg(lambda s: s.value_counts().index[0]))

    agg = df.groupby("norm").agg(
        TOTAL_ENTREGAS=("no_prazo", "count"),
        NO_PRAZO=("no_prazo", "sum"),
        VALOR_NF=("valor", "sum"),
    ).reset_index()
    agg["FORNECEDOR"] = agg["norm"].map(nome_display)
    agg["COMPRADOR"]  = agg["norm"].map(comprador_pred)
    agg["ATRASOS"]    = agg["TOTAL_ENTREGAS"] - agg["NO_PRAZO"]
    return agg


# ─── LEITURA: QUALIDADE ──────────────────────────────────────────────────────

def ler_qualidade(path: str, ano: int, mes: int):
    """Lê a aba Recebimento 2026 (header na linha 5) e conta NCs do mês alvo."""
    # Detecta a aba de recebimento do ano
    xls = pd.ExcelFile(path)
    sheet = next((s for s in xls.sheet_names if "RECEBIMENTO" in s.upper() and str(ano) in s),
                 None)
    if sheet is None:
        sheet = next((s for s in xls.sheet_names if "RECEBIMENTO" in s.upper()),
                     xls.sheet_names[0])

    # Header está na linha 5 (índice 4) no layout Selgron
    df = pd.read_excel(path, sheet_name=sheet, header=4)
    df = df.dropna(subset=["Fornecedor"])
    df = df[df["Fornecedor"].astype(str).str.strip() != ""].copy()

    df["dt"] = df["Data de inspeção"].apply(parse_excel_date)
    df = df[(df["dt"].dt.year == ano) & (df["dt"].dt.month == mes)].copy()

    df["norm"] = df["Fornecedor"].apply(normalize_name)
    df["eh_nc"] = (df["Situação lote"].astype(str).str.upper().str.strip() == "REPROVADO").astype(int)

    agg = df.groupby("norm").agg(
        INSPECOES=("eh_nc", "count"),
        TOTAL_ALERTAS=("eh_nc", "sum"),
    ).reset_index()
    nome_display = df.groupby("norm")["Fornecedor"].agg(lambda s: s.value_counts().index[0])
    agg["FORNECEDOR_Q"] = agg["norm"].map(nome_display)
    return agg


# ─── CRUZAMENTO + SCORE ──────────────────────────────────────────────────────

def gerar(prazo_path, qual_path, ano, mes):
    prazo = ler_prazo(prazo_path, ano, mes)
    qual  = ler_qualidade(qual_path, ano, mes)

    # UNIÃO pela chave normalizada
    base = pd.merge(prazo, qual, on="norm", how="outer")

    # Nome de exibição: prefere o do prazo; senão o da qualidade
    base["FORNECEDOR"] = base["FORNECEDOR"].fillna(base["FORNECEDOR_Q"])
    base["COMPRADOR"]  = base["COMPRADOR"].fillna("(sem entrega no mês)")

    # Regra: sem entrega → prazo 100% (não atrasou nada)
    base["TOTAL_ENTREGAS"] = base["TOTAL_ENTREGAS"].fillna(0).astype(int)
    base["NO_PRAZO"]       = base["NO_PRAZO"].fillna(0).astype(int)
    base["ATRASOS"]        = base["ATRASOS"].fillna(0).astype(int)
    base["VALOR_NF"]       = base["VALOR_NF"].fillna(0)
    base["SCORE_PRAZO"] = np.where(
        base["TOTAL_ENTREGAS"] > 0,
        base["NO_PRAZO"] / base["TOTAL_ENTREGAS"].replace(0, np.nan),
        1.0,
    )

    # ─── IQF (Qualidade) — denominador = ENTREGAS do mês ─────────────────
    # Regra Selgron: IQF = (itens entregues − itens com problema) / itens entregues
    #   • cada linha REPROVADO = 1 item com problema (independe da qtd de peças)
    #   • a NC conta no mês da INSPEÇÃO, mesmo que o item tenha sido entregue antes
    #   • sem NC no mês                       → qualidade 100%
    #   • tem entregas e tem NC               → (entregas − NCs) / entregas
    #   • ZERO entregas no mês mas tem NC     → qualidade 0% (só movimento de problema)
    base["INSPECOES"]     = base["INSPECOES"].fillna(0).astype(int)
    base["TOTAL_ALERTAS"] = base["TOTAL_ALERTAS"].fillna(0).astype(int)

    entregas = base["TOTAL_ENTREGAS"]
    ncs      = base["TOTAL_ALERTAS"]
    base["SCORE_QUALIDADE"] = np.select(
        [
            ncs == 0,                       # sem problema → 100%
            (entregas > 0) & (ncs > 0),     # tem entrega e problema → fração real
            (entregas == 0) & (ncs > 0),    # só problema, sem entrega → 0%
        ],
        [
            1.0,
            (entregas - ncs) / entregas.replace(0, np.nan),
            0.0,
        ],
        default=1.0,
    )
    base["SCORE_QUALIDADE"] = base["SCORE_QUALIDADE"].clip(0, 1)

    # Score geral
    base["SCORE_GERAL"] = base["SCORE_PRAZO"] * PESO_PRAZO + base["SCORE_QUALIDADE"] * PESO_QUAL
    base["CLASSE"]      = base["SCORE_GERAL"].apply(classify)
    base["TEM_NC"]      = (base["TOTAL_ALERTAS"] > 0).map({True: "SIM", False: "NÃO"})

    # Diagnóstico automático
    def diag(r):
        partes = []
        if r["SCORE_PRAZO"] < 0.70 and r["TOTAL_ENTREGAS"] > 0:
            partes.append(f"{int(r['ATRASOS'])} de {int(r['TOTAL_ENTREGAS'])} entregas atrasadas")
        if r["TOTAL_ALERTAS"] > 0:
            partes.append(f"{int(r['TOTAL_ALERTAS'])} não conformidade(s)")
        return " · ".join(partes) if partes else "Sem ocorrências no período"
    base["DIAGNOSTICO"] = base.apply(diag, axis=1)

    # Ordena e ranqueia
    base = base.sort_values("SCORE_GERAL", ascending=False).reset_index(drop=True)

    # Colunas finais no formato BASE_DADOS (compatível com o app)
    cols = ["FORNECEDOR", "COMPRADOR", "SCORE_GERAL", "SCORE_QUALIDADE", "SCORE_PRAZO",
            "CLASSE", "TOTAL_ENTREGAS", "NO_PRAZO", "ATRASOS", "VALOR_NF",
            "TEM_NC", "TOTAL_ALERTAS", "INSPECOES", "DIAGNOSTICO"]
    return base[cols]


def main():
    ap = argparse.ArgumentParser(description="Gera o fechamento mensal Selgron (AAAA-MM.xlsx)")
    ap.add_argument("--prazo",     required=True, help="Planilha de PRAZO DE ENTREGA do mês")
    ap.add_argument("--qualidade", required=True, help="Planilha de INSPEÇÃO DE RECEBIMENTO (histórico)")
    ap.add_argument("--mes",       required=True, help="Mês alvo no formato AAAA-MM (ex: 2026-05)")
    ap.add_argument("--saida",     default=None,  help="Nome do arquivo de saída (padrão: AAAA-MM.xlsx)")
    args = ap.parse_args()

    m = re.match(r"(\d{4})-(\d{1,2})", args.mes)
    if not m:
        print("ERRO: --mes deve estar no formato AAAA-MM (ex: 2026-05)")
        sys.exit(1)
    ano, mes = int(m.group(1)), int(m.group(2))
    saida = args.saida or f"{ano}-{mes:02d}.xlsx"

    print(f"\n{'='*60}")
    print(f"  FECHAMENTO {MESES_PT[mes]}/{ano}")
    print(f"{'='*60}")

    base = gerar(args.prazo, args.qualidade, ano, mes)

    # Grava no formato que o app espera (aba BASE_DADOS)
    with pd.ExcelWriter(saida, engine="openpyxl") as w:
        base.to_excel(w, sheet_name="BASE_DADOS", index=False)

    # Resumo no terminal
    n = len(base)
    print(f"\n✅ Gerado: {saida}")
    print(f"   Fornecedores: {n}")
    print(f"   Score médio do setor: {base['SCORE_GERAL'].mean()*100:.1f}%")
    print(f"   Prazo médio: {base['SCORE_PRAZO'].mean()*100:.1f}%  |  "
          f"Qualidade média: {base['SCORE_QUALIDADE'].mean()*100:.1f}%")
    print(f"\n   Distribuição por classe:")
    for cls in ["A - EXCELENTE","B - BOM","C - REGULAR","D - ATENCAO","E - CRITICO"]:
        c = (base["CLASSE"] == cls).sum()
        if c:
            print(f"     {cls}: {c}")
    print(f"\n   Fornecedores com NC: {(base['TOTAL_ALERTAS']>0).sum()}")
    print(f"   Fornecedores com atraso: {(base['ATRASOS']>0).sum()}")
    print(f"\n   → Suba '{saida}' na pasta dados/ do GitHub.\n")


if __name__ == "__main__":
    main()
