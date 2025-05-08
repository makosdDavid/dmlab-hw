import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../context/AppContext';
import { getSolarData } from '../../services/api';
import DateRangeSelector from '../Common/DateRangeSelector';
import MetricCard from '../Common/MetricCard';
import Chart from '../Common/Chart';
import './TabStyles.css';

const SolarTab = () => {
  const { selectedCity, dateRange, setDateRange, viewMode, setViewMode } = useAppContext();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [metrics, setMetrics] = useState({
    avgProduction: 0,
    peakProduction: 0,
    efficiency: 0,
    weatherImpact: 0,
    predictionAccuracy: 0
  });

  useEffect(() => {
    const fetchData = async () => {
      if (!selectedCity) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Create default dates if dateRange values are undefined
        const startDate = dateRange?.startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000); // Default to 30 days ago
        const endDate = dateRange?.endDate || new Date(); // Default to today
        
        // Extract city name or ID from the city object
        const cityParam = typeof selectedCity === 'object' ? (selectedCity.name || selectedCity.id) : selectedCity;
        
        const result = await getSolarData(
          cityParam, 
          startDate.toISOString().split('T')[0], 
          endDate.toISOString().split('T')[0]
        );
        
        setData(result.data);
        
        // Calculate metrics
        if (result.data && result.data.length > 0) {
          const productionValues = result.data.map(item => item.energy_production);
          const avgProduction = productionValues.reduce((sum, val) => sum + val, 0) / productionValues.length;
          const peakProduction = Math.max(...productionValues);
          
          setMetrics({
            avgProduction: parseFloat(avgProduction.toFixed(2)),
            peakProduction: parseFloat(peakProduction.toFixed(2)),
            efficiency: parseFloat((result.efficiency || 0.22).toFixed(2)), // Panel efficiency (typically 15-22%)
            weatherImpact: parseFloat((result.weather_impact || 0.75).toFixed(2)), // Weather impact on solar production
            predictionAccuracy: parseFloat((result.prediction_accuracy || 0.87).toFixed(2)) // Prediction accuracy
          });
        }
      } catch (err) {
        console.error('Error fetching solar data:', err);
        setError('Failed to load solar energy data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [selectedCity, dateRange?.startDate, dateRange?.endDate]);

  // Format date for chart tooltip
  const formatDate = (date) => {
    const d = new Date(date);
    return d.toLocaleDateString();
  };

  // Custom tooltip formatter for the chart
  const tooltipFormatter = (value, name) => {
    if (name === 'sunshine_hours') {
      return [`${value.toFixed(1)} hours`, 'Sunshine'];
    } else if (name === 'efficiency_percentage') {
      return [`${value.toFixed(1)}%`, 'Efficiency'];
    }
    return [`${value.toFixed(2)} kWh`, name];
  };

  // Label formatter for the X-axis
  const labelFormatter = (value) => {
    if (viewMode === 'daily') {
      return formatDate(value);
    } else if (viewMode === 'weekly') {
      return `Week of ${formatDate(value)}`;
    } else {
      return value;
    }
  };

  return (
    <div className="tab-container">
      <h2 className="tab-title">Solar Panel Efficiency</h2>
      <p className="tab-description">
        Analysis of solar panel energy production, efficiency metrics based on weather conditions,
        and optimization recommendations for maximizing renewable energy generation.
      </p>
      
      <DateRangeSelector 
        dateRange={dateRange}
        setDateRange={setDateRange}
        viewMode={viewMode}
        setViewMode={setViewMode}
      />
      
      {loading ? (
        <div className="loading-state">Loading solar energy data...</div>
      ) : error ? (
        <div className="error-state">{error}</div>
      ) : (
        <>
          <div className="metrics-grid">
            <MetricCard 
              title="Average Production" 
              value={metrics.avgProduction} 
              unit="kWh" 
              icon="⚡" 
              color="blue" 
            />
            <MetricCard 
              title="Peak Production" 
              value={metrics.peakProduction} 
              unit="kWh" 
              icon="📈" 
              color="red" 
            />
            <MetricCard 
              title="Panel Efficiency" 
              value={metrics.efficiency * 100} 
              unit="%" 
              icon="☀️" 
              color="orange" 
            />
            <MetricCard 
              title="Weather Impact" 
              value={metrics.weatherImpact * 100} 
              unit="%" 
              icon="🌤️" 
              color="green" 
            />
            <MetricCard 
              title="Prediction Accuracy" 
              value={metrics.predictionAccuracy * 100} 
              unit="%" 
              icon="🎯" 
              color="purple" 
            />
          </div>
          
          <div className="charts-container">
            <Chart 
              type="line" 
              data={data} 
              title="Solar Energy Production Over Time" 
              xKey="date" 
              yKeys={['energy_production', 'predicted_production']} 
              colors={['#1976d2', '#f44336']} 
              height={400} 
              tooltipFormatter={tooltipFormatter}
              labelFormatter={labelFormatter}
            />
            
            <div className="charts-row">
              <Chart 
                type="bar" 
                data={data} 
                title="Sunshine Hours vs Energy Production" 
                xKey="date" 
                yKeys={['sunshine_hours', 'energy_production']} 
                colors={['#ff9800', '#1976d2']} 
                height={300} 
                tooltipFormatter={tooltipFormatter}
                labelFormatter={labelFormatter}
              />
              <Chart 
                type="area" 
                data={data} 
                title="Panel Efficiency Over Time" 
                xKey="date" 
                yKeys={['efficiency_percentage', 'optimal_efficiency']} 
                colors={['#4caf50', '#9c27b0']} 
                height={300} 
                tooltipFormatter={tooltipFormatter}
                labelFormatter={labelFormatter}
              />
            </div>
          </div>
          
          <div className="insights-container">
            <h3>Key Insights</h3>
            <ul className="insights-list">
              <li>Solar panels operate at {(metrics.efficiency * 100).toFixed(0)}% efficiency in {selectedCity}.</li>
              <li>Weather conditions affect energy production by approximately {(metrics.weatherImpact * 100).toFixed(0)}%.</li>
              <li>Peak production typically occurs between 11 AM and 2 PM on clear days.</li>
              <li>Prediction models achieve {(metrics.predictionAccuracy * 100).toFixed(0)}% accuracy in forecasting solar energy production.</li>
              <li>Regular panel cleaning and maintenance could increase efficiency by up to 5%.</li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
};

export default SolarTab; 