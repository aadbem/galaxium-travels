from sqlalchemy.orm import Session
from models import Flight, FlightSeatClass
from schemas import FlightOut, FlightSeatClassOut


def list_flights(db: Session) -> list[FlightOut]:
    """List all available flights."""
    flights = db.query(Flight).all()
    result = []
    for flight in flights:
        seat_class_rows = db.query(FlightSeatClass).filter(
            FlightSeatClass.flight_id == flight.flight_id
        ).all()
        seat_classes = [
            FlightSeatClassOut(
                id=row.id,
                flight_id=row.flight_id,
                class_name=row.class_name,
                seats_available=row.seats_available,
                price=round(flight.price * row.price_multiplier)
            )
            for row in seat_class_rows
        ]
        flight_out = FlightOut.model_validate(flight)
        flight_out.seat_classes = seat_classes
        result.append(flight_out)
    return result
