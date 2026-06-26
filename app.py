# ─────────────────────────────────────────────────────────────────────────────
#  SELGRON INDUSTRIAL — Score de Fornecedores v2.0
#  Departamento de Suprimentos · Lucas Melo Nasato
#  Para executar: streamlit run app.py
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io, os

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Score Fornecedores | Selgron",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── BRAND ───────────────────────────────────────────────────────────────────
NAVY   = "#1E2761"
GOLD   = "#F7A600"
WHITE  = "#FFFFFF"
LGRAY  = "#F5F5F5"
MGRAY  = "#DDDDDD"
DGRAY  = "#595959"

C_GREEN  = "#155724"; BG_GREEN  = "#D4EDDA"; BAR_GREEN  = "#27AE60"
C_BLUE   = "#1A5276"; BG_BLUE   = "#DDEEFF"; BAR_BLUE   = "#2980B9"
C_AMBER  = "#7D6608"; BG_AMBER  = "#FFF3BF"; BAR_AMBER  = "#F59F00"
C_ORANGE = "#7E5109"; BG_ORANGE = "#FDE8D8"; BAR_ORANGE = "#E67E22"
C_RED    = "#721C24"; BG_RED    = "#F8D7DA"; BAR_RED    = "#E74C3C"

CLASSES = {
    "A - EXCELENTE": dict(min=0.90, max=1.01, bg=BG_GREEN,  text=C_GREEN,  bar=BAR_GREEN,  emoji="🟢", label="EXCELENTE"),
    "B - BOM":       dict(min=0.80, max=0.90, bg=BG_BLUE,   text=C_BLUE,   bar=BAR_BLUE,   emoji="🔵", label="BOM"),
    "C - REGULAR":   dict(min=0.70, max=0.80, bg=BG_AMBER,  text=C_AMBER,  bar=BAR_AMBER,  emoji="🟡", label="REGULAR"),
    "D - ATENCAO":   dict(min=0.60, max=0.70, bg=BG_ORANGE, text=C_ORANGE, bar=BAR_ORANGE, emoji="🟠", label="ATENÇÃO"),
    "E - CRITICO":   dict(min=0.00, max=0.60, bg=BG_RED,    text=C_RED,    bar=BAR_RED,    emoji="🔴", label="CRÍTICO"),
}

CLASS_ALIASES = {
    "A – EXCELENTE":"A - EXCELENTE","A - EXCELENTE":"A - EXCELENTE",
    "B – BOM":"B - BOM","B - BOM":"B - BOM",
    "C – REGULAR":"C - REGULAR","C - REGULAR":"C - REGULAR",
    "D – ATENÇÃO":"D - ATENCAO","D – ATENCAO":"D - ATENCAO","D - ATENCAO":"D - ATENCAO",
    "E – CRÍTICO":"E - CRITICO","E – CRITICO":"E - CRITICO","E - CRITICO":"E - CRITICO",
}

PESO_PRAZO = 0.60
PESO_QUAL  = 0.40

# Logo Selgron (ícone diamante/grão) em base64
LOGO_ICON_B64 = "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"

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def get_class(score: float) -> str:
    for name, c in CLASSES.items():
        if c["min"] <= score < c["max"]:
            return name
    return "E - CRITICO"

def normalise_class(raw: str) -> str:
    raw = str(raw).strip()
    if raw in CLASSES:      return raw
    if raw in CLASS_ALIASES: return CLASS_ALIASES[raw]
    letter = raw[0].upper() if raw else "E"
    for k in CLASSES:
        if k.startswith(letter): return k
    return "E - CRITICO"

def score_bar_color(score: float) -> str:
    return CLASSES[get_class(score)]["bar"]

def pct(v: float) -> str:
    return f"{v * 100:.1f}%"

