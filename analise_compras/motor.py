# ─────────────────────────────────────────────────────────────────────────────
#  SELGRON INDUSTRIAL — Análise de Quantidade de Compra · motor de cálculo
#  Departamento de Suprimentos · Lucas Melo Nasato
#
#  Responde a uma pergunta só: "a quantidade deste pedido faz sentido?"
#  Cruza estoque, empenho, pedido de venda, compras em aberto, parâmetros de
#  estoque (PP, ES, máximo, lotes) e o consumo médio do kardex.
#  Sem dependência de Streamlit — pode ser testado e reutilizado isoladamente.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass, field, asdict

import numpy as np
import pandas as pd

DIAS_MES = 30.0

# ─── Vereditos ───────────────────────────────────────────────────────────────
ADEQUADO      = "ADEQUADO"
EXCESSO       = "EXCESSO"
INSUFICIENTE  = "INSUFICIENTE"
SEM_NECESS    = "SEM NECESSIDADE"
SEM_GIRO      = "SEM GIRO"
DADOS_INSUF   = "DADOS INSUFICIENTES"

VEREDITOS = {
    ADEQUADO:     dict(emoji="🟢", cor="#155724", bg="#D4EDDA", ordem=5,
                       desc="Quantidade dentro da faixa justificável."),
    INSUFICIENTE: dict(emoji="🟠", cor="#7E5109", bg="#FDE8D8", ordem=2,
                       desc="Pedido não cobre a demanda até a próxima reposição — risco de falta."),
    EXCESSO:      dict(emoji="🔴", cor="#721C24", bg="#F8D7DA", ordem=1,
                       desc="Pedido acima do que a demanda + parâmetros justificam — capital parado."),
    SEM_NECESS:   dict(emoji="🔴", cor="#721C24", bg="#F8D7DA", ordem=0,
                       desc="Estoque + compras em aberto já cobrem o horizonte. Pedido não precisaria existir."),
    SEM_GIRO:     dict(emoji="🟣", cor="#4A235A", bg="#EBDEF0", ordem=3,
                       desc="Item sem consumo no kardex e sem empenho/PV — compra sem demanda visível."),
    DADOS_INSUF:  dict(emoji="⚪", cor="#595959", bg="#EEEEEE", ordem=4,
                       desc="Faltam dados mínimos (estoque ou consumo) para julgar."),
}

UNIDADES_INTEIRAS = {"PC", "PCS", "PCA", "UN", "UND", "UNID", "CJ", "JG", "KIT", "CX", "PAR"}

MODO_MAXIMO = "max"     # demanda = max(firme, prevista) → evita dupla contagem
MODO_SOMA   = "soma"    # demanda = firme + prevista     → conservador


@dataclass
class Premissas:
    """Parâmetros globais da análise (ajustáveis na tela)."""
    cobertura_alvo_dias: float = 30.0     # período de revisão: quanto estoque o pedido deve cobrir após chegar
    lead_time_padrao_dias: float = 30.0   # usado quando o item não tem prazo de entrega cadastrado
    tolerancia_excesso: float = 0.20      # folga acima da qtd ideal antes de chamar de EXCESSO
    modo_demanda: str = MODO_MAXIMO
    usar_estoque_maximo: bool = True      # se o item tem estoque máximo, ele limita a qtd aceitável


@dataclass
class Item:
    produto: str
    qtd_pedido: float
    descricao: str = ""
    estoque: float | None = None          # saldo físico atual
    empenhado: float = 0.0                # reservado para OPs (produção)
    pedido_venda: float = 0.0             # reservado para pedidos de venda
    compras_abertas: float = 0.0          # saldo de OUTROS pedidos de compra ainda não recebidos
    consumo_medio_mensal: float | None = None   # kardex
    estoque_seguranca: float = 0.0
    ponto_pedido: float = 0.0
    estoque_maximo: float = 0.0
    lead_time_dias: float | None = None
    lote_minimo: float = 0.0
    lote_multiplo: float = 0.0            # lote econômico / embalagem
    preco_unit: float = 0.0
    pedido: str = ""
    fornecedor: str = ""
    comprador: str = ""
    unidade: str = ""


