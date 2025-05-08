import React from 'react';
import './DateRangeSelector.css';

const DateRangeSelector = ({ dateRange, setDateRange, viewMode, setViewMode }) => {
  // Handle null or undefined dateRange gracefully
  const safeRange = dateRange || {
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // Default to 7 days ago
    endDate: new Date() // Default to today
  };
  
  const handleStartDateChange = (e) => {
    const newStartDate = new Date(e.target.value);
    setDateRange(prev => ({
      ...prev,
      startDate: newStartDate
    }));
  };

  const handleEndDateChange = (e) => {
    const newEndDate = new Date(e.target.value);
    setDateRange(prev => ({
      ...prev,
      endDate: newEndDate
    }));
  };

  const handleViewModeChange = (e) => {
    setViewMode(e.target.value);
  };

  // Preset date range options
  const setPresetRange = (days) => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);
    
    setDateRange({
      startDate,
      endDate
    });
  };

  // Format date for input with safety check
  const formatDateForInput = (date) => {
    if (!date) {
      return new Date().toISOString().split('T')[0]; // Default to today if date is undefined
    }
    return date.toISOString().split('T')[0];
  };

  return (
    <div className="date-range-selector">
      <div className="date-inputs">
        <div className="date-field">
          <label htmlFor="start-date">From:</label>
          <input
            type="date"
            id="start-date"
            value={formatDateForInput(safeRange.startDate)}
            onChange={handleStartDateChange}
            max={formatDateForInput(safeRange.endDate)}
          />
        </div>
        
        <div className="date-field">
          <label htmlFor="end-date">To:</label>
          <input
            type="date"
            id="end-date"
            value={formatDateForInput(safeRange.endDate)}
            onChange={handleEndDateChange}
            min={formatDateForInput(safeRange.startDate)}
            max={formatDateForInput(new Date())}
          />
        </div>
      </div>
      
      <div className="date-presets">
        <button onClick={() => setPresetRange(7)}>Last 7 days</button>
        <button onClick={() => setPresetRange(30)}>Last 30 days</button>
        <button onClick={() => setPresetRange(90)}>Last 90 days</button>
      </div>
      
      <div className="view-mode-selector">
        <label>View:</label>
        <div className="view-mode-options">
          <label>
            <input
              type="radio"
              name="viewMode"
              value="daily"
              checked={viewMode === 'daily'}
              onChange={handleViewModeChange}
            />
            Daily
          </label>
          
          <label>
            <input
              type="radio"
              name="viewMode"
              value="weekly"
              checked={viewMode === 'weekly'}
              onChange={handleViewModeChange}
            />
            Weekly
          </label>
          
          <label>
            <input
              type="radio"
              name="viewMode"
              value="monthly"
              checked={viewMode === 'monthly'}
              onChange={handleViewModeChange}
            />
            Monthly
          </label>
        </div>
      </div>
    </div>
  );
};

export default DateRangeSelector; 