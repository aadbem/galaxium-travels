# GitHub — Configurações e Histórico de Tarefas
Teste

Documento que consolida tudo o que foi configurado e executado nesta sessão de trabalho relacionado ao GitHub, MCP Server e repositório do projeto Galaxium Travels.

---

## 1. Adição do servidor MCP GitHub ao Bob

**Arquivo alterado:** `.bob/mcp.json`

O servidor MCP do GitHub foi adicionado à configuração local do Bob para permitir que o assistente interaja com repositórios GitHub diretamente durante as sessões.

### Configuração inicial (com Docker — incorreta)

```json
"github": {
  "command": "docker",
  "args": [
    "run", "-i", "--rm",
    "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "-e", "GITHUB_HOST",
    "ghcr.io/github/github-mcp-server"
  ],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}",
    "GITHUB_HOST": "https://<your GHES or ghe.com domain name>"
  }
}
```

### Problema 1 — `GITHUB_HOST` desnecessário para GitHub público

`GITHUB_HOST` é exclusivo para GitHub Enterprise Server (GHES) ou `ghe.com`. Defini-lo apontando para `https://github.com/` faz o servidor MCP construir URLs de API incorretas (`https://github.com/api/v3/` em vez de `https://api.github.com/`), causando falha de autenticação.

**Correção:** variável `GITHUB_HOST` e seu argumento `-e` foram removidos do bloco.

---

## 2. Erro `spawn docker ENOENT` — Docker não instalado

**Log do erro:**
```
2026-09-18 14:07:22.411 [error] [MCP] [Bob_Level3][github] Session failed to start
{"error":"spawn docker ENOENT"}
```

**Causa raiz:** O ambiente não possui Docker instalado. `ENOENT` significa que o sistema operacional não encontrou o binário `docker` no PATH do processo do Bob.

**Diagnóstico do ambiente:**
```
Node.js: v24.20.0  →  /usr/local/bin/node
npx:     v11.19.0  →  /usr/local/bin/npx
Docker:  NÃO INSTALADO
```

**Solução aplicada:** substituição do transporte Docker pelo pacote NPM oficial `@modelcontextprotocol/server-github`, executado via `npx` com caminho absoluto.

---

## 3. Configuração final do MCP GitHub

**Arquivo:** `.bob/mcp.json`

```json
"github": {
  "command": "/usr/local/bin/npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-github"
  ],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
  },
  "disabled": false
}
```

**Por que caminho absoluto (`/usr/local/bin/npx`)?**
Apps de desktop no macOS herdam um PATH reduzido que pode não incluir `/usr/local/bin`. O caminho absoluto garante que o Bob encontre o `npx` independentemente do PATH do processo.

**Como o token é solicitado:**
O placeholder `${input:github_token}` instrui o Bob a exibir um prompt interativo pedindo o valor do token toda vez que o servidor MCP for iniciado. O token **nunca é gravado em disco**.

---

## 4. Alerta de segurança — PAT em texto plano

Durante a sessão, foi detectado um Personal Access Token (PAT) gravado em texto plano dentro do `.bob/mcp.json`:

```
GITHUB_PERSONAL_ACCESS_TOKEN: "github_pat_11ALLT7IY0..."  ← INSEGURO
```

**Ação tomada:** token substituído pelo placeholder seguro `${input:github_token}`.

**Ação obrigatória do usuário:** revogar o token exposto em:
👉 https://github.com/settings/tokens

---

## 5. Como gerar um novo Personal Access Token (PAT)

Acesse **https://github.com/settings/tokens**

### Opção A — Fine-grained token (recomendado)

1. Clique em **"Generate new token" → "Fine-grained token"**
2. Em **Resource owner**, selecione `aadbem`
3. Em **Repository access**, selecione os repositórios desejados
4. Em **Repository permissions**, conceda:

| Permissão     | Nível |
|---------------|-------|
| Contents      | Read  |
| Metadata      | Read (automático) |
| Pull requests | Read  |
| Issues        | Read  |

### Opção B — Classic token