@dataclass
class Resultado:
    veredito: str
    qtd_min: float = 0.0          # o mínimo para não faltar até a chegada
    qtd_ideal: float = 0.0        # cobre lead time + cobertura alvo + ES (arredondado ao lote)
    qtd_max: float = 0.0          # teto aceitável (tolerância ou estoque máximo)
    qtd_sugerida: float = 0.0     # o que o app recomendaria comprar
    delta_qtd: float = 0.0        # pedido − sugerida (+ = comprou a mais)
    delta_valor: float = 0.0
    disponivel: float = 0.0       # estoque − empenho − PV
    posicao_projetada: float = 0.0  # disponível + compras em aberto (antes deste pedido)
    cobertura_atual_dias: float | None = None
    cobertura_pos_pedido_dias: float | None = None
    pp_teorico: float | None = None
    alertas: list = field(default_factory=list)
    memoria: list = field(default_factory=list)   # passo a passo do cálculo, legível

    def as_dict(self) -> dict:
        d = asdict(self)
        d["alertas"] = " | ".join(self.alertas)
        d["memoria"] = "\n".join(self.memoria)
        return d


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _arredonda_lote(qtd: float, lote_min: float, multiplo: float) -> float:
    if qtd <= 0:
        return 0.0
    if lote_min and qtd < lote_min:
        qtd = lote_min
    if multiplo and multiplo > 0:
        qtd = math.ceil(round(qtd / multiplo, 6)) * multiplo
    return float(qtd)


def _fmt(v) -> str:
    if v is None:
        return "—"
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").rstrip("0").rstrip(",")


def _cobertura_dias(qtd: float, consumo_dia: float) -> float | None:
    if consumo_dia <= 0:
        return None
    return qtd / consumo_dia


# ─── Núcleo ──────────────────────────────────────────────────────────────────

