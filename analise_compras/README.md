# Selgron — Análise de Quantidade de Compra v1.0

Responde, item a item: **a quantidade deste pedido faz sentido?**
Cruza estoque, empenho (OPs), pedido de venda, outros pedidos de compra em aberto,
ponto de pedido, estoque de segurança, estoque máximo, lotes e o consumo médio do kardex.

## Rodar
```bash
pip install -r analise_compras/requirements.txt
streamlit run analise_compras/app.py
```
No Streamlit Cloud: novo app apontando para `analise_compras/app.py` (mesmo repositório).
Senha: a mesma do Score (`senha_app` nos Secrets, padrão `Acesso2026`).

## Arquivos
| Arquivo | Papel |
|---|---|
| `motor.py` | Cálculo (sem Streamlit): necessidade líquida, faixa mín/ideal/máx, veredito, alertas de cadastro, consumo do kardex |
| `conector_consulta.py` | Leitura de consulta.selgron.com.br (HTTP na rede interna ou HTML salvo), por rótulo |
| `app.py` | Interface: análise em lote, item avulso, explicação do método |

## Entrada
Planilha com 1 linha por item de pedido. Obrigatórias: `PRODUTO`, `QTD_PEDIDO`.
Demais colunas (estoque, empenho, PV, consumo, PP, ES...) vêm da planilha ou do site.
Nomes alternativos e campos TOTVS Protheus (`B2_QATU`, `B2_QEMP`, `B1_EMIN`, `B1_ESTSEG`, `B1_PE`...)
são reconhecidos. Baixe o modelo pelo app.

## Pendência — conector do site
O site só responde dentro da rede Selgron. A extração é genérica (por rótulo) e precisa
ser validada com uma página real: na aba **Item avulso**, suba a página de um produto salva
com Ctrl+S e confira o "Diagnóstico da leitura". Rótulos diferentes se ajustam em
`ROTULOS` (`conector_consulta.py`).
