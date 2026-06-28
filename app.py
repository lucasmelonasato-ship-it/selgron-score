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

# ─── Paleta moderna (dashboard premium) ──────────────────────────────────────
NAVY_900 = "#141A3C"   # navy profundo (fundos escuros, hero)
NAVY_700 = "#1E2761"   # navy Selgron (identidade)
NAVY_500 = "#2E3A82"   # navy claro (hover, acentos)
GOLD_500 = "#F7A600"   # dourado Selgron
GOLD_400 = "#FFB627"   # dourado claro (highlights)
INK      = "#0F1320"   # texto quase preto
SLATE    = "#64748B"   # texto secundário moderno
SLATE_2  = "#94A3B8"   # texto terciário
CLOUD    = "#F8FAFC"   # fundo geral claro (cinza-azulado)
CARD     = "#FFFFFF"   # fundo de cards
LINE     = "#E8ECF2"   # bordas sutis
GLASS    = "rgba(255,255,255,0.7)"

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

# ─── TEMA PLOTLY (identidade Selgron) ────────────────────────────────────────
PLOTLY_FONT = "Inter, 'Plus Jakarta Sans', sans-serif"

def style_fig(fig, height=240, showlegend=False, legend_opts=None):
    """Aplica o tema visual Selgron a qualquer gráfico Plotly."""
    fig.update_layout(
        height=height,
        margin=dict(l=6, r=10, t=10, b=6),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=PLOTLY_FONT, size=11, color=INK),
        showlegend=showlegend,
        hoverlabel=dict(
            bgcolor=NAVY_700, font_size=12,
            font_family=PLOTLY_FONT, font_color="white",
            bordercolor=NAVY_700,
        ),
        bargap=0.32,
    )
    if legend_opts:
        fig.update_layout(legend=legend_opts)
    # eixos limpos: sem linha pesada, grid sutil
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False,
                     tickfont=dict(size=10, color=SLATE), title=None)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(100,116,139,0.10)", gridwidth=1,
                     zeroline=False, showline=False,
                     tickfont=dict(size=10, color=SLATE), title=None)
    return fig