def analisar_item(it: Item, p: Premissas = Premissas()) -> Resultado:
    """Julga se `it.qtd_pedido` é coerente com a necessidade líquida do item.

    Lógica (MRP simplificado, ponto de pedido + período de revisão):
        disponível        = estoque − empenhado − pedido de venda
        posição projetada = disponível + compras em aberto (outros pedidos)
        horizonte         = lead time + cobertura alvo
        demanda prevista  = consumo médio diário × horizonte
        demanda firme     = empenho + PV  (já descontada do disponível)
        necessidade       = ES + demanda prevista − posição projetada
                            (modo 'max': só a parte da previsão que excede a
                             demanda firme, para não contar o empenho 2×)
    """
    alertas, mem = [], []

    if it.estoque is None or (it.consumo_medio_mensal is None
                              and (it.empenhado or 0) + (it.pedido_venda or 0) == 0):
        r = Resultado(veredito=DADOS_INSUF, qtd_sugerida=0.0)
        r.alertas.append("Sem estoque e/ou sem consumo médio — complete os dados do item.")
        return r

    cmm = float(it.consumo_medio_mensal or 0.0)
    cd = cmm / DIAS_MES
    lt = float(it.lead_time_dias) if it.lead_time_dias else p.lead_time_padrao_dias
    if not it.lead_time_dias:
        alertas.append(f"Sem lead time cadastrado — usado padrão de {lt:.0f} dias.")

    firme = float(it.empenhado or 0) + float(it.pedido_venda or 0)
    disponivel = float(it.estoque) - firme
    posicao = disponivel + float(it.compras_abertas or 0)
    es = float(it.estoque_seguranca or 0)

    mem.append(f"Disponível = estoque {_fmt(it.estoque)} − empenho {_fmt(it.empenhado)} "
               f"− PV {_fmt(it.pedido_venda)} = {_fmt(disponivel)}")
    mem.append(f"Posição projetada = disponível {_fmt(disponivel)} + compras em aberto "
               f"{_fmt(it.compras_abertas)} = {_fmt(posicao)}")

    def demanda_prevista(dias: float) -> float:
        prev = cd * dias
        if p.modo_demanda == MODO_MAXIMO:
            # O consumo histórico já contém o que hoje aparece como empenho/PV:
            # somar os dois conta a mesma peça duas vezes. Só entra a previsão
            # que excede a demanda firme já reservada.
            return max(0.0, prev - firme)
        return prev

    # Mínimo: chegar ao fim do lead time sem romper o estoque de segurança.
    nec_min = es + demanda_prevista(lt) - posicao
    # Ideal: cobrir lead time + período de revisão.
    horizonte = lt + p.cobertura_alvo_dias
    nec_ideal = es + demanda_prevista(horizonte) - posicao

    mem.append(f"Consumo médio = {_fmt(cmm)}/mês ({_fmt(cd)}/dia) · lead time {lt:.0f} d · "
               f"horizonte {horizonte:.0f} d")
    mem.append(f"Necessidade mínima (até a chegada) = ES {_fmt(es)} + demanda "
               f"{_fmt(demanda_prevista(lt))} − posição {_fmt(posicao)} = {_fmt(nec_min)}")
    mem.append(f"Necessidade ideal (lead time + {p.cobertura_alvo_dias:.0f} d) = ES {_fmt(es)} + demanda "
               f"{_fmt(demanda_prevista(horizonte))} − posição {_fmt(posicao)} = {_fmt(nec_ideal)}")

    qtd_min = max(0.0, nec_min)
    qtd_ideal_bruta = max(0.0, nec_ideal)
    multiplo = it.lote_multiplo
    if not multiplo and _chave(it.unidade) in UNIDADES_INTEIRAS:
        multiplo = 1.0   # peça não se compra fracionada
    qtd_ideal = _arredonda_lote(qtd_ideal_bruta, it.lote_minimo, multiplo)
    if qtd_ideal > qtd_ideal_bruta + 1e-9 and qtd_ideal_bruta > 0:
        mem.append(f"Arredondado ao lote (mín {_fmt(it.lote_minimo)}, múltiplo "
                   f"{_fmt(it.lote_multiplo)}): {_fmt(qtd_ideal_bruta)} → {_fmt(qtd_ideal)}")

    qtd_max = qtd_ideal * (1 + p.tolerancia_excesso)
    if p.usar_estoque_maximo and it.estoque_maximo and it.estoque_maximo > 0:
        teto_emax = it.estoque_maximo - posicao
        if teto_emax < qtd_max:
            mem.append(f"Teto pelo estoque máximo: {_fmt(it.estoque_maximo)} − posição "
                       f"{_fmt(posicao)} = {_fmt(teto_emax)}")
            qtd_max = teto_emax
    # Nunca abaixo do mínimo para não faltar (arredondado ao lote do fornecedor):
    # lote mínimo, por si só, não torna o pedido 'excessivo'.
    qtd_max = max(qtd_max, _arredonda_lote(qtd_min, it.lote_minimo, multiplo))

    q = float(it.qtd_pedido or 0)
    qtd_sug = min(qtd_ideal, qtd_max)

    # ── Veredito ──
    if cmm <= 0 and firme <= 0:
        veredito = SEM_GIRO
        qtd_sug = _arredonda_lote(max(0.0, es - posicao), it.lote_minimo, it.lote_multiplo)
        alertas.append("Kardex sem consumo e nenhuma reserva — confirmar se é item novo, "
                       "projeto específico (MTO) ou compra a ser cancelada.")
    elif qtd_ideal <= 0:
        veredito = SEM_NECESS if q > 0 else ADEQUADO
    elif q + 1e-9 < qtd_min:
        veredito = INSUFICIENTE
    elif q > qtd_max + 1e-9:
        veredito = EXCESSO
    else:
        veredito = ADEQUADO

    # ── Coberturas ──
    cob_atual = _cobertura_dias(max(posicao, 0.0), cd) if cd > 0 else None
    cob_pos = _cobertura_dias(max(posicao + q, 0.0), cd) if cd > 0 else None

    # ── Diagnóstico de parâmetros (o pedido pode estar certo e o cadastro errado) ──
    pp_teo = None
    if cd > 0:
        pp_teo = cd * lt + es
        pp = float(it.ponto_pedido or 0)
        if pp > 0:
            desvio = (pp - pp_teo) / pp_teo if pp_teo else 0
            if abs(desvio) > 0.5:
                alertas.append(f"Ponto de pedido cadastrado ({_fmt(pp)}) difere "
                               f"{desvio:+.0%} do teórico ({_fmt(pp_teo)} = consumo × LT + ES).")
        else:
            alertas.append(f"Sem ponto de pedido cadastrado (teórico ≈ {_fmt(pp_teo)}).")
        if es <= 0:
            alertas.append("Sem estoque de segurança cadastrado.")
    if it.ponto_pedido and es and it.ponto_pedido < es:
        alertas.append("Ponto de pedido menor que o estoque de segurança — parâmetro incoerente.")
    if it.estoque_maximo and it.ponto_pedido and it.estoque_maximo < it.ponto_pedido:
        alertas.append("Estoque máximo menor que o ponto de pedido — parâmetro incoerente.")
    if disponivel < 0:
        alertas.append(f"Estoque não cobre empenho + PV hoje (faltam {_fmt(-disponivel)}).")
    if cob_pos and cob_pos > 180:
        alertas.append(f"Após o pedido a cobertura será de {cob_pos/DIAS_MES:.1f} meses.")
    if it.lote_minimo and q > 0 and q <= it.lote_minimo + 1e-9 and veredito == EXCESSO:
        alertas.append("Excesso explicado pelo lote mínimo do fornecedor — negociar lote ou consignação.")

    delta = q - qtd_sug
    return Resultado(
        veredito=veredito,
        qtd_min=round(qtd_min, 4),
        qtd_ideal=round(qtd_ideal, 4),
        qtd_max=round(qtd_max, 4),
        qtd_sugerida=round(qtd_sug, 4),
        delta_qtd=round(delta, 4),
        delta_valor=round(delta * float(it.preco_unit or 0), 2),
        disponivel=round(disponivel, 4),
        posicao_projetada=round(posicao, 4),
        cobertura_atual_dias=None if cob_atual is None else round(cob_atual, 1),
        cobertura_pos_pedido_dias=None if cob_pos is None else round(cob_pos, 1),
        pp_teorico=None if pp_teo is None else round(pp_teo, 2),
        alertas=alertas,
        memoria=mem,
    )


