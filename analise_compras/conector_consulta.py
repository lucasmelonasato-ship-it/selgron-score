# ─────────────────────────────────────────────────────────────────────────────
#  Conector · consulta.selgron.com.br/produto.consulta.php
#
#  Lê a página de consulta de produto e extrai estoque, empenho, pedido de
#  venda, compras em aberto, parâmetros (PP, ES, máximo, lotes, prazo) e o
#  kardex. O site só é acessível pela rede da Selgron: o app precisa rodar
#  numa máquina interna (ou o usuário sobe o HTML salvo da página).
#
#  A extração é por RÓTULO ("Estoque", "Empenhado", "Ponto de Pedido"...), não
#  por posição — sobrevive a mudanças de layout. Os rótulos ficam em ROTULOS;
#  se o site usar outro nome, basta acrescentá-lo ali.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import io
import re

import pandas as pd

from motor import _chave, _num, normalizar_colunas, consumo_do_kardex

URL_PADRAO = "https://consulta.selgron.com.br/produto.consulta.php"

# campo interno → rótulos possíveis na página (comparação sem acento/caixa)
ROTULOS = {
    "DESCRICAO":            ["Descrição", "Descricao", "Desc. Produto"],
    "UNIDADE":              ["Unidade", "UN", "U.M."],
    "ESTOQUE":              ["Estoque", "Saldo", "Saldo Atual", "Estoque Atual", "Qtd. Estoque", "Saldo em Estoque"],
    "EMPENHADO":            ["Empenhado", "Empenho", "Qtd. Empenhada", "Empenhada"],
    "PEDIDO_VENDA":         ["Pedido de Venda", "Pedidos de Venda", "Qtd. Pedido Venda", "Ped. Venda", "Reservado"],
    "COMPRAS_ABERTAS":      ["Pedido de Compra", "Pedidos de Compra", "Em Pedido", "Saldo Pedido Compra", "A Receber", "Ped. Compra"],
    "PONTO_PEDIDO":         ["Ponto de Pedido", "Ponto Pedido", "Estoque Mínimo", "Est. Mínimo"],
    "ESTOQUE_SEGURANCA":    ["Estoque de Segurança", "Estoque Segurança", "Est. Segurança", "Segurança"],
    "ESTOQUE_MAXIMO":       ["Estoque Máximo", "Est. Máximo", "Máximo"],
    "LEAD_TIME_DIAS":       ["Prazo de Entrega", "Prazo Entrega", "Lead Time", "Prazo"],
    "LOTE_MINIMO":          ["Lote Mínimo", "Lote Min"],
    "LOTE_MULTIPLO":        ["Lote Econômico", "Lote Economico", "Qtd. Embalagem", "Múltiplo"],
    "CONSUMO_MEDIO_MENSAL": ["Consumo Médio", "Consumo Medio", "Média de Consumo", "Consumo Mensal"],
    "PRECO_UNIT":           ["Custo Médio", "Custo Medio", "Último Preço", "Ultimo Preco", "Preço"],
}
_ROT_IDX = {_chave(r): campo for campo, lst in ROTULOS.items() for r in lst}
_NUMERICOS = set(ROTULOS) - {"DESCRICAO", "UNIDADE"}


def _campo_do_rotulo(txt: str) -> str | None:
    return _ROT_IDX.get(_chave(txt.rstrip(":").strip()))


