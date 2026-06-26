# ─────────────────────────────────────────────────────────────────────────────
#  SELGRON INDUSTRIAL — Score de Fornecedores v1.0
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

# ─── BRAND & CONSTANTS ───────────────────────────────────────────────────────
NAVY   = "#1E2761"
GOLD   = "#F7A600"
WHITE  = "#FFFFFF"
LGRAY  = "#F5F5F5"
MGRAY  = "#DDDDDD"
DGRAY  = "#595959"

C_GREEN  = "#1F7A4E"; BG_GREEN  = "#E2EFDA"; BAR_GREEN  = "#27AE60"
C_BLUE   = "#1A5276"; BG_BLUE   = "#DDEEFF"; BAR_BLUE   = "#2980B9"
C_AMBER  = "#7D6608"; BG_AMBER  = "#FFF3BF"; BAR_AMBER  = "#F59F00"
C_ORANGE = "#7E5109"; BG_ORANGE = "#FDE8D8"; BAR_ORANGE = "#E67E22"
C_RED    = "#C00000"; BG_RED    = "#FCE4D6"; BAR_RED    = "#E74C3C"

CLASSES = {
    "A - EXCELENTE": dict(min=0.90, max=1.01, bg=BG_GREEN,  text=C_GREEN,  bar=BAR_GREEN,  emoji="🟢"),
    "B - BOM":       dict(min=0.80, max=0.90, bg=BG_BLUE,   text=C_BLUE,   bar=BAR_BLUE,   emoji="🔵"),
    "C - REGULAR":   dict(min=0.70, max=0.80, bg=BG_AMBER,  text=C_AMBER,  bar=BAR_AMBER,  emoji="🟡"),
    "D - ATENCAO":   dict(min=0.60, max=0.70, bg=BG_ORANGE, text=C_ORANGE, bar=BAR_ORANGE, emoji="🟠"),
    "E - CRITICO":   dict(min=0.00, max=0.60, bg=BG_RED,    text=C_RED,    bar=BAR_RED,    emoji="🔴"),
}

# Also register the em-dash variants for matching uploaded files
CLASS_ALIASES = {
    "A – EXCELENTE": "A - EXCELENTE",
    "B – BOM":       "B - BOM",
    "C – REGULAR":   "C - REGULAR",
    "D – ATENÇÃO":   "D - ATENCAO",
    "D – ATENCAO":   "D - ATENCAO",
    "E – CRÍTICO":   "E - CRITICO",
    "E – CRITICO":   "E - CRITICO",
}

PESO_PRAZO = 0.60
PESO_QUAL  = 0.40

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def get_class(score: float) -> str:
    for name, c in CLASSES.items():
        if c["min"] <= score < c["max"]:
            return name
    return "E - CRITICO"

def normalise_class(raw: str) -> str:
    raw = str(raw).strip()
    if raw in CLASSES:
        return raw
    if raw in CLASS_ALIASES:
        return CLASS_ALIASES[raw]
    # fuzzy: match first letter
    letter = raw[0].upper() if raw else "E"
    for k in CLASSES:
        if k.startswith(letter):
            return k
    return "E - CRITICO"

def score_bar_color(score: float) -> str:
    return CLASSES[get_class(score)]["bar"]

def pct(v: float) -> str:
    return f"{v * 100:.1f}%"