# ─── CSS ─────────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {{
        --navy900:{NAVY_900}; --navy700:{NAVY_700}; --navy500:{NAVY_500};
        --gold:{GOLD_500}; --gold400:{GOLD_400};
        --ink:{INK}; --slate:{SLATE}; --slate2:{SLATE_2};
        --cloud:{CLOUD}; --card:{CARD}; --line:{LINE};
    }}

    html, body, [class*="css"] {{
        font-family:'Inter','Plus Jakarta Sans',sans-serif;
        color:{INK};
    }}
    h1,h2,h3,.display {{ font-family:'Plus Jakarta Sans','Inter',sans-serif; }}
    #MainMenu, footer, header {{ visibility:hidden; }}

    /* ── App background: gradiente sutil ── */
    [data-testid="stAppViewContainer"] {{
        background:
          radial-gradient(1200px 600px at 90% -10%, rgba(247,166,0,0.06), transparent 60%),
          radial-gradient(900px 500px at -10% 0%, rgba(46,58,130,0.07), transparent 55%),
          {CLOUD};
    }}
    .block-container {{ padding-top:1.4rem !important; max-width:1320px; }}

    /* ── Sidebar premium (navy translúcido) ── */
    [data-testid="stSidebar"] {{
        background:linear-gradient(180deg, {NAVY_900} 0%, {NAVY_700} 100%) !important;
        border-right:1px solid rgba(247,166,0,0.15);
        min-width:235px !important;
    }}
    [data-testid="stSidebar"] * {{ color:#E8EBF5 !important; }}
    [data-testid="stSidebar"] hr {{ border-color:rgba(255,255,255,0.08) !important; }}
    [data-testid="stSidebar"] .stRadio > label {{
        color:{GOLD_400} !important; font-size:0.62rem !important;
        font-weight:700 !important; text-transform:uppercase; letter-spacing:0.14em;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
        color:#E8EBF5 !important; font-size:0.85rem !important;
        font-weight:500 !important; padding:8px 10px; border-radius:8px;
        transition:all 0.15s; margin:1px 0;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{
        color:#fff !important; background:rgba(247,166,0,0.12);
    }}
    [data-testid="stSidebar"] .stSelectbox label {{
        color:{GOLD_400} !important; font-size:0.62rem !important;
        font-weight:700; text-transform:uppercase; letter-spacing:0.12em;
    }}
    [data-testid="stSidebar"] .stSelectbox > div > div {{
        background:rgba(255,255,255,0.06) !important;
        border:1px solid rgba(247,166,0,0.25) !important; border-radius:9px;
    }}
    [data-testid="stSidebarCollapseButton"] button {{
        background:rgba(247,166,0,0.18) !important;
        border:1px solid rgba(247,166,0,0.4) !important;
        border-radius:8px !important; color:{GOLD_400} !important;
    }}
    [data-testid="stSidebarCollapseButton"] button:hover {{
        background:{GOLD_500} !important; color:{NAVY_900} !important;
    }}

    /* ── KPI cards (glass + hover lift) ── */
    .kpi-card {{
        background:{CARD}; border-radius:18px; padding:18px 20px;
        border:1px solid {LINE};
        box-shadow:0 1px 2px rgba(16,19,32,0.04), 0 8px 24px rgba(16,19,32,0.05);
        height:100%; position:relative; overflow:hidden;
        transition:transform 0.18s ease, box-shadow 0.18s ease;
    }}
    .kpi-card::before {{
        content:""; position:absolute; top:0; left:0; right:0; height:3px;
        background:linear-gradient(90deg, {GOLD_500}, {GOLD_400});
        opacity:0.9;
    }}
    .kpi-card:hover {{
        transform:translateY(-3px);
        box-shadow:0 2px 4px rgba(16,19,32,0.05), 0 16px 40px rgba(16,19,32,0.10);
    }}
    .kpi-label {{
        font-size:0.64rem; font-weight:700; text-transform:uppercase;
        letter-spacing:0.1em; color:{SLATE}; margin-bottom:8px;
    }}
    .kpi-value {{
        font-family:'Plus Jakarta Sans',sans-serif;
        font-size:2.1rem; font-weight:800; color:{NAVY_700}; line-height:1;
        letter-spacing:-0.02em;
    }}
    .kpi-sub {{ font-size:0.74rem; color:{SLATE}; margin-top:7px; font-weight:500; }}

    /* ── Section title ── */
    .sec-title {{
        font-size:0.66rem; font-weight:700; color:{SLATE};
        text-transform:uppercase; letter-spacing:0.13em;
        margin:24px 0 12px 0; padding-bottom:0;
        display:flex; align-items:center; gap:10px;
    }}
    .sec-title::after {{
        content:""; flex:1; height:1px;
        background:linear-gradient(90deg, {LINE}, transparent);
    }}

    /* ── Page header (hero band) ── */
    .page-header {{
        background:linear-gradient(120deg, {NAVY_900} 0%, {NAVY_700} 55%, {NAVY_500} 100%);
        color:#fff; padding:22px 28px; border-radius:20px; margin-bottom:22px;
        display:flex; align-items:center; justify-content:space-between;
        position:relative; overflow:hidden;
        box-shadow:0 12px 40px rgba(30,39,97,0.22);
    }}
    .page-header::after {{
        content:""; position:absolute; right:-40px; top:-60px;
        width:280px; height:280px; border-radius:50%;
        background:radial-gradient(circle, rgba(247,166,0,0.22), transparent 70%);
    }}
    .page-header h1 {{
        margin:0; font-size:1.5rem; font-weight:800; color:#fff;
        letter-spacing:-0.02em; position:relative; z-index:1;
    }}
    .page-header .sub {{
        font-size:0.82rem; color:{GOLD_400}; margin-top:4px;
        font-weight:600; position:relative; z-index:1;
    }}
    .ph-logo {{ display:flex; align-items:center; gap:11px; position:relative; z-index:1; }}
    .ph-logo-text {{
        font-family:'Plus Jakarta Sans',sans-serif;
        font-size:1.55rem; font-weight:800; color:{GOLD_500};
        letter-spacing:-0.04em;
    }}

    /* ── Ranking table ── */
    .rank-table {{ width:100%; border-collapse:separate; border-spacing:0; font-size:0.82rem; }}
    .rank-table th {{
        background:{NAVY_700}; color:#fff; padding:11px 13px;
        font-size:0.62rem; font-weight:700; text-transform:uppercase;
        letter-spacing:0.09em; text-align:left; position:sticky; top:0;
    }}
    .rank-table th:first-child {{ border-top-left-radius:12px; }}
    .rank-table th:last-child {{ border-top-right-radius:12px; }}
    .rank-table th.num {{ text-align:center; width:46px; }}
    .rank-table th.pct {{ text-align:center; width:78px; }}
    .rank-table td {{ padding:9px 13px; border-bottom:1px solid {LINE}; }}
    .rank-table td.num {{ text-align:center; font-weight:700; color:{SLATE}; }}
    .rank-table td.pct {{ text-align:center; font-weight:700; font-family:'Plus Jakarta Sans',sans-serif; }}
    .rank-table tbody tr {{ transition:background 0.12s; }}
    .rank-table tbody tr:hover {{ filter:brightness(0.97); }}

    /* ── Ficha ── */
    .ficha-wrap {{
        background:{CARD}; border:1px solid {LINE}; border-radius:18px;
        padding:28px 32px; max-width:740px; margin:0 auto;
        box-shadow:0 12px 40px rgba(30,39,97,0.12);
    }}

    /* ── Login ── */
    .login-wrap {{
        max-width:400px; margin:5vh auto; background:{CARD};
        border-radius:22px; padding:44px 40px;
        box-shadow:0 30px 80px rgba(10,14,30,0.45);
        border:1px solid rgba(247,166,0,0.2); text-align:center;
    }}

    /* ── Buttons ── */
    .stButton > button {{
        border-radius:11px !important; font-weight:600 !important;
        transition:all 0.16s !important;
    }}
    .stButton > button[kind="primary"] {{
        background:linear-gradient(135deg, {NAVY_700}, {NAVY_500}) !important;
        color:#fff !important; border:none !important;
        box-shadow:0 6px 18px rgba(30,39,97,0.28) !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background:linear-gradient(135deg, {GOLD_500}, {GOLD_400}) !important;
        color:{NAVY_900} !important; transform:translateY(-1px);
    }}

    /* ── Top nav buttons ── */
    div[data-testid="stHorizontalBlock"] .stButton button {{
        border-radius:12px !important; font-size:0.8rem !important;
        font-weight:600 !important; padding:9px 6px !important;
    }}

    /* ── Selectbox / inputs ── */
    .stSelectbox > div > div, .stTextInput > div > div {{
        border-radius:11px !important; border-color:{LINE} !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{ gap:4px; }}
    .stTabs [data-baseweb="tab"] {{
        border-radius:10px 10px 0 0; font-weight:600; font-size:0.85rem;
    }}

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] {{ border-radius:12px; overflow:hidden; border:1px solid {LINE}; }}

    /* ── Print ── */
    @media print {{
        [data-testid="stSidebar"], .page-header, .stButton,
        .stSelectbox, .no-print {{ display:none !important; }}
        .ficha-wrap {{ box-shadow:none; border:1px solid #ccc; }}
        body {{ -webkit-print-color-adjust:exact !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)


# ─── JAVASCRIPT — botão expandir menu (sidebar colapsado) ────────────────────

def inject_sidebar_js():
    """Injeta JS que mantém o botão de expandir sidebar sempre visível e estilizado."""
    import streamlit.components.v1 as components
    components.html("""
    <script>
    (function() {
        function fixExpandBtn() {
            // Tenta no documento pai (Streamlit usa iframe)
            var root = window.parent.document;
            var btn = root.querySelector('[data-testid="collapsedControl"]');
            if (btn) {
                btn.style.display         = 'flex';
                btn.style.opacity         = '1';
                btn.style.visibility      = 'visible';
                btn.style.background      = '#F7A600';
                btn.style.width           = '34px';
                btn.style.height          = '62px';
                btn.style.borderRadius    = '0 10px 10px 0';
                btn.style.cursor          = 'pointer';
                btn.style.position        = 'fixed';
                btn.style.left            = '0';
                btn.style.top             = '44vh';
                btn.style.zIndex          = '9999';
                btn.style.alignItems      = 'center';
                btn.style.justifyContent  = 'center';
                btn.style.boxShadow       = '3px 2px 14px rgba(0,0,0,0.35)';
                btn.style.border          = 'none';
                btn.style.transition      = 'background 0.2s';
                var svg = btn.querySelector('svg');
                if (svg) {
                    svg.style.fill   = '#1E2761';
                    svg.style.width  = '18px';
                    svg.style.height = '18px';
                }
                btn.onmouseenter = function(){ this.style.background = '#1E2761'; var s=this.querySelector('svg'); if(s) s.style.fill='#F7A600'; };
                btn.onmouseleave = function(){ this.style.background = '#F7A600'; var s=this.querySelector('svg'); if(s) s.style.fill='#1E2761'; };
            }
        }
        // Executa agora e a cada 400ms (cobre re-renders do Streamlit)
        fixExpandBtn();
        setInterval(fixExpandBtn, 400);
    })();
    </script>
    """, height=0, scrolling=False)

# ─── SNAPSHOTS MENSAIS (pasta /dados no repositório GitHub) ──────────────────
# PERSISTÊNCIA REAL: cada mês é um arquivo .xlsx dentro da pasta 'dados/' do
# repositório. Como o Streamlit Cloud reimplanta o repo a cada reinício, esses
# arquivos NUNCA são perdidos. Para adicionar um mês, basta enviar o arquivo
# para a pasta 'dados/' no GitHub, nomeado como AAAA-MM.xlsx (ex: 2026-05.xlsx).

DADOS_DIR = "dados"

def _find_dados_dir():
    """Acha a pasta de dados em qualquer variação de maiúscula (dados, Dados, DADOS)."""
    candidatos = ["dados", "Dados", "DADOS", "data", "Data"]
    for nome in candidatos:
        if os.path.isdir(nome):
            return nome
    # Procura qualquer pasta cujo nome normalizado seja "dados"
    try:
        for item in os.listdir("."):
            if os.path.isdir(item) and item.lower() in ("dados", "data"):
                return item
    except Exception:
        pass
    return None

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

def _parse_month_from_filename(fname: str):
    """Extrai (ano, mes, label) de um nome tipo '2026-05.xlsx' ou '2026-05_maio.xlsx'."""
    import re
    base = os.path.basename(fname)
    m = re.match(r"(\d{4})[-_](\d{1,2})", base)
    if m:
        ano, mes = int(m.group(1)), int(m.group(2))
        label = f"{MESES_PT.get(mes, mes)}/{ano}"
        return ano, mes, label
    # Sem padrão de data → usa o nome do arquivo como label
    return 0, 0, base.replace(".xlsx", "").replace(".parquet", "")

@st.cache_data(show_spinner=False)
def load_all_snapshots():
    """
    Lê TODOS os arquivos da pasta 'dados/' e retorna:
      (snapshots, erros)
    snapshots = [(label, ano, mes, df), ...] ordenado cronologicamente
    erros     = [(arquivo, motivo), ...]  para diagnóstico visível
    """
    snapshots = []
    erros = []

    dados_dir = _find_dados_dir()
    if dados_dir is None:
        erros.append(("dados/", "Pasta de dados não encontrada (procurei: dados, Dados, DADOS)"))
        return snapshots, erros

    files = [f for f in os.listdir(dados_dir)
             if f.lower().endswith((".xlsx", ".xls", ".parquet"))
             and not f.startswith("~") and not f.startswith(".")]

    if not files:
        erros.append((dados_dir, f"Pasta '{dados_dir}/' existe mas não tem .xlsx dentro"))
        return snapshots, erros

    for fname in files:
        path = os.path.join(dados_dir, fname)
        try:
            if fname.lower().endswith(".parquet"):
                df = pd.read_parquet(path)
                df = _normalise_base_dados(df) if "SCORE_GERAL" in df.columns else _normalise(df)
            else:
                xls = pd.ExcelFile(path, engine="openpyxl")
                if "BASE_DADOS" in xls.sheet_names:
                    df = pd.read_excel(path, sheet_name="BASE_DADOS", engine="openpyxl")
                    df = _normalise_base_dados(df)
                else:
                    sheet = next((s for s in xls.sheet_names
                                  if "SCORE" in s.upper() and "GERAL" in s.upper()),
                                 xls.sheet_names[0])
                    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
                    df = _normalise(df)

            if "SCORE_GERAL" not in df.columns or "FORNECEDOR" not in df.columns:
                erros.append((fname, f"Colunas obrigatórias ausentes. Achei: {list(df.columns)[:6]}"))
                continue

            ano, mes, label = _parse_month_from_filename(fname)
            snapshots.append((label, ano, mes, df))
        except Exception as e:
            erros.append((fname, f"{type(e).__name__}: {str(e)[:120]}"))

    snapshots.sort(key=lambda x: (x[1], x[2]))
    return snapshots, erros

# ─── PERSISTÊNCIA EM SESSÃO (upload temporário / preview) ────────────────────
# Mantido para preview rápido dentro de uma sessão. NÃO persiste entre reinícios.

DATA_FILE      = "selgron_data.parquet"
DATA_INFO_FILE = "selgron_data_info.txt"

def save_shared_data(df: pd.DataFrame, info: str) -> bool:
    """Salva os dados no disco — compartilhado entre TODOS os usuários."""
    try:
        df.to_parquet(DATA_FILE, index=False)
        with open(DATA_INFO_FILE, "w", encoding="utf-8") as f:
            f.write(info)
        st.cache_data.clear()
        return True
    except Exception as e:
        return False

def get_data_mtime() -> float:
    """Retorna o timestamp de modificação do arquivo de dados compartilhado."""
    try:
        return os.path.getmtime(DATA_FILE)
    except:
        return 0.0

def load_shared_data():
    """Carrega dados do arquivo compartilhado no disco (todos os usuários)."""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_parquet(DATA_FILE)
            info = ""
            if os.path.exists(DATA_INFO_FILE):
                with open(DATA_INFO_FILE, "r", encoding="utf-8") as f:
                    info = f.read()
            return df, info
        except Exception:
            pass
    return None, None

# ─── SESSION STATE ────────────────────────────────────────────────────────────

def init_state():
    for k, v in [("authenticated", False), ("df", None), ("data_info", ""),
                 ("page", "Painel Geral"), ("data_mtime", 0.0),
                 ("sel_month", None), ("prev_df", None), ("month_label", "")]:
        if k not in st.session_state:
            st.session_state[k] = v

# ─── SAMPLE DATA ─────────────────────────────────────────────────────────────

def _sample_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    # Compradores e volumes reais da Selgron (dados de demonstração)
    buyers_cfg = [
        ("Edson Carlos Borges",               52, 0.88, 0.94),
        ("Arthur Gabriel Dero",               22, 0.85, 0.94),
        ("Tatiana Carvalho de Souza",         111, 0.84, 0.96),
        ("Misael Severino",                   51, 0.84, 0.98),
        ("Alex Sandro Jung",                  14, 0.83, 0.95),
        ("Nithael Alexandre Krepsky Silveira", 15, 0.78, 0.98),
        ("Jair Wermuth",                      29, 0.62, 0.96),
    ]
    rows = []
    for buyer, n, p_mean, q_mean in buyers_cfg:
        for i in range(n):
            prazo = float(np.clip(rng.normal(p_mean, 0.11), 0.05, 1.0))
            qual  = float(np.clip(rng.normal(q_mean, 0.05), 0.05, 1.0))
            geral = prazo * PESO_PRAZO + qual * PESO_QUAL
            total = max(1, int(rng.exponential(8)))
            ncs   = max(0, int(total * (1 - qual)))
            fname = f"[DEMO] FORNECEDOR {buyer.split()[0].upper()} {i+1:03d}"
            rows.append({
                "FORNECEDOR":       fname,
                "COMPRADOR":        buyer,
                "SCORE_GERAL":      round(geral, 4),
                "SCORE_PRAZO":      round(prazo, 4),
                "SCORE_QUALIDADE":  round(qual, 4),
                "TOTAL_ENTREGAS":   total,
                "ENTREGA_NO_PRAZO": max(0, total - int(total * (1 - prazo))),
                "TOTAL_NCS":        ncs,
                "VALOR_NF":         0,
                "DIAGNOSTICO":      "",
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

def _normalise_base_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza a aba BASE_DADOS do arquivo Score_Fornecedores_Selgron_v*.xlsx"""
    rename = {
        "NO_PRAZO":      "ENTREGA_NO_PRAZO",
        "TOTAL_ALERTAS": "TOTAL_NCS",
    }
    df = df.rename(columns=rename)

    for col in ["ENTREGA_NO_PRAZO", "TOTAL_NCS", "TOTAL_ENTREGAS", "VALOR_NF"]:
        if col not in df.columns:
            df[col] = 0

    if "CLASSE" in df.columns:
        df["CLASSE"] = df["CLASSE"].apply(normalise_class)
    elif "SCORE_GERAL" in df.columns:
        df["CLASSE"] = df["SCORE_GERAL"].apply(get_class)

    df = df.sort_values("SCORE_GERAL", ascending=False).reset_index(drop=True)
    df["RANK"] = range(1, len(df) + 1)
    return df


@st.cache_data(show_spinner=False)
def load_local_score():
    for path in ["Score_Fornecedores_Selgron_v8.xlsx", "Score_Fornecedores_Selgron_v7.xlsx",
                 "Score_Fornecedores_Selgron.xlsx", "score_data.xlsx"]:
        if os.path.exists(path):
            try:
                xls = pd.ExcelFile(path)
                # Prioridade: BASE_DADOS (estrutura limpa e completa)
                if "BASE_DADOS" in xls.sheet_names:
                    df = pd.read_excel(path, sheet_name="BASE_DADOS")
                    df = _normalise_base_dados(df)
                    return df, f"{path} | BASE_DADOS | {len(df)} fornecedores"
                # Fallback: busca aba com "SCORE" e "GERAL" no nome
                score_sheet = next((s for s in xls.sheet_names
                                    if "SCORE" in s.upper() and "GERAL" in s.upper()), None)
                if score_sheet:
                    df = pd.read_excel(path, sheet_name=score_sheet)
                    df = _normalise(df)
                    return df, f"{path} | '{score_sheet}' | {len(df)} fornecedores"
            except Exception:
                pass
    return _sample_data(), "DEMO — coloque Score_Fornecedores_Selgron_v7.xlsx na pasta do app ou importe em 'Atualizar Base'"


def load_from_upload(uploaded):
    try:
        xls = pd.ExcelFile(uploaded)

        # 1. Prioridade máxima: BASE_DADOS (estrutura limpa)
        if "BASE_DADOS" in xls.sheet_names:
            df = pd.read_excel(uploaded, sheet_name="BASE_DADOS")
            df = _normalise_base_dados(df)
            return df, f"BASE_DADOS | {len(df)} fornecedores carregados"

        # 2. Planilha com aba SCORE GERAL genérica (header pode estar na linha 2)
        score_sheet = next((s for s in xls.sheet_names
                            if "SCORE" in s.upper() and "GERAL" in s.upper()), None)
        if score_sheet:
            # Tenta header na linha 0
            df = pd.read_excel(uploaded, sheet_name=score_sheet)
            # Se primeira coluna parecer um título, tenta header=2
            first_col = str(df.columns[0])
            if len(first_col) > 30 or "SELGRON" in first_col.upper() or "SCORE" in first_col.upper():
                df = pd.read_excel(uploaded, sheet_name=score_sheet, header=2)
            df = _normalise(df)
            if "FORNECEDOR" in df.columns and len(df) > 0:
                return df, f"'{score_sheet}' | {len(df)} fornecedores carregados"

        # 3. Dados brutos de prazo (aba BASE)
        if "BASE" in xls.sheet_names:
            df = _process_raw_prazo(uploaded)
            return df, f"Dados brutos processados | {len(df)} fornecedores"

        # 4. Última tentativa: primeira aba
        df = pd.read_excel(uploaded, sheet_name=0)
        df = _normalise(df)
        return df, f"Primeira aba | {len(df)} registros importados"

    except Exception as e:
        return _sample_data(), f"Erro ao processar arquivo: {e}"

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
        <div style="position:relative;z-index:1;">
            <div style="display:inline-block;font-size:0.6rem;font-weight:700;
                        text-transform:uppercase;letter-spacing:0.16em;color:{GOLD_400};
                        background:rgba(247,166,0,0.14);padding:4px 11px;border-radius:20px;
                        border:1px solid rgba(247,166,0,0.3);margin-bottom:9px;">
                Suprimentos · Score de Fornecedores
            </div>
            <h1>{title}</h1>
            <div class="sub">{subtitle}</div>
        </div>
        <div class="ph-logo">
            <img src="data:image/png;base64,{LOGO_ICON_B64}"
                 style="width:52px;height:52px;object-fit:cover;border-radius:13px;
                        box-shadow:0 6px 18px rgba(0,0,0,0.3);">
            <div class="ph-logo-text">selgron</div>
        </div>
    </div>"""

# ─── LOGIN ────────────────────────────────────────────────────────────────────

def page_login():
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background:
          radial-gradient(900px 500px at 80% -10%, rgba(247,166,0,0.18), transparent 55%),
          radial-gradient(700px 500px at 10% 110%, rgba(46,58,130,0.5), transparent 55%),
          linear-gradient(160deg, {NAVY_900} 0%, {NAVY_700} 60%, {NAVY_500} 100%);
    }}
    .block-container {{ padding-top:3vh !important; }}
    .login-badges {{ display:flex; gap:8px; justify-content:center; flex-wrap:wrap; margin:18px 0 6px; }}
    .login-badge {{
        font-size:0.64rem; font-weight:600; color:{SLATE};
        background:{CLOUD}; border:1px solid {LINE};
        padding:5px 12px; border-radius:20px;
    }}
    @keyframes floatIn {{ from {{ opacity:0; transform:translateY(14px); }} to {{ opacity:1; transform:none; }} }}
    .login-wrap {{ animation:floatIn 0.6s ease; }}
    </style>

    <div style="text-align:center;margin:2vh auto 0;max-width:560px;animation:floatIn 0.5s ease;">
        <div style="display:inline-flex;align-items:center;gap:12px;margin-bottom:6px;">
            <img src="data:image/png;base64,{LOGO_ICON_B64}"
                 style="width:46px;height:46px;border-radius:12px;object-fit:cover;
                        box-shadow:0 8px 24px rgba(0,0,0,0.4);">
            <span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:2rem;
                         font-weight:800;color:{GOLD_500};letter-spacing:-0.04em;">selgron</span>
        </div>
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:2.1rem;font-weight:800;
                    color:#fff;letter-spacing:-0.03em;line-height:1.15;margin-top:8px;">
            Score de Fornecedores
        </div>
        <div style="font-size:0.95rem;color:#B8C0DB;margin-top:10px;line-height:1.5;">
            Inteligência de Suprimentos · Selgron Industrial<br>
            <span style="color:{GOLD_400};font-weight:600;">Prazo de entrega + Qualidade</span> em um único score por fornecedor
        </div>
    </div>

    <div class="login-wrap">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.15rem;font-weight:700;
                    color:{INK};margin-bottom:4px;">Acesso restrito</div>
        <div style="font-size:0.8rem;color:{SLATE};margin-bottom:22px;">
            Área de Suprimentos · entre com a senha da equipe
        </div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c2:
        pw = st.text_input("Senha", type="password",
                           placeholder="Digite a senha de acesso...", label_visibility="collapsed")
        if st.button("Entrar no painel", use_container_width=True, type="primary"):
            if pw == "Acesso2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
        st.markdown(f"""
        <div class="login-badges">
            <span class="login-badge">🏭 200+ fornecedores</span>
            <span class="login-badge">📊 7 compradores</span>
            <span class="login-badge">📅 Fechamento mensal</span>
        </div>
        <div style="text-align:center;margin-top:14px;font-size:0.7rem;color:#8B95B8;">
            Selgron Industrial · Suprimentos · 2026
        </div>""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────

PAGES_LIST = [
    "🏠  Painel Geral",
    "📊  Painel Comprador",
    "🏭  Painel Fornecedor",
    "⚠️  Acao Prioritaria",
    "📤  Atualizar Base",
]
PAGES_KEYS = [
    "Painel Geral",
    "Painel Comprador",
    "Painel Fornecedor",
    "Acao Prioritaria",
    "Atualizar Base",
]

def show_sidebar(df: pd.DataFrame):
    with st.sidebar:
        # Logo Selgron com ícone real
        st.html(f"""
        <div style="padding:16px 16px 14px;border-bottom:1px solid rgba(247,166,0,0.25);margin-bottom:14px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <img src="data:image/png;base64,{LOGO_ICON_B64}"
                     style="width:42px;height:42px;object-fit:cover;border-radius:6px;">
                <div>
                    <div style="font-size:1.6rem;font-weight:800;color:{GOLD};letter-spacing:-1px;line-height:1;">selgron</div>
                    <div style="font-size:0.6rem;color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:0.12em;">Score de Fornecedores</div>
                </div>
            </div>
        </div>""")

        # Radio sincronizado com session_state.page
        current_idx = PAGES_KEYS.index(st.session_state.page) if st.session_state.page in PAGES_KEYS else 0
        selected = st.radio("MENU", options=PAGES_LIST,
                            index=current_idx,
                            label_visibility="visible")

        # Sincroniza sessão
        selected_key = PAGES_KEYS[PAGES_LIST.index(selected)]
        if selected_key != st.session_state.page:
            st.session_state.page = selected_key
            st.rerun()

        st.markdown("---")

        n_tot  = len(df)
        n_crit = len(df[df["CLASSE"].str.startswith("E")])
        n_atn  = len(df[df["CLASSE"].str.startswith("D")])
        n_exc  = len(df[df["CLASSE"].str.startswith("A")])
        avg    = df["SCORE_GERAL"].mean()

        st.html(f"""
        <div style="font-size:0.65rem;color:{GOLD};font-weight:700;text-transform:uppercase;
                    letter-spacing:0.1em;margin-bottom:8px;">Resumo</div>
        <div style="font-size:0.8rem;line-height:2.1;">
            📦 {n_tot} fornecedores<br>
            📈 Score medio: <b>{pct(avg)}</b><br>
            🟢 Excelentes (A): {n_exc}<br>
            🟠 Atencao (D): {n_atn}<br>
            🔴 Criticos (E): {n_crit}
        </div>""")

        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.df = None
            st.rerun()

        if st.session_state.data_info:
            st.html(f"""
            <div style="font-size:0.62rem;color:rgba(255,255,255,0.3);margin-top:10px;line-height:1.5;">
                {st.session_state.data_info}
            </div>""")


def show_top_nav():
    """Barra de navegação SEMPRE visível no topo — funciona com sidebar aberto ou fechado."""
    current = st.session_state.page
    labels  = ["🏠 Geral", "📊 Comprador", "🏭 Fornecedor", "⚠️ Prioritário", "📤 Base"]

    st.markdown(f"""
    <div style="background:linear-gradient(120deg, {NAVY_900}, {NAVY_700} 70%, {NAVY_500});
                padding:11px 18px;border-radius:14px;margin-bottom:14px;
                display:flex;align-items:center;gap:11px;
                box-shadow:0 8px 26px rgba(30,39,97,0.22);position:relative;overflow:hidden;">
        <div style="position:absolute;right:-30px;top:-40px;width:160px;height:160px;
                    border-radius:50%;background:radial-gradient(circle,rgba(247,166,0,0.18),transparent 70%);"></div>
        <img src="data:image/png;base64,{LOGO_ICON_B64}"
             style="width:34px;height:34px;object-fit:cover;border-radius:9px;flex-shrink:0;
                    box-shadow:0 4px 12px rgba(0,0,0,0.3);position:relative;z-index:1;">
        <span style="font-family:'Plus Jakarta Sans',sans-serif;color:{GOLD_500};font-weight:800;
                     font-size:1.1rem;letter-spacing:-0.04em;position:relative;z-index:1;">selgron</span>
        <span style="color:rgba(255,255,255,0.5);font-size:0.72rem;font-weight:500;
                     border-left:1px solid rgba(255,255,255,0.2);padding-left:11px;
                     position:relative;z-index:1;">Score de Fornecedores · Suprimentos</span>
    </div>""", unsafe_allow_html=True)

    cols = st.columns(5, gap="small")
    for col, label, key in zip(cols, labels, PAGES_KEYS):
        with col:
            is_active = (current == key)
            btn_style = "primary" if is_active else "secondary"
            if st.button(label, use_container_width=True,
                         type=btn_style, key=f"tnav_{key}"):
                st.session_state.page = key
                st.rerun()

# ─── PAINEL GERAL ────────────────────────────────────────────────────────────

def page_dashboard(df: pd.DataFrame):
    month_label = st.session_state.get("month_label", "Período atual")
    st.html(logo_header("Painel Geral de Fornecedores",
                         f"Performance consolidada · {month_label}"))

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

    # Score por comprador
    st.markdown('<div class="sec-title">Score Médio por Comprador</div>', unsafe_allow_html=True)
    bav = df.groupby("COMPRADOR")["SCORE_GERAL"].mean().sort_values(ascending=False).reset_index()
    bav["first"] = bav["COMPRADOR"].apply(lambda x: x.split()[0])
    fig = go.Figure(go.Bar(
        x=bav["first"], y=bav["SCORE_GERAL"]*100,
        marker=dict(
            color=bav["SCORE_GERAL"].apply(score_bar_color).tolist(),
            cornerradius=8,
            line=dict(width=0),
        ),
        text=bav["SCORE_GERAL"].apply(pct), textposition="outside",
        textfont=dict(size=12, color=INK, family=PLOTLY_FONT),
        hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}%<extra></extra>",
    ))
    style_fig(fig, height=240)
    fig.update_yaxes(range=[0, 112], ticksuffix="%")
    fig.update_xaxes(tickfont=dict(size=11, color=INK))
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
    st.html(ranking_table_html(df_show))

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("⬇️ Exportar base filtrada (.csv)",
                       df_filt.to_csv(index=False).encode("utf-8"),
                       "selgron_score_geral.csv","text/csv")

# ─── PAINEL COMPRADOR ────────────────────────────────────────────────────────

def page_por_comprador(df: pd.DataFrame):
    st.html(logo_header("Painel Comprador",
                            "Visao individual da carteira de fornecedores"))

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
        st.markdown('<div class="sec-title">Distribuição por Classe</div>', unsafe_allow_html=True)
        cc_counts = dfb["CLASSE"].value_counts()
        lbs_raw = [c for c in CLASSES if c in cc_counts.index]
        lbs_full  = [CLASSES[c]["label"] for c in lbs_raw]
        fig_pie = go.Figure(go.Pie(
            labels=lbs_full,
            values=[cc_counts[c] for c in lbs_raw],
            marker=dict(colors=[CLASSES[c]["bar"] for c in lbs_raw],
                        line=dict(color="white", width=2)),
            textinfo="label+value",
            textfont=dict(size=11, family=PLOTLY_FONT, color="white"),
            hole=0.58,
            hovertemplate="<b>%{label}</b><br>%{value} fornecedores · %{percent}<extra></extra>",
            sort=False,
        ))
        total_forn = len(dfb)
        fig_pie.add_annotation(text=f"<b>{total_forn}</b><br><span style='font-size:10px'>fornecedores</span>",
                               x=0.5, y=0.5, showarrow=False,
                               font=dict(size=22, family=PLOTLY_FONT, color=NAVY_700))
        style_fig(fig_pie, height=300)
        fig_pie.update_xaxes(visible=False); fig_pie.update_yaxes(visible=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_scatter:
        st.markdown('<div class="sec-title">Prazo × Qualidade</div>', unsafe_allow_html=True)
        color_map = {c: CLASSES[c]["bar"] for c in CLASSES}
        fig_sc = px.scatter(dfb, x="SCORE_PRAZO", y="SCORE_QUALIDADE",
                            color="CLASSE", color_discrete_map=color_map,
                            hover_name="FORNECEDOR",
                            labels={"SCORE_PRAZO":"Prazo","SCORE_QUALIDADE":"Qualidade"})
        fig_sc.update_traces(marker=dict(size=10, line=dict(width=1, color="white"), opacity=0.85))
        # Zona de meta (verde claro no canto superior direito)
        fig_sc.add_shape(type="rect", x0=0.70, y0=0.70, x1=1.08, y1=1.08,
                         fillcolor="rgba(39,174,96,0.06)", line=dict(width=0), layer="below")
        fig_sc.add_vline(x=0.70, line_dash="dash", line_color="rgba(100,116,139,0.4)", line_width=1)
        fig_sc.add_hline(y=0.70, line_dash="dash", line_color="rgba(100,116,139,0.4)", line_width=1)
        style_fig(fig_sc, height=300, showlegend=True,
                  legend_opts=dict(font=dict(size=9), title="", orientation="h", y=-0.18))
        fig_sc.update_xaxes(tickformat=".0%", range=[0,1.08], title="Prazo",
                            title_font=dict(size=10, color=SLATE))
        fig_sc.update_yaxes(tickformat=".0%", range=[0,1.08], title="Qualidade",
                            title_font=dict(size=10, color=SLATE),
                            gridcolor="rgba(100,116,139,0.10)")
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
    st.html(ranking_table_html(df_filt))

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(f"⬇️ Exportar carteira de {sel.split()[0]}",
                       dfb.to_csv(index=False).encode("utf-8"),
                       f"selgron_{sel.split()[0].lower()}.csv","text/csv")

# ─── PAINEL FORNECEDOR ───────────────────────────────────────────────────────

def page_ficha(df: pd.DataFrame):
    import streamlit.components.v1 as components

    st.html(logo_header("Painel Fornecedor",
                        "Performance individual · Exportável como imagem para e-mail/chat"))

    fc1, fc2, _ = st.columns([1.1, 1.1, 1.8])
    with fc1:
        sel_buyer = st.selectbox("Comprador", sorted(df["COMPRADOR"].unique()), key="fich_buyer")
    with fc2:
        dfb = df[df["COMPRADOR"] == sel_buyer]
        sel_sup = st.selectbox("Fornecedor", sorted(dfb["FORNECEDOR"].unique()), key="fich_sup")

    if not sel_sup:
        return

    row   = dfb[dfb["FORNECEDOR"] == sel_sup].iloc[0]
    cls   = normalise_class(row["CLASSE"])
    cc    = CLASSES.get(cls, CLASSES["E - CRITICO"])
    score = row["SCORE_GERAL"]
    prazo = row["SCORE_PRAZO"]
    qual  = row["SCORE_QUALIDADE"]
    today = datetime.now().strftime("%d/%m/%Y")
    month_label = st.session_state.get("month_label", "Período atual")

    # ── EVOLUÇÃO vs mês anterior ──
    prev_df = st.session_state.get("prev_df")
    evo_html = ""
    if prev_df is not None:
        prev_row = prev_df[prev_df["FORNECEDOR"] == sel_sup]
        if len(prev_row) > 0:
            prev_score = prev_row.iloc[0]["SCORE_GERAL"]
            delta = (score - prev_score) * 100
            if delta > 0.5:
                arrow, dcolor, dword = "▲", BAR_GREEN, "melhorou"
            elif delta < -0.5:
                arrow, dcolor, dword = "▼", BAR_RED, "piorou"
            else:
                arrow, dcolor, dword = "▬", DGRAY, "estável"
            evo_html = f"""
            <div style="display:flex;gap:16px;margin-bottom:16px;">
                <div style="flex:1;background:#FAFAFA;border:1px solid #E8E8E8;border-radius:8px;padding:14px;text-align:center;">
                    <div style="font-size:0.6rem;color:{DGRAY};font-weight:700;text-transform:uppercase;letter-spacing:0.08em;">Mês Anterior</div>
                    <div style="font-size:1.6rem;font-weight:800;color:{DGRAY};">{prev_score*100:.1f}%</div>
                </div>
                <div style="flex:1;background:#FAFAFA;border:1px solid #E8E8E8;border-radius:8px;padding:14px;text-align:center;">
                    <div style="font-size:0.6rem;color:{DGRAY};font-weight:700;text-transform:uppercase;letter-spacing:0.08em;">Mês Atual</div>
                    <div style="font-size:1.6rem;font-weight:800;color:{cc['text']};">{score*100:.1f}%</div>
                </div>
                <div style="flex:1.2;background:{dcolor}1A;border:1.5px solid {dcolor};border-radius:8px;padding:14px;text-align:center;">
                    <div style="font-size:0.6rem;color:{dcolor};font-weight:700;text-transform:uppercase;letter-spacing:0.08em;">Evolução</div>
                    <div style="font-size:1.6rem;font-weight:800;color:{dcolor};">{arrow} {abs(delta):.1f} pts</div>
                    <div style="font-size:0.62rem;color:{dcolor};font-weight:600;">desempenho {dword}</div>
                </div>
            </div>"""
        else:
            evo_html = f"""
            <div style="background:{BG_BLUE};border:1px solid {BAR_BLUE};border-radius:8px;padding:10px 16px;margin-bottom:16px;">
                <span style="font-size:0.78rem;font-weight:600;color:{C_BLUE};">🆕 Fornecedor sem registro no mês anterior — primeiro fechamento monitorado.</span>
            </div>"""

    # ── Diagnóstico ──
    issues = []
    if prazo < 0.70:
        late = int(row["TOTAL_ENTREGAS"]) - int(row["ENTREGA_NO_PRAZO"])
        issues.append(f"prazo de entrega abaixo do mínimo ({pct(prazo)}) — {late} entregas atrasadas no período")
    if qual < 0.70:
        issues.append(f"qualidade abaixo do mínimo ({pct(qual)}) — {int(row['TOTAL_NCS'])} não conformidades registradas")
    if issues:
        bullets = "".join(f"<li>{i}</li>" for i in issues)
        diag = f'<div style="background:#FFF3CD;border:1px solid #FFC107;border-radius:8px;padding:12px 16px;margin-bottom:16px;"><div style="font-size:0.75rem;font-weight:700;color:#856404;margin-bottom:6px;">⚠️ Pontos de Atenção Identificados</div><ul style="font-size:0.8rem;color:#6d5402;margin:0;padding-left:18px;line-height:1.8;">{bullets}</ul></div>'
    else:
        diag = f'<div style="background:{BG_GREEN};border:1px solid {BAR_GREEN};border-radius:8px;padding:10px 16px;margin-bottom:16px;"><div style="font-size:0.78rem;font-weight:700;color:{C_GREEN};">✅ Fornecedor dentro dos parâmetros esperados.</div></div>'

    # ── Escala de classes ──
    meta_rows = ""
    for cname, cdata in CLASSES.items():
        hl  = "font-weight:700;" if cname == cls else ""
        bg  = cdata["bg"] if cname == cls else "white"
        rng = (">= 90%" if cname.startswith("A") else "80 - 89%" if cname.startswith("B")
               else "70 - 79%" if cname.startswith("C") else "60 - 69%" if cname.startswith("D") else "< 60%")
        atual = "&larr; ATUAL" if cname == cls else ""
        meta_rows += f'<tr style="background:{bg};{hl}"><td style="padding:5px 14px;color:{cdata["text"]};">{cdata["emoji"]} {cname}</td><td style="padding:5px 14px;text-align:center;color:{DGRAY};">{rng}</td><td style="padding:5px 14px;text-align:center;font-weight:700;color:{cdata["text"]};">{atual}</td></tr>'

    def bar(v, color):
        return f'<div style="background:#E8E8E8;border-radius:4px;height:9px;margin:3px 0 10px 0;"><div style="background:{color};width:{min(v*100,100):.1f}%;height:9px;border-radius:4px;"></div></div>'

    nc_color = C_RED if row['TOTAL_NCS'] > 0 else BAR_GREEN

    # ════════════════════════════════════════════════════════════════════
    #  FICHA AUTOCONTIDA (HTML + html2canvas) — exportável como IMAGEM
    # ════════════════════════════════════════════════════════════════════
    ficha_html = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        * {{ box-sizing:border-box; margin:0; padding:0; font-family:'Segoe UI',Arial,sans-serif; }}
        body {{ background:#F4F5F9; padding:8px; }}
        .toolbar {{ display:flex; gap:10px; margin-bottom:14px; align-items:center; }}
        .btn {{ border:none; border-radius:6px; padding:9px 18px; cursor:pointer;
                font-size:0.85rem; font-weight:600; transition:all 0.15s; }}
        .btn-primary {{ background:{NAVY}; color:#fff; }}
        .btn-primary:hover {{ background:{GOLD}; color:{NAVY}; }}
        .btn-gold {{ background:{GOLD}; color:{NAVY}; }}
        .btn-gold:hover {{ background:{NAVY}; color:#fff; }}
        .hint {{ font-size:0.72rem; color:#888; }}
        #ficha {{ background:#fff; border:1px solid #DDD; border-radius:10px;
                  padding:26px 30px; max-width:720px; box-shadow:0 4px 20px rgba(30,39,97,0.1); }}
    </style></head>
    <body>
        <div class="toolbar">
            <button class="btn btn-gold" onclick="copiarImagem()">📋 Copiar imagem</button>
            <button class="btn btn-primary" onclick="baixarImagem()">💾 Baixar PNG</button>
            <span class="hint" id="status">Copie e cole direto no e-mail ou WhatsApp</span>
        </div>

        <div id="ficha">
            <div style="background:{NAVY};padding:16px 20px;border-radius:8px;margin-bottom:16px;
                        display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div style="font-size:0.6rem;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:0.12em;">Selgron Industrial · Suprimentos</div>
                    <div style="font-size:1.25rem;font-weight:700;color:#fff;margin:4px 0;">Ficha de Performance de Fornecedor</div>
                    <div style="font-size:0.78rem;color:{GOLD};">Comprador: {sel_buyer} &nbsp;·&nbsp; Referência: {month_label}</div>
                </div>
                <div style="text-align:right;display:flex;align-items:center;gap:8px;">
                    <img src="data:image/png;base64,{LOGO_ICON_B64}" style="width:40px;height:40px;object-fit:cover;border-radius:6px;">
                    <div>
                        <div style="font-size:1.5rem;font-weight:800;color:{GOLD};letter-spacing:-1px;">selgron</div>
                        <div style="font-size:0.6rem;color:rgba(255,255,255,0.4);">{today}</div>
                    </div>
                </div>
            </div>

            <div style="background:{cc['bg']};border-radius:8px;padding:12px 18px;margin-bottom:16px;border-left:4px solid {cc['bar']};">
                <div style="font-size:0.6rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">Fornecedor</div>
                <div style="font-size:1.25rem;font-weight:700;color:{cc['text']};margin:3px 0;">{sel_sup}</div>
            </div>

            <div style="display:flex;gap:16px;margin-bottom:16px;">
                <div style="flex:1;background:{cc['bg']};border-radius:8px;padding:18px;text-align:center;border:2px solid {cc['bar']};">
                    <div style="font-size:0.6rem;color:{DGRAY};font-weight:700;text-transform:uppercase;letter-spacing:0.09em;margin-bottom:6px;">Score Geral</div>
                    <div style="font-size:3.3rem;font-weight:800;color:{cc['text']};line-height:1;">{score*100:.1f}<span style="font-size:1.5rem;">%</span></div>
                    <div style="font-size:0.86rem;font-weight:700;color:{cc['text']};margin-top:6px;">{cls}</div>
                    <div style="font-size:0.68rem;color:{DGRAY};margin-top:4px;">Ranking #{int(row['RANK'])} de {len(df)} fornecedores</div>
                </div>
                <div style="flex:2;background:#FAFAFA;border-radius:8px;padding:16px;border:1px solid #E8E8E8;">
                    <div style="font-size:0.6rem;color:{DGRAY};font-weight:700;text-transform:uppercase;letter-spacing:0.09em;margin-bottom:10px;">Detalhamento</div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
                        <span style="font-size:0.8rem;font-weight:600;color:#333;">🚚 Prazo de Entrega <span style="color:{DGRAY};font-weight:400;">(peso 60%)</span></span>
                        <span style="font-size:0.85rem;font-weight:700;color:{score_bar_color(prazo)};">{pct(prazo)}</span>
                    </div>
                    {bar(prazo, score_bar_color(prazo))}
                    <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
                        <span style="font-size:0.8rem;font-weight:600;color:#333;">✅ Qualidade <span style="color:{DGRAY};font-weight:400;">(peso 40%)</span></span>
                        <span style="font-size:0.85rem;font-weight:700;color:{score_bar_color(qual)};">{pct(qual)}</span>
                    </div>
                    {bar(qual, score_bar_color(qual))}
                    <div style="border-top:1px solid #E8E8E8;margin-top:8px;padding-top:10px;display:flex;gap:20px;">
                        <div><div style="font-size:0.6rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">Entregas</div><div style="font-size:1.1rem;font-weight:700;color:{NAVY};">{int(row['TOTAL_ENTREGAS'])}</div></div>
                        <div><div style="font-size:0.6rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">No Prazo</div><div style="font-size:1.1rem;font-weight:700;color:{BAR_GREEN};">{int(row['ENTREGA_NO_PRAZO'])}</div></div>
                        <div><div style="font-size:0.6rem;color:{DGRAY};font-weight:700;text-transform:uppercase;">Não Conf.</div><div style="font-size:1.1rem;font-weight:700;color:{nc_color};">{int(row['TOTAL_NCS'])}</div></div>
                    </div>
                </div>
            </div>

            {evo_html}
            {diag}

            <div style="border:1px solid #E8E8E8;border-radius:8px;overflow:hidden;margin-bottom:14px;">
                <div style="background:{NAVY};color:#fff;padding:8px 14px;font-size:0.66rem;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;">Escala de Classificação</div>
                <table style="width:100%;border-collapse:collapse;font-size:0.78rem;">
                    <tr style="background:{LGRAY};"><th style="padding:6px 14px;text-align:left;color:{DGRAY};font-weight:600;">Classe</th><th style="padding:6px 14px;text-align:center;color:{DGRAY};font-weight:600;">Score</th><th style="padding:6px 14px;text-align:center;color:{DGRAY};font-weight:600;">Situação</th></tr>
                    {meta_rows}
                </table>
            </div>

            <div style="background:{NAVY};color:rgba(255,255,255,0.65);padding:8px 14px;border-radius:6px;font-size:0.62rem;text-align:center;">
                Selgron Industrial · Suprimentos · {month_label} · Gerado em {today} · Metodologia: 60% Prazo + 40% Qualidade
            </div>
        </div>

        <script>
        function render(cb) {{
            html2canvas(document.getElementById('ficha'),
                {{scale:2, backgroundColor:'#ffffff', useCORS:true}}).then(cb);
        }}
        function baixarImagem() {{
            render(function(canvas) {{
                var link = document.createElement('a');
                link.download = 'Ficha_{sel_sup.split()[0]}_{month_label.replace("/","-")}.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
                document.getElementById('status').innerText = '✅ Imagem baixada!';
            }});
        }}
        function copiarImagem() {{
            render(function(canvas) {{
                canvas.toBlob(function(blob) {{
                    try {{
                        navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})]).then(function() {{
                            document.getElementById('status').innerText = '✅ Copiado! Cole com Ctrl+V no e-mail ou WhatsApp.';
                        }}).catch(function() {{
                            document.getElementById('status').innerText = '⚠️ Navegador bloqueou cópia — use "Baixar PNG".';
                        }});
                    }} catch(e) {{
                        document.getElementById('status').innerText = '⚠️ Use "Baixar PNG" neste navegador.';
                    }}
                }});
            }});
        }}
        </script>
    </body></html>"""

    components.html(ficha_html, height=1050, scrolling=True)

# ─── ACAO PRIORITARIA ────────────────────────────────────────────────────────

def page_acao(df: pd.DataFrame):
    st.html(logo_header("Acao Prioritaria",
                            "Fornecedores Classe D e E · Intervencao necessaria"))

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
                st.markdown('<div class="sec-title">Prazo × Qualidade por Fornecedor</div>', unsafe_allow_html=True)
                ds = dfs.sort_values("SCORE_GERAL", ascending=True)
                fig = go.Figure()
                fig.add_trace(go.Bar(y=ds["FORNECEDOR"].apply(lambda x: x[:38]),
                                     x=ds["SCORE_PRAZO"]*100, name="Prazo (60%)",
                                     orientation="h",
                                     marker=dict(color=BAR_BLUE, cornerradius=5),
                                     hovertemplate="<b>%{y}</b><br>Prazo: %{x:.1f}%<extra></extra>"))
                fig.add_trace(go.Bar(y=ds["FORNECEDOR"].apply(lambda x: x[:38]),
                                     x=ds["SCORE_QUALIDADE"]*100, name="Qualidade (40%)",
                                     orientation="h",
                                     marker=dict(color=BAR_GREEN, cornerradius=5),
                                     hovertemplate="<b>%{y}</b><br>Qualidade: %{x:.1f}%<extra></extra>"))
                fig.add_vline(x=70, line_dash="dash", line_color="rgba(100,116,139,0.5)", line_width=1,
                              annotation_text="Meta 70%", annotation_font_size=9,
                              annotation_font_color=SLATE)
                style_fig(fig, height=max(320, len(dfs)*34), showlegend=True,
                          legend_opts=dict(orientation="h", y=1.04, font=dict(size=10)))
                fig.update_layout(barmode="group")
                fig.update_xaxes(range=[0,110], ticksuffix="%")
                fig.update_yaxes(tickfont=dict(size=9, color=INK), showgrid=False)
                st.plotly_chart(fig, use_container_width=True)

            with col_s:
                st.markdown('<div class="sec-title">Por Comprador</div>', unsafe_allow_html=True)
                bc = dfs["COMPRADOR"].value_counts().reset_index()
                bc.columns = ["Comprador","Qtd"]
                bc["first"] = bc["Comprador"].apply(lambda x: x.split()[0])
                clr = BAR_RED if tag == "E" else BAR_ORANGE
                fig2 = go.Figure(go.Bar(
                    x=bc["first"], y=bc["Qtd"],
                    marker=dict(color=clr, cornerradius=7),
                    text=bc["Qtd"], textposition="outside",
                    textfont=dict(family=PLOTLY_FONT, color=INK),
                    hovertemplate="<b>%{x}</b><br>%{y} fornecedor(es)<extra></extra>"))
                style_fig(fig2, height=240)
                st.plotly_chart(fig2, use_container_width=True)

                st.markdown('<div class="sec-title">Os 5 Piores</div>', unsafe_allow_html=True)
                worst = dfs.nsmallest(5,"SCORE_GERAL")[["FORNECEDOR","COMPRADOR","SCORE_GERAL","TOTAL_NCS"]].copy()
                worst["SCORE_GERAL"] = worst["SCORE_GERAL"].apply(pct)
                worst.columns = ["Fornecedor","Comprador","Score","NCs"]
                st.dataframe(worst, use_container_width=True, hide_index=True)

            st.markdown('<div class="sec-title">Lista Completa</div>', unsafe_allow_html=True)
            st.html(ranking_table_html(dfs))
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(f"⬇️ Exportar Classe {tag}",
                               dfs.to_csv(index=False).encode("utf-8"),
                               f"selgron_classe_{tag.lower()}.csv","text/csv")

# ─── ATUALIZAR BASE ──────────────────────────────────────────────────────────

def page_atualizar(df: pd.DataFrame):
    st.html(logo_header("Atualizar Base de Dados",
                        "Fechamento mensal · Persistência permanente via GitHub"))

    left, right = st.columns([1, 1])

    with left:
        st.html(f"""
        <div style="background:{LGRAY};border-radius:10px;padding:20px 24px;border:1px solid {MGRAY};">
            <div class="sec-title">✅ Método permanente (recomendado)</div>

            <div style="background:{BG_GREEN};border-radius:8px;padding:14px;margin-bottom:14px;">
                <div style="font-size:0.78rem;font-weight:700;color:{C_GREEN};margin-bottom:8px;">
                    Salvar o mês na pasta <code>dados/</code> do GitHub
                </div>
                <div style="font-size:0.78rem;color:{DGRAY};line-height:1.9;">
                    Este é o único jeito que <b>nunca perde os dados</b>, mesmo quando o site reinicia.<br><br>
                    <b>Passo a passo (1x por mês):</b><br>
                    1. No GitHub, abra seu repositório<br>
                    2. Entre na pasta <code>dados/</code> (crie se não existir)<br>
                    3. Clique em <b>Add file → Upload files</b><br>
                    4. Envie a planilha do mês nomeada assim:<br>
                    &nbsp;&nbsp;&nbsp;<code>2026-05.xlsx</code> → Maio<br>
                    &nbsp;&nbsp;&nbsp;<code>2026-06.xlsx</code> → Junho<br>
                    &nbsp;&nbsp;&nbsp;<code>2026-07.xlsx</code> → Julho...<br>
                    5. <b>Commit changes</b> → pronto, fica salvo para sempre
                </div>
            </div>

            <div style="background:{BG_BLUE};border-radius:8px;padding:12px 14px;">
                <div style="font-size:0.74rem;font-weight:700;color:{C_BLUE};margin-bottom:6px;">
                    Estrutura da planilha
                </div>
                <div style="font-size:0.76rem;color:{DGRAY};line-height:1.7;">
                    Aba <b>BASE_DADOS</b> com: FORNECEDOR, COMPRADOR, SCORE_GERAL,
                    SCORE_PRAZO, SCORE_QUALIDADE, CLASSE, TOTAL_ENTREGAS, NO_PRAZO, TOTAL_ALERTAS.
                    <br>(É exatamente o formato do seu arquivo v7.)
                </div>
            </div>

            <div style="background:{BG_AMBER};border-radius:8px;padding:11px 14px;margin-top:12px;
                        font-size:0.74rem;color:{C_AMBER};line-height:1.6;">
                💡 Cada arquivo = 1 mês. O filtro de mês no topo lê automaticamente
                todos os arquivos da pasta. Para separar maio e junho, suba os dois arquivos.
            </div>
        </div>""")

    with right:
        st.html(f"""
        <div style="background:white;border-radius:10px;padding:20px 24px;border:1px solid {MGRAY};">
            <div class="sec-title">Preview rápido (temporário)</div>
            <div style="font-size:0.76rem;color:{DGRAY};line-height:1.6;margin-bottom:4px;">
                Use abaixo só para <b>conferir</b> uma planilha antes de subir ao GitHub.
                Esta importação vale apenas nesta sessão e <b>não fica salva</b> para os outros.
            </div>
        </div>""")

        uploaded = st.file_uploader("Selecione o Excel (.xlsx)", type=["xlsx","xls"], key="uploader_main")

        if uploaded:
            with st.spinner("Processando..."):
                df_new, msg = load_from_upload(uploaded)

            if msg.startswith("Erro"):
                st.error(msg)
            else:
                st.success(msg)

            st.markdown(f"**{len(df_new)} fornecedores | {df_new['COMPRADOR'].nunique()} compradores**")
            prev = df_new.head(8).copy()
            for c in ["SCORE_GERAL","SCORE_PRAZO","SCORE_QUALIDADE"]:
                if c in prev.columns: prev[c] = prev[c].apply(pct)
            st.dataframe(prev, use_container_width=True, hide_index=True)
            if st.button("👁️ Ver no painel (só nesta sessão)", type="primary", use_container_width=True):
                save_shared_data(df_new, msg)
                st.session_state.df         = df_new
                st.session_state.data_info  = msg
                st.session_state.data_mtime = get_data_mtime()
                st.session_state.sel_month  = None   # força usar este preview
                st.info("👁️ Carregado para conferência nesta sessão. Para salvar de forma permanente "
                        "e para todos, suba o arquivo na pasta `dados/` do GitHub (instruções à esquerda).")
                st.rerun()

        # Base atual carregada
        _snaps, _ = load_all_snapshots()
        n_meses = len(_snaps)
        meses_txt = f"📅 {n_meses} mês(es) na pasta dados/<br>" if n_meses else "📅 Nenhum mês na pasta dados/ ainda<br>"
        st.html(f"""
        <div style="background:{LGRAY};border-radius:8px;padding:14px 18px;margin-top:16px;border:1px solid {MGRAY};">
            <div style="font-size:0.68rem;font-weight:700;color:{DGRAY};text-transform:uppercase;margin-bottom:8px;">Base em exibição ({st.session_state.get('month_label','atual')})</div>
            <div style="font-size:0.82rem;color:{DGRAY};line-height:2;">
                {meses_txt}
                📦 {len(df)} fornecedores<br>
                👤 {df['COMPRADOR'].nunique()} compradores<br>
                📈 Score medio: <b>{pct(df['SCORE_GERAL'].mean())}</b><br>
                🔴 Criticos (E): {len(df[df['CLASSE'].str.startswith("E")])}<br>
                🟠 Atencao (D): {len(df[df['CLASSE'].str.startswith("D")])}
            </div>
        </div>""")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    init_state()
    inject_css()

    if not st.session_state.authenticated:
        page_login()
        return

    # ════════════════════════════════════════════════════════════════════
    #  RESOLUÇÃO DE DADOS POR MÊS (snapshots da pasta /dados no GitHub)
    # ════════════════════════════════════════════════════════════════════
    snapshots, erros_snap = load_all_snapshots()   # [(label, ano, mes, df), ...]

    df = None
    prev_df = None
    month_label = ""
    month_labels = []

    if snapshots:
        # Há fechamentos mensais salvos no repositório → fonte oficial
        month_labels = [s[0] for s in snapshots]

        # Mês selecionado (default = mais recente)
        if st.session_state.sel_month not in month_labels:
            st.session_state.sel_month = month_labels[-1]
        sel_idx = month_labels.index(st.session_state.sel_month)

        month_label = snapshots[sel_idx][0]
        df          = snapshots[sel_idx][3]
        # Mês anterior (para evolução)
        if sel_idx > 0:
            prev_df = snapshots[sel_idx - 1][3]
        st.session_state.data_info = f"{month_label} | {len(df)} fornecedores | {len(snapshots)} meses na base"
    else:
        # SEM pasta /dados → fallback: upload em sessão, Excel local ou demo
        disk_mtime    = get_data_mtime()
        session_mtime = st.session_state.get("data_mtime", 0.0)
        if st.session_state.df is None or disk_mtime > session_mtime:
            df_shared, info_shared = load_shared_data()
            if df_shared is not None:
                st.session_state.df        = df_shared
                st.session_state.data_info = info_shared
                st.session_state.data_mtime = disk_mtime
            elif st.session_state.df is None:
                with st.spinner("Carregando dados..."):
                    df_local, info_local = load_local_score()
                st.session_state.df        = df_local
                st.session_state.data_info = info_local
                st.session_state.data_mtime = 0.0
        df = st.session_state.df
        month_label = "Período atual"

    # Salva em sessão para uso nas páginas (evolução etc.)
    st.session_state.df          = df
    st.session_state.prev_df     = prev_df
    st.session_state.month_label = month_label

    # Sidebar (stats + radio sincronizado)
    show_sidebar(df)

    # Nav bar no topo — sempre visível
    show_top_nav()

    # ── Seletor de MÊS DE REFERÊNCIA (só aparece se houver snapshots) ──
    if month_labels:
        mc1, mc2 = st.columns([1.3, 3])
        with mc1:
            new_month = st.selectbox(
                "📅 Mês de referência (fechamento)",
                month_labels,
                index=month_labels.index(st.session_state.sel_month),
                key="month_selector",
            )
            if new_month != st.session_state.sel_month:
                st.session_state.sel_month = new_month
                st.rerun()

    # Banner de dados de demonstração + diagnóstico de erros de leitura
    if "DEMO" in st.session_state.data_info:
        st.warning(
            "⚠️ **Dados de demonstração** — Os nomes de fornecedores são placeholders. "
            "Para dados reais que **persistem para sempre**, crie a pasta `dados/` no GitHub "
            "e envie `2026-05.xlsx` (maio), `2026-06.xlsx` (junho), etc. Veja instruções em **📤 Base**."
        )
        # Diagnóstico: por que não carregou a pasta dados/?
        if erros_snap:
            with st.expander("🔍 Diagnóstico — por que os dados reais não apareceram?", expanded=True):
                st.markdown("**O app tentou ler a pasta `dados/` e encontrou estes problemas:**")
                for arquivo, motivo in erros_snap:
                    st.markdown(f"- `{arquivo}` → {motivo}")
                st.markdown("---")
                st.markdown(
                    "**Causas comuns:**\n"
                    "- A pasta no GitHub não se chama exatamente `dados` (minúsculo, sem acento)\n"
                    "- Falta a biblioteca `openpyxl` no `requirements.txt` (atualize-o no GitHub)\n"
                    "- O arquivo não tem a aba `BASE_DADOS` ou faltam colunas (FORNECEDOR, SCORE_GERAL)\n"
                    "- O arquivo foi gerado por uma ferramenta diferente do `gerar_mes.py`"
                )

    # Roteamento
    key = st.session_state.page
    if   key == "Painel Geral":      page_dashboard(df)
    elif key == "Painel Comprador":  page_por_comprador(df)
    elif key == "Painel Fornecedor": page_ficha(df)
    elif key == "Acao Prioritaria":  page_acao(df)
    elif key == "Atualizar Base":    page_atualizar(df)

if __name__ == "__main__":
    main()