# ─── Kardex → consumo médio ──────────────────────────────────────────────────

def consumo_do_kardex(kardex: pd.DataFrame, meses: int = 6,
                      ref: pd.Timestamp | None = None) -> dict:
    """Calcula consumo médio mensal a partir das saídas do kardex.

    Espera colunas DATA, QTD_SAIDA (ou QTD + TIPO 'S'/'E') e opcionalmente
    HISTORICO/TIPO_MOV. Ignora transferências e devoluções de compra.
    Meses sem saída contam como zero (média honesta, não a média dos meses ativos).
    """
    if kardex is None or kardex.empty:
        return dict(consumo_medio_mensal=None, meses=0, cv=None, mensal=pd.Series(dtype=float))
    k = normalizar_colunas(kardex.copy())
    if "DATA" not in k.columns:
        return dict(consumo_medio_mensal=None, meses=0, cv=None, mensal=pd.Series(dtype=float))
    k["DATA"] = pd.to_datetime(k["DATA"], errors="coerce", dayfirst=True)
    k = k.dropna(subset=["DATA"])

    if "QTD_SAIDA" in k.columns:
        k["_S"] = pd.to_numeric(k["QTD_SAIDA"], errors="coerce").fillna(0).abs()
    elif "QTD" in k.columns and "TIPO_MOV" in k.columns:
        q = pd.to_numeric(k["QTD"], errors="coerce").fillna(0)
        tipo = k["TIPO_MOV"].astype(str).str.upper().str.strip()
        k["_S"] = np.where(tipo.str.startswith("S") | (q < 0), q.abs(), 0)
    else:
        return dict(consumo_medio_mensal=None, meses=0, cv=None, mensal=pd.Series(dtype=float))

    if "HISTORICO" in k.columns:
        h = k["HISTORICO"].astype(str).map(_sem_acento).str.upper()
        ignorar = h.str.contains("TRANSF|DEVOL|ACERTO|INVENT|ESTORNO", regex=True)
        k.loc[ignorar, "_S"] = 0

    ref = ref or pd.Timestamp.today().normalize()
    inicio = (ref.to_period("M") - meses).to_timestamp()
    fim = ref.to_period("M").to_timestamp()           # mês corrente fica de fora (incompleto)
    k = k[(k["DATA"] >= inicio) & (k["DATA"] < fim)]
    idx = pd.period_range(inicio, periods=meses, freq="M")
    mensal = k.groupby(k["DATA"].dt.to_period("M"))["_S"].sum().reindex(idx, fill_value=0.0)
    media = float(mensal.mean())
    cv = float(mensal.std(ddof=0) / media) if media > 0 else None
    return dict(consumo_medio_mensal=media, meses=meses, cv=cv, mensal=mensal)


