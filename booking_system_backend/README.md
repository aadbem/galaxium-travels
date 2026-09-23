# Galaxium Booking System — Backend

Sistema de reservas interplanetárias com suporte duplo de protocolo: **REST API** e **MCP (Model Context Protocol)**, servidos a partir de um único servidor FastAPI.

## Stack

| Componente | Tecnologia |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Validação | Pydantic v2 |
| Protocolo AI | FastMCP |
| Banco de dados | SQLite |
| Servidor ASGI | Uvicorn |
| Testes | pytest + httpx |

## Quick Start

```bash
cd booking_system_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

O servidor sobe na porta **8080**:
- REST endpoints em `/`
- Swagger UI em `/docs`
- MCP endpoint em `/mcp`
- Health check em `/`

---

## REST API

### Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/flights` | Lista todos os voos disponíveis (com classes de assento) |
| `POST` | `/book` | Reserva um assento |
| `GET` | `/bookings/{user_id}` | Lista reservas de um usuário |
| `POST` | `/cancel/{booking_id}` | Cancela uma reserva |
| `POST` | `/register` | Registra um novo usuário |
| `GET` | `/user?name=...&email=...` | Busca usuário por nome e e-mail |

### Exemplos com curl

```bash
# Health check
curl http://localhost:8080/

# Listar voos
curl http://localhost:8080/flights

# Registrar usuário
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# Buscar usuário
curl "http://localhost:8080/user?name=Alice&email=alice@example.com"

# Reservar voo (seat_class obrigatório: economy | executive | galaxium)
curl -X POST http://localhost:8080/book \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "name": "Alice", "flight_id": 1, "seat_class": "economy"}'

# Listar reservas do usuário
curl http://localhost:8080/bookings/1

# Cancelar reserva
curl -X POST http://localhost:8080/cancel/1
```

### Respostas de erro

Todas as rotas retornam HTTP 200 com o corpo abaixo em caso de erro de negócio:

```json
{
  "success": false,
  "error": "Mensagem curta",
  "error_code": "CODIGO_DO_ERRO",
  "details": "Descrição detalhada"
}
```

#### Códigos de erro

| Código | Situação |
|---|---|
| `FLIGHT_NOT_FOUND` | `flight_id` não existe |
| `SEAT_CLASS_NOT_FOUND` | `seat_class` inválido para o voo |
| `NO_SEATS_AVAILABLE` | Classe solicitada está lotada |
| `USER_NOT_FOUND` | `user_id` ou e-mail não encontrado |
| `NAME_MISMATCH` | Nome não corresponde ao `user_id` |
| `BOOKING_NOT_FOUND` | `booking_id` não existe |
| `ALREADY_CANCELLED` | Reserva já foi cancelada |
| `EMAIL_EXISTS` | E-mail já cadastrado |

---

## MCP Tools

Conecte em `http://localhost:8080/mcp` e use as ferramentas:

| Ferramenta | Parâmetros | Descrição |
|---|---|---|
| `list_flights` | — | Lista voos com classes de assento |
| `book_flight` | `user_id`, `name`, `flight_id`, `seat_class` | Reserva um assento |
| `get_bookings` | `user_id` | Lista reservas do usuário |
| `cancel_booking` | `booking_id` | Cancela uma reserva |
| `register_user` | `name`, `email` | Registra usuário |
| `get_user_id` | `name`, `email` | Busca usuário por nome e e-mail |

### Exemplos MCP

```
list_flights()
register_user(name="Alice", email="alice@example.com")
book_flight(user_id=1, name="Alice", flight_id=1, seat_class="economy")
get_bookings(user_id=1)
cancel_booking(booking_id=1)
```

> Erros de negócio são propagados como exceções no MCP (não como `ErrorResponse`).

---

## Classes de Assento

Cada voo possui três classes de assento. O preço por classe é calculado a partir do preço base do voo:

| Classe (`seat_class`) | Label | Multiplicador | Assentos iniciais |
|---|---|---|---|
| `economy` | Econômica | 1.0× | 10 |
| `executive` | Executiva | 1.5× | 5 |
| `galaxium` | Galaxium | 3.0× | 2 |

