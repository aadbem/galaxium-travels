import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import User, Flight, FlightSeatClass, Booking
from schemas import ErrorResponse
from services import flight, user, booking


def make_flight(db, seats=5, price=1000000):
    """Helper: cria um voo com as três classes de assento."""
    f = Flight(
        origin="Earth",
        destination="Mars",
        departure_time="2099-01-01T09:00:00Z",
        arrival_time="2099-01-01T17:00:00Z",
        price=price,
        seats_available=seats,
    )
    db.add(f)
    db.flush()
    db.add(FlightSeatClass(flight_id=f.flight_id, class_name="economy",   seats_available=10, price_multiplier=1.0))
    db.add(FlightSeatClass(flight_id=f.flight_id, class_name="executive", seats_available=5,  price_multiplier=1.5))
    db.add(FlightSeatClass(flight_id=f.flight_id, class_name="galaxium",  seats_available=2,  price_multiplier=3.0))
    db.commit()
    return f


def make_user(db, name="Test User", email="test@example.com"):
    """Helper: cria um usuário."""
    u = User(name=name, email=email)
    db.add(u)
    db.commit()
    return u


class TestFlightService:
    """Testa funções do serviço de voos."""

    def test_list_flights_empty(self, db_session):
        """Lista de voos vazia quando banco está vazio."""
        result = flight.list_flights(db_session)
        assert result == []

    def test_list_flights_with_data(self, db_session):
        """Lista de voos retorna o voo com seat_classes aninhados."""
        make_flight(db_session)

        result = flight.list_flights(db_session)
        assert len(result) == 1
        assert result[0].origin == "Earth"
        assert result[0].destination == "Mars"
        assert len(result[0].seat_classes) == 3

    def test_list_flights_seat_classes_fields(self, db_session):
        """Cada seat_class contém os campos esperados."""
        make_flight(db_session, price=1000)

        result = flight.list_flights(db_session)
        classes = {sc.class_name: sc for sc in result[0].seat_classes}

        assert classes["economy"].seats_available == 10
        assert classes["economy"].price == 1000        # 1000 * 1.0
        assert classes["executive"].price == 1500      # 1000 * 1.5
        assert classes["galaxium"].price == 3000       # 1000 * 3.0


class TestUserService:
    """Testa funções do serviço de usuários."""

    def test_register_user_success(self, db_session):
        """Registro de usuário bem-sucedido."""
        result = user.register_user(db_session, "Test User", "test@example.com")
        assert result.name == "Test User"
        assert result.email == "test@example.com"
        assert result.user_id > 0

    def test_register_user_duplicate_email(self, db_session):
        """Registro com e-mail duplicado retorna EMAIL_EXISTS."""
        user.register_user(db_session, "User 1", "test@example.com")
        result = user.register_user(db_session, "User 2", "test@example.com")

        assert isinstance(result, ErrorResponse)
        assert result.error_code == "EMAIL_EXISTS"

    def test_get_user_success(self, db_session):
        """Busca de usuário existente retorna os dados corretos."""
        db_session.add(User(name="Test User", email="test@example.com"))
        db_session.commit()

        result = user.get_user(db_session, "Test User", "test@example.com")
        assert result.name == "Test User"
        assert result.email == "test@example.com"

    def test_get_user_not_found(self, db_session):
        """Busca de usuário inexistente retorna USER_NOT_FOUND."""
        result = user.get_user(db_session, "NonExistent", "none@example.com")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "USER_NOT_FOUND"