# ─── Normalização de planilhas (TOTVS / consulta / manual) ───────────────────

def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))


def _chave(s: str) -> str:
    s = _sem_acento(s).upper().strip()
    for ch in ".:/()-#º°":
        s = s.replace(ch, " ")
    return "_".join(s.split())


# Sinônimos aceitos → nome interno. Inclui nomes de campo do TOTVS Protheus
# (SB1/SB2/SC7) para quem extrair direto do ERP.
ALIASES = {
    "PRODUTO":              ["PRODUTO", "COD_PRODUTO", "CODIGO", "COD", "PROD", "ITEM", "B1_COD", "C7_PRODUTO", "COD_ITEM"],
    "DESCRICAO":            ["DESCRICAO", "DESC", "DESCR", "DESCRICAO_PRODUTO", "B1_DESC", "C7_DESCRI"],
    "QTD_PEDIDO":           ["QTD_PEDIDO", "QUANTIDADE", "QTD", "QTDE", "QUANT", "QTD_COMPRA", "QTDE_PEDIDO", "C7_QUANT", "SALDO_PEDIDO"],
    "ESTOQUE":              ["ESTOQUE", "SALDO", "SALDO_ATUAL", "ESTOQUE_ATUAL", "QTD_ESTOQUE", "SALDO_ESTOQUE", "B2_QATU", "DISPONIVEL_FISICO"],
    "EMPENHADO":            ["EMPENHADO", "EMPENHO", "QTD_EMPENHADA", "EMPENHADA", "B2_QEMP"],
    "PEDIDO_VENDA":         ["PEDIDO_VENDA", "PED_VENDA", "QTD_PEDIDO_VENDA", "PV", "RESERVA", "RESERVADO", "B2_QPEDVEN", "B2_RESERVA"],
    "COMPRAS_ABERTAS":      ["COMPRAS_ABERTAS", "PEDIDO_COMPRA", "PED_COMPRA", "EM_PEDIDO", "QTD_PEDIDO_COMPRA", "SALDO_PEDIDO_COMPRA", "A_RECEBER", "B2_SALPEDI"],
    "CONSUMO_MEDIO_MENSAL": ["CONSUMO_MEDIO_MENSAL", "CONSUMO_MEDIO", "CMM", "MEDIA_CONSUMO", "CONSUMO_MENSAL", "CONSUMO", "B3_MEDIA"],
    "ESTOQUE_SEGURANCA":    ["ESTOQUE_SEGURANCA", "EST_SEGURANCA", "ES", "SEGURANCA", "ESTOQUE_MINIMO_SEGURANCA", "B1_ESTSEG"],
    "PONTO_PEDIDO":         ["PONTO_PEDIDO", "PONTO_DE_PEDIDO", "PP", "ESTOQUE_MINIMO", "EST_MINIMO", "B1_EMIN"],
    "ESTOQUE_MAXIMO":       ["ESTOQUE_MAXIMO", "EST_MAXIMO", "MAXIMO", "B1_EMAX"],
    "LEAD_TIME_DIAS":       ["LEAD_TIME_DIAS", "LEAD_TIME", "LT", "PRAZO_ENTREGA", "PRAZO", "PRAZO_DIAS", "B1_PE"],
    "LOTE_MINIMO":          ["LOTE_MINIMO", "LOTE_MIN", "B1_LM"],
    "LOTE_MULTIPLO":        ["LOTE_MULTIPLO", "LOTE_ECONOMICO", "MULTIPLO", "EMBALAGEM", "QTD_EMBALAGEM", "B1_LE", "B1_QE"],
    "PRECO_UNIT":           ["PRECO_UNIT", "PRECO", "PRECO_UNITARIO", "VLR_UNIT", "VALOR_UNITARIO", "VL_UNIT", "CUSTO_UNIT", "CUSTO_MEDIO", "C7_PRECO"],
    "PEDIDO":               ["PEDIDO", "NUM_PEDIDO", "N_PEDIDO", "NR_PEDIDO", "PEDIDO_COMPRA_NUM", "C7_NUM", "SC", "NUM_SC"],
    "FORNECEDOR":           ["FORNECEDOR", "RAZAO_SOCIAL", "NOME_FORNECEDOR", "C7_FORNECE"],
    "COMPRADOR":            ["COMPRADOR", "USUARIO", "C7_COMPRA"],
    "UNIDADE":              ["UNIDADE", "UN", "UM", "B1_UM"],
    # kardex
    "DATA":                 ["DATA", "DT", "DATA_MOV", "DATA_MOVIMENTO", "DT_EMISSAO", "EMISSAO", "D3_EMISSAO"],
    "QTD_SAIDA":            ["QTD_SAIDA", "SAIDA", "SAIDAS", "QTDE_SAIDA", "QUANT_SAIDA"],
    "TIPO_MOV":             ["TIPO_MOV", "TIPO", "E_S", "ES_TIPO", "TM", "D3_TM"],
    "HISTORICO":            ["HISTORICO", "OBS", "DOCUMENTO", "ORIGEM", "MOVIMENTO"],
}
_ALIAS_IDX = {_chave(a): k for k, lst in ALIASES.items() for a in lst}


