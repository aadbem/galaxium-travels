# Documentação — Galaxium Travels

> Sistema de reservas de voos interplanetários com interface web e acesso via agente de IA (MCP).

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura Funcional](#2-arquitetura-funcional)
3. [Arquitetura Técnica](#3-arquitetura-técnica)
4. [Backend](#4-backend)
   - [Modelos de Dados](#41-modelos-de-dados)
   - [Schemas Pydantic](#42-schemas-pydantic)
   - [Camada de Serviços](#43-camada-de-serviços)
   - [API REST](#44-api-rest)
   - [Servidor MCP](#45-servidor-mcp)
   - [Banco de Dados](#46-banco-de-dados)
   - [Seed de Dados](#47-seed-de-dados)
5. [Frontend](#5-frontend)
   - [Estrutura de Páginas e Rotas](#51-estrutura-de-páginas-e-rotas)
   - [Componentes](#52-componentes)
   - [Serviço de API](#53-serviço-de-api)
   - [Estado Global do Usuário](#54-estado-global-do-usuário)
   - [Tipos TypeScript](#55-tipos-typescript)
   - [Utilitários de Formatação](#56-utilitários-de-formatação)
6. [Fluxos Funcionais](#6-fluxos-funcionais)
7. [Testes](#7-testes)
8. [Inicialização](#8-inicialização)
9. [Dependências](#9-dependências)

---

## 1. Visão Geral

O **Galaxium Travels** é uma aplicação fullstack para reserva de voos interplanetários ambientada no século XXII. A plataforma oferece dois modos de acesso:

- **Interface Web**: aplicação React que permite ao usuário buscar voos, filtrar por origem/destino/preço, efetuar reservas e gerenciar seus bilhetes.
- **Agente de IA (MCP)**: servidor FastMCP montado na mesma porta do backend, que expõe as operações de negócio como ferramentas consumíveis por agentes de linguagem (LLMs).

```
┌─────────────────────────────────────────────────────────────────┐
│                        Galaxium Travels                         │
│                                                                 │
│   ┌──────────────────────┐     ┌──────────────────────────┐    │
│   │   React Frontend     │     │      AI Agent / LLM      │    │
│   │   (porta :5173)      │     │   (via MCP protocol)     │    │
│   └──────────┬───────────┘     └───────────┬──────────────┘    │
│              │ HTTP/REST                    │ MCP (HTTP)        │
│              ▼                              ▼                   │
│   ┌──────────────────────────────────────────────────────┐     │
│   │          FastAPI + FastMCP  (porta :8080)            │     │
│   │                                                      │     │
│   │   REST endpoints   │   MCP tools (/mcp)              │     │
│   └──────────────────────────────┬───────────────────────┘     │
│                                  │ SQLAlchemy ORM              │
│                                  ▼                             │
│                       ┌──────────────────┐                     │
│                       │   SQLite (DB)    │                     │
│                       │  booking.db      │                     │
│                       └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Arquitetura Funcional

### Atores

| Ator | Descrição |
|------|-----------|
| **Usuário Web** | Pessoa que acessa a interface React para buscar e reservar voos |
| **Agente de IA** | LLM ou sistema automatizado que consome ferramentas MCP |

### Capacidades por ator

**Usuário Web:**
- Visualizar voos disponíveis com filtros por origem, destino e faixa de preço da classe econômica
- Registrar-se ou identificar-se com nome + e-mail
- Reservar um assento em um voo, escolhendo a classe (Econômica, Executiva, Galaxium)
- Visualizar reservas ativas e passadas
- Cancelar reservas ativas

**Agente de IA (MCP):**
- Listar voos disponíveis (`list_flights`)
- Reservar um voo em nome de um usuário (`book_flight`)
- Consultar reservas de um usuário (`get_bookings`)
- Cancelar uma reserva (`cancel_booking`)
- Registrar novo usuário (`register_user`)
- Obter dados de um usuário existente (`get_user_id`)

### Classes de assento

| Classe | Multiplicador de preço | Assentos por voo |
|--------|------------------------|------------------|
| `economy` | 1.0× | 10 |
| `executive` | 1.5× | 5 |
| `galaxium` | 3.0× | 2 |

O preço exibido por classe é calculado como `round(flight.price × price_multiplier)` — não é armazenado no banco.

---

## 3. Arquitetura Técnica

### Layout do repositório

```
galaxium-travels/
├── booking_system_backend/       # Python — FastAPI + FastMCP + SQLite
│   ├── server.py                 # Ponto de entrada; REST + MCP
│   ├── models.py                 # Modelos ORM (SQLAlchemy)
│   ├── schemas.py                # Schemas Pydantic de entrada/saída
│   ├── db.py                     # Engine, SessionLocal, get_db
│   ├── seed.py                   # Carga inicial de dados demo
│   ├── services/
│   │   ├── booking.py            # Lógica de reservas
│   │   ├── flight.py             # Lógica de voos
│   │   └── user.py               # Lógica de usuários
│   └── tests/
│       ├── conftest.py           # Fixtures pytest (SQLite em memória)
│       ├── test_services.py      # Testes unitários de serviços
│       └── test_rest.py          # Testes de integração REST
│
└── booking_system_frontend/      # TypeScript — React 19 + Vite + Tailwind
    └── src/
        ├── App.tsx               # Roteador e providers raiz
        ├── main.tsx              # Entry point React
        ├── pages/
        │   ├── Home.tsx          # Página inicial
        │   ├── Flights.tsx       # Listagem e busca de voos
        │   └── MyBookings.tsx    # Gerenciamento de reservas
        ├── components/
        │   ├── common/           # Button, Card, Input, Modal, Spinner, Starfield
        │   ├── flights/          # FlightCard
        │   ├── bookings/         # BookingCard, BookingModal
        │   ├── layout/           # Header, Footer, Layout
        │   └── user/             # UserIdentification
        ├── hooks/
        │   └── useUser.tsx       # Contexto global de usuário + localStorage
        ├── services/
        │   └── api.ts            # Axios + funções de acesso à API
        ├── types/
        │   └── index.ts          # Tipos TypeScript que espelham os schemas do backend
        └── utils/
            └── formatters.ts     # Funções de formatação de data, hora, moeda e duração
```

---

## 4. Backend

### 4.1 Modelos de Dados

Arquivo: [`models.py`](booking_system_backend/models.py)

| Tabela | Colunas principais |
|--------|--------------------|
| `users` | `user_id (PK)`, `name`, `email (unique)` |
| `flights` | `flight_id (PK)`, `origin`, `destination`, `departure_time`, `arrival_time`, `price`, `seats_available` |
| `flight_seat_classes` | `id (PK)`, `flight_id (FK)`, `class_name`, `seats_available`, `price_multiplier` |
| `bookings` | `booking_id (PK)`, `user_id (FK)`, `flight_id (FK)`, `status`, `booking_time`, `seat_class` |

> **Atenção:** a disponibilidade de assentos é controlada em `FlightSeatClass.seats_available`, não em `Flight.seats_available` (campo legado).

### 4.2 Schemas Pydantic

Arquivo: [`schemas.py`](booking_system_backend/schemas.py)

| Schema | Uso |
|--------|-----|
| `FlightOut` | Resposta de voo com lista de `FlightSeatClassOut` |
| `FlightSeatClassOut` | Classe de assento com preço computado |
| `BookingRequest` | Corpo do `POST /book` |
| `BookingOut` | Resposta de reserva |
| `UserRegistration` | Corpo do `POST /register` |
| `UserOut` | Resposta de usuário |
| `ErrorResponse` | Resposta padronizada de erro (`success: false`, `error`, `error_code`, `details`) |

### 4.3 Camada de Serviços

Todos os serviços retornam `ErrorResponse` em caso de falha — **nunca levantam exceções**.

#### `services/booking.py`

| Função | Descrição |
|--------|-----------|
| `book_flight(db, user_id, name, flight_id, seat_class)` | Valida voo, classe de assento, disponibilidade e usuário; decrementa `FlightSeatClass.seats_available`; cria `Booking` com `status="booked"` |
| `cancel_booking(db, booking_id)` | Valida existência e status; incrementa `FlightSeatClass.seats_available`; muda status para `"cancelled"` |
| `get_bookings(db, user_id)` | Retorna todas as reservas do usuário |

**Códigos de erro possíveis:**

| `error_code` | Situação |
|---|---|
| `FLIGHT_NOT_FOUND` | `flight_id` inexistente |
| `SEAT_CLASS_NOT_FOUND` | Classe inválida para o voo |
| `NO_SEATS_AVAILABLE` | Sem vagas na classe solicitada |
| `USER_NOT_FOUND` | `user_id` inexistente |
| `NAME_MISMATCH` | Nome não coincide com o `user_id` |
| `BOOKING_NOT_FOUND` | `booking_id` inexistente |
| `ALREADY_CANCELLED` | Reserva já cancelada |

#### `services/flight.py`

| Função | Descrição |
|--------|-----------|
| `list_flights(db)` | Retorna todos os voos com classes de assento e preço calculado (`round(flight.price × price_multiplier)`) |

#### `services/user.py`

| Função | Descrição |
|--------|-----------|
| `register_user(db, name, email)` | Cria usuário; retorna `EMAIL_EXISTS` se e-mail duplicado |
| `get_user(db, name, email)` | Busca usuário por nome + e-mail; retorna `USER_NOT_FOUND` se não encontrado |

### 4.4 API REST

Arquivo: [`server.py`](booking_system_backend/server.py) — porta **:8080**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Health check |
| `GET` | `/flights` | Lista todos os voos |
| `POST` | `/book` | Cria uma reserva |
| `GET` | `/bookings/{user_id}` | Reservas de um usuário |
| `POST` | `/cancel/{booking_id}` | Cancela uma reserva |
| `POST` | `/register` | Registra novo usuário |
| `GET` | `/user?name=&email=` | Recupera dados do usuário |

> Swagger UI disponível em `http://localhost:8080/docs`.

### 4.5 Servidor MCP

O servidor MCP é criado via `FastMCP("Galaxium Booking System")` e montado em `/mcp`. Deve ser instanciado **antes** do `FastAPI app` por dependência do lifespan.

| Ferramenta MCP | Mapeamento |
|----------------|-----------|
| `list_flights` | `flight.list_flights` |
| `book_flight` | `booking.book_flight` |
| `get_bookings` | `booking.get_bookings` |
| `cancel_booking` | `booking.cancel_booking` |
| `register_user` | `user.register_user` |
| `get_user_id` | `user.get_user` |

As ferramentas MCP abrem sessão de banco diretamente via `SessionLocal()` com `try/finally` — sem `Depends` do FastAPI.

### 4.6 Banco de Dados

Arquivo: [`db.py`](booking_system_backend/db.py)

- Engine SQLite em `./booking.db` com `check_same_thread=False`
- `init_db()` cria tabelas via `Base.metadata.create_all`
- `get_db()` é generator FastAPI Depends com `try/finally`

### 4.7 Seed de Dados

Arquivo: [`seed.py`](booking_system_backend/seed.py)

Executado automaticamente no startup via lifespan. **Apaga e reconstrói todos os dados** a cada inicialização:

- 10 usuários demo
- 10 voos interplanetários (2099), com preços de $500k a $5M
- 3 classes de assento por voo (economy/executive/galaxium)
- 20 reservas aleatórias com status variados

---

## 5. Frontend

### 5.1 Estrutura de Páginas e Rotas

Arquivo: [`App.tsx`](booking_system_frontend/src/App.tsx)

| Rota | Componente | Descrição |
|------|------------|-----------|
| `/` | `Home` | Página inicial com boas-vindas |
| `/flights` | `Flights` | Busca e reserva de voos |
| `/bookings` | `MyBookings` | Reservas do usuário logado |
| `*` | `Home` | Fallback |

Toda a árvore de componentes é envolta por `UserProvider` (contexto de usuário) e `Layout` (cabeçalho, rodapé, fundo de estrelas).

### 5.2 Componentes

#### Páginas

**`Flights.tsx`**
- Carrega voos via `getFlights()` com retry exponencial (até 3 tentativas)
- Filtros reativos: origem, destino, preço mínimo/máximo (baseado na classe econômica)
- Ao clicar em "Reservar": se não autenticado, abre `UserIdentification`; se autenticado, abre `BookingModal`
- Recarrega voos após reserva bem-sucedida para atualizar disponibilidade

**`MyBookings.tsx`**
- Redireciona para `/flights` se não houver usuário logado
- Carrega reservas e voos em paralelo com `Promise.all`
- Separa reservas em "ativas" (`status === 'booked'`) e "passadas"
- Cancela reservas com modal de confirmação

#### Componentes de Layout

| Componente | Função |
|------------|--------|
| `Layout.tsx` | Container principal com `Header`, `Footer` e `Starfield` |
| `Header.tsx` | Navegação com links e estado do usuário |
| `Footer.tsx` | Rodapé |
| `Starfield.tsx` | Fundo animado com estrelas (decorativo) |

#### Componentes Comuns

| Componente | Função |
|------------|--------|
| `Button.tsx` | Botão reutilizável com variantes `primary`, `secondary`, `danger` |
| `Card.tsx` | Card com estilo `glass-card` |
| `Input.tsx` | Campo de entrada com estilo `input-field` |
| `Modal.tsx` | Modal genérico com backdrop |
| `LoadingSpinner.tsx` | Spinner de carregamento com texto opcional |

#### Componentes de Domínio

| Componente | Função |
|------------|--------|
| `FlightCard.tsx` | Exibe voo com origem, destino, horários, duração e classes de assento com preços |
| `BookingModal.tsx` | Modal de confirmação de reserva; exibe detalhes do voo e permite escolher classe |
| `BookingCard.tsx` | Exibe reserva com status, voo associado e opção de cancelamento |
| `UserIdentification.tsx` | Modal de login/registro com nome + e-mail; usa `registerUser` e `getUserByCredentials` |

### 5.3 Serviço de API

Arquivo: [`services/api.ts`](booking_system_frontend/src/services/api.ts)

- Instância Axios com `baseURL` configurável via `VITE_API_URL` (padrão: `http://localhost:8080`)
- Interceptor de resposta normaliza erros de rede para `ErrorResponse`
- `isErrorResponse(response)`: narrowing de tipo — verifica `response.success === false`

| Função exportada | Endpoint chamado |
|-----------------|-----------------|
| `getFlights()` | `GET /flights` |
| `registerUser(data)` | `POST /register` |
| `getUserByCredentials(name, email)` | `GET /user` |
| `bookFlight(data)` | `POST /book` |
| `getUserBookings(userId)` | `GET /bookings/{userId}` |
| `cancelBooking(bookingId)` | `POST /cancel/{bookingId}` |
| `healthCheck()` | `GET /` |

### 5.4 Estado Global do Usuário

Arquivo: [`hooks/useUser.tsx`](booking_system_frontend/src/hooks/useUser.tsx)

- `UserProvider`: Context Provider com estado `user: User | null`
- Persiste e carrega usuário de `localStorage` na chave `galaxium_user`
- `setUser(user)`: atualiza estado e localStorage
- `logout()`: limpa estado e localStorage
- `useUser()`: hook de acesso; lança erro se usado fora do `UserProvider`

### 5.5 Tipos TypeScript

Arquivo: [`types/index.ts`](booking_system_frontend/src/types/index.ts)

Tipos que espelham exatamente os schemas do backend:

| Tipo | Uso |
|------|-----|
| `SeatClass` | `'economy' \| 'executive' \| 'galaxium'` |
| `Flight` | Voo com array de `FlightSeatClass` |
| `FlightSeatClass` | Classe de assento com preço computado |
| `Booking` | Reserva com status tipado |
| `User` | Dados do usuário |
| `BookingRequest` | Payload de reserva |
| `UserRegistration` | Payload de registro |
| `ErrorResponse` | Resposta de erro com `success: false` |
| `BookingWithFlight` | Reserva enriquecida com dados do voo (uso interno de UI) |
| `FlightFilters` | Filtros de busca de voos |

### 5.6 Utilitários de Formatação

Arquivo: [`utils/formatters.ts`](booking_system_frontend/src/utils/formatters.ts)

Todas as formatações de data, hora e moeda devem passar por estas funções (não usar `new Date()` ou `Intl` diretamente em componentes):

| Função | Descrição |
|--------|-----------|
| `formatDate(dateString, formatString?)` | Formata data ISO com `date-fns` |
| `formatDateShort(dateString)` | Formato curto: `Jan 1, 2099` |
| `formatTime(dateString)` | Somente hora: `09:00` |
| `formatCurrency(amount)` | Moeda USD sem casas decimais |
| `formatNumber(num)` | Número com separador de milhar |
| `getRelativeTime(dateString)` | Tempo relativo: `2 hours ago` |
| `calculateDuration(departure, arrival)` | Duração do voo: `8h 30m` |

---

## 6. Fluxos Funcionais

### Reservar um voo (interface web)

```
Usuário acessa /flights
  → Frontend carrega GET /flights
  → Usuário filtra e clica em "Reservar"
    → [sem sessão] Abre UserIdentification Modal
        → POST /register  OU  GET /user
        → Salva User em localStorage
        → Abre BookingModal
    → [com sessão] Abre BookingModal diretamente
  → Usuário confirma reserva e classe
  → Frontend: POST /book { user_id, name, flight_id, seat_class }
  → Backend: decrementa FlightSeatClass.seats_available, cria Booking
  → Frontend: recarrega GET /flights (atualiza disponibilidade)
```

### Cancelar uma reserva

```
Usuário acessa /bookings
  → [sem sessão] Redireciona para /flights
  → Frontend carrega Promise.all([GET /bookings/{id}, GET /flights])
  → Usuário clica em "Cancelar"
  → Modal de confirmação
  → Frontend: POST /cancel/{booking_id}
  → Backend: restaura FlightSeatClass.seats_available, status = "cancelled"
  → Frontend: recarrega dados
```

### Reserva via agente de IA

```
Agente conecta ao MCP em http://localhost:8080/mcp
  → Chama list_flights() para listar voos disponíveis
  → Chama get_user_id(name, email) para obter user_id
    → Se não existir: chama register_user(name, email)
  → Chama book_flight(user_id, name, flight_id, seat_class)
  → Em caso de ErrorResponse: lança Exception com details ou error
```

---

## 7. Testes

### Backend

Diretório: `booking_system_backend/tests/`

- **`conftest.py`**: fixture `db_session` com SQLite em memória; suprime o `seed()` de produção; injeta `sys.path` para imports planos
- **`test_services.py`**: testes unitários dos serviços (`book_flight`, `cancel_booking`, `register_user`, etc.) usando `make_flight(db)` e `make_user(db)`
- **`test_rest.py`**: testes de integração dos endpoints REST usando `TestClient` do FastAPI e `add_flight_with_classes(db)`

Executar testes:
```bash
cd galaxium-travels/booking_system_backend
source .venv/bin/activate
pytest                              # todos os testes
pytest tests/test_services.py       # apenas serviços
pytest -k "test_book_flight"        # por palavra-chave
```

---

## 8. Inicialização

### Iniciar ambos os serviços (recomendado)

```bash
cd galaxium-travels
./start.sh
```

### Backend isolado

```bash
cd galaxium-travels/booking_system_backend
source .venv/bin/activate
python server.py
# Disponível em http://localhost:8080
# Swagger UI: http://localhost:8080/docs
# MCP: http://localhost:8080/mcp
```

### Frontend isolado

```bash
cd galaxium-travels/booking_system_frontend
npm run dev
# Disponível em http://localhost:5173
```

### Build de produção (frontend)

```bash
cd galaxium-travels/booking_system_frontend
npm run build    # tsc -b && vite build
```

### Variável de ambiente do frontend

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `VITE_API_URL` | `http://localhost:8080` | URL base do backend |

---

## 9. Dependências

### Backend (Python)

| Pacote | Função |
|--------|--------|
| `fastapi` | Framework REST |
| `fastmcp` | Servidor MCP sobre FastAPI |
| `uvicorn` | Servidor ASGI |
| `sqlalchemy` | ORM e abstração de banco |
| `pydantic[email]` | Validação de schemas e e-mails |
| `python-dotenv` | Variáveis de ambiente |
| `pytest` / `pytest-asyncio` / `pytest-cov` | Testes |
| `httpx` | Client HTTP para testes |

### Frontend (Node.js / TypeScript)

| Pacote | Função |
|--------|--------|
| `react` 19 | Framework UI |
| `react-router-dom` 7 | Roteamento SPA |
| `axios` | Client HTTP |
| `date-fns` | Manipulação de datas |
| `framer-motion` | Animações |
| `lucide-react` | Ícones SVG |
| `react-hot-toast` | Notificações toast |
| `clsx` | Composição de classes CSS |
| `tailwindcss` | Framework CSS utilitário |
| `vite` | Bundler e dev server |
| `typescript` | Tipagem estática |