**Exemplo:** voo com preço base R$ 1.000.000
- Econômica: R$ 1.000.000
- Executiva: R$ 1.500.000
- Galaxium: R$ 3.000.000

A reserva decrementa `FlightSeatClass.seats_available` da classe escolhida. O cancelamento restaura o assento na mesma classe.

---

## Modelo de Dados

```
users
  user_id (PK), name, email (unique)

flights
  flight_id (PK), origin, destination,
  departure_time, arrival_time, price, seats_available (legado)

flight_seat_classes
  id (PK), flight_id (FK → flights), class_name,
  seats_available, price_multiplier

bookings
  booking_id (PK), user_id (FK → users),
  flight_id (FK → flights), status, booking_time, seat_class
```

> `Flight.seats_available` é um campo legado mantido por compatibilidade. A fonte de verdade para disponibilidade é `FlightSeatClass.seats_available`.

---

## Dados de Demo

O banco é recriado a cada inicialização do servidor via `seed()`.

**10 usuários:** Alice, Bob, Charlie, Diana, Eve, Frank, Grace, Heidi, Ivan, Judy

**10 voos:**

| Origem | Destino | Preço base |
|---|---|---|
| Earth | Mars | 1.000.000 |
| Earth | Moon | 500.000 |
| Mars | Earth | 950.000 |
| Venus | Earth | 1.200.000 |
| Jupiter | Europa | 2.000.000 |
| Earth | Venus | 1.100.000 |
| Moon | Mars | 800.000 |
| Mars | Jupiter | 2.500.000 |
| Europa | Earth | 3.000.000 |
| Earth | Pluto | 5.000.000 |

**30 FlightSeatClass rows** (3 por voo: economy, executive, galaxium)

**20 reservas demo** com `seat_class` aleatório e status variado (booked / cancelled / completed)

---

## Testes

```bash
# Rodar todos os testes
pytest

# Somente testes de serviço
pytest tests/test_services.py

# Somente testes REST
pytest tests/test_rest.py

# Filtrar por nome
pytest -k "seat_class"

# Com cobertura
pytest --cov=. --cov-report=term-missing
```

Os testes usam SQLite **em memória** — o arquivo `booking.db` não é afetado. O `conftest.py` recria o schema e injeta a sessão de teste em cada função.

---

## Estrutura do Projeto

```
booking_system_backend/
├── server.py          # Servidor principal — REST + MCP
├── services/
│   ├── booking.py     # Lógica de reservas
│   ├── flight.py      # Lógica de voos
│   └── user.py        # Lógica de usuários
├── models.py          # Modelos SQLAlchemy (User, Flight, FlightSeatClass, Booking)
├── schemas.py         # Schemas Pydantic (FlightOut, BookingOut, BookingRequest, …)
├── db.py              # Configuração do banco de dados
├── seed.py            # Dados de demo
├── tests/
│   ├── conftest.py    # Fixtures: banco em memória + TestClient
│   ├── test_services.py
│   └── test_rest.py
├── requirements.txt
├── Dockerfile
└── pytest.ini
```

---

## Docker

```bash
# Build
docker build -t galaxium-booking .

# Run
docker run -p 8080:127.0.0.1:8080 galaxium-booking
```

> Para ambientes IBM, use `registry.redhat.io/ubi9/python-311-minimal:latest` como imagem base em vez de `python:3.11-slim`.

---

## Arquitetura

```
┌─────────────────────────────────────┐
│           server.py                 │
│  ┌─────────────┐  ┌──────────────┐  │
│  │  FastAPI    │  │   FastMCP    │  │
│  │ (REST /docs)│  │  (/mcp)      │  │
│  └──────┬──────┘  └──────┬───────┘  │
│         └────────┬────────┘          │
│            services/                 │
│   booking.py · flight.py · user.py  │
│                  │                   │
│         models.py / schemas.py       │
│                  │                   │
│            SQLite (booking.db)       │
└─────────────────────────────────────┘
```

Padrão de camadas:
1. **Services** — lógica de negócio pura, retornam `ErrorResponse` em vez de exceções
2. **Server** — wrappers finos que expõem os services via REST e MCP
3. **Models** — definições ORM SQLAlchemy
4. **Schemas** — validação e serialização Pydantic v2
