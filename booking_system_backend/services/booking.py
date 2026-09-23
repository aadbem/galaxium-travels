from sqlalchemy.orm import Session
from datetime import datetime
from models import User, Flight, Booking, FlightSeatClass
from schemas import BookingOut, ErrorResponse


def book_flight(db: Session, user_id: int, name: str, flight_id: int, seat_class: str) -> BookingOut | ErrorResponse:
    """Book a seat on a specific flight for a user."""
    # Check flight exists
    flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
    if not flight:
        return ErrorResponse(
            error="Flight not found",
            error_code="FLIGHT_NOT_FOUND",
            details=f"The specified flight_id {flight_id} does not exist in our system. Please check the flight_id or use list_flights to see available flights."
        )

    # Check seat class exists for this flight
    seat_class_row = db.query(FlightSeatClass).filter(
        FlightSeatClass.flight_id == flight_id,
        FlightSeatClass.class_name == seat_class
    ).first()
    if not seat_class_row:
        return ErrorResponse(
            error="Seat class not found",
            error_code="SEAT_CLASS_NOT_FOUND",
            details=f"The seat class '{seat_class}' is not available for flight {flight_id}. Valid classes are: economy, executive, galaxium."
        )

    # Check seats available for the requested class
    if seat_class_row.seats_available < 1:
        return ErrorResponse(
            error="No seats available",
            error_code="NO_SEATS_AVAILABLE",
            details=f"The '{seat_class}' class on this flight is fully booked. Please choose a different class or try another flight."
        )

    # Check user exists and name matches
    user = db.query(User).filter(User.user_id == user_id, User.name == name).first()
    if not user:
        existing_user = db.query(User).filter(User.user_id == user_id).first()
        if existing_user:
            return ErrorResponse(
                error="Name mismatch",
                error_code="NAME_MISMATCH",
                details=f"User ID {user_id} exists but the name '{name}' does not match the registered name '{existing_user.name}'. Please verify the user's name or use the correct name for this user ID."
            )
        else:
            return ErrorResponse(
                error="User not found",
                error_code="USER_NOT_FOUND",
                details=f"User with ID {user_id} is not registered in our system. The user might need to register first, or you may need to check if the user_id is correct."
            )

    # Create booking
    seat_class_row.seats_available -= 1
    new_booking = Booking(
        user_id=user_id,
        flight_id=flight_id,
        seat_class=seat_class,
        status="booked",
        booking_time=datetime.utcnow().isoformat()
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return BookingOut.model_validate(new_booking)


def cancel_booking(db: Session, booking_id: int) -> BookingOut | ErrorResponse:
    """Cancel an existing booking by its booking_id."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        return ErrorResponse(
            error="Booking not found",
            error_code="BOOKING_NOT_FOUND",
            details=f"Booking with ID {booking_id} not found. The booking may have been deleted or the booking_id may be incorrect. Please verify the booking_id or check if the booking exists."
        )

    if booking.status == "cancelled":
        return ErrorResponse(
            error="Booking already cancelled",
            error_code="ALREADY_CANCELLED",
            details=f"Booking {booking_id} is already cancelled and cannot be cancelled again. The booking status is currently '{booking.status}'. If you need to make changes, please contact support."
        )

    # Restore seat to the specific class
    seat_class_row = db.query(FlightSeatClass).filter(
        FlightSeatClass.flight_id == booking.flight_id,
        FlightSeatClass.class_name == booking.seat_class
    ).first()
    if seat_class_row:
        seat_class_row.seats_available += 1

    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return BookingOut.model_validate(booking)


def get_bookings(db: Session, user_id: int) -> list[BookingOut]:
    """Retrieve all bookings for a specific user."""
    bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
    return [BookingOut.model_validate(b) for b in bookings]
