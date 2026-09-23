import { useState, useEffect, useMemo } from 'react';
import type { Flight, FlightFilters } from '../types';
import { LoadingSpinner } from '../components/common';
import { FlightCard } from '../components/flights/FlightCard';
import { UserIdentification } from '../components/user/UserIdentification';
import { BookingModal } from '../components/bookings/BookingModal';
import { getFlights } from '../services/api';
import { useUser } from '../hooks/useUser';
import { Filter } from 'lucide-react';
import toast from 'react-hot-toast';
import { motion } from 'framer-motion';

const EMPTY_FILTERS: FlightFilters = {
  origin: '',
  destination: '',
  minPrice: undefined,
  maxPrice: undefined,
};

/** Retorna o preço da classe econômica de um voo, ou Infinity se não existir. */
const economyPrice = (flight: Flight): number =>
  flight.seat_classes.find((c) => c.class_name === 'economy')?.price ?? Infinity;

export const Flights = () => {
  const { user } = useUser();
  const [flights, setFlights] = useState<Flight[]>([]);
  const [filteredFlights, setFilteredFlights] = useState<Flight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState<FlightFilters>(EMPTY_FILTERS);
  const [selectedFlight, setSelectedFlight] = useState<Flight | null>(null);
  const [showUserModal, setShowUserModal] = useState(false);
  const [showBookingModal, setShowBookingModal] = useState(false);

  /** Listas únicas de origens e destinos derivadas dos voos carregados. */
  const origins = useMemo(
    () => [...new Set(flights.map((f) => f.origin))].sort(),
    [flights],
  );
  const destinations = useMemo(
    () => [...new Set(flights.map((f) => f.destination))].sort(),
    [flights],
  );

  // Fetch flights on mount
  useEffect(() => {
    loadFlights();
  }, []);

  // Aplica filtros sempre que flights ou filters mudam
  useEffect(() => {
    let result = flights;

    if (filters.origin) {
      result = result.filter((f) => f.origin === filters.origin);
    }
    if (filters.destination) {
      result = result.filter((f) => f.destination === filters.destination);
    }
    if (filters.minPrice !== undefined) {
      result = result.filter((f) => economyPrice(f) >= filters.minPrice!);
    }
    if (filters.maxPrice !== undefined) {
      result = result.filter((f) => economyPrice(f) <= filters.maxPrice!);
    }

    setFilteredFlights(result);
  }, [filters, flights]);

  /** Atualiza um campo individual dos filtros. */
  const handleFilterChange = <K extends keyof FlightFilters>(
    key: K,
    value: FlightFilters[K],
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const hasActiveFilters =
    !!filters.origin ||
    !!filters.destination ||
    filters.minPrice !== undefined ||
    filters.maxPrice !== undefined;

  const loadFlights = async (retryCount = 0) => {
    const MAX_RETRIES = 3;
    const RETRY_DELAY = 1000; // 1 second

    setIsLoading(true);
    try {
      const data = await getFlights();
      setFlights(data);
      setFilteredFlights(data);
    } catch (error: any) {
      if (retryCount < MAX_RETRIES) {
        toast.error(`Failed to load flights. Retrying... (${retryCount + 1}/${MAX_RETRIES})`);
        setTimeout(() => {
          loadFlights(retryCount + 1);
        }, RETRY_DELAY * (retryCount + 1)); // Exponential backoff
      } else {
        toast.error('Failed to load flights after multiple attempts');
        console.error(error);
        setIsLoading(false);
      }
      return;
    }
    setIsLoading(false);
  };

  const handleBookFlight = (flight: Flight) => {
    setSelectedFlight(flight);
    
    if (!user) {
      // Show user identification modal first
      setShowUserModal(true);
    } else {
      // Show booking confirmation modal
      setShowBookingModal(true);
    }
  };

  const handleUserIdentified = () => {
    // After user signs in, show booking modal
    setShowBookingModal(true);
  };

  const handleBookingSuccess = () => {
    // Reload flights to get updated seat availability
    loadFlights();
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl md:text-5xl font-bold text-star-white mb-4">
          Available <span className="bg-cosmic-gradient bg-clip-text text-transparent">Flights</span>
        </h1>
        <p className="text-star-white/70 text-lg">
          Choose your destination and embark on an interplanetary adventure
        </p>
      </motion.div>

      {/* Filtros */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-6"
      >
        <div className="flex flex-col md:flex-row gap-4 items-end">
          {/* Origem */}
          <div className="flex-1 flex flex-col gap-1">
            <label className="text-star-white/60 text-xs uppercase tracking-wider">Origem</label>
            <select
              value={filters.origin ?? ''}
              onChange={(e) => handleFilterChange('origin', e.target.value || undefined)}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-star-white focus:outline-none focus:ring-2 focus:ring-cosmic-purple"
            >
              <option value="">Todas as origens</option>
              {origins.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </div>

          {/* Destino */}
          <div className="flex-1 flex flex-col gap-1">
            <label className="text-star-white/60 text-xs uppercase tracking-wider">Destino</label>
            <select
              value={filters.destination ?? ''}
              onChange={(e) => handleFilterChange('destination', e.target.value || undefined)}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-star-white focus:outline-none focus:ring-2 focus:ring-cosmic-purple"
            >
              <option value="">Todos os destinos</option>
              {destinations.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          {/* Faixa de preço — classe Econômica */}
          <div className="flex flex-col gap-1">
            <label className="text-star-white/60 text-xs uppercase tracking-wider">Preço Econômica (min)</label>
            <input
              type="number"
              min={0}
              placeholder="Mín."
              value={filters.minPrice ?? ''}
              onChange={(e) =>
                handleFilterChange('minPrice', e.target.value ? Number(e.target.value) : undefined)
              }
              className="w-32 px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-star-white placeholder-star-white/50 focus:outline-none focus:ring-2 focus:ring-cosmic-purple"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-star-white/60 text-xs uppercase tracking-wider">Preço Econômica (max)</label>
            <input
              type="number"
              min={0}
              placeholder="Máx."
              value={filters.maxPrice ?? ''}
              onChange={(e) =>
                handleFilterChange('maxPrice', e.target.value ? Number(e.target.value) : undefined)
              }
              className="w-32 px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-star-white placeholder-star-white/50 focus:outline-none focus:ring-2 focus:ring-cosmic-purple"
            />
          </div>

          {/* Indicador + Limpar */}
          <div className="flex items-center gap-3 text-star-white/70 pb-1">
            <Filter size={20} />
            <span className="text-sm whitespace-nowrap">
              {filteredFlights.length} de {flights.length} voos
            </span>
            {hasActiveFilters && (
              <button
                onClick={() => setFilters(EMPTY_FILTERS)}
                className="text-xs text-nebula-pink hover:text-nebula-pink/80 underline whitespace-nowrap"
              >
                Limpar filtros
              </button>
            )}
          </div>
        </div>
      </motion.div>

      {/* Flights Grid */}
      {isLoading ? (
        <LoadingSpinner size="lg" text="Loading flights..." />
      ) : filteredFlights.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <p className="text-star-white/70 text-lg">
            {hasActiveFilters ? 'Nenhum voo encontrado com os filtros aplicados' : 'Nenhum voo disponível'}
          </p>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {filteredFlights.map((flight) => (
            <FlightCard
              key={flight.flight_id}
              flight={flight}
              onBook={handleBookFlight}
            />
          ))}
        </motion.div>
      )}

      {/* User Identification Modal */}
      <UserIdentification
        isOpen={showUserModal}
        onClose={() => setShowUserModal(false)}
        onSuccess={handleUserIdentified}
      />

      {/* Booking Confirmation Modal */}
      <BookingModal
        isOpen={showBookingModal}
        onClose={() => setShowBookingModal(false)}
        flight={selectedFlight}
        onSuccess={handleBookingSuccess}
      />
    </div>
  );
};

// Made with Bob