def kpi_card(label: str, value: str, sub: str = "", color: str = NAVY) -> str:
    sub_html = f"<div class='kpi-sub'>{sub}</div>" if sub else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color};">{value}</div>
        {sub_html}
    </div>"""

def progress_bar(v: float, color: str) -> str:
    pct_w = min(v * 100, 100)
    return f"""
    <div style="background:#E8E8E8;border-radius:4px;height:9px;margin:3px 0 10px 0;">
        <div style="background:{color};width:{pct_w:.1f}%;height:9px;border-radius:4px;"></div>
    </div>"""

# ─── CSS ─────────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family:'Inter','Calibri',sans-serif; }}
    #MainMenu, footer, header {{ visibility:hidden; }}

    [data-testid="stSidebar"] {{ background:{NAVY} !important; min-width:220px !important; }}
    [data-testid="stSidebar"] * {{ color:{WHITE} !important; }}
    [data-testid="stSidebar"] hr {{ border-color:rgba(255,255,255,0.12) !important; }}

    [data-testid="stSidebar"] .stRadio > label {{
        color:{GOLD} !important; font-size:0.68rem !important;
        font-weight:700 !important; text-transform:uppercase; letter-spacing:0.09em;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
        color:{WHITE} !important; font-size:0.84rem !important;
        font-weight:500 !important; text-transform:none; letter-spacing:0; padding:6px 0;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{
        color:{GOLD} !important;
    }}
    [data-testid="stSidebar"] .stSelectbox label {{
        color:{GOLD} !important; font-size:0.68rem !important;
        font-weight:700; text-transform:uppercase; letter-spacing:0.09em;
    }}
    [data-testid="stSidebar"] .stSelectbox > div > div {{
        background:rgba(255,255,255,0.08) !important;
        border:1px solid rgba(247,166,0,0.35) !important; border-radius:6px;
    }}

    [data-testid="stAppViewContainer"] > .main {{ background:#F4F5F9; }}

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

    .sec-title {{
        font-size:0.72rem; font-weight:700; color:{DGRAY};
        text-transform:uppercase; letter-spacing:0.09em;
        margin:20px 0 10px 0; padding-bottom:6px; border-bottom:2px solid {GOLD};
    }}

    .page-header {{
        background:{NAVY}; color:{WHITE}; padding:16px 24px;
        border-radius:10px; margin-bottom:20px;
        display:flex; align-items:center; justify-content:space-between;
    }}
    .page-header h1 {{ margin:0; font-size:1.35rem; font-weight:700; color:{WHITE}; }}
    .page-header .sub {{ font-size:0.8rem; color:{GOLD}; margin-top:2px; }}
    .ph-logo {{ font-size:1.6rem; font-weight:800; color:{GOLD}; letter-spacing:-1px; opacity:0.85; }}

    .ficha-wrap {{
        background:{WHITE}; border:1px solid {MGRAY}; border-radius:10px;
        padding:28px 32px; max-width:740px; margin:0 auto;
        box-shadow:0 4px 20px rgba(30,39,97,0.1);
    }}

    .login-wrap {{
        max-width:370px; margin:7vh auto; background:{WHITE};
        border-radius:12px; padding:40px 36px;
        box-shadow:0 8px 40px rgba(30,39,97,0.15);
        border-top:4px solid {GOLD}; text-align:center;
    }}

    .stButton > button[kind="primary"] {{
        background:{NAVY} !important; color:{WHITE} !important;
        border:none !important; border-radius:6px !important; font-weight:600 !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background:{GOLD} !important; color:{NAVY} !important;
    }}

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
    buyers_cfg = [
        ("Edson Carlos Borges",               45, 0.91, 0.83),
        ("Arthur da Silva",                    38, 0.85, 0.78),
        ("Tatiana Goncalves",                  32, 0.82, 0.75),
        ("Jair Wermuth",                       40, 0.58, 0.69),
        ("Nithael Alexandre Krepsky Silveira", 35, 0.76, 0.71),
        ("Lara Beatriz Schmidt",               30, 0.79, 0.73),
        ("Isabela Costa",                      33, 0.84, 0.77),
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

# ─── DATA NORMALISE ──────────────────────────────────────────────────────────

def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "Fornecedor":"FORNECEDOR","fornecedor":"FORNECEDOR",
        "Comprador":"COMPRADOR","comprador":"COMPRADOR",
        "Score Geral":"SCORE_GERAL","SCORE GERAL":"SCORE_GERAL","Score_Geral":"SCORE_GERAL",
        "Score Prazo":"SCORE_PRAZO","SCORE PRAZO":"SCORE_PRAZO","Score_Prazo":"SCORE_PRAZO",
        "Score Qualidade":"SCORE_QUALIDADE","SCORE QUALIDADE":"SCORE_QUALIDADE","Score_Qualidade":"SCORE_QUALIDADE",
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
        if col not in df.columns:
            df[col] = 0
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
        raise ValueError("Colunas FORNECEDOR, COMPRADOR, ATRASO ? nao encontradas")
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

# ─── DATA LOAD ────────────────────────────────────────────────────────────────

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
                return df, f"Arquivo: {path} | Aba: {sheet} | {len(df)} fornecedores"
            except:
                pass
    return _sample_data(), "DEMO — coloque Score_Fornecedores_Selgron_v7.xlsx na pasta do app.py ou importe em 'Atualizar Base'"

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

# ─── PAGE: LOGIN ──────────────────────────────────────────────────────────────

def page_login():
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(145deg, {NAVY} 0%, #0d1540 100%);
    }}
    </style>
    <div class="login-wrap">
        <div style="font-size:2.4rem;font-weight:800;color:{NAVY};letter-spacing:-1px;margin-bottom:2px;">
            sel<span style="color:{GOLD};">g</span>ron
        </div>
        <div style="font-size:0.82rem;color:{DGRAY};margin-bottom:28px;">
            Sistema de Score de Fornecedores
        </div>
    </div>
    """, unsafe_allow_html=True)
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
        st.markdown(f"""
        <div style="padding:20px 16px 14px;border-bottom:1px solid rgba(247,166,0,0.25);margin-bottom:14px;">
            <div style="font-size:2rem;font-weight:800;color:{GOLD};letter-spacing:-2px;line-height:1;">selgron</div>
            <div style="font-size:0.64rem;color:rgba(255,255,255,0.45);text-transform:uppercase;
                        letter-spacing:0.12em;margin-top:2px;">Score de Fornecedores</div>
        </div>""", unsafe_allow_html=True)

        page = st.radio("MENU", options=[
            "🏠  Dashboard Geral",
            "📊  Por Comprador",
            "🏭  Ficha do Fornecedor",
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
                    letter-spacing:0.1em;margin-bottom:8px;">Resumo Rapido</div>
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
            <div style="font-size:0.62rem;color:rgba(255,255,255,0.35);margin-top:10px;line-height:1.5;">
                {st.session_state.data_info}
            </div>""", unsafe_allow_html=True)

    return page.strip()

# ─── PAGE: DASHBOARD GERAL ────────────────────────────────────────────────────

def page_dashboard(df: pd.DataFrame):
    st.markdown(f"""
    <div class="page-header">
        <div>
            <h1>Dashboard Geral de Fornecedores</h1>
            <div class="sub">Performance consolidada · {datetime.now().strftime("%B %Y")}</div>
        </div>
        <div class="ph-logo">selgron</div>
    </div>""", unsafe_allow_html=True)

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
    left, right = st.columns([1.65, 1])

    with left:
        st.markdown('<div class="sec-title">Top 30 Fornecedores — Ranking Geral</div>', unsafe_allow_html=True)
        top30 = df.head(30).copy()
        fig = go.Figure(go.Bar(
            y=top30["FORNECEDOR"].apply(lambda x: x[:35])[::-1],
            x=(top30["SCORE_GERAL"]*100)[::-1],
            orientation="h",
            marker_color=top30["SCORE_GERAL"].apply(score_bar_color).tolist()[::-1],
            text=(top30["SCORE_GERAL"]*100).apply(lambda v: f"{v:.1f}%")[::-1],
            textposition="outside", textfont=dict(size=9),
        ))
        fig.update_layout(
            height=540, margin=dict(l=10,r=55,t=8,b=8),
            xaxis=dict(range=[0,112],showgrid=True,gridcolor="#EEE",ticksuffix="%",tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=9)),
            plot_bgcolor="white",paper_bgcolor="white",showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown('<div class="sec-title">Distribuicao por Classe</div>', unsafe_allow_html=True)
        cc  = df["CLASSE"].value_counts()
        lbs = [c for c in CLASSES if c in cc.index]
        fig2 = go.Figure(go.Pie(
            labels=[c.split("-")[0].strip() for c in lbs],
            values=[cc[c] for c in lbs],
            marker_colors=[CLASSES[c]["bar"] for c in lbs],
            textinfo="label+value+percent", textfont=dict(size=11), hole=0.42,
        ))
        fig2.update_layout(height=265,margin=dict(l=0,r=0,t=8,b=8),
                           plot_bgcolor="white",paper_bgcolor="white",showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="sec-title">Score Medio por Comprador</div>', unsafe_allow_html=True)
        bav = df.groupby("COMPRADOR")["SCORE_GERAL"].mean().sort_values(ascending=False).reset_index()
        bav["first"] = bav["COMPRADOR"].apply(lambda x: x.split()[0])
        fig3 = go.Figure(go.Bar(
            x=bav["first"], y=bav["SCORE_GERAL"]*100,
            marker_color=bav["SCORE_GERAL"].apply(score_bar_color).tolist(),
            text=bav["SCORE_GERAL"].apply(pct), textposition="outside", textfont=dict(size=10),
        ))
        fig3.update_layout(height=235,margin=dict(l=0,r=0,t=8,b=8),
                           yaxis=dict(range=[0,112],ticksuffix="%",showgrid=True,gridcolor="#EEE",tickfont=dict(size=9)),
                           xaxis=dict(tickfont=dict(size=9)),
                           plot_bgcolor="white",paper_bgcolor="white",showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<div class="sec-title">Tabela Completa</div>', unsafe_allow_html=True)
    disp = df[["RANK","FORNECEDOR","COMPRADOR","SCORE_GERAL","SCORE_PRAZO","SCORE_QUALIDADE",
               "TOTAL_ENTREGAS","TOTAL_NCS","CLASSE"]].copy()
    for c in ["SCORE_GERAL","SCORE_PRAZO","SCORE_QUALIDADE"]:
        disp[c] = disp[c].apply(pct)
    disp.columns = ["#","Fornecedor","Comprador","Score Geral","Prazo","Qualidade","Entregas","NCs","Classe"]
    st.dataframe(disp, use_container_width=True, height=420)
    st.download_button("⬇️ Exportar base completa (.csv)",
                       df.to_csv(index=False).encode("utf-8"),
                       "selgron_score_geral.csv","text/csv")

# ─── PAGE: POR COMPRADOR ──────────────────────────────────────────────────────

def page_por_comprador(df: pd.DataFrame):
    st.markdown(f"""
    <div class="page-header">
        <div><h1>Dashboard por Comprador</h1>
        <div class="sub">Visao individual da carteira de fornecedores</div></div>
        <div class="ph-logo">selgron</div>
    </div>""", unsafe_allow_html=True)

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
    left, right = st.columns([1.5, 1])

    with left:
        st.markdown('<div class="sec-title">Ranking da Carteira</div>', unsafe_allow_html=True)
        ds = dfb.sort_values("SCORE_GERAL", ascending=True)
        fig = go.Figure(go.Bar(
            y=ds["FORNECEDOR"].apply(lambda x: x[:38]),
            x=ds["SCORE_GERAL"]*100,
            orientation="h",
            marker_color=ds["SCORE_GERAL"].apply(score_bar_color).tolist(),
            text=(ds["SCORE_GERAL"]*100).apply(lambda v: f"{v:.1f}%"),
            textposition="outside", textfont=dict(size=9),
        ))
        fig.update_layout(
            height=max(320,len(dfb)*26), margin=dict(l=10,r=55,t=8,b=8),
            xaxis=dict(range=[0,115],showgrid=True,gridcolor="#EEE",ticksuffix="%",tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=9)),
            plot_bgcolor="white",paper_bgcolor="white",showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown('<div class="sec-title">Distribuicao por Classe</div>', unsafe_allow_html=True)
        cc  = dfb["CLASSE"].value_counts()
        lbs = [c for c in CLASSES if c in cc.index]
        fig2 = go.Figure(go.Pie(
            labels=[c.split("-")[0].strip() for c in lbs],
            values=[cc[c] for c in lbs],
            marker_colors=[CLASSES[c]["bar"] for c in lbs],
            textinfo="label+value+percent",textfont=dict(size=11),hole=0.42,
        ))
        fig2.update_layout(height=260,margin=dict(l=0,r=0,t=8,b=8),
                           plot_bgcolor="white",paper_bgcolor="white",showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="sec-title">Prazo x Qualidade</div>', unsafe_allow_html=True)
        color_map = {c: CLASSES[c]["bar"] for c in CLASSES}
        fig3 = px.scatter(dfb, x="SCORE_PRAZO", y="SCORE_QUALIDADE",
                          color="CLASSE", color_discrete_map=color_map,
                          hover_name="FORNECEDOR",
                          labels={"SCORE_PRAZO":"Prazo","SCORE_QUALIDADE":"Qualidade"})
        fig3.update_traces(marker=dict(size=8))
        fig3.add_vline(x=0.70,line_dash="dash",line_color="#aaa",line_width=1)
        fig3.add_hline(y=0.70,line_dash="dash",line_color="#aaa",line_width=1)
        fig3.update_layout(height=290,margin=dict(l=0,r=0,t=8,b=8),
                           xaxis=dict(tickformat=".0%",range=[0,1.08],showgrid=True,gridcolor="#EEE"),
                           yaxis=dict(tickformat=".0%",range=[0,1.08],showgrid=True,gridcolor="#EEE"),
                           plot_bgcolor="white",paper_bgcolor="white",
                           legend=dict(font=dict(size=8),title=""))
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<div class="sec-title">Carteira Completa</div>', unsafe_allow_html=True)
    disp = dfb[["RANK","FORNECEDOR","SCORE_GERAL","SCORE_PRAZO","SCORE_QUALIDADE",
                "TOTAL_ENTREGAS","TOTAL_NCS","CLASSE"]].copy()
    for c in ["SCORE_GERAL","SCORE_PRAZO","SCORE_QUALIDADE"]:
        disp[c] = disp[c].apply(pct)
    disp.columns = ["# Geral","Fornecedor","Score Geral","Prazo","Qualidade","Entregas","NCs","Classe"]
    st.dataframe(disp, use_container_width=True, height=380)
    st.download_button(f"⬇️ Exportar carteira de {sel.split()[0]}",
                       dfb.to_csv(index=False).encode("utf-8"),
                       f"selgron_{sel.split()[0].lower()}.csv","text/csv")

# ─── PAGE: FICHA DO FORNECEDOR ────────────────────────────────────────────────

def page_ficha(df: pd.DataFrame):
    st.markdown(f"""
    <div class="page-header no-print">
        <div><h1>Ficha do Fornecedor</h1>
        <div class="sub">Painel de performance individual · Otimizado para impressao e PDF</div></div>
        <div class="ph-logo">selgron</div>
    </div>""", unsafe_allow_html=True)

    fc1, fc2, _ = st.columns([1.1, 1.1, 1.8])
    with fc1:
        sel_buyer = st.selectbox("Comprador", sorted(df["COMPRADOR"].unique()), key="fich_buyer")
    with fc2:
        dfb = df[df["COMPRADOR"] == sel_buyer]
        sel_sup = st.selectbox("Fornecedor", sorted(dfb["FORNECEDOR"].unique()), key="fich_sup")

    if not sel_sup:
        return

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
                ✅ Fornecedor dentro dos parametros esperados. Bom desempenho — mantenha as condicoes atuais.
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
                            letter-spacing:0.12em;">Selgron Industrial · Departamento de Suprimentos</div>
                <div style="font-size:1.25rem;font-weight:700;color:{WHITE};margin:4px 0;">
                    Ficha de Performance de Fornecedor
                </div>
                <div style="font-size:0.78rem;color:{GOLD};">Comprador: {sel_buyer}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.65rem;font-weight:800;color:{GOLD};letter-spacing:-1px;">selgron</div>
                <div style="font-size:0.62rem;color:rgba(255,255,255,0.4);">{today}</div>
            </div>
        </div>

        <div style="background:{cc['bg']};border-radius:8px;padding:12px 18px;
                    margin-bottom:16px;border-left:4px solid {cc['bar']};">
            <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;
                        letter-spacing:0.09em;">Fornecedor</div>
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

                <div style="border-top:1px solid #E8E8E8;margin-top:8px;padding-top:10px;
                            display:flex;gap:24px;">
                    <div>
                        <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">
                            Total Entregas</div>
                        <div style="font-size:1.15rem;font-weight:700;color:{NAVY};">{int(row['TOTAL_ENTREGAS'])}</div>
                    </div>
                    <div>
                        <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">
                            No Prazo</div>
                        <div style="font-size:1.15rem;font-weight:700;color:{BAR_GREEN};">{int(row['ENTREGA_NO_PRAZO'])}</div>
                    </div>
                    <div>
                        <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">
                            Nao Conformidades</div>
                        <div style="font-size:1.15rem;font-weight:700;
                                    color:{C_RED if row['TOTAL_NCS'] > 0 else C_GREEN};">{int(row['TOTAL_NCS'])}</div>
                    </div>
                    <div>
                        <div style="font-size:0.62rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">
                            Periodo</div>
                        <div style="font-size:1.15rem;font-weight:700;color:{NAVY};">Mai-Jun 2026</div>
                    </div>
                </div>
            </div>
        </div>

        {diag}

        <div style="border:1px solid #E8E8E8;border-radius:8px;overflow:hidden;margin-bottom:16px;">
            <div style="background:{NAVY};color:white;padding:8px 14px;font-size:0.68rem;
                        font-weight:700;text-transform:uppercase;letter-spacing:0.09em;">
                Escala de Classificacao de Fornecedores
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
            Metodologia: 60% Prazo de Entrega + 40% Qualidade (Inspecao de Recebimento)
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── PAGE: ACAO PRIORITARIA ───────────────────────────────────────────────────

def page_acao(df: pd.DataFrame):
    st.markdown(f"""
    <div class="page-header">
        <div><h1>Acao Prioritaria</h1>
        <div class="sub">Fornecedores Classe D e E · Intervencao necessaria</div></div>
        <div class="ph-logo">selgron</div>
    </div>""", unsafe_allow_html=True)

    df_e = df[df["CLASSE"].str.startswith("E")].copy()
    df_d = df[df["CLASSE"].str.startswith("D")].copy()
    total = len(df_e) + len(df_d)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(kpi_card("Criticos (E)", str(len(df_e)), "Score < 60%", C_RED), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Atencao (D)", str(len(df_d)), "Score 60-69%", C_ORANGE), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Total c/ Problema", str(total), f"{total/len(df)*100:.1f}% da base", C_AMBER), unsafe_allow_html=True)
    with c4:
        avg_e = df_e["SCORE_GERAL"].mean() if len(df_e) > 0 else 0
        st.markdown(kpi_card("Score Medio (E)", pct(avg_e) if len(df_e) else "—", "grupo critico", C_RED), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab_e, tab_d = st.tabs(["🔴 Criticos — Classe E", "🟠 Atencao — Classe D"])

    for tab, df_seg, tag, clr in [(tab_e,df_e,"E",BAR_RED),(tab_d,df_d,"D",BAR_ORANGE)]:
        with tab:
            if len(df_seg) == 0:
                st.success("Nenhum fornecedor nesta categoria.")
                continue

            buyers_ap = ["Todos"] + sorted(df_seg["COMPRADOR"].unique())
            sel_b = st.selectbox("Filtrar por Comprador", buyers_ap, key=f"ap_{tag}")
            dfs = df_seg if sel_b == "Todos" else df_seg[df_seg["COMPRADOR"] == sel_b]

            left, right = st.columns([1.6, 1])

            with left:
                st.markdown('<div class="sec-title">Prazo x Qualidade por Fornecedor</div>', unsafe_allow_html=True)
                ds = dfs.sort_values("SCORE_GERAL", ascending=True)
                fig = go.Figure()
                fig.add_trace(go.Bar(y=ds["FORNECEDOR"].apply(lambda x: x[:38]),
                                     x=ds["SCORE_PRAZO"]*100,
                                     name="Prazo (60%)",orientation="h",
                                     marker_color=BAR_BLUE,opacity=0.85))
                fig.add_trace(go.Bar(y=ds["FORNECEDOR"].apply(lambda x: x[:38]),
                                     x=ds["SCORE_QUALIDADE"]*100,
                                     name="Qualidade (40%)",orientation="h",
                                     marker_color=BAR_GREEN,opacity=0.85))
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

            with right:
                st.markdown('<div class="sec-title">Por Comprador</div>', unsafe_allow_html=True)
                bc = dfs["COMPRADOR"].value_counts().reset_index()
                bc.columns = ["Comprador","Qtd"]
                bc["first"] = bc["Comprador"].apply(lambda x: x.split()[0])
                fig2 = go.Figure(go.Bar(x=bc["first"],y=bc["Qtd"],marker_color=clr,
                                        text=bc["Qtd"],textposition="outside"))
                fig2.update_layout(height=280,margin=dict(l=0,r=0,t=8,b=8),
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
            disp = dfs[["RANK","FORNECEDOR","COMPRADOR","SCORE_GERAL","SCORE_PRAZO",
                         "SCORE_QUALIDADE","TOTAL_ENTREGAS","TOTAL_NCS"]].copy()
            for c in ["SCORE_GERAL","SCORE_PRAZO","SCORE_QUALIDADE"]:
                disp[c] = disp[c].apply(pct)
            disp.columns = ["#","Fornecedor","Comprador","Score","Prazo","Qualidade","Entregas","NCs"]
            st.dataframe(disp, use_container_width=True, height=350)
            st.download_button(f"⬇️ Exportar Classe {tag}",
                               dfs.to_csv(index=False).encode("utf-8"),
                               f"selgron_classe_{tag.lower()}.csv","text/csv")

# ─── PAGE: ATUALIZAR BASE ─────────────────────────────────────────────────────

def page_atualizar(df: pd.DataFrame):
    st.markdown(f"""
    <div class="page-header">
        <div><h1>Atualizar Base de Dados</h1>
        <div class="sub">Importar dados de novos meses (julho, agosto...)</div></div>
        <div class="ph-logo">selgron</div>
    </div>""", unsafe_allow_html=True)

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
                    Aba obrigatoria: <b>SCORE GERAL</b><br>
                    Colunas:<br>
                    • FORNECEDOR · COMPRADOR<br>
                    • SCORE_GERAL (0 a 1 ou 0 a 100)<br>
                    • SCORE_PRAZO · SCORE_QUALIDADE<br>
                    • TOTAL_ENTREGAS · TOTAL_NCS
                </div>
            </div>

            <div style="background:{BG_AMBER};border-radius:8px;padding:14px;margin-bottom:12px;">
                <div style="font-size:0.76rem;font-weight:700;color:{C_AMBER};margin-bottom:8px;">
                    OPCAO 2 — Dados Brutos de Prazo (PRAZO_ENTREGA)
                </div>
                <div style="font-size:0.78rem;color:{DGRAY};line-height:1.8;">
                    Aba obrigatoria: <b>BASE</b><br>
                    Colunas:<br>
                    • COMPRADOR · FORNECEDOR<br>
                    • ATRASO ? → "NO PRAZO" ou "ATRASADO"<br>
                    • NF (numero da nota fiscal)<br><br>
                    <i>Qualidade = 100% se nao houver planilha de NCs.</i>
                </div>
            </div>

            <div style="background:{BG_RED};border-radius:8px;padding:10px 14px;
                        font-size:0.75rem;color:{C_RED};">
                ⚠️ A importacao substitui a base atual. Faca backup antes.
            </div>
        </div>""", unsafe_allow_html=True)

    with right:
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:20px 24px;border:1px solid {MGRAY};">
            <div class="sec-title">Importar Planilha</div>""", unsafe_allow_html=True)

        uploaded = st.file_uploader("Selecione o Excel (.xlsx)",
                                    type=["xlsx","xls"], key="uploader_main")

        if uploaded:
            with st.spinner("Processando..."):
                df_new, msg = load_from_upload(uploaded)

            if msg.startswith("✅") or msg.startswith("Aba"):
                st.success(msg)
            else:
                st.error(msg)

            prev = df_new.head(8).copy()
            for c in ["SCORE_GERAL","SCORE_PRAZO","SCORE_QUALIDADE"]:
                if c in prev.columns:
                    prev[c] = prev[c].apply(pct)
            st.markdown(f"**{len(df_new)} fornecedores | {df_new['COMPRADOR'].nunique()} compradores**")
            st.dataframe(prev, use_container_width=True, hide_index=True)

            if st.button("✅ Confirmar e atualizar dashboard", type="primary", use_container_width=True):
                st.session_state.df = df_new
                st.session_state.data_info = msg
                st.cache_data.clear()
                st.success("Dashboard atualizado!")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:{LGRAY};border-radius:8px;padding:14px 18px;
                    margin-top:16px;border:1px solid {MGRAY};">
            <div style="font-size:0.68rem;font-weight:700;color:{DGRAY};
                        text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Base Atual</div>
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
        st.session_state.df  = df
        st.session_state.data_info = info

    df   = st.session_state.df
    page = show_sidebar(df)

    # Strip emoji prefix and match
    key = page.split("  ", 1)[-1].strip()

    if   "Dashboard Geral"   in key: page_dashboard(df)
    elif "Por Comprador"     in key: page_por_comprador(df)
    elif "Ficha"             in key: page_ficha(df)
    elif "Acao"              in key: page_acao(df)
    elif "Atualizar"         in key: page_atualizar(df)

if __name__ == "__main__":
    main()
