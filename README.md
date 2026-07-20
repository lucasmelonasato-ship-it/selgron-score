# Selgron — Score de Fornecedores v2.0

Dashboard web para monitorar a performance dos fornecedores da Selgron Industrial,
cruzando **Prazo de Entrega** e **Qualidade (Inspeção de Recebimento)** em um único
score por fornecedor, por comprador e para o setor todo.

Desenvolvido para o Departamento de Suprimentos.

---

## Como rodar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar o app
```bash
streamlit run app.py
```
Acesse: **http://localhost:8501** · Senha de acesso: `Acesso2026`

---

## De onde vêm os dados (fechamento mensal)

Cada mês é **um arquivo** dentro da pasta `dados/`, nomeado `AAAA-MM.xlsx`:

```
dados/2026-05.xlsx   → Maio
dados/2026-06.xlsx   → Junho
dados/2026-07.xlsx   → Julho ...
```

Como o Streamlit Cloud reimplanta o repositório a cada reinício, esses arquivos
**nunca se perdem**. Para adicionar um mês, basta subir o `.xlsx` na pasta `dados/`
do GitHub — o seletor de mês do topo passa a enxergá-lo automaticamente.

Cada arquivo tem a aba **`BASE_DADOS`** com as colunas:

| Coluna            | Descrição                          |
|-------------------|------------------------------------|
| FORNECEDOR        | Nome do fornecedor                 |
| COMPRADOR         | Comprador responsável              |
| SCORE_GERAL       | Score 0–1 (60% prazo + 40% qual.)  |
| SCORE_PRAZO       | Score de prazo de entrega          |
| SCORE_QUALIDADE   | Score de qualidade (IQF)           |
| CLASSE            | A a E                              |
| TOTAL_ENTREGAS    | Entregas do mês                    |
| NO_PRAZO          | Entregas no prazo                  |
| TOTAL_ALERTAS     | Não conformidades (NCs)            |

> Os arquivos mensais são gerados por `gerar_mes.py`, que cruza a planilha de
> **prazo de entrega** com a de **inspeção de recebimento**:
> ```bash
> python gerar_mes.py --prazo PRAZO_MAIO.xlsx --qualidade Inspecao.xlsx --mes 2026-05
> ```
> O `.xlsx` gerado é o que sobe para a pasta `dados/`.

---

## Como os números do topo são calculados

Os KPIs de setor e de comprador são **ponderados por volume**, não a média simples
entre fornecedores. Ou seja:

- **Prazo do setor** = Σ entregas no prazo ÷ Σ entregas
- **Qualidade do setor** = (Σ entregas − Σ NCs) ÷ Σ entregas
- **Score geral** = 60% × prazo + 40% × qualidade

Isso faz o número bater com a fonte. O score **individual** de cada fornecedor
permanece intacto.

| Classe        | Score      |
|---------------|------------|
| A – EXCELENTE | ≥ 90%      |
| B – BOM       | 80 – 89%   |
| C – REGULAR   | 70 – 79%   |
| D – ATENÇÃO   | 60 – 69%   |
| E – CRÍTICO   | < 60%      |

---

## Páginas do painel

1. **🏠 Painel Geral** — saúde do setor, ranking completo, distribuição por classe.
2. **📈 Evolução** — tendência mês a mês do setor, de cada comprador e de cada
   fornecedor (maiores altas e quedas, trajetória individual). *Aparece a partir
   de 2 meses na pasta `dados/`.*
3. **📊 Painel Comprador** — carteira individual, prazo × qualidade, ranking.
4. **🏭 Painel Fornecedor** — ficha individual + variação vs. mês anterior.
5. **⚠️ Ação Prioritária** — fornecedores Classe D e E por comprador.
6. **🔑 Acessos / 📤 Atualizar Base** — histórico de acessos e instruções de upload.

---

## Histórico de acessos (log permanente)

O painel registra quem acessa (nome, data, hora). Por padrão o log fica só na
sessão e some no reinício. Para deixá-lo **permanente**, configure 1 token do
GitHub — passo a passo em **[`CONFIGURAR_LOG.md`](CONFIGURAR_LOG.md)** (2 minutos).

---

## Deploy (Streamlit Community Cloud)

1. Suba os arquivos num repositório GitHub.
2. Acesse **share.streamlit.io** e conecte o repositório (`app.py`).
3. A URL é gerada automaticamente — toda a equipe acessa sem instalar nada.
