import React, { useState } from 'react';
import { useAppContext } from '../../context/AppContext';
import { triggerDataProcessing, checkApiHealth } from '../../services/api';
import './Header.css';

const Header = () => {
  const { selectedCity, setSelectedCity, cities } = useAppContext();
  const [refreshing, setRefreshing] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState(null);
  const [showStatus, setShowStatus] = useState(false);

  const handleCityChange = (event) => {
    const cityId = parseInt(event.target.value);
    const city = cities.find(c => c.id === cityId);
    setSelectedCity(city);
  };

  const handleRefreshData = async () => {
    if (refreshing) return;

    try {
      setRefreshing(true);
      setRefreshStatus('Checking API health...');
      setShowStatus(true);
      
      // First check if API is healthy
      try {
        await checkApiHealth();
        
        // If health check passes, try to trigger data processing
        setRefreshStatus('Refreshing data...');
        await triggerDataProcessing();
        
        setRefreshStatus('Data refreshed successfully!');
        
        // Hide success message after 3 seconds
        setTimeout(() => {
          setShowStatus(false);
        }, 3000);
      } catch (error) {
        console.error('API error:', error);
        setRefreshStatus('API not responding. Using cached data.');
      }
    } catch (error) {
      console.error('Error refreshing data:', error);
      setRefreshStatus('Failed to refresh data. Using cached data.');
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <header className="header">
      <div className="logo">
        <h1>Energy Consumption Forecast</h1>
      </div>
      <div className="controls">
        <div className="city-selector">
          <label htmlFor="city-select">City:</label>
          <select 
            id="city-select" 
            value={selectedCity?.id || ''} 
            onChange={handleCityChange}
            disabled={cities.length === 0}
          >
            {cities.length === 0 && <option value="">Loading cities...</option>}
            {cities.map(city => (
              <option key={city.id} value={city.id}>
                {city.name}, {city.country}
              </option>
            ))}
          </select>
          <span className="note">(More cities coming soon)</span>
        </div>
        <div className="refresh-container">
          <button 
            className={`refresh-button ${refreshing ? 'refreshing' : ''}`} 
            onClick={handleRefreshData}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh Data'}
          </button>
          {showStatus && refreshStatus && (
            <div className="refresh-status">
              {refreshStatus}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header; 