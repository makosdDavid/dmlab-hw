import React, { createContext, useState, useContext, useEffect } from 'react';
import { fetchCities } from '../services/api';

// Create context
const AppContext = createContext();

// Provider component
export const AppProvider = ({ children }) => {
  const [selectedCity, setSelectedCity] = useState(null);
  const [cities, setCities] = useState([]);
  const [activeTab, setActiveTab] = useState('residential'); // 'residential', 'commercial', 'industrial', 'tourism', 'solar'
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
    endDate: new Date(),
  });
  const [viewMode, setViewMode] = useState('daily'); // 'daily', 'weekly', 'monthly'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Default cities to use as fallback
  const defaultCities = [
    { id: 3054643, name: 'Budapest', country: 'HU', lat: 47.4984, lon: 19.0404 },
    { id: 2643743, name: 'London', country: 'GB', lat: 51.5085, lon: -0.1257 },
    { id: 5128581, name: 'New York', country: 'US', lat: 40.7143, lon: -74.006 },
    { id: 1850147, name: 'Tokyo', country: 'JP', lat: 35.6895, lon: 139.6917 },
    { id: 6455259, name: 'Paris', country: 'FR', lat: 48.8534, lon: 2.3488 }
  ];

  // Fetch cities on component mount
  useEffect(() => {
    const loadCities = async () => {
      try {
        setLoading(true);
        const citiesData = await fetchCities();
        
        // If we got cities from the API, use them
        if (citiesData && Array.isArray(citiesData) && citiesData.length > 0) {
          setCities(citiesData);
          
          // Set default selected city (Budapest)
          const budapestCity = citiesData.find(city => city.name === 'Budapest');
          if (budapestCity) {
            setSelectedCity(budapestCity);
          } else {
            setSelectedCity(citiesData[0]);
          }
        } else {
          // If no cities from API, use fallback
          console.log('No cities received from API, using fallback cities');
          setCities(defaultCities);
          setSelectedCity(defaultCities[0]); // Default to Budapest
        }
      } catch (err) {
        // On error, use default cities
        console.error('Error loading cities:', err);
        setError('Failed to load cities from API. Using default cities.');
        setCities(defaultCities);
        setSelectedCity(defaultCities[0]); // Default to Budapest
      } finally {
        setLoading(false);
      }
    };

    loadCities();
  }, []);

  // Context value
  const value = {
    selectedCity,
    setSelectedCity,
    cities,
    activeTab,
    setActiveTab,
    dateRange,
    setDateRange,
    viewMode,
    setViewMode,
    loading,
    error,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Custom hook to use the context
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export default AppContext; 