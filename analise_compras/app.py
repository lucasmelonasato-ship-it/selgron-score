# ─────────────────────────────────────────────────────────────────────────────
#  SELGRON INDUSTRIAL — Análise de Quantidade de Compra v1.0
#  Departamento de Suprimentos · Lucas Melo Nasato
#  Para executar: streamlit run analise_compras/app.py
# ─────────────────────────────────────────────────────────────────────────────

import io
import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motor as m                      # noqa: E402
import conector_consulta as cc         # noqa: E402

st.set_page_config(page_title="Análise de Compras | Selgron", page_icon="📦",
                   layout="wide", initial_sidebar_state="expanded")

NAVY, GOLD, SLATE, LINE = "#1E2761", "#F7A600", "#64748B", "#E8ECF2"

st.markdown(f"""
<style>
.block-container {{ padding-top:1.4rem; }}
.kpi {{ background:#fff; border:1px solid {LINE}; border-radius:12px; padding:14px 16px; }}
.kpi .l {{ font-size:.72rem; color:{SLATE}; text-transform:uppercase; letter-spacing:.04em; }}
.kpi .v {{ font-size:1.6rem; font-weight:800; color:{NAVY}; line-height:1.2; }}
.kpi .s {{ font-size:.75rem; color:{SLATE}; }}
.tag {{ display:inline-block; padding:3px 10px; border-radius:20px; font-weight:700; font-size:.8rem; }}
.hero {{ background:linear-gradient(135deg,#141A3C,{NAVY}); color:#fff; border-radius:14px;
         padding:18px 22px; margin-bottom:14px; }}
.hero b {{ color:{GOLD}; }}
</style>""", unsafe_allow_html=True)


# ─── Login (mesma senha do Score de Fornecedores) ────────────────────────────
def _senha_ok() -> bool:
    if st.session_state.get("auth"):
        return True
    try:
        senha = st.secrets.get("senha_app", "Acesso2026")
    except Exception:  # noqa: BLE001 — sem secrets.toml local
        senha = "Acesso2026"
    st.markdown("<div class='hero'><h2 style='margin:0'>📦 Análise de Quantidade de Compra</h2>"
                "Selgron · Suprimentos — <b>acesso restrito</b></div>", unsafe_allow_html=True)
    c = st.columns([1, 1.2, 1])[1]
    pw = c.text_input("Senha", type="password")
    if c.button("Entrar", type="primary", width="stretch"):
        if pw == senha:
            st.session_state.auth = True
            st.rerun()
        c.error("Senha incorreta.")
    return False


if not _senha_ok():
    st.stop()


# ─── Helpers de exibição ─────────────────────────────────────────────────────
def kpi(col, label, valor, sub=""):
    col.markdown(f"<div class='kpi'><div class='l'>{label}</div><div class='v'>{valor}</div>"
                 f"<div class='s'>{sub}</div></div>", unsafe_allow_html=True)


def brl(v) -> str:
    return ("R$ " + f"{v:,.0f}".replace(",", ".")) if v else "R$ 0"


def num(v, casas=2) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.rstrip("0").rstrip(",") if "," in s else s


def tag(ver: str) -> str:
    i = m.VEREDITOS[ver]
    return f"<span class='tag' style='background:{i['bg']};color:{i['cor']}'>{i['emoji']} {ver}</span>"


def ler_planilha(up) -> pd.DataFrame:
    if up.name.lower().endswith(".csv"):
        raw = up.getvalue()
        for enc in ("utf-8-sig", "latin-1"):
            try:
                return pd.read_csv(io.BytesIO(raw), sep=None, engine="python", encoding=enc)
            except UnicodeDecodeError:
                continue
    return pd.read_excel(up)