def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    ren, usados = {}, set()
    for c in df.columns:
        alvo = _ALIAS_IDX.get(_chave(c))
        if alvo and alvo not in usados:
            ren[c] = alvo
            usados.add(alvo)
    return df.rename(columns=ren)


def _num(v, padrao=0.0):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return padrao
    if isinstance(v, str):
        s = v.strip().replace("R$", "").replace(" ", "")
        if not s:
            return padrao
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return padrao
    try:
        f = float(v)
        return padrao if math.isnan(f) else f
    except (TypeError, ValueError):
        return padrao


def item_de_linha(row: dict) -> Item:
    g = row.get
    return Item(
        produto=str(g("PRODUTO", "")).strip(),
        descricao=str(g("DESCRICAO", "") or "").strip(),
        qtd_pedido=_num(g("QTD_PEDIDO")),
        estoque=_num(g("ESTOQUE"), None),
        empenhado=_num(g("EMPENHADO")),
        pedido_venda=_num(g("PEDIDO_VENDA")),
        compras_abertas=_num(g("COMPRAS_ABERTAS")),
        consumo_medio_mensal=_num(g("CONSUMO_MEDIO_MENSAL"), None),
        estoque_seguranca=_num(g("ESTOQUE_SEGURANCA")),
        ponto_pedido=_num(g("PONTO_PEDIDO")),
        estoque_maximo=_num(g("ESTOQUE_MAXIMO")),
        lead_time_dias=_num(g("LEAD_TIME_DIAS"), None) or None,
        lote_minimo=_num(g("LOTE_MINIMO")),
        lote_multiplo=_num(g("LOTE_MULTIPLO")),
        preco_unit=_num(g("PRECO_UNIT")),
        pedido=str(g("PEDIDO", "") or "").strip(),
        fornecedor=str(g("FORNECEDOR", "") or "").strip(),
        comprador=str(g("COMPRADOR", "") or "").strip(),
        unidade=str(g("UNIDADE", "") or "").strip(),
    )


