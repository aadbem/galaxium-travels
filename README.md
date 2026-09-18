# 🚀 Galaxium Travels — Sistema de Reservas Interplanetárias

Aplicação full-stack para reservas de viagens espaciais, com frontend React e backend FastAPI com suporte duplo a REST e MCP.

## Stack

### Backend
- **FastAPI** — framework web Python
- **SQLAlchemy** — ORM
- **Pydantic v2** — validação de dados
- **FastMCP** — suporte ao protocolo MCP
- **SQLite** — banco de dados leve
- **Uvicorn** — servidor ASGI

### Frontend
- **React 19** — biblioteca UI
- **TypeScript** — tipagem estática
- **Vite** — build tool
- **Tailwind CSS** — estilização
- **Framer Motion** — animações
- **React Router** — roteamento
- **Axios** — cliente HTTP
- **React Hot Toast** — notificações

---

## Estrutura do Projeto

```
galaxium-travels/
├── booking_system_backend/     # FastAPI backend (Python)
│   ├── server.py              # Servidor principal REST + MCP
│   ├── services/              # Camada de lógica de negócio
│   ├── models.py              # Modelos SQLAlchemy
│   ├── schemas.py             # Schemas Pydantic
│   └── tests/                 # Suíte de testes
│
├── booking_system_frontend/    # React frontend (TypeScript)
│   ├── src/
│   │   ├── components/        # Componentes reutilizáveis
│   │   ├── pages/             # Páginas de rota
│   │   ├── services/          # Integração com a API
│   │   ├── hooks/             # Hooks customizados
│   │   └── types/             # Definições TypeScript
│   └── dist/                  # Build de produção
│
└── start.sh                   # Script de inicialização (macOS/Linux)
```

---

## Quick Start

### Pré-requisitos

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **Node.js 18+** — [Download](https://nodejs.org/)

### Inicialização com um comando (recomendado)

```bash
./start.sh
```

O script instala dependências automaticamente e sobe os dois servidores:
- ✅ Backend em `http://localhost:8080`
- ✅ Frontend em `http://localhost:5173`

### Inicialização manual

**Backend:**
```bash
cd booking_system_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

**Frontend** (em outro terminal):
```bash
cd booking_system_frontend
npm install
npm run dev
```

---

## Acesso

| URL | Descrição |
|---|---|
| `http://localhost:5173` | Frontend |
| `http://localhost:8080` | Backend REST |
| `http://localhost:8080/docs` | Swagger UI |
| `http://localhost:8080/mcp` | MCP endpoint |

---

## Funcionalidades

- **Busca de voos** — navegue e filtre voos interplanetários disponíveis
- **Classes de assento** — Econômica, Executiva e Galaxium com preços e disponibilidade por classe
- **Reservas** — escolha o voo, selecione a classe e confirme
- **Gerenciamento** — visualize e cancele reservas em "Minhas Reservas"
- **Identificação** — cadastro e login por nome + e-mail
- **Dual protocol** — mesma lógica de negócio via REST e MCP

---

## Classes de Assento

| Classe | Label | Multiplicador de preço | Assentos por voo |
|---|---|---|---|
| `economy` | Econômica | 1.0× | 10 |
| `executive` | Executiva | 1.5× | 5 |
| `galaxium` | Galaxium | 3.0× | 2 |

---

## Dados de Demo

O banco é recriado a cada inicialização do backend.

- **10 usuários**: Alice, Bob, Charlie, Diana, Eve, Frank, Grace, Heidi, Ivan, Judy
- **10 voos**: rotas entre Earth, Mars, Moon, Venus, Jupiter, Europa e Pluto
- **30 FlightSeatClass rows**: 3 classes por voo (economy, executive, galaxium)
- **20 reservas**: status variado (booked / cancelled / completed)

---

## Testes

```bash
cd booking_system_backend
source .venv/bin/activate
pytest
```

Para build de verificação do frontend:
```bash
cd booking_system_frontend
npm run build
npm run lint
```

---

## Documentação Detalhada

- [Backend — endpoints, MCP tools, error codes, modelo de dados](booking_system_backend/README.md)

---

## Troubleshooting

**Backend não sobe**
- Verifique Python 3.8+: `python3 --version`
- Porta 8080 ocupada: `lsof -i :8080`
- Dependências: `pip install -r requirements.txt`

**Frontend não sobe**
- Verifique Node.js 18+: `node --version`
- Porta 5173 ocupada: `lsof -i :5173`
- Reinstale: `rm -rf node_modules && npm install`

**Frontend não conecta ao backend**
- Confirme que o backend está em `http://localhost:8080`
- Verifique se o arquivo `.env` existe em `booking_system_frontend/` com `VITE_API_URL=http://localhost:8080`

---

*Explore o cosmos, uma reserva de cada vez.* 🚀✨