def excel_resultado(res: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    cols = ["veredito", "pedido", "produto", "descricao", "fornecedor", "comprador", "qtd_pedido",
            "qtd_min", "qtd_ideal", "qtd_max", "qtd_sugerida", "delta_qtd", "delta_valor",
            "estoque", "empenhado", "pedido_venda", "compras_abertas", "disponivel",
            "posicao_projetada", "consumo_medio_mensal", "lead_time_dias", "estoque_seguranca",
            "ponto_pedido", "pp_teorico", "estoque_maximo", "lote_minimo", "lote_multiplo",
            "preco_unit", "cobertura_atual_dias", "cobertura_pos_pedido_dias", "alertas", "memoria"]
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        res[[c for c in cols if c in res.columns]].to_excel(xw, index=False, sheet_name="ANALISE")
        resumo = (res.groupby("veredito").agg(itens=("produto", "count"),
                                              delta_valor=("delta_valor", "sum")).reset_index())
        resumo.to_excel(xw, index=False, sheet_name="RESUMO")
        ws = xw.sheets["ANALISE"]
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 16
        ws.freeze_panes = "D2"
    return buf.getvalue()


def bloco_detalhe(row: pd.Series):
    st.markdown(f"#### {row['produto']} — {row.get('descricao', '')}  {tag(row['veredito'])}",
                unsafe_allow_html=True)
    st.caption(m.VEREDITOS[row["veredito"]]["desc"])
    c = st.columns(5)
    kpi(c[0], "Qtd pedida", num(row["qtd_pedido"]), row.get("unidade", ""))
    kpi(c[1], "Faixa justificável", f"{num(row['qtd_min'])} – {num(row['qtd_max'])}",
        f"ideal {num(row['qtd_ideal'])}")
    kpi(c[2], "Sugerido", num(row["qtd_sugerida"]),
        f"diferença {num(row['delta_qtd'])} · {brl(row['delta_valor'])}")
    kpi(c[3], "Cobertura hoje", f"{num(row['cobertura_atual_dias'], 0)} d", "posição projetada / consumo")
    kpi(c[4], "Cobertura pós-pedido", f"{num(row['cobertura_pos_pedido_dias'], 0)} d",
        "se o pedido for recebido")
    if row.get("alertas"):
        for a in str(row["alertas"]).split(" | "):
            st.warning(a, icon="⚠️")
    with st.expander("Memória de cálculo", expanded=False):
        st.code(row.get("memoria") or "—", language=None)


# ─── Sidebar: premissas ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Premissas")
    cobertura = st.slider("Cobertura alvo após a chegada (dias)", 7, 120, 30, 1,
                          help="Período de revisão: quanto tempo o pedido deve cobrir depois de "
                               "recebido, além do lead time.")
    lt_pad = st.number_input("Lead time padrão (dias)", 1, 365, 30,
                             help="Usado só para itens sem prazo de entrega cadastrado.")
    tol = st.slider("Tolerância antes de 'EXCESSO'", 0, 100, 20, 5, format="%d%%") / 100
    modo = st.radio("Demanda no horizonte",
                    ["Máximo entre empenho/PV e consumo (recomendado)", "Somar empenho/PV + consumo"],
                    help="O consumo médio do kardex já contém as saídas que hoje aparecem como "
                         "empenho. Somar os dois conta a mesma peça duas vezes. Use 'Somar' só "
                         "para itens cujo empenho seja demanda extra (projeto especial).")
    usar_emax = st.checkbox("Estoque máximo limita a quantidade", True)
    meses_k = st.slider("Meses de kardex para o consumo médio", 3, 12, 6)
    P = m.Premissas(cobertura_alvo_dias=cobertura, lead_time_padrao_dias=lt_pad,
                    tolerancia_excesso=tol,
                    modo_demanda=m.MODO_MAXIMO if modo.startswith("Máximo") else m.MODO_SOMA,
                    usar_estoque_maximo=usar_emax)

st.markdown("<div class='hero'><h2 style='margin:0'>📦 Análise de Quantidade de Compra</h2>"
            "A quantidade do pedido faz sentido? Estoque, <b>empenho</b>, <b>pedido de venda</b>, "
            "compras em aberto, <b>PP / ES / máximo</b> e <b>consumo do kardex</b> em um veredito "
            "por item.</div>", unsafe_allow_html=True)

aba_lote, aba_item, aba_ajuda = st.tabs(["📋 Análise em lote", "🔎 Item avulso", "📘 Como funciona"])

# ─── ABA 1 · lote ────────────────────────────────────────────────────────────
with aba_lote:
    c1, c2 = st.columns([2, 1])
    up = c1.file_uploader("Planilha de pedidos / SCs (xlsx ou csv) — 1 linha por item",
                          type=["xlsx", "xls", "csv"])
    usar_ex = c2.toggle("Usar dados de exemplo", value=up is None)
    modelo = io.BytesIO()
    m.planilha_exemplo().to_excel(modelo, index=False)
    c2.download_button("⬇️ Baixar planilha modelo", modelo.getvalue(), "modelo_analise_compras.xlsx",
                       width="stretch")

    df_in = None
    if up is not None:
        try:
            df_in = ler_planilha(up)
        except Exception as e:  # noqa: BLE001
            st.error(f"Não consegui ler a planilha: {e}")
    elif usar_ex:
        df_in = m.planilha_exemplo()

    with st.expander("🌐 Completar dados pelo site de consulta (só na rede Selgron)"):
        st.caption("Busca estoque, empenho, PV, parâmetros e kardex de cada produto em "
                   "consulta.selgron.com.br. Colunas já preenchidas na planilha têm prioridade.")
        url_p = st.text_input("Modelo da URL do produto", cc.URL_PADRAO + "?produto={codigo}",
                              help="Copie da barra de endereço ao consultar um item e troque o "
                                   "código por {codigo}.")
        url_k = st.text_input("Modelo da URL do kardex (se for outra página)", "")
        cu, cs, cl = st.columns(3)
        usr = cu.text_input("Usuário (se houver login)")
        pwd = cs.text_input("Senha do site", type="password")
        url_l = cl.text_input("URL de login", "")
        buscar = st.button("Buscar no site", disabled=df_in is None)
        if buscar and df_in is not None:
            try:
                cli = cc.ClienteConsulta(url_p, url_k, usr, pwd, url_l)
                barra = st.progress(0.0, "Consultando...")
                df_in, erros = cc.completar_com_consulta(
                    df_in, cli, meses_k, lambda f, cod: barra.progress(f, f"Consultando {cod}"))
                st.session_state.df_site = df_in
                if erros:
                    st.warning(f"{len(erros)} itens com erro:\n\n" + "\n".join(erros[:20]))
                else:
                    st.success("Dados completados pelo site.")
            except Exception as e:  # noqa: BLE001
                st.error(f"Falha ao acessar o site: {e}. Este app precisa rodar dentro da rede "
                         "Selgron para alcançar o site de consulta.")
    if up is None and not usar_ex and "df_site" in st.session_state:
        df_in = st.session_state.df_site

    if df_in is None:
        st.info("Suba a planilha de pedidos ou ative os dados de exemplo.")
    else:
        try:
            res = m.analisar_tabela(df_in, P)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        excesso = res[res["veredito"].isin([m.EXCESSO, m.SEM_NECESS, m.SEM_GIRO])]
        val_exc = excesso["delta_valor"].clip(lower=0).sum()
        val_tot = (res["qtd_pedido"] * res["preco_unit"]).sum()
        insuf = res[res["veredito"] == m.INSUFICIENTE]
        k = st.columns(5)
        kpi(k[0], "Itens analisados", len(res), f"{res['pedido'].nunique()} pedidos")
        kpi(k[1], "Adequados", f"{(res['veredito'] == m.ADEQUADO).mean():.0%}",
            f"{(res['veredito'] == m.ADEQUADO).sum()} itens")
        kpi(k[2], "Compra acima do justificável", brl(val_exc),
            f"{val_exc / val_tot:.0%} do valor analisado" if val_tot else "")
        kpi(k[3], "Risco de falta", len(insuf), "itens com pedido insuficiente")
        kpi(k[4], "Sem dados", (res["veredito"] == m.DADOS_INSUF).sum(), "itens a completar")

        g1, g2 = st.columns([1, 1.4])
        cont = res["veredito"].value_counts().reset_index()
        cont.columns = ["veredito", "itens"]
        fig = px.bar(cont, x="itens", y="veredito", orientation="h", color="veredito",
                     color_discrete_map={v: i["cor"] for v, i in m.VEREDITOS.items()})
        fig.update_layout(height=260, showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
                          yaxis_title=None, xaxis_title="itens")
        g1.plotly_chart(fig, width="stretch")
        if res["comprador"].astype(bool).any() and val_exc > 0:
            porc = (excesso.groupby("comprador")["delta_valor"].sum().clip(lower=0)
                    .sort_values().reset_index())
            fig2 = px.bar(porc, x="delta_valor", y="comprador", orientation="h",
                          color_discrete_sequence=[NAVY], title="R$ acima do justificável por comprador")
            fig2.update_layout(height=260, margin=dict(l=0, r=0, t=40, b=0),
                               yaxis_title=None, xaxis_title="R$")
            g2.plotly_chart(fig2, width="stretch")

        f1, f2 = st.columns(2)
        sel_v = f1.multiselect("Veredito", list(m.VEREDITOS), default=[])
        compradores = sorted(x for x in res["comprador"].unique() if x)
        sel_c = f2.multiselect("Comprador", compradores, default=[])
        vis = res.copy()
        if sel_v:
            vis = vis[vis["veredito"].isin(sel_v)]
        if sel_c:
            vis = vis[vis["comprador"].isin(sel_c)]

        tabela = vis[["veredito", "pedido", "produto", "descricao", "comprador", "qtd_pedido",
                      "qtd_min", "qtd_ideal", "qtd_max", "qtd_sugerida", "delta_valor",
                      "cobertura_pos_pedido_dias", "alertas"]].copy()
        tabela["veredito"] = tabela["veredito"].map(lambda v: f"{m.VEREDITOS[v]['emoji']} {v}")
        st.dataframe(
            tabela, width="stretch", hide_index=True, height=380,
            column_config={
                "qtd_pedido": st.column_config.NumberColumn("Pedido", format="%.2f"),
                "qtd_min": st.column_config.NumberColumn("Mín", format="%.2f"),
                "qtd_ideal": st.column_config.NumberColumn("Ideal", format="%.2f"),
                "qtd_max": st.column_config.NumberColumn("Máx", format="%.2f"),
                "qtd_sugerida": st.column_config.NumberColumn("Sugerido", format="%.2f"),
                "delta_valor": st.column_config.NumberColumn("Δ R$", format="R$ %.0f"),
                "cobertura_pos_pedido_dias": st.column_config.NumberColumn("Cobertura pós (d)",
                                                                           format="%.0f"),
            })
        st.download_button("⬇️ Exportar análise (Excel)", excel_resultado(res),
                           "analise_quantidade_compras.xlsx", type="primary")

        st.divider()
        opcoes = [f"{r.produto} · {r.descricao[:40]} · {r.veredito}" for r in vis.itertuples()]
        if opcoes:
            esc = st.selectbox("Detalhar item", range(len(opcoes)), format_func=lambda i: opcoes[i])
            bloco_detalhe(vis.iloc[esc])

# ─── ABA 2 · item avulso ─────────────────────────────────────────────────────
with aba_item:
    st.caption("Simule um item: digite os números da tela de consulta, ou suba a página salva "
               "(Ctrl+S no navegador) para preencher automaticamente.")
    pre = {}
    html_up = st.file_uploader("Página de consulta salva (.html) — opcional", type=["html", "htm"])
    if html_up is not None:
        raw = html_up.getvalue()
        html = raw.decode("utf-8", errors="ignore")
        if "Ã" in html:
            html = raw.decode("latin-1", errors="ignore")
        pre = cc.dados_do_produto(html, meses_k)
        dbg = pre.pop("_DEBUG")
        achados = {k: v for k, v in pre.items() if not k.startswith("_")}
        st.success(f"{len(achados)} campos reconhecidos: " + ", ".join(achados) if achados
                   else "Nenhum campo reconhecido — veja os rótulos encontrados abaixo.")
        with st.expander("Diagnóstico da leitura (para ajustar o conector)"):
            st.write("Pares rótulo → valor encontrados:")
            st.dataframe(pd.DataFrame(dbg["pares"], columns=["rótulo", "valor"]).drop_duplicates(),
                         width="stretch", height=220)
            st.write(f"Tabelas na página: {len(dbg['tabelas'])} · kardex detectado: "
                     f"{'sim' if dbg['kardex'] is not None else 'não'}")
            for i, t in enumerate(dbg["tabelas"][:6]):
                st.caption(f"Tabela {i + 1}")
                st.dataframe(t.head(15), width="stretch")

    def v(campo, padrao=0.0):
        x = pre.get(campo)
        return float(x) if isinstance(x, (int, float)) and x is not None else padrao

    with st.form("item"):
        a, b, c, d = st.columns(4)
        prod = a.text_input("Produto", "")
        qtd = b.number_input("Qtd do pedido", 0.0, value=0.0, step=1.0)
        preco = c.number_input("Preço unitário (R$)", 0.0, value=v("PRECO_UNIT"))
        lt = d.number_input("Lead time (dias)", 0.0, value=v("LEAD_TIME_DIAS", 0.0))
        a, b, c, d = st.columns(4)
        est = a.number_input("Estoque", value=v("ESTOQUE"))
        emp = b.number_input("Empenhado (OPs)", 0.0, value=v("EMPENHADO"))
        pv = c.number_input("Pedido de venda", 0.0, value=v("PEDIDO_VENDA"))
        oc = d.number_input("Outros pedidos de compra em aberto", 0.0, value=v("COMPRAS_ABERTAS"))
        a, b, c, d = st.columns(4)
        cmm = a.number_input("Consumo médio mensal (kardex)", 0.0, value=v("CONSUMO_MEDIO_MENSAL"))
        es = b.number_input("Estoque de segurança", 0.0, value=v("ESTOQUE_SEGURANCA"))
        pp = c.number_input("Ponto de pedido", 0.0, value=v("PONTO_PEDIDO"))
        emax = d.number_input("Estoque máximo", 0.0, value=v("ESTOQUE_MAXIMO"))
        a, b, _, _ = st.columns(4)
        lmin = a.number_input("Lote mínimo", 0.0, value=v("LOTE_MINIMO"))
        lmul = b.number_input("Múltiplo / embalagem", 0.0, value=v("LOTE_MULTIPLO"))
        ok = st.form_submit_button("Analisar", type="primary")
    if ok:
        it = m.Item(produto=prod or "item", descricao=str(pre.get("DESCRICAO", "")), qtd_pedido=qtd,
                    estoque=est, empenhado=emp, pedido_venda=pv, compras_abertas=oc,
                    consumo_medio_mensal=cmm, estoque_seguranca=es, ponto_pedido=pp,
                    estoque_maximo=emax, lead_time_dias=lt or None, lote_minimo=lmin,
                    lote_multiplo=lmul, preco_unit=preco)
        r = m.analisar_item(it, P)
        from dataclasses import asdict
        bloco_detalhe(pd.Series({**asdict(it), **r.as_dict()}))

# ─── ABA 3 · ajuda ───────────────────────────────────────────────────────────
with aba_ajuda:
    st.markdown("""
### A pergunta que o app responde
**"Com o que temos, o que já está reservado e o que vamos consumir, esta quantidade se justifica?"**

### Cálculo (por item)
| Etapa | Fórmula |
|---|---|
| Disponível | Estoque − Empenhado − Pedido de venda |
| Posição projetada | Disponível + **outros** pedidos de compra em aberto |
| Demanda prevista | Consumo médio diário (kardex) × horizonte |
| **Qtd mínima** | ES + demanda no **lead time** − posição → abaixo disso, falta antes da chegada |
| **Qtd ideal** | ES + demanda em **lead time + cobertura alvo** − posição, arredondada ao lote |
| **Qtd máxima** | Ideal × (1 + tolerância), limitada pelo estoque máximo (se houver) |

### Vereditos
| | Quando |
|---|---|
| 🔴 SEM NECESSIDADE | Posição projetada já cobre todo o horizonte |
| 🔴 EXCESSO | Pedido > qtd máxima |
| 🟠 INSUFICIENTE | Pedido < qtd mínima (risco de parar produção) |
| 🟣 SEM GIRO | Kardex sem consumo e nenhuma reserva |
| 🟢 ADEQUADO | Dentro da faixa mínima–máxima |
| ⚪ DADOS INSUFICIENTES | Falta estoque ou consumo |

### Dupla contagem empenho × consumo
O consumo do kardex é a soma das requisições passadas, ou seja, os empenhos de ontem.
Somar o empenho de hoje com o consumo previsto conta a mesma peça duas vezes. No modo
recomendado, a demanda do horizonte é o **maior** entre o firme (empenho + PV) e o
previsto (consumo × dias).

### Kardex
Saídas por mês nos últimos N meses **fechados**. Meses sem saída contam como zero.
Transferências, devoluções, acertos de inventário e estornos são ignorados.

### Alertas de cadastro
O app compara o ponto de pedido cadastrado com o teórico (consumo × lead time + ES).
Desvio acima de 50% indica parâmetro desatualizado: o pedido pode estar certo e o cadastro, errado.
""")
    st.markdown("**Colunas aceitas na planilha** (nomes alternativos e campos TOTVS também são "
                "reconhecidos):")
    st.dataframe(pd.DataFrame([(k, ", ".join(v[:6])) for k, v in m.ALIASES.items()
                               if k not in ("DATA", "QTD_SAIDA", "TIPO_MOV", "HISTORICO")],
                              columns=["Coluna", "Também aceita"]),
                 width="stretch", hide_index=True)