def analisar_tabela(df: pd.DataFrame, p: Premissas = Premissas()) -> pd.DataFrame:
    """Recebe uma planilha (1 linha = 1 item de pedido) e devolve com o veredito."""
    base = normalizar_colunas(df)
    if "PRODUTO" not in base.columns or "QTD_PEDIDO" not in base.columns:
        raise ValueError("A planilha precisa ter ao menos as colunas PRODUTO e QTD_PEDIDO.")
    base = base[base["PRODUTO"].notna() & (base["PRODUTO"].astype(str).str.strip() != "")]
    linhas = []
    for row in base.to_dict("records"):
        it = item_de_linha(row)
        r = analisar_item(it, p)
        linhas.append({**asdict(it), **r.as_dict()})
    out = pd.DataFrame(linhas)
    if not out.empty:
        out["_ordem"] = out["veredito"].map(lambda v: VEREDITOS[v]["ordem"])
        out = out.sort_values(["_ordem", "delta_valor"], ascending=[True, False]).drop(columns="_ordem")
    return out.reset_index(drop=True)


COLUNAS_MODELO = [
    "PEDIDO", "PRODUTO", "DESCRICAO", "UNIDADE", "FORNECEDOR", "COMPRADOR",
    "QTD_PEDIDO", "PRECO_UNIT", "ESTOQUE", "EMPENHADO", "PEDIDO_VENDA",
    "COMPRAS_ABERTAS", "CONSUMO_MEDIO_MENSAL", "ESTOQUE_SEGURANCA", "PONTO_PEDIDO",
    "ESTOQUE_MAXIMO", "LEAD_TIME_DIAS", "LOTE_MINIMO", "LOTE_MULTIPLO",
]


def planilha_exemplo() -> pd.DataFrame:
    rows = [
        # pedido, produto, desc, un, forn, comp, qtd, preço, est, emp, pv, oc, cmm, es, pp, emax, lt, lmin, lmult
        ["4501", "100234", "PARAFUSO SEXT M8X30 ZINC", "PC", "FIXAR", "ANA", 5000, 0.35, 1200, 300, 0, 0, 800, 400, 1200, 3000, 15, 1000, 500],
        ["4502", "200871", "ROLAMENTO 6205 2RS", "PC", "ROLMAX", "JOÃO", 40, 28.90, 6, 4, 2, 0, 12, 4, 10, 30, 20, 0, 0],
        ["4503", "310045", "CHAPA INOX 304 2MM", "KG", "AÇOS SUL", "ANA", 2500, 24.50, 1800, 600, 0, 500, 700, 300, 1000, 2500, 25, 0, 0],
        ["4504", "410990", "MOTOR WEG 1,5CV", "PC", "WEG", "JOÃO", 2, 1450.00, 0, 3, 0, 0, 1.5, 0, 0, 0, 35, 0, 0],
        ["4505", "520013", "SENSOR INDUTIVO M12", "PC", "SICK", "PEDRO", 30, 189.00, 25, 0, 0, 10, 0, 0, 0, 0, 30, 0, 0],
        ["4506", "600112", "CORREIA A-42", "PC", "GATES", "PEDRO", 10, 42.00, 4, 6, 0, 0, 9, 3, 8, 20, 10, 0, 0],
    ]
    return pd.DataFrame(rows, columns=COLUNAS_MODELO)
