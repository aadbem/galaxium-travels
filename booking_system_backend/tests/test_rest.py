import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import User, Flight, FlightSeatClass, Booking


def add_flight_with_classes(db, price=1000000, econ_seats=10, exec_seats=5, gal_seats=2):
    """Helper: insere um voo com as três FlightSeatClass."""
    f = Flight(
        origin="Earth",
        destination="Mars",
        departure_time="2099-01-01T09:00:00Z",
        arrival_time="2099-01-01T17:00:00Z",
        price=price,
        seats_available=econ_seats,
    )
    db.add(f)
    db.flush()
    db.add(FlightSeatClass(flight_id=f.flight_id, class_name="economy",   seats_available=econ_seats, price_multiplier=1.0))
    db.add(FlightSeatClass(flight_id=f.flight_id, class_name="executive", seats_available=exec_seats, price_multiplier=1.5))
    db.add(FlightSeatClass(flight_id=f.flight_id, class_name="galaxium",  seats_available=gal_seats,  price_multiplier=3.0))
    db.commit()
    return f


class TestFlightsEndpoint:
    """Testa o endpoint /flights."""

    def test_get_flights_empty(self, client, db_session):
        """Banco vazio retorna lista vazia."""
        response = client.get("/flights")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_flights_with_data(self, client, db_session):
        """Retorna voo com o campo seat_classes aninhado."""
        add_flight_with_classes(db_session)

        response = client.get("/flights")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["origin"] == "Earth"
        assert data[0]["destination"] == "Mars"
        assert len(data[0]["seat_classes"]) == 3

    def test_get_flights_seat_classes_fields(self, client, db_session):
        """Cada seat_class contém class_name, seats_available e price calculado."""
        add_flight_with_classes(db_session, price=1000)

        response = client.get("/flights")
        data = response.json()
        classes = {sc["class_name"]: sc for sc in data[0]["seat_classes"]}

        assert classes["economy"]["seats_available"] == 10
        assert classes["economy"]["price"] == 1000
        assert classes["executive"]["price"] == 1500
        assert classes["galaxium"]["price"] == 3000


class TestRegisterEndpoint:
    """Testa o endpoint /register."""

    def test_register_success(self, client, db_session, sample_user_data):
        """Registro bem-sucedido retorna os dados do usuário."""
        response = client.post("/register", json=sample_user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_user_data["name"]
        assert data["email"] == sample_user_data["email"]
        assert "user_id" in data

    def test_register_duplicate_email(self, client, db_session, sample_user_data):
        """E-mail duplicado retorna EMAIL_EXISTS."""
        client.post("/register", json=sample_user_data)
        response = client.post("/register", json=sample_user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "EMAIL_EXISTS"


class TestUserEndpoint:
    """Testa o endpoint /user."""

    def test_get_user_success(self, client, db_session, sample_user_data):
        """Busca de usuário existente retorna os dados."""
        client.post("/register", json=sample_user_data)

        response = client.get(
            "/user",
            params={"name": sample_user_data["name"], "email": sample_user_data["email"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_user_data["name"]

    def test_get_user_not_found(self, client, db_session):
        """Busca de usuário inexistente retorna USER_NOT_FOUND."""
        response = client.get(
            "/user",
            params={"name": "NonExistent", "email": "none@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "USER_NOT_FOUND"


class TestBookEndpoint:
    """Testa o endpoint /book."""

    def test_book_flight_success(self, client, db_session, sample_user_data):
        """Reserva bem-sucedida retorna booking com seat_class."""
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        flight = add_flight_with_classes(db_session)

        response = client.post("/book", json={
            "user_id": user_id,
            "name": sample_user_data["name"],
            "flight_id": flight.flight_id,
            "seat_class": "economy",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "booked"
        assert data["user_id"] == user_id
        assert data["seat_class"] == "economy"

    def test_book_flight_executive_class(self, client, db_session, sample_user_data):
        """Reserva na classe executiva retorna seat_class correto."""
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        flight = add_flight_with_classes(db_session)

        response = client.post("/book", json={
            "user_id": user_id,
            "name": sample_user_data["name"],
            "flight_id": flight.flight_id,
            "seat_class": "executive",
        })

        assert response.status_code == 200
        assert response.json()["seat_class"] == "executive"

    def test_book_flight_not_found(self, client, db_session, sample_user_data):
        """Reserva em voo inexistente retorna FLIGHT_NOT_FOUND."""
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        response = client.post("/book", json={
            "user_id": user_id,
            "name": sample_user_data["name"],
            "flight_id": 999,
            "seat_class": "economy",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "FLIGHT_NOT_FOUND"

    def test_book_flight_seat_class_not_found(self, client, db_session, sample_user_data):
        """Classe inválida retorna SEAT_CLASS_NOT_FOUND."""
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        flight = add_flight_with_classes(db_session)

        response = client.post("/book", json={
            "user_id": user_id,
            "name": sample_user_data["name"],
            "flight_id": flight.flight_id,
            "seat_class": "vip_gold",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "SEAT_CLASS_NOT_FOUND"

    def test_book_flight_no_seats(self, client, db_session, sample_user_data):
        """Classe lotada retorna NO_SEATS_AVAILABLE."""
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        flight = add_flight_with_classes(db_session, econ_seats=0)

        response = client.post("/book", json={
            "user_id": user_id,
            "name": sample_user_data["name"],
            "flight_id": flight.flight_id,
            "seat_class": "economy",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "NO_SEATS_AVAILABLE"


class TestBookingsEndpoint:
    """Testa o endpoint /bookings/{user_id}."""

    def test_get_bookings_success(self, client, db_session, sample_user_data):
        """Retorna reservas do usuário com seat_class."""
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        flight = add_flight_with_classes(db_session)

        db_session.add(Booking(
            user_id=user_id,
            flight_id=flight.flight_id,
            status="booked",
            booking_time="2099-01-01T10:00:00Z",
            seat_class="galaxium",
        ))
        db_session.commit()

        response = client.get(f"/bookings/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "booked"
        assert data[0]["seat_class"] == "galaxium"

    def test_get_bookings_empty(self, client, db_session):
        """Usuário sem reservas retorna lista vazia."""
        response = client.get("/bookings/999")
        assert response.status_code == 200
        assert response.json() == []


class TestCancelEndpoint:
    """Testa o endpoint /cancel/{booking_id}."""

    def test_cancel_booking_success(self, client, db_session, sample_user_data):
        """Cancelamento bem-sucedido retorna status cancelled."""
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        flight = add_flight_with_classes(db_session)

        db_session.add(Booking(
            user_id=user_id,
            flight_id=flight.flight_id,
            status="booked",
            booking_time="2099-01-01T10:00:00Z",
            seat_class="economy",
        ))
        db_session.commit()
        b = db_session.query(Booking).first()

        response = client.post(f"/cancel/{b.booking_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_cancel_booking_not_found(self, client, db_session):
        """Cancelamento de reserva inexistente retorna BOOKING_NOT_FOUND."""
        response = client.post("/cancel/999")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "BOOKING_NOT_FOUND"


class TestHealthEndpoint:
    """Testa o endpoint de health check."""

    def test_health_check(self, client, db_session):
        """Health check retorna OK."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}