def kpi_card(label, value, sub="", color=NAVY):
    sub_html = f"<div class='kpi-sub'>{sub}</div>" if sub else ""
    return f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color};">{value}</div>
        {sub_html}</div>"""

def progress_bar(v, color):
    pct_w = min(v * 100, 100)
    return f"""<div style="background:#E8E8E8;border-radius:4px;height:9px;margin:3px 0 10px 0;">
        <div style="background:{color};width:{pct_w:.1f}%;height:9px;border-radius:4px;"></div></div>"""

# ─── CSS ─────────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family:'Inter','Calibri',sans-serif; }}
    #MainMenu, footer, header {{ visibility:hidden; }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{ background:{NAVY} !important; min-width:230px !important; }}
    [data-testid="stSidebar"] * {{ color:{WHITE} !important; }}
    [data-testid="stSidebar"] hr {{ border-color:rgba(255,255,255,0.12) !important; }}
    [data-testid="stSidebar"] .stRadio > label {{
        color:{GOLD} !important; font-size:0.68rem !important;
        font-weight:700 !important; text-transform:uppercase; letter-spacing:0.09em;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
        color:{WHITE} !important; font-size:0.85rem !important;
        font-weight:500 !important; padding:7px 0;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{ color:{GOLD} !important; }}
    [data-testid="stSidebar"] .stSelectbox label {{
        color:{GOLD} !important; font-size:0.68rem !important;
        font-weight:700; text-transform:uppercase; letter-spacing:0.09em;
    }}
    [data-testid="stSidebar"] .stSelectbox > div > div {{
        background:rgba(255,255,255,0.08) !important;
        border:1px solid rgba(247,166,0,0.35) !important; border-radius:6px;
    }}

    /* ── Sidebar toggle button — sempre visível ── */
    [data-testid="collapsedControl"] {{
        display:flex !important;
        background:{GOLD} !important;
        border-radius:0 8px 8px 0 !important;
        color:{NAVY} !important;
        width:28px !important;
        height:56px !important;
        align-items:center;
        justify-content:center;
        box-shadow:2px 0 8px rgba(0,0,0,0.2);
        top:50vh !important;
        position:fixed !important;
        left:0 !important;
    }}
    [data-testid="collapsedControl"] svg {{ fill:{NAVY} !important; }}
    [data-testid="stSidebarCollapseButton"] button {{
        background:rgba(247,166,0,0.15) !important;
        border:1px solid rgba(247,166,0,0.3) !important;
        border-radius:6px !important;
        color:{GOLD} !important;
    }}
    [data-testid="stSidebarCollapseButton"] button:hover {{
        background:{GOLD} !important;
        color:{NAVY} !important;
    }}

    /* ── Main BG ── */
    [data-testid="stAppViewContainer"] > .main {{ background:#F4F5F9; }}

    /* ── KPI Cards ── */
    .kpi-card {{
        background:{WHITE}; border-radius:10px; padding:16px 20px;
        border:1px solid {MGRAY}; border-top:3px solid {GOLD};
        box-shadow:0 2px 8px rgba(30,39,97,0.07); height:100%;
    }}
    .kpi-label {{
        font-size:0.68rem; font-weight:700; text-transform:uppercase;
        letter-spacing:0.07em; color:{DGRAY}; margin-bottom:6px;
    }}
    .kpi-value {{ font-size:1.9rem; font-weight:800; color:{NAVY}; line-height:1; }}
    .kpi-sub {{ font-size:0.75rem; color:{DGRAY}; margin-top:5px; }}

    /* ── Section title ── */
    .sec-title {{
        font-size:0.72rem; font-weight:700; color:{DGRAY};
        text-transform:uppercase; letter-spacing:0.09em;
        margin:20px 0 10px 0; padding-bottom:6px; border-bottom:2px solid {GOLD};
    }}

    /* ── Page header ── */
    .page-header {{
        background:{NAVY}; color:{WHITE}; padding:16px 24px;
        border-radius:10px; margin-bottom:20px;
        display:flex; align-items:center; justify-content:space-between;
    }}
    .page-header h1 {{ margin:0; font-size:1.35rem; font-weight:700; color:{WHITE}; }}
    .page-header .sub {{ font-size:0.8rem; color:{GOLD}; margin-top:2px; }}
    .ph-logo {{
        display:flex; align-items:center; gap:10px;
    }}
    .ph-logo-text {{
        font-size:1.6rem; font-weight:800; color:{GOLD}; letter-spacing:-1px; opacity:0.9;
    }}

    /* ── Ranking table ── */
    .rank-table {{ width:100%; border-collapse:collapse; font-size:0.82rem; border-radius:8px; overflow:hidden; }}
    .rank-table th {{
        background:{NAVY}; color:{WHITE}; padding:9px 12px;
        font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.07em;
        text-align:left;
    }}
    .rank-table th.num {{ text-align:center; width:50px; }}
    .rank-table th.pct {{ text-align:center; width:80px; }}
    .rank-table td {{ padding:7px 12px; border-bottom:1px solid rgba(0,0,0,0.04); }}
    .rank-table td.num {{ text-align:center; font-weight:700; color:{DGRAY}; }}
    .rank-table td.pct {{ text-align:center; font-weight:700; }}
    .rank-table tbody tr:hover {{ filter:brightness(0.96); cursor:default; }}

    /* ── Ficha ── */
    .ficha-wrap {{
        background:{WHITE}; border:1px solid {MGRAY}; border-radius:10px;
        padding:28px 32px; max-width:740px; margin:0 auto;
        box-shadow:0 4px 20px rgba(30,39,97,0.1);
    }}

    /* ── Login ── */
    .login-wrap {{
        max-width:370px; margin:7vh auto; background:{WHITE};
        border-radius:12px; padding:40px 36px;
        box-shadow:0 8px 40px rgba(30,39,97,0.15);
        border-top:4px solid {GOLD}; text-align:center;
    }}

    /* ── Buttons ── */
    .stButton > button[kind="primary"] {{
        background:{NAVY} !important; color:{WHITE} !important;
        border:none !important; border-radius:6px !important; font-weight:600 !important;
    }}
    .stButton > button[kind="primary"]:hover {{ background:{GOLD} !important; color:{NAVY} !important; }}

    /* ── Print ── */
    @media print {{
        [data-testid="stSidebar"], .page-header, .stButton,
        .stSelectbox, .no-print {{ display:none !important; }}
        .ficha-wrap {{ box-shadow:none; border:1px solid #ccc; }}
        body {{ -webkit-print-color-adjust:exact !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────

def init_state():
    for k, v in [("authenticated", False), ("df", None), ("data_info", "")]:
        if k not in st.session_state:
            st.session_state[k] = v

# ─── SAMPLE DATA ─────────────────────────────────────────────────────────────

def _sample_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    # Compradores reais da Selgron (ajuste 3: Misael e Alex no lugar de Isabela e Lara)
    buyers_cfg = [
        ("Edson Carlos Borges",               45, 0.91, 0.83),
        ("Arthur da Silva",                    38, 0.85, 0.78),
        ("Tatiana Goncalves",                  32, 0.82, 0.75),
        ("Jair Wermuth",                       40, 0.58, 0.69),
        ("Nithael Alexandre Krepsky Silveira", 35, 0.76, 0.71),
        ("Misael Souza",                       30, 0.79, 0.73),
        ("Alex Rodrigues",                     33, 0.84, 0.77),
    ]
    rows = []
    for buyer, n, p_mean, q_mean in buyers_cfg:
        for i in range(n):
            prazo = float(np.clip(rng.normal(p_mean, 0.11), 0.05, 1.0))
            qual  = float(np.clip(rng.normal(q_mean, 0.09), 0.05, 1.0))
            geral = prazo * PESO_PRAZO + qual * PESO_QUAL
            total = max(1, int(rng.exponential(8)))
            ncs   = max(0, int(total * (1 - qual)))
            fname = f"{buyer.split()[0][:4].upper()}-FORN-{i+1:03d} COM LTDA"
            rows.append({
                "FORNECEDOR":       fname,
                "COMPRADOR":        buyer,
                "SCORE_GERAL":      round(geral, 4),
                "SCORE_PRAZO":      round(prazo, 4),
                "SCORE_QUALIDADE":  round(qual, 4),
                "TOTAL_ENTREGAS":   total,
                "ENTREGA_NO_PRAZO": max(0, total - int(total * (1 - prazo))),
                "TOTAL_NCS":        ncs,
            })
    df = pd.DataFrame(rows)
    df["CLASSE"] = df["SCORE_GERAL"].apply(get_class)
    df = df.sort_values("SCORE_GERAL", ascending=False).reset_index(drop=True)
    df["RANK"] = range(1, len(df) + 1)
    return df

# ─── NORMALISE ────────────────────────────────────────────────────────────────

def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "Fornecedor":"FORNECEDOR","fornecedor":"FORNECEDOR",
        "Comprador":"COMPRADOR","comprador":"COMPRADOR",
        "Score Geral":"SCORE_GERAL","SCORE GERAL":"SCORE_GERAL","Score_Geral":"SCORE_GERAL",
        "Score Prazo":"SCORE_PRAZO","SCORE PRAZO":"SCORE_PRAZO","Score_Prazo":"SCORE_PRAZO",
        "Score Qualidade":"SCORE_QUALIDADE","SCORE QUALIDADE":"SCORE_QUALIDADE",
        "Total Entregas":"TOTAL_ENTREGAS","TOTAL ENTREGAS":"TOTAL_ENTREGAS",
        "Entrega No Prazo":"ENTREGA_NO_PRAZO","ENTREGA NO PRAZO":"ENTREGA_NO_PRAZO",
        "Total NCs":"TOTAL_NCS","TOTAL NCS":"TOTAL_NCS",
        "Classe":"CLASSE","classe":"CLASSE",
    }
    df = df.rename(columns=rename)
    for col in ["SCORE_GERAL","SCORE_PRAZO","SCORE_QUALIDADE"]:
        if col in df.columns and df[col].dropna().max() > 1.5:
            df[col] = df[col] / 100
    if "SCORE_QUALIDADE" not in df.columns and "SCORE_GERAL" in df.columns and "SCORE_PRAZO" in df.columns:
        df["SCORE_QUALIDADE"] = (df["SCORE_GERAL"] - df["SCORE_PRAZO"] * PESO_PRAZO) / PESO_QUAL
    for col in ["TOTAL_ENTREGAS","ENTREGA_NO_PRAZO","TOTAL_NCS"]:
        if col not in df.columns: df[col] = 0
    if "CLASSE" not in df.columns and "SCORE_GERAL" in df.columns:
        df["CLASSE"] = df["SCORE_GERAL"].apply(get_class)
    else:
        df["CLASSE"] = df["CLASSE"].apply(normalise_class)
    df = df.sort_values("SCORE_GERAL", ascending=False).reset_index(drop=True)
    df["RANK"] = range(1, len(df) + 1)
    return df

def _process_raw_prazo(file) -> pd.DataFrame:
    xls = pd.ExcelFile(file)
    sheet = "BASE" if "BASE" in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(file, sheet_name=sheet)
    atraso_col = next((c for c in df.columns if "ATRASO" in str(c).upper()), None)
    forn_col   = next((c for c in df.columns if "FORNECEDOR" in str(c).upper()), None)
    comp_col   = next((c for c in df.columns if "COMPRADOR"  in str(c).upper()), None)
    if not all([atraso_col, forn_col, comp_col]):
        raise ValueError("Colunas FORNECEDOR, COMPRADOR, ATRASO? nao encontradas")
    df["_np"] = df[atraso_col].astype(str).str.upper().str.contains("NO PRAZO").astype(int)
    result = df.groupby([comp_col, forn_col]).agg(
        TOTAL_ENTREGAS=("_np","count"), ENTREGA_NO_PRAZO=("_np","sum"),
    ).reset_index().rename(columns={comp_col:"COMPRADOR", forn_col:"FORNECEDOR"})
    result["SCORE_PRAZO"]     = result["ENTREGA_NO_PRAZO"] / result["TOTAL_ENTREGAS"]
    result["SCORE_QUALIDADE"] = 1.0
    result["TOTAL_NCS"]       = 0
    result["SCORE_GERAL"]     = result["SCORE_PRAZO"] * PESO_PRAZO + result["SCORE_QUALIDADE"] * PESO_QUAL
    result["CLASSE"]          = result["SCORE_GERAL"].apply(get_class)
    result = result.sort_values("SCORE_GERAL", ascending=False).reset_index(drop=True)
    result["RANK"] = range(1, len(result) + 1)
    return result

# ─── LOAD ────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_local_score():
    for path in ["Score_Fornecedores_Selgron_v8.xlsx","Score_Fornecedores_Selgron_v7.xlsx",
                 "Score_Fornecedores_Selgron.xlsx","score_data.xlsx"]:
        if os.path.exists(path):
            try:
                xls = pd.ExcelFile(path)
                sheet = next((s for s in xls.sheet_names
                              if "SCORE" in s.upper() and "GERAL" in s.upper()), xls.sheet_names[0])
                df = pd.read_excel(path, sheet_name=sheet)
                df = _normalise(df)
                return df, f"{path} | aba '{sheet}' | {len(df)} fornecedores"
            except: pass
    return _sample_data(), "DEMO — coloque Score_Fornecedores_Selgron_v7.xlsx na pasta do app ou importe em 'Atualizar Base'"

def load_from_upload(uploaded):
    try:
        xls = pd.ExcelFile(uploaded)
        score_sheet = next((s for s in xls.sheet_names
                            if "SCORE" in s.upper() and "GERAL" in s.upper()), None)
        if score_sheet:
            df = pd.read_excel(uploaded, sheet_name=score_sheet)
            df = _normalise(df)
            return df, f"Aba '{score_sheet}' | {len(df)} fornecedores carregados"
        if "BASE" in xls.sheet_names:
            df = _process_raw_prazo(uploaded)
            return df, f"Dados brutos processados | {len(df)} fornecedores"
        df = pd.read_excel(uploaded, sheet_name=0)
        df = _normalise(df)
        return df, f"Primeira aba | {len(df)} registros"
    except Exception as e:
        return _sample_data(), f"Erro: {e}"

# ─── RANKING TABLE (HTML colorida) ───────────────────────────────────────────

def ranking_table_html(df_show: pd.DataFrame) -> str:
    rows_html = ""
    for _, row in df_show.iterrows():
        cls  = str(row.get("CLASSE", "E - CRITICO"))
        cc   = CLASSES.get(normalise_class(cls), CLASSES["E - CRITICO"])
        bg   = cc["bg"]
        tc   = cc["text"]
        emj  = cc["emoji"]
        sg   = row["SCORE_GERAL"] * 100
        sp   = row["SCORE_PRAZO"] * 100
        sq   = row["SCORE_QUALIDADE"] * 100
        forn = str(row["FORNECEDOR"])[:45]
        comp = str(row["COMPRADOR"]).split()[0]
        rank = int(row["RANK"])
        ent  = int(row["TOTAL_ENTREGAS"])
        ncs  = int(row["TOTAL_NCS"])

        rows_html += f"""
        <tr style="background:{bg};">
            <td class="num" style="color:{DGRAY};">{rank}</td>
            <td style="color:{tc};font-weight:600;">{forn}</td>
            <td style="color:{DGRAY};">{comp}</td>
            <td class="pct" style="color:{tc};font-size:0.9rem;">{sg:.1f}%</td>
            <td class="pct" style="color:{BAR_BLUE};">{sp:.1f}%</td>
            <td class="pct" style="color:{BAR_GREEN};">{sq:.1f}%</td>
            <td class="num" style="color:{DGRAY};">{ent}</td>
            <td class="num" style="color:{'#C00000' if ncs > 0 else BAR_GREEN};">{ncs}</td>
            <td class="num">{emj} <span style="color:{tc};font-weight:700;font-size:0.72rem;">{cc['label']}</span></td>
        </tr>"""

    return f"""
    <div style="overflow-x:auto;border-radius:8px;border:1px solid {MGRAY};box-shadow:0 2px 8px rgba(30,39,97,0.07);">
    <table class="rank-table">
        <thead>
            <tr>
                <th class="num">#</th>
                <th>Fornecedor</th>
                <th>Comprador</th>
                <th class="pct">Score</th>
                <th class="pct">Prazo</th>
                <th class="pct">Qualidade</th>
                <th class="num">Entregas</th>
                <th class="num">NCs</th>
                <th>Classe</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>"""

# ─── LOGO COMPONENT ──────────────────────────────────────────────────────────

def logo_header(title, subtitle):
    return f"""
    <div class="page-header">
        <div>
            <h1>{title}</h1>
            <div class="sub">{subtitle}</div>
        </div>
        <div class="ph-logo">
            <img src="data:image/png;base64,{LOGO_ICON_B64}"
                 style="width:48px;height:48px;object-fit:cover;border-radius:6px;opacity:0.9;">
            <div class="ph-logo-text">selgron</div>
        </div>
    </div>"""

# ─── LOGIN ────────────────────────────────────────────────────────────────────

def page_login():
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(145deg, {NAVY} 0%, #0d1540 100%);
    }}
    </style>
    <div class="login-wrap">
        <img src="data:image/png;base64,{LOGO_ICON_B64}"
             style="width:70px;height:70px;object-fit:cover;border-radius:10px;margin-bottom:10px;">
        <div style="font-size:2rem;font-weight:800;color:{NAVY};letter-spacing:-1px;">
            sel<span style="color:{GOLD};">g</span>ron
        </div>
        <div style="font-size:0.82rem;color:{DGRAY};margin-bottom:28px;">
            Sistema de Score de Fornecedores
        </div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.1, 1])
    with c2:
        pw = st.text_input("Senha", type="password",
                           placeholder="Digite a senha...", label_visibility="collapsed")
        if st.button("Entrar", use_container_width=True, type="primary"):
            if pw == "Acesso2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
        st.markdown(f"""
        <div style="text-align:center;margin-top:20px;font-size:0.72rem;color:rgba(30,39,97,0.4);">
            Selgron Industrial · Suprimentos · 2026
        </div>""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────

