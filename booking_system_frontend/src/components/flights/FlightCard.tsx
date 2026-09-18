import type { Flight, FlightSeatClass } from '../../types';
import { Card, Button } from '../common';
import { Plane, Clock, DollarSign } from 'lucide-react';
import { formatCurrency, formatDate, formatTime, calculateDuration } from '../../utils/formatters';
import { motion } from 'framer-motion';

interface FlightCardProps {
  flight: Flight;
  onBook: (flight: Flight) => void;
}

const CLASS_LABELS: Record<string, string> = {
  economy: 'Econômica',
  executive: 'Executiva',
  galaxium: 'Galaxium',
};

export const FlightCard = ({ flight, onBook }: FlightCardProps) => {
  const hasSeatClasses = flight.seat_classes && flight.seat_classes.length > 0;

  const isSoldOut = hasSeatClasses
    ? flight.seat_classes.every(sc => sc.seats_available === 0)
    : flight.seats_available === 0;

  const displayPrice = hasSeatClasses
    ? Math.min(...flight.seat_classes.map(sc => sc.price))
    : flight.price;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="h-full flex flex-col">
        {/* Route Header */}
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
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
        </div>

        {/* Flight Details */}
        <div className="space-y-3 mb-6 flex-1">
          {/* Departure & Arrival */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-star-white/60 mb-1">Departure</p>
              <p className="text-sm font-medium text-star-white">
                {formatDate(flight.departure_time, 'MMM dd, yyyy')}
              </p>
              <p className="text-lg font-bold text-cosmic-purple">
                {formatTime(flight.departure_time)}
              </p>
            </div>
            <div>
              <p className="text-xs text-star-white/60 mb-1">Arrival</p>
              <p className="text-sm font-medium text-star-white">
                {formatDate(flight.arrival_time, 'MMM dd, yyyy')}
              </p>
              <p className="text-lg font-bold text-cosmic-purple">
                {formatTime(flight.arrival_time)}
              </p>
            </div>
          </div>

          {/* Duration */}
          <div className="flex items-center gap-2 text-star-white/70">
            <Clock size={16} />
            <span className="text-sm">
              Duration: {calculateDuration(flight.departure_time, flight.arrival_time)}
            </span>
          </div>

          {/* Price */}
          <div className="flex items-center gap-2">
            <DollarSign size={16} className="text-alien-green" />
            <span className="text-xs text-star-white/60 mr-1">from</span>
            <span className="text-2xl font-bold text-star-white">
              {formatCurrency(displayPrice)}
            </span>
          </div>

          {/* Per-Class Availability */}
          {hasSeatClasses && (
            <div className="space-y-1 pt-1 border-t border-white/10">
              {flight.seat_classes.map((sc: FlightSeatClass) => {
                const isClassSoldOut = sc.seats_available === 0;
                const isClassLow = !isClassSoldOut && sc.seats_available <= 2;
                return (
                  <div key={sc.class_name} className="flex items-center justify-between text-xs">
                    <span className="text-star-white/70 w-20">
                      {CLASS_LABELS[sc.class_name] ?? sc.class_name}
                    </span>
                    <span className="text-star-white/50">{formatCurrency(sc.price)}</span>
                    <span
                      className={
                        isClassSoldOut
                          ? 'text-red-400 font-semibold'
                          : isClassLow
                          ? 'text-solar-orange font-semibold'
                          : 'text-star-white/60'
                      }
                    >
                      {isClassSoldOut ? 'Esgotado' : `${sc.seats_available} lugares`}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Book Button */}
        <Button
          onClick={() => onBook(flight)}
          disabled={isSoldOut}
          className="w-full"
        >
          {isSoldOut ? 'Sold Out' : 'Book Now'}
        </Button>
      </Card>
    </motion.div>
  );
};

// Made with Bob