def extrair_pagina(html: str) -> dict:
    """Extrai {campos, kardex(DataFrame), tabelas(list), pares(list)} do HTML."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    pares: list[tuple[str, str]] = []

    # 1) células rótulo → valor (<th>/<td> vizinhos, <dt>/<dd>, <label> + input/span)
    for cel in soup.find_all(["th", "td", "dt", "label", "b", "strong", "span"]):
        txt = cel.get_text(" ", strip=True)
        if not txt or len(txt) > 40:
            continue
        if ":" in txt and cel.name in ("span", "b", "strong", "label", "td"):
            rot, _, val = txt.partition(":")
            if val.strip():
                pares.append((rot.strip(), val.strip()))
                continue
        viz = cel.find_next_sibling(["td", "dd", "span", "input"])
        if viz is None and cel.name in ("label", "b", "strong"):
            viz = cel.find_next(["input", "span", "td"])
        if viz is not None:
            val = viz.get("value") if viz.name == "input" else viz.get_text(" ", strip=True)
            if val:
                pares.append((txt, str(val)))
    for inp in soup.find_all("input"):
        nome = inp.get("name") or inp.get("id") or ""
        if nome and inp.get("value"):
            pares.append((nome, inp["value"]))

    campos: dict = {}
    for rot, val in pares:
        campo = _campo_do_rotulo(rot)
        if campo and campo not in campos:
            campos[campo] = _num(val, None) if campo in _NUMERICOS else val

    # 2) tabelas — a do kardex é a que tem data + saída/quantidade
    tabelas = []
    try:
        tabelas = pd.read_html(io.StringIO(html), decimal=",", thousands=".")
    except ValueError:
        pass
    kardex = None
    for t in tabelas:
        if isinstance(t.columns, pd.MultiIndex):
            t.columns = [" ".join(str(x) for x in c if "Unnamed" not in str(x)) for c in t.columns]
        n = normalizar_colunas(t.copy())
        if "DATA" in n.columns and ("QTD_SAIDA" in n.columns or {"QTD", "TIPO_MOV"} <= set(n.columns)):
            kardex = t
            break
        # tabela de 2 colunas tipo "rótulo | valor"
        if t.shape[1] == 2:
            for rot, val in t.astype(str).itertuples(index=False):
                campo = _campo_do_rotulo(rot)
                if campo and campo not in campos:
                    campos[campo] = _num(val, None) if campo in _NUMERICOS else val

    return dict(campos=campos, kardex=kardex, tabelas=tabelas, pares=pares)


def dados_do_produto(html: str, meses_consumo: int = 6) -> dict:
    """Campos prontos para o motor. Consumo do kardex tem prioridade sobre o campo."""
    ext = extrair_pagina(html)
    campos = dict(ext["campos"])
    if ext["kardex"] is not None:
        k = consumo_do_kardex(ext["kardex"], meses=meses_consumo)
        if k["consumo_medio_mensal"] is not None:
            campos["CONSUMO_MEDIO_MENSAL"] = k["consumo_medio_mensal"]
            campos["_CV_CONSUMO"] = k["cv"]
    campos["_FONTE"] = "consulta"
    campos["_DEBUG"] = ext
    return campos


class ClienteConsulta:
    """Sessão HTTP no site de consulta. Só funciona dentro da rede Selgron.

    url_produto: modelo da URL da página do produto, com {codigo}.
    url_kardex:  idem para a aba kardex, se ela for outra requisição.
    Os modelos reais devem ser copiados da barra de endereço do navegador.
    """

    def __init__(self, url_produto: str, url_kardex: str = "", usuario: str = "",
                 senha: str = "", url_login: str = "", campos_login: tuple = ("usuario", "senha"),
                 timeout: int = 20):
        import requests
        self.s = requests.Session()
        self.url_produto = url_produto
        self.url_kardex = url_kardex
        self.timeout = timeout
        if usuario and url_login:
            self.s.post(url_login, data={campos_login[0]: usuario, campos_login[1]: senha},
                        timeout=timeout)

    def _get(self, url: str) -> str:
        r = self.s.get(url, timeout=self.timeout)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or r.encoding
        return r.text

    def buscar(self, codigo: str, meses_consumo: int = 6) -> dict:
        html = self._get(self.url_produto.format(codigo=codigo))
        if self.url_kardex:
            html += self._get(self.url_kardex.format(codigo=codigo))
        return dados_do_produto(html, meses_consumo)


def completar_com_consulta(df: pd.DataFrame, cliente: ClienteConsulta,
                           meses_consumo: int = 6, progresso=None) -> tuple[pd.DataFrame, list]:
    """Preenche colunas vazias da planilha com o que vier do site. Planilha manda."""
    base = normalizar_colunas(df.copy())
    erros = []
    codigos = base["PRODUTO"].astype(str).str.strip().unique()
    cache = {}
    for i, cod in enumerate(codigos):
        try:
            cache[cod] = cliente.buscar(cod, meses_consumo)
        except Exception as e:  # noqa: BLE001 — erro por item não derruba o lote
            erros.append(f"{cod}: {e}")
        if progresso:
            progresso((i + 1) / len(codigos), cod)
    for campo in [c for c in ROTULOS if c not in ("PRECO_UNIT",)] + ["PRECO_UNIT"]:
        if campo not in base.columns:
            base[campo] = None
        vals = base["PRODUTO"].astype(str).str.strip().map(lambda c: cache.get(c, {}).get(campo))
        vazio = base[campo].isna() | (base[campo].astype(str).str.strip() == "")
        base.loc[vazio, campo] = vals[vazio]
    return base, erros


def limpar_html(txt: str) -> str:
    return re.sub(r"\s+", " ", txt or "").strip()
