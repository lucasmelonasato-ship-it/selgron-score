# Como deixar o log de acessos permanente (2 minutos)

Por padrão, o histórico de quem acessa o painel fica guardado **só na sessão** —
ou seja, some quando o Streamlit Cloud reinicia o app. Para que o log **nunca
mais se perca**, o app grava cada acesso como uma linha no arquivo
`dados/_acessos.csv` do próprio repositório GitHub.

Para isso funcionar, o app precisa de **1 token do GitHub** com permissão de
escrita, guardado nos *Secrets* do Streamlit. Siga os passos abaixo.

---

## Passo 1 — Criar o token no GitHub

1. Acesse: **https://github.com/settings/tokens?type=beta**
   (GitHub → Settings → Developer settings → **Fine-grained tokens**)
2. Clique em **Generate new token**.
3. Preencha:
   - **Token name:** `selgron-score-log`
   - **Expiration:** 1 ano (ou "No expiration")
   - **Repository access:** *Only select repositories* → escolha
     **`selgron-score`**
   - **Permissions → Repository permissions → Contents:** mude para
     **Read and write**
4. Clique em **Generate token** e **copie o token** (começa com `github_pat_...`).
   Ele só aparece uma vez.

---

## Passo 2 — Colar o token nos Secrets do Streamlit

1. Abra o painel do app em **https://share.streamlit.io** → seu app →
   menu **⋮** → **Settings** → aba **Secrets**.
2. Cole o bloco abaixo (troque apenas o valor do token e, se preciso, o repositório):

```toml
github_token  = "github_pat_COLE_AQUI_O_SEU_TOKEN"
github_repo   = "lucasmelonasato-ship-it/selgron-score"
github_branch = "main"
```

3. Clique em **Save**. O app reinicia sozinho.

---

## Passo 3 — Conferir

1. Entre no painel normalmente (com seu nome + senha).
2. Vá em **🔑 Acessos** (menu do topo).
3. No rodapé do histórico deve aparecer:
   > ✅ Log conectado ao **GitHub** — registros salvos permanentemente no repositório.

Se aparecer **"⚠️ Modo temporário"**, o token não foi lido — revise o Passo 2
(nome exato das chaves, token válido, permissão *Contents: Read and write*).

---

## Observações

- **Cada acesso vira um commit** em `dados/_acessos.csv`. Como o Streamlit Cloud
  observa o branch publicado, esse commit provoca um *reboot* rápido do app
  (poucos segundos, sem perder nada). Para uma equipe pequena isso é irrelevante.
- **Quer evitar até o reboot?** Crie um branch separado só para o log
  (ex: `logs`) no GitHub e troque `github_branch = "logs"` nos Secrets. O log
  passa a ser gravado nesse branch, sem mexer no app publicado.
- **Alternativa:** o app também aceita Google Sheets (chave
  `gcp_service_account` + `log_sheet_id` nos Secrets). Use só se preferir planilha
  em vez de GitHub — não precisa dos dois.