def show_sidebar(df: pd.DataFrame) -> str:
    with st.sidebar:
        # Logo Selgron com ícone real
        st.markdown(f"""
        <div style="padding:16px 16px 14px;border-bottom:1px solid rgba(247,166,0,0.25);margin-bottom:14px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <img src="data:image/png;base64,{LOGO_ICON_B64}"
                     style="width:42px;height:42px;object-fit:cover;border-radius:6px;">
                <div>
                    <div style="font-size:1.6rem;font-weight:800;color:{GOLD};letter-spacing:-1px;line-height:1;">selgron</div>
                    <div style="font-size:0.6rem;color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:0.12em;">Score de Fornecedores</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        page = st.radio("MENU", options=[
            "🏠  Painel Geral",
            "📊  Painel Comprador",
            "🏭  Painel Fornecedor",
            "⚠️  Acao Prioritaria",
            "📤  Atualizar Base",
        ], label_visibility="visible")

        st.markdown("---")

        n_tot  = len(df)
        n_crit = len(df[df["CLASSE"].str.startswith("E")])
        n_atn  = len(df[df["CLASSE"].str.startswith("D")])
        n_exc  = len(df[df["CLASSE"].str.startswith("A")])
        avg    = df["SCORE_GERAL"].mean()

        st.markdown(f"""
        <div style="font-size:0.65rem;color:{GOLD};font-weight:700;text-transform:uppercase;
                    letter-spacing:0.1em;margin-bottom:8px;">Resumo</div>
        <div style="font-size:0.8rem;line-height:2.1;">
            📦 {n_tot} fornecedores<br>
            📈 Score medio: <b>{pct(avg)}</b><br>
            🟢 Excelentes (A): {n_exc}<br>
            🟠 Atencao (D): {n_atn}<br>
            🔴 Criticos (E): {n_crit}
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.df = None
            st.rerun()

        if st.session_state.data_info:
            st.markdown(f"""
            <div style="font-size:0.62rem;color:rgba(255,255,255,0.3);margin-top:10px;line-height:1.5;">
                {st.session_state.data_info}
            </div>""", unsafe_allow_html=True)

    return page.strip()

# ─── PAINEL GERAL ────────────────────────────────────────────────────────────

def page_dashboard(df: pd.DataFrame):
    st.markdown(logo_header("Painel Geral de Fornecedores",
                            f"Performance consolidada · {datetime.now().strftime('%B %Y')}"),
                unsafe_allow_html=True)

    avg  = df["SCORE_GERAL"].mean()
    avgP = df["SCORE_PRAZO"].mean()
    avgQ = df["SCORE_QUALIDADE"].mean()
    n_crit = len(df[df["CLASSE"].str.startswith("E")])
    n_atn  = len(df[df["CLASSE"].str.startswith("D")])
    n_exc  = len(df[df["CLASSE"].str.startswith("A")])

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(kpi_card("Score Geral", pct(avg), f"Classe {get_class(avg)[0]}", score_bar_color(avg)), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Prazo de Entrega", pct(avgP), f"Peso {int(PESO_PRAZO*100)}%", BAR_BLUE), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Qualidade", pct(avgQ), f"Peso {int(PESO_QUAL*100)}%", BAR_GREEN), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("Fornecedores", str(len(df)), f"{n_exc} excelentes | {df['COMPRADOR'].nunique()} compradores", NAVY), unsafe_allow_html=True)
    with c5: st.markdown(kpi_card("Acao Prioritaria", str(n_crit+n_atn), f"🔴 {n_crit} criticos | 🟠 {n_atn} atencao", C_RED), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Score por comprador (mantido conforme solicitado)
    st.markdown('<div class="sec-title">Score Medio por Comprador</div>', unsafe_allow_html=True)
    bav = df.groupby("COMPRADOR")["SCORE_GERAL"].mean().sort_values(ascending=False).reset_index()
    bav["first"] = bav["COMPRADOR"].apply(lambda x: x.split()[0])
    fig = go.Figure(go.Bar(
        x=bav["first"], y=bav["SCORE_GERAL"]*100,
        marker_color=bav["SCORE_GERAL"].apply(score_bar_color).tolist(),
        text=bav["SCORE_GERAL"].apply(pct), textposition="outside", textfont=dict(size=11),
    ))
    fig.update_layout(
        height=220, margin=dict(l=0,r=0,t=8,b=8),
        yaxis=dict(range=[0,112],ticksuffix="%",showgrid=True,gridcolor="#EEE",tickfont=dict(size=10)),
        xaxis=dict(tickfont=dict(size=11)),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Filtros do ranking ──
    st.markdown('<div class="sec-title">Ranking Completo de Fornecedores</div>', unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns([1.6, 1, 1, 0.7])
    with f1:
        busca = st.text_input("🔍 Buscar fornecedor", placeholder="Digite o nome...", key="geral_busca")
    with f2:
        compradores = ["Todos"] + sorted(df["COMPRADOR"].unique())
        comp_sel = st.selectbox("Comprador", compradores, key="geral_comp")
    with f3:
        classes = ["Todas"] + list(CLASSES.keys())
        cls_sel = st.selectbox("Classe", classes, key="geral_cls")
    with f4:
        st.markdown("<br>", unsafe_allow_html=True)
        show_n = st.selectbox("Exibir", [50, 100, 200, "Todos"], key="geral_n")

    # Aplicar filtros
    df_filt = df.copy()
    if busca:
        df_filt = df_filt[df_filt["FORNECEDOR"].str.upper().str.contains(busca.upper())]
    if comp_sel != "Todos":
        df_filt = df_filt[df_filt["COMPRADOR"] == comp_sel]
    if cls_sel != "Todas":
        df_filt = df_filt[df_filt["CLASSE"] == cls_sel]

    n_show = len(df_filt) if show_n == "Todos" else int(show_n)
    df_show = df_filt.head(n_show)

    st.caption(f"Exibindo {len(df_show)} de {len(df_filt)} fornecedores filtrados")
    st.markdown(ranking_table_html(df_show), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("⬇️ Exportar base filtrada (.csv)",
                       df_filt.to_csv(index=False).encode("utf-8"),
                       "selgron_score_geral.csv","text/csv")

# ─── PAINEL COMPRADOR ────────────────────────────────────────────────────────

def page_por_comprador(df: pd.DataFrame):
    st.markdown(logo_header("Painel Comprador",
                            "Visao individual da carteira de fornecedores"),
                unsafe_allow_html=True)

    buyers = sorted(df["COMPRADOR"].unique())
    sel = st.selectbox("Selecione o Comprador", buyers, key="comp_sel")
    dfb = df[df["COMPRADOR"] == sel].copy()

    avg  = dfb["SCORE_GERAL"].mean()
    avgP = dfb["SCORE_PRAZO"].mean()
    avgQ = dfb["SCORE_QUALIDADE"].mean()
    ranks = df.groupby("COMPRADOR")["SCORE_GERAL"].mean().sort_values(ascending=False)
    rank  = list(ranks.index).index(sel) + 1

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(kpi_card("Score Medio", pct(avg), f"Classe {get_class(avg)[0]}", score_bar_color(avg)), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Prazo", pct(avgP), f"Peso {int(PESO_PRAZO*100)}%", BAR_BLUE), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Qualidade", pct(avgQ), f"Peso {int(PESO_QUAL*100)}%", BAR_GREEN), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("Fornecedores", str(len(dfb)), "na carteira", NAVY), unsafe_allow_html=True)
    with c5: st.markdown(kpi_card("Ranking", f"#{rank}", f"de {len(buyers)} compradores", GOLD), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Pizza com nomes completos (Ajuste 5)
    col_pie, col_scatter = st.columns(2)

    with col_pie:
        st.markdown('<div class="sec-title">Distribuicao por Classe</div>', unsafe_allow_html=True)
        cc_counts = dfb["CLASSE"].value_counts()
        lbs_raw = [c for c in CLASSES if c in cc_counts.index]
        # Nomes completos no label (ex: "EXCELENTE", "CRÍTICO")
        lbs_full  = [CLASSES[c]["emoji"] + " " + CLASSES[c]["label"] for c in lbs_raw]
        fig_pie = go.Figure(go.Pie(
            labels=lbs_full,
            values=[cc_counts[c] for c in lbs_raw],
            marker_colors=[CLASSES[c]["bar"] for c in lbs_raw],
            textinfo="label+value+percent",
            textfont=dict(size=12),
            hole=0.42,
        ))
        fig_pie.update_layout(height=300, margin=dict(l=0,r=0,t=8,b=8),
                              plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_scatter:
        st.markdown('<div class="sec-title">Prazo x Qualidade</div>', unsafe_allow_html=True)
        color_map = {c: CLASSES[c]["bar"] for c in CLASSES}
        fig_sc = px.scatter(dfb, x="SCORE_PRAZO", y="SCORE_QUALIDADE",
                            color="CLASSE", color_discrete_map=color_map,
                            hover_name="FORNECEDOR",
                            labels={"SCORE_PRAZO":"Prazo","SCORE_QUALIDADE":"Qualidade"})
        fig_sc.update_traces(marker=dict(size=8))
        fig_sc.add_vline(x=0.70,line_dash="dash",line_color="#aaa",line_width=1)
        fig_sc.add_hline(y=0.70,line_dash="dash",line_color="#aaa",line_width=1)
        fig_sc.update_layout(
            height=300, margin=dict(l=0,r=0,t=8,b=8),
            xaxis=dict(tickformat=".0%",range=[0,1.08],showgrid=True,gridcolor="#EEE"),
            yaxis=dict(tickformat=".0%",range=[0,1.08],showgrid=True,gridcolor="#EEE"),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(font=dict(size=8),title=""))
        st.plotly_chart(fig_sc, use_container_width=True)

    # Tabela colorida da carteira
    st.markdown('<div class="sec-title">Carteira Completa</div>', unsafe_allow_html=True)

    f1, f2 = st.columns([2, 1])
    with f1:
        busca = st.text_input("🔍 Buscar fornecedor", placeholder="Nome do fornecedor...", key="comp_busca")
    with f2:
        cls_f = st.selectbox("Filtrar por Classe", ["Todas"] + list(CLASSES.keys()), key="comp_cls")

    df_filt = dfb.copy()
    if busca:
        df_filt = df_filt[df_filt["FORNECEDOR"].str.upper().str.contains(busca.upper())]
    if cls_f != "Todas":
        df_filt = df_filt[df_filt["CLASSE"] == cls_f]

    st.caption(f"{len(df_filt)} fornecedores")
    st.markdown(ranking_table_html(df_filt), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(f"⬇️ Exportar carteira de {sel.split()[0]}",
                       dfb.to_csv(index=False).encode("utf-8"),
                       f"selgron_{sel.split()[0].lower()}.csv","text/csv")

# ─── PAINEL FORNECEDOR ───────────────────────────────────────────────────────

def page_ficha(df: pd.DataFrame):
    st.markdown(logo_header("Painel Fornecedor",
                            "Performance individual · Otimizado para impressao e PDF"),
                unsafe_allow_html=True)

    fc1, fc2, _ = st.columns([1.1, 1.1, 1.8])
    with fc1:
        sel_buyer = st.selectbox("Comprador", sorted(df["COMPRADOR"].unique()), key="fich_buyer")
    with fc2:
        dfb = df[df["COMPRADOR"] == sel_buyer]
        sel_sup = st.selectbox("Fornecedor", sorted(dfb["FORNECEDOR"].unique()), key="fich_sup")

    if not sel_sup: return

    row   = dfb[dfb["FORNECEDOR"] == sel_sup].iloc[0]
    cls   = row["CLASSE"]
    cc    = CLASSES.get(cls, CLASSES["E - CRITICO"])
    score = row["SCORE_GERAL"]
    prazo = row["SCORE_PRAZO"]
    qual  = row["SCORE_QUALIDADE"]
    today = datetime.now().strftime("%d/%m/%Y")

    issues = []
    if prazo < 0.70:
        late = int(row["TOTAL_ENTREGAS"]) - int(row["ENTREGA_NO_PRAZO"])
        issues.append(f"prazo de entrega abaixo do minimo ({pct(prazo)}) — {late} entregas atrasadas no periodo")
    if qual < 0.70:
        issues.append(f"qualidade abaixo do minimo ({pct(qual)}) — {int(row['TOTAL_NCS'])} nao conformidades registradas")

    if issues:
        bullets = "".join(f"<li>{i}</li>" for i in issues)
        diag = f"""
        <div style="background:#FFF3CD;border:1px solid #FFC107;border-radius:8px;
                    padding:12px 16px;margin-bottom:16px;">
            <div style="font-size:0.75rem;font-weight:700;color:#856404;margin-bottom:6px;">
                ⚠️ Pontos de Atencao Identificados
            </div>
            <ul style="font-size:0.8rem;color:#6d5402;margin:0;padding-left:18px;line-height:1.8;">
                {bullets}
            </ul>
        </div>"""
    else:
        diag = f"""
        <div style="background:{BG_GREEN};border:1px solid {BAR_GREEN};border-radius:8px;
                    padding:10px 16px;margin-bottom:16px;">
            <div style="font-size:0.78rem;font-weight:700;color:{C_GREEN};">
                ✅ Fornecedor dentro dos parametros esperados.
            </div>
        </div>"""

    meta_rows = ""
    for cname, cdata in CLASSES.items():
        hl  = "font-weight:700;" if cname == cls else ""
        bg  = cdata["bg"] if cname == cls else "white"
        rng = (">= 90%" if cname.startswith("A") else "80 - 89%" if cname.startswith("B")
               else "70 - 79%" if cname.startswith("C") else "60 - 69%" if cname.startswith("D") else "< 60%")
        atual = "← ATUAL" if cname == cls else ""
        meta_rows += f"""
        <tr style="background:{bg};{hl}">
            <td style="padding:5px 14px;color:{cdata['text']};">{cdata['emoji']} {cname}</td>
            <td style="padding:5px 14px;text-align:center;color:{DGRAY};">{rng}</td>
            <td style="padding:5px 14px;text-align:center;font-weight:700;color:{cdata['text']};">{atual}</td>
        </tr>"""

    st.markdown("""
    <div class="no-print" style="margin-bottom:14px;">
        <button onclick="window.print()" style="
            background:#1E2761;color:white;border:none;padding:8px 22px;
            border-radius:6px;cursor:pointer;font-size:0.85rem;font-weight:600;
            font-family:Inter,sans-serif;">
            🖨️ Imprimir / Salvar PDF
        </button>
        <span style="font-size:0.75rem;color:#888;margin-left:12px;">Ctrl+P → Salvar como PDF</span>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="ficha-wrap">
        <div style="background:{NAVY};padding:16px 20px;border-radius:8px;margin-bottom:18px;
                    display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <div style="font-size:0.62rem;color:rgba(255,255,255,0.5);text-transform:uppercase;
                            letter-spacing:0.12em;">Selgron Industrial · Suprimentos</div>
                <div style="font-size:1.25rem;font-weight:700;color:{WHITE};margin:4px 0;">
                    Ficha de Performance de Fornecedor
                </div>
                <div style="font-size:0.78rem;color:{GOLD};">Comprador: {sel_buyer}</div>
            </div>
            <div style="text-align:right;display:flex;align-items:center;gap:10px;">
                <img src="data:image/png;base64,{LOGO_ICON_B64}"
                     style="width:42px;height:42px;object-fit:cover;border-radius:6px;">
                <div>
                    <div style="font-size:1.5rem;font-weight:800;color:{GOLD};letter-spacing:-1px;">selgron</div>
                    <div style="font-size:0.62rem;color:rgba(255,255,255,0.4);">{today}</div>
                </div>
            </div>
        </div>

        <div style="background:{cc['bg']};border-radius:8px;padding:12px 18px;
                    margin-bottom:16px;border-left:4px solid {cc['bar']};">
            <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">Fornecedor</div>
            <div style="font-size:1.25rem;font-weight:700;color:{cc['text']};margin:3px 0;">{sel_sup}</div>
        </div>

        <div style="display:flex;gap:16px;margin-bottom:16px;">
            <div style="flex:1;background:{cc['bg']};border-radius:8px;padding:18px;
                        text-align:center;border:2px solid {cc['bar']};">
                <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;
                            letter-spacing:0.09em;margin-bottom:6px;">Score Geral</div>
                <div style="font-size:3.4rem;font-weight:800;color:{cc['text']};line-height:1;">
                    {score*100:.1f}<span style="font-size:1.6rem;">%</span>
                </div>
                <div style="font-size:0.88rem;font-weight:700;color:{cc['text']};margin-top:6px;">{cls}</div>
                <div style="font-size:0.7rem;color:{DGRAY};margin-top:4px;">
                    Ranking #{int(row['RANK'])} de {len(df)} fornecedores
                </div>
            </div>
            <div style="flex:2;background:#FAFAFA;border-radius:8px;padding:16px;border:1px solid #E8E8E8;">
                <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;
                            letter-spacing:0.09em;margin-bottom:10px;">Detalhamento</div>
                <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
                    <span style="font-size:0.8rem;font-weight:600;color:#333;">
                        🚚 Prazo de Entrega <span style="color:{DGRAY};font-weight:400;">(peso 60%)</span>
                    </span>
                    <span style="font-size:0.85rem;font-weight:700;color:{score_bar_color(prazo)};">{pct(prazo)}</span>
                </div>
                {progress_bar(prazo, score_bar_color(prazo))}
                <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
                    <span style="font-size:0.8rem;font-weight:600;color:#333;">
                        ✅ Qualidade <span style="color:{DGRAY};font-weight:400;">(peso 40%)</span>
                    </span>
                    <span style="font-size:0.85rem;font-weight:700;color:{score_bar_color(qual)};">{pct(qual)}</span>
                </div>
                {progress_bar(qual, score_bar_color(qual))}
                <div style="border-top:1px solid #E8E8E8;margin-top:8px;padding-top:10px;display:flex;gap:24px;">
                    <div>
                        <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">Total Entregas</div>
                        <div style="font-size:1.15rem;font-weight:700;color:{NAVY};">{int(row['TOTAL_ENTREGAS'])}</div>
                    </div>
                    <div>
                        <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">No Prazo</div>
                        <div style="font-size:1.15rem;font-weight:700;color:{BAR_GREEN};">{int(row['ENTREGA_NO_PRAZO'])}</div>
                    </div>
                    <div>
                        <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">Nao Conformidades</div>
                        <div style="font-size:1.15rem;font-weight:700;color:{'#C00000' if row['TOTAL_NCS'] > 0 else BAR_GREEN};">{int(row['TOTAL_NCS'])}</div>
                    </div>
                    <div>
                        <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">Periodo</div>
                        <div style="font-size:1.15rem;font-weight:700;color:{NAVY};">Mai-Jun 2026</div>
                    </div>
                </div>
            </div>
        </div>

        {diag}

        <div style="border:1px solid #E8E8E8;border-radius:8px;overflow:hidden;margin-bottom:16px;">
            <div style="background:{NAVY};color:white;padding:8px 14px;font-size:0.68rem;
                        font-weight:700;text-transform:uppercase;letter-spacing:0.09em;">
                Escala de Classificacao
            </div>
            <table style="width:100%;border-collapse:collapse;font-size:0.8rem;">
                <tr style="background:{LGRAY};">
                    <th style="padding:6px 14px;text-align:left;color:{DGRAY};font-weight:600;">Classe</th>
                    <th style="padding:6px 14px;text-align:center;color:{DGRAY};font-weight:600;">Score</th>
                    <th style="padding:6px 14px;text-align:center;color:{DGRAY};font-weight:600;">Situacao</th>
                </tr>
                {meta_rows}
            </table>
        </div>

        <div style="background:{NAVY};color:rgba(255,255,255,0.65);padding:8px 14px;
                    border-radius:6px;font-size:0.63rem;text-align:center;">
            Selgron Industrial · Suprimentos · Gerado em {today} ·
            Metodologia: 60% Prazo + 40% Qualidade
        </div>
    </div>""", unsafe_allow_html=True)

# ─── ACAO PRIORITARIA ────────────────────────────────────────────────────────

def page_acao(df: pd.DataFrame):
    st.markdown(logo_header("Acao Prioritaria",
                            "Fornecedores Classe D e E · Intervencao necessaria"),
                unsafe_allow_html=True)

    df_e = df[df["CLASSE"].str.startswith("E")].copy()
    df_d = df[df["CLASSE"].str.startswith("D")].copy()
    total = len(df_e) + len(df_d)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(kpi_card("Criticos (E)", str(len(df_e)), "Score < 60%", C_RED), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Atencao (D)", str(len(df_d)), "Score 60-69%", C_ORANGE), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Total c/ Problema", str(total), f"{total/len(df)*100:.1f}% da base", C_AMBER), unsafe_allow_html=True)
    with c4:
        avg_e = df_e["SCORE_GERAL"].mean() if len(df_e) > 0 else 0
        st.markdown(kpi_card("Score Medio Criticos", pct(avg_e) if len(df_e) else "—", "grupo E", C_RED), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab_e, tab_d = st.tabs(["🔴 Criticos — Classe E", "🟠 Atencao — Classe D"])

    for tab, df_seg, tag in [(tab_e,df_e,"E"),(tab_d,df_d,"D")]:
        with tab:
            if len(df_seg) == 0:
                st.success("Nenhum fornecedor nesta categoria.")
                continue

            buyers_ap = ["Todos"] + sorted(df_seg["COMPRADOR"].unique())
            sel_b = st.selectbox("Filtrar por Comprador", buyers_ap, key=f"ap_{tag}")
            dfs = df_seg if sel_b == "Todos" else df_seg[df_seg["COMPRADOR"] == sel_b]

            # Grafico Prazo x Qualidade agrupado
            col_g, col_s = st.columns([1.6, 1])
            with col_g:
                st.markdown('<div class="sec-title">Prazo x Qualidade por Fornecedor</div>', unsafe_allow_html=True)
                ds = dfs.sort_values("SCORE_GERAL", ascending=True)
                fig = go.Figure()
                fig.add_trace(go.Bar(y=ds["FORNECEDOR"].apply(lambda x: x[:38]),
                                     x=ds["SCORE_PRAZO"]*100, name="Prazo (60%)",
                                     orientation="h", marker_color=BAR_BLUE, opacity=0.85))
                fig.add_trace(go.Bar(y=ds["FORNECEDOR"].apply(lambda x: x[:38]),
                                     x=ds["SCORE_QUALIDADE"]*100, name="Qualidade (40%)",
                                     orientation="h", marker_color=BAR_GREEN, opacity=0.85))
                fig.add_vline(x=70,line_dash="dash",line_color="#888",line_width=1,
                              annotation_text="Meta 70%",annotation_font_size=9)
                fig.update_layout(barmode="group",height=max(320,len(dfs)*32),
                                  margin=dict(l=10,r=20,t=8,b=8),
                                  xaxis=dict(range=[0,110],ticksuffix="%",showgrid=True,
                                             gridcolor="#EEE",tickfont=dict(size=9)),
                                  yaxis=dict(tickfont=dict(size=9)),
                                  plot_bgcolor="white",paper_bgcolor="white",
                                  legend=dict(orientation="h",y=1.04,font=dict(size=9)))
                st.plotly_chart(fig, use_container_width=True)

            with col_s:
                st.markdown('<div class="sec-title">Por Comprador</div>', unsafe_allow_html=True)
                bc = dfs["COMPRADOR"].value_counts().reset_index()
                bc.columns = ["Comprador","Qtd"]
                bc["first"] = bc["Comprador"].apply(lambda x: x.split()[0])
                clr = BAR_RED if tag == "E" else BAR_ORANGE
                fig2 = go.Figure(go.Bar(x=bc["first"],y=bc["Qtd"],marker_color=clr,
                                        text=bc["Qtd"],textposition="outside"))
                fig2.update_layout(height=240,margin=dict(l=0,r=0,t=8,b=8),
                                   yaxis=dict(showgrid=True,gridcolor="#EEE",tickfont=dict(size=9)),
                                   xaxis=dict(tickfont=dict(size=9)),
                                   plot_bgcolor="white",paper_bgcolor="white",showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

                st.markdown('<div class="sec-title">Os 5 Piores</div>', unsafe_allow_html=True)
                worst = dfs.nsmallest(5,"SCORE_GERAL")[["FORNECEDOR","COMPRADOR","SCORE_GERAL","TOTAL_NCS"]].copy()
                worst["SCORE_GERAL"] = worst["SCORE_GERAL"].apply(pct)
                worst.columns = ["Fornecedor","Comprador","Score","NCs"]
                st.dataframe(worst, use_container_width=True, hide_index=True)

            st.markdown('<div class="sec-title">Lista Completa</div>', unsafe_allow_html=True)
            st.markdown(ranking_table_html(dfs), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(f"⬇️ Exportar Classe {tag}",
                               dfs.to_csv(index=False).encode("utf-8"),
                               f"selgron_classe_{tag.lower()}.csv","text/csv")

# ─── ATUALIZAR BASE ──────────────────────────────────────────────────────────

def page_atualizar(df: pd.DataFrame):
    st.markdown(logo_header("Atualizar Base de Dados",
                            "Importar dados de novos meses (julho, agosto...)"),
                unsafe_allow_html=True)

    left, right = st.columns([1, 1])

    with left:
        st.markdown(f"""
        <div style="background:{LGRAY};border-radius:10px;padding:20px 24px;border:1px solid {MGRAY};">
            <div class="sec-title">Como preparar a planilha</div>
            <div style="background:{BG_BLUE};border-radius:8px;padding:14px;margin-bottom:12px;">
                <div style="font-size:0.76rem;font-weight:700;color:{C_BLUE};margin-bottom:8px;">
                    OPCAO 1 (Recomendada) — Planilha Score Selgron
                </div>
                <div style="font-size:0.78rem;color:{DGRAY};line-height:1.8;">
                    Aba: <b>SCORE GERAL</b><br>
                    • FORNECEDOR · COMPRADOR<br>
                    • SCORE_GERAL (0 a 1 ou 0 a 100)<br>
                    • SCORE_PRAZO · SCORE_QUALIDADE<br>
                    • TOTAL_ENTREGAS · TOTAL_NCS
                </div>
            </div>
            <div style="background:{BG_AMBER};border-radius:8px;padding:14px;margin-bottom:12px;">
                <div style="font-size:0.76rem;font-weight:700;color:{C_AMBER};margin-bottom:8px;">
                    OPCAO 2 — Dados Brutos de Prazo
                </div>
                <div style="font-size:0.78rem;color:{DGRAY};line-height:1.8;">
                    Aba: <b>BASE</b><br>
                    • COMPRADOR · FORNECEDOR<br>
                    • ATRASO? → "NO PRAZO" ou "ATRASADO"<br>
                    • NF (nota fiscal)
                </div>
            </div>
            <div style="background:{BG_RED};border-radius:8px;padding:10px 14px;
                        font-size:0.75rem;color:{C_RED};">
                ⚠️ A importacao substitui a base atual.
            </div>
        </div>""", unsafe_allow_html=True)

    with right:
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:20px 24px;border:1px solid {MGRAY};">
            <div class="sec-title">Importar Planilha</div>""", unsafe_allow_html=True)

        uploaded = st.file_uploader("Selecione o Excel (.xlsx)", type=["xlsx","xls"], key="uploader_main")

        if uploaded:
            with st.spinner("Processando..."):
                df_new, msg = load_from_upload(uploaded)
            st.success(msg) if not msg.startswith("Erro") else st.error(msg)
            st.markdown(f"**{len(df_new)} fornecedores | {df_new['COMPRADOR'].nunique()} compradores**")
            prev = df_new.head(8).copy()
            for c in ["SCORE_GERAL","SCORE_PRAZO","SCORE_QUALIDADE"]:
                if c in prev.columns: prev[c] = prev[c].apply(pct)
            st.dataframe(prev, use_container_width=True, hide_index=True)
            if st.button("✅ Confirmar e atualizar", type="primary", use_container_width=True):
                st.session_state.df = df_new
                st.session_state.data_info = msg
                st.cache_data.clear()
                st.success("Dashboard atualizado!")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:{LGRAY};border-radius:8px;padding:14px 18px;margin-top:16px;border:1px solid {MGRAY};">
            <div style="font-size:0.68rem;font-weight:700;color:{DGRAY};text-transform:uppercase;margin-bottom:8px;">Base Atual</div>
            <div style="font-size:0.82rem;color:{DGRAY};line-height:2;">
                📦 {len(df)} fornecedores<br>
                👤 {df['COMPRADOR'].nunique()} compradores<br>
                📈 Score medio: <b>{pct(df['SCORE_GERAL'].mean())}</b><br>
                🔴 Criticos (E): {len(df[df['CLASSE'].str.startswith("E")])}<br>
                🟠 Atencao (D): {len(df[df['CLASSE'].str.startswith("D")])}
            </div>
        </div>""", unsafe_allow_html=True)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    init_state()
    inject_css()

    if not st.session_state.authenticated:
        page_login()
        return

    if st.session_state.df is None:
        with st.spinner("Carregando dados..."):
            df, info = load_local_score()
        st.session_state.df = df
        st.session_state.data_info = info

    df   = st.session_state.df
    page = show_sidebar(df)
    key  = page.split("  ", 1)[-1].strip()

    if   "Painel Geral"      in key: page_dashboard(df)
    elif "Painel Comprador"  in key: page_por_comprador(df)
    elif "Painel Fornecedor" in key: page_ficha(df)
    elif "Acao"              in key: page_acao(df)
    elif "Atualizar"         in key: page_atualizar(df)

if __name__ == "__main__":
    main()