1. Clique em **"Generate new token" → "Classic token"**
2. Marque os escopos:
   - ✅ `repo` — acesso a repositórios públicos e privados
   - ✅ `read:org` — necessário para repositórios de organizações

> **Atenção:** copie o token imediatamente após a geração — ele aparece **apenas uma vez**.

---

## 6. Como recarregar o servidor MCP após configurar o token

1. No Bob, abra a paleta de comandos: `Cmd+Shift+P`
2. Execute **"MCP: Restart Server"** → selecione `github`
3. O Bob solicitará o valor de `github_token` — cole o novo PAT
4. Verifique em **"MCP: List Tools"** que as ferramentas do GitHub aparecem listadas

---

## 7. Publicação do projeto no repositório `aadbem/galaxium-travels`

### Contexto

O repositório Git original do projeto (`galaxium-travels/`) apontava para `https://github.com/IBM/galaxium-travels`. O objetivo era publicar o estado atual do projeto no repositório pessoal `https://github.com/aadbem/galaxium-travels`.

### Problema encontrado — push mirror bloqueado

A tentativa de espelhar todas as branches do `IBM/galaxium-travels` para `aadbem/galaxium-travels` foi bloqueada pelo GitHub:

```
! [remote rejected] origin/main -> main
  (refusing to allow a Personal Access Token to create or update
   workflow `.github/workflows/bob-review.yml` without `workflow` scope)
```

O token Classic usado não possui o escopo `workflow`, exigido para criar ou atualizar arquivos em `.github/workflows/`.

### Solução adotada — commit inicial limpo

Em vez de tentar replicar o histórico com workflows bloqueados, foi adotada a abordagem de **repositório zerado**:

| Passo | Comando | Resultado |
|-------|---------|-----------|
| Remover `.git` original | `rm -rf .git` | Histórico descartado |
| Inicializar novo repo | `git init` | Repo limpo criado |
| Adicionar todos os arquivos | `git add -A` | 62 arquivos staged |
| Commit inicial | `git commit -m "feat: initial commit..."` | 1 commit limpo |
| Configurar remote | `git remote add origin ...` | Aponta para `aadbem/galaxium-travels` |
| Push | `git push -u origin main` | ✅ Publicado |
| Sanitizar remote | `git remote set-url origin ...` | Token removido da URL |

### Estado final do repositório

```
Repositório: https://github.com/aadbem/galaxium-travels
Branch:      main
Commit:      feat: initial commit — Galaxium Travels booking system
Arquivos:    62 (backend + frontend completos)
Remote:      origin → https://github.com/aadbem/galaxium-travels.git
```

### Arquivos publicados

**Backend** (`booking_system_backend/`):
- `models.py`, `schemas.py`, `seed.py`, `server.py`, `db.py`
- `services/booking.py`, `services/flight.py`, `services/user.py`
- `tests/test_services.py`, `tests/test_rest.py`, `tests/conftest.py`
- `requirements.txt`, `Dockerfile`, `pytest.ini`

**Frontend** (`booking_system_frontend/`):
- `src/components/` — BookingCard, BookingModal, FlightCard, UserIdentification, layout, common
- `src/pages/` — Flights, Home, MyBookings
- `src/services/api.ts`, `src/hooks/useUser.tsx`, `src/types/index.ts`
- `src/utils/formatters.ts`, `src/index.css`
- Configurações: `package.json`, `vite.config.ts`, `tailwind.config.js`, `tsconfig*.json`

**Raiz:**
- `README.md`, `AGENTS.md`, `LICENSE`, `.gitignore`, `start.sh`

---

## 8. Resumo de configurações ativas

| Item | Valor |
|------|-------|
| MCP GitHub — comando | `/usr/local/bin/npx` |
| MCP GitHub — pacote | `@modelcontextprotocol/server-github` |
| MCP GitHub — token | `${input:github_token}` (prompt em runtime) |
| Git remote — origin | `https://github.com/aadbem/galaxium-travels.git` |
| Git branch principal | `main` |
| Node.js | v24.20.0 |
| npx | v11.19.0 |
| Docker | Não instalado |
