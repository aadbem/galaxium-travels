import { useState } from 'react';
import type { Flight, SeatClass, FlightSeatClass } from '../../types';
import { Modal, Button } from '../common';
import { Plane, Calendar, Clock, DollarSign } from 'lucide-react';
import { formatCurrency, formatDate, calculateDuration } from '../../utils/formatters';
import { bookFlight, isErrorResponse } from '../../services/api';
import { useUser } from '../../hooks/useUser';
import toast from 'react-hot-toast';

interface BookingModalProps {
  isOpen: boolean;
  onClose: () => void;
  flight: Flight | null;
  onSuccess: () => void;
}

const CLASS_LABELS: Record<SeatClass, string> = {
  economy: 'Econômica',
  executive: 'Executiva',
  galaxium: 'Galaxium',
};

export const BookingModal = ({ isOpen, onClose, flight, onSuccess }: BookingModalProps) => {
  const { user } = useUser();
  const [isLoading, setIsLoading] = useState(false);
  const [selectedClass, setSelectedClass] = useState<SeatClass>('economy');

  if (!flight) return null;

  const selectedSeatClass: FlightSeatClass | undefined = flight.seat_classes?.find(
    (sc) => sc.class_name === selectedClass
  );

  const isSoldOut = selectedSeatClass?.seats_available === 0;

  const handleConfirmBooking = async () => {
    if (!user) {
      toast.error('Please sign in to book a flight');
      return;
    }

    setIsLoading(true);

    try {
      const result = await bookFlight({
        user_id: user.user_id,
        name: user.name,
        flight_id: flight.flight_id,
        seat_class: selectedClass,
      });

      if (isErrorResponse(result)) {
        toast.error(result.details || result.error);
        return;
      }

      toast.success('Flight booked successfully!');
      onSuccess();
      onClose();
    } catch (error: any) {
      toast.error(error.details || error.error || 'Failed to book flight');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Confirm Your Booking"
      size="md"
    >
      <div className="space-y-6">
        {/* Flight Summary */}
        <div className="glass-card p-4 bg-white/5">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-cosmic-gradient">
              <Plane className="text-white" size={24} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-star-white">
                {flight.origin} → {flight.destination}
              </h3>
              <p className="text-sm text-star-white/60">
                Flight #{flight.flight_id}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {/* Departure */}
            <div className="flex items-start gap-3">
              <Calendar className="text-cosmic-purple mt-1" size={20} />
              <div>
                <p className="text-xs text-star-white/60">Departure</p>
                <p className="text-star-white font-medium">
                  {formatDate(flight.departure_time)}
                </p>
              </div>
            </div>

            {/* Arrival */}
            <div className="flex items-start gap-3">
              <Calendar className="text-cosmic-purple mt-1" size={20} />
              <div>
                <p className="text-xs text-star-white/60">Arrival</p>
                <p className="text-star-white font-medium">
                  {formatDate(flight.arrival_time)}
                </p>
              </div>
            </div>

            {/* Duration */}
            <div className="flex items-start gap-3">
              <Clock className="text-cosmic-purple mt-1" size={20} />
              <div>
                <p className="text-xs text-star-white/60">Duration</p>
                <p className="text-star-white font-medium">
                  {calculateDuration(flight.departure_time, flight.arrival_time)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Class Selector */}
        {flight.seat_classes && flight.seat_classes.length > 0 && (
          <div>
            <p className="text-sm font-semibold text-star-white mb-3">
              Escolha sua Classe
            </p>
            <div className="grid grid-cols-3 gap-3">
              {flight.seat_classes.map((sc) => {
                const isSelected = selectedClass === sc.class_name;
                const soldOut = sc.seats_available === 0;
                const lowSeats = sc.seats_available > 0 && sc.seats_available <= 2;

                return (
                  <button
                    key={sc.class_name}
                    type="button"
                    disabled={soldOut}
                    onClick={() => setSelectedClass(sc.class_name)}
                    className={[
                      'glass-card p-3 flex flex-col items-center gap-1 rounded-xl border transition-all text-left',
                      isSelected
                        ? 'border-cosmic-purple bg-cosmic-purple/20'
                        : 'border-white/10 bg-white/5 hover:bg-white/10',
                      soldOut ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer',
                    ].join(' ')}
                  >
                    <span className={`text-sm font-bold ${isSelected ? 'text-cosmic-purple' : 'text-star-white'}`}>
                      {CLASS_LABELS[sc.class_name]}
                    </span>
                    <span className="text-xs font-semibold text-star-white">
                      {formatCurrency(sc.price)}
                    </span>
                    {soldOut ? (
                      <span className="text-xs font-medium text-red-400">Esgotado</span>
                    ) : (
                      <span className={`text-xs ${lowSeats ? 'text-solar-orange font-semibold' : 'text-star-white/60'}`}>
                        {sc.seats_available} {sc.seats_available === 1 ? 'lugar' : 'lugares'}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Passenger Info */}
        {user && (
          <div className="glass-card p-4 bg-white/5">
            <h4 className="text-sm font-semibold text-star-white mb-2">
              Passenger Information
            </h4>
            <p className="text-star-white">{user.name}</p>
            <p className="text-star-white/60 text-sm">{user.email}</p>
          </div>
        )}

        {/* Price */}
        <div className="flex items-center justify-between p-4 glass-card bg-cosmic-gradient">
          <div className="flex items-center gap-2">
            <DollarSign className="text-white" size={24} />
            <span className="text-white font-semibold">Total Price</span>
          </div>
          <span className="text-2xl font-bold text-white">
            {formatCurrency(selectedSeatClass?.price ?? flight.price)}
          </span>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={isLoading}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirmBooking}
            isLoading={isLoading}
            disabled={isSoldOut}
            className="flex-1"
          >
            Confirm Booking
          </Button>
        </div>

        <p className="text-xs text-star-white/60 text-center">
          By confirming, you agree to our terms and conditions
        </p>
      </div>
    </Modal>
  );
};

// Made with Bob