class TestBookingService:
    """Testa funções do serviço de reservas."""

    def test_book_flight_success(self, db_session):
        """Reserva bem-sucedida decrementa FlightSeatClass.seats_available."""
        u = make_user(db_session)
        f = make_flight(db_session)

        seat_class_row = db_session.query(FlightSeatClass).filter_by(
            flight_id=f.flight_id, class_name="economy"
        ).first()
        seats_before = seat_class_row.seats_available

        result = booking.book_flight(db_session, u.user_id, u.name, f.flight_id, "economy")

        assert result.status == "booked"
        assert result.user_id == u.user_id
        assert result.flight_id == f.flight_id
        assert result.seat_class == "economy"

        db_session.refresh(seat_class_row)
        assert seat_class_row.seats_available == seats_before - 1

    def test_book_flight_executive_class(self, db_session):
        """Reserva na classe executiva decrementa o contador correto."""
        u = make_user(db_session)
        f = make_flight(db_session)

        result = booking.book_flight(db_session, u.user_id, u.name, f.flight_id, "executive")

        assert result.seat_class == "executive"
        exec_row = db_session.query(FlightSeatClass).filter_by(
            flight_id=f.flight_id, class_name="executive"
        ).first()
        assert exec_row.seats_available == 4  # 5 - 1

        # Econômica não é afetada
        econ_row = db_session.query(FlightSeatClass).filter_by(
            flight_id=f.flight_id, class_name="economy"
        ).first()
        assert econ_row.seats_available == 10

    def test_book_flight_not_found(self, db_session):
        """Reserva em voo inexistente retorna FLIGHT_NOT_FOUND."""
        u = make_user(db_session)

        result = booking.book_flight(db_session, u.user_id, u.name, 999, "economy")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "FLIGHT_NOT_FOUND"

    def test_book_flight_seat_class_not_found(self, db_session):
        """Reserva com classe inválida retorna SEAT_CLASS_NOT_FOUND."""
        u = make_user(db_session)
        f = make_flight(db_session)

        result = booking.book_flight(db_session, u.user_id, u.name, f.flight_id, "vip_gold")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "SEAT_CLASS_NOT_FOUND"

    def test_book_flight_no_seats(self, db_session):
        """Reserva quando classe está lotada retorna NO_SEATS_AVAILABLE."""
        u = make_user(db_session)
        f = Flight(
            origin="Earth", destination="Mars",
            departure_time="2099-01-01T09:00:00Z",
            arrival_time="2099-01-01T17:00:00Z",
            price=1000000, seats_available=0,
        )
        db_session.add(f)
        db_session.flush()
        db_session.add(FlightSeatClass(
            flight_id=f.flight_id, class_name="economy",
            seats_available=0, price_multiplier=1.0
        ))
        db_session.commit()

        result = booking.book_flight(db_session, u.user_id, u.name, f.flight_id, "economy")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "NO_SEATS_AVAILABLE"

    def test_book_flight_user_not_found(self, db_session):
        """Reserva com usuário inexistente retorna USER_NOT_FOUND."""
        f = make_flight(db_session)

        result = booking.book_flight(db_session, 999, "Fake User", f.flight_id, "economy")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "USER_NOT_FOUND"

    def test_book_flight_name_mismatch(self, db_session):
        """Reserva com nome errado para o user_id retorna NAME_MISMATCH."""
        u = make_user(db_session, name="Real Name")
        f = make_flight(db_session)

        result = booking.book_flight(db_session, u.user_id, "Wrong Name", f.flight_id, "economy")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "NAME_MISMATCH"

    def test_cancel_booking_success(self, db_session):
        """Cancelamento restaura FlightSeatClass.seats_available da classe correta."""
        u = make_user(db_session)
        f = make_flight(db_session)

        exec_row = db_session.query(FlightSeatClass).filter_by(
            flight_id=f.flight_id, class_name="executive"
        ).first()
        seats_before = exec_row.seats_available

        b = Booking(
            user_id=u.user_id, flight_id=f.flight_id,
            status="booked", booking_time="2099-01-01T10:00:00Z",
            seat_class="executive",
        )
        db_session.add(b)
        db_session.commit()

        result = booking.cancel_booking(db_session, b.booking_id)
        assert result.status == "cancelled"

        db_session.refresh(exec_row)
        assert exec_row.seats_available == seats_before + 1

        # Econômica não é afetada
        econ_row = db_session.query(FlightSeatClass).filter_by(
            flight_id=f.flight_id, class_name="economy"
        ).first()
        assert econ_row.seats_available == 10

    def test_cancel_booking_not_found(self, db_session):
        """Cancelamento de reserva inexistente retorna BOOKING_NOT_FOUND."""
        result = booking.cancel_booking(db_session, 999)
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "BOOKING_NOT_FOUND"

    def test_cancel_booking_already_cancelled(self, db_session):
        """Cancelamento de reserva já cancelada retorna ALREADY_CANCELLED."""
        u = make_user(db_session)
        f = make_flight(db_session)

        b = Booking(
            user_id=u.user_id, flight_id=f.flight_id,
            status="cancelled", booking_time="2099-01-01T10:00:00Z",
            seat_class="economy",
        )
        db_session.add(b)
        db_session.commit()

        result = booking.cancel_booking(db_session, b.booking_id)
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "ALREADY_CANCELLED"

    def test_get_bookings_success(self, db_session):
        """Retorna as reservas do usuário com seat_class correto."""
        u = make_user(db_session)
        f = make_flight(db_session)

        b = Booking(
            user_id=u.user_id, flight_id=f.flight_id,
            status="booked", booking_time="2099-01-01T10:00:00Z",
            seat_class="galaxium",
        )
        db_session.add(b)
        db_session.commit()

        result = booking.get_bookings(db_session, u.user_id)
        assert len(result) == 1
        assert result[0].status == "booked"
        assert result[0].seat_class == "galaxium"

    def test_get_bookings_empty(self, db_session):
        """Retorna lista vazia quando usuário não tem reservas."""
        result = booking.get_bookings(db_session, 999)
        assert result == []
