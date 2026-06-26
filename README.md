# Selgron — Score de Fornecedores v1.0

Dashboard web para monitoramento de performance de fornecedores.  
Desenvolvido para o Departamento de Suprimentos da Selgron Industrial.

---

## Como rodar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Colocar a planilha na mesma pasta
Renomeie sua planilha para um destes nomes (o app detecta automaticamente):
- `Score_Fornecedores_Selgron_v8.xlsx`
- `Score_Fornecedores_Selgron_v7.xlsx`

Se a planilha não for encontrada, o app carrega **dados de demonstração**.

### 3. Iniciar o app
```bash
streamlit run app.py
```

Acesse: **http://localhost:8501**

---

## Senha de acesso
```
Acesso2026
```

---

## Estrutura esperada da planilha (aba: SCORE GERAL)

| Coluna            | Descrição                        |
|-------------------|----------------------------------|
| FORNECEDOR        | Nome do fornecedor               |
| COMPRADOR         | Nome do comprador                |
| SCORE_GERAL       | Score 0 a 1 (ou 0 a 100)        |
| SCORE_PRAZO       | Score de prazo de entrega        |
| SCORE_QUALIDADE   | Score de qualidade               |
| TOTAL_ENTREGAS    | Qtd total de entregas            |
| ENTREGA_NO_PRAZO  | Qtd entregas no prazo            |
| TOTAL_NCS         | Qtd de não conformidades         |

---

## Metodologia de Score
- **60%** — Performance de Prazo de Entrega
- **40%** — Performance de Qualidade (Inspeção de Recebimento)

| Classe       | Score      |
|--------------|------------|
| A – EXCELENTE| ≥ 90%      |
| B – BOM      | 80 – 89%   |
| C – REGULAR  | 70 – 79%   |
| D – ATENÇÃO  | 60 – 69%   |
| E – CRÍTICO  | < 60%      |

---

## Páginas do dashboard

1. **Dashboard Geral** — KPIs + ranking completo + distribuição por classe
2. **Por Comprador** — filtro por comprador, carteira individual, scatter prazo×qualidade
3. **Ficha do Fornecedor** — painel individual otimizado para impressão/PDF (enviar ao fornecedor)
4. **Ação Prioritária** — fornecedores Classe D e E por comprador
5. **Atualizar Base** — importar planilha dos meses seguintes (jul, ago...)

---

## Deploy na nuvem (opcional)

Para hospedar e compartilhar com toda a equipe:

```bash
# Streamlit Community Cloud (gratuito)
# 1. Suba os arquivos num repositório GitHub privado
# 2. Acesse share.streamlit.io
# 3. Conecte o repositório — URL gerada automaticamente
```

Todos os compradores e o diretor acessam pela URL sem instalar nada.
