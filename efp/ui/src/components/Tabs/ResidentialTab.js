import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../context/AppContext';
import { getResidentialData } from '../../services/api';
import DateRangeSelector from '../Common/DateRangeSelector';
import MetricCard from '../Common/MetricCard';
import Chart from '../Common/Chart';
import './TabStyles.css';

const ResidentialTab = () => {
  const { selectedCity, dateRange, setDateRange, viewMode, setViewMode } = useAppContext();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [metrics, setMetrics] = useState({
    avgConsumption: 0,
    peakConsumption: 0,
    savingsPotential: 0,
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
        
        const result = await getResidentialData(
          cityParam, 
          startDate.toISOString().split('T')[0], 
          endDate.toISOString().split('T')[0]
        );
        
        setData(result.data);
        
        // Calculate metrics
        if (result.data && result.data.length > 0) {
          const consumptionValues = result.data.map(item => item.consumption);
          const avgConsumption = consumptionValues.reduce((sum, val) => sum + val, 0) / consumptionValues.length;
          const peakConsumption = Math.max(...consumptionValues);
          
          setMetrics({
            avgConsumption: parseFloat(avgConsumption.toFixed(2)),
            peakConsumption: parseFloat(peakConsumption.toFixed(2)),
            savingsPotential: parseFloat((avgConsumption * 0.15).toFixed(2)), // Assuming 15% savings potential
            weatherImpact: parseFloat((result.weather_impact || 0.3).toFixed(2)), // Weather impact coefficient
            predictionAccuracy: parseFloat((result.prediction_accuracy || 0.92).toFixed(2)) // Prediction accuracy
          });
        }
      } catch (err) {
        console.error('Error fetching residential data:', err);
        setError('Failed to load residential energy data. Please try again later.');
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
      <h2 className="tab-title">Residential Energy Consumption</h2>
      <p className="tab-description">
        Analysis of energy consumption patterns in residential areas, with weather-based predictions 
        and energy-saving recommendations.
      </p>
      
      <DateRangeSelector 
        dateRange={dateRange}
        setDateRange={setDateRange}
        viewMode={viewMode}
        setViewMode={setViewMode}
      />
      
      {loading ? (
        <div className="loading-state">Loading residential energy data...</div>
      ) : error ? (
        <div className="error-state">{error}</div>
      ) : (
        <>
          <div className="metrics-grid">
            <MetricCard 
              title="Average Consumption" 
              value={metrics.avgConsumption} 
              unit="kWh" 
              icon="📊" 
              color="blue" 
            />
            <MetricCard 
              title="Peak Consumption" 
              value={metrics.peakConsumption} 
              unit="kWh" 
              icon="⚡" 
              color="red" 
            />
            <MetricCard 
              title="Savings Potential" 
              value={metrics.savingsPotential} 
              unit="kWh" 
              icon="💰" 
              color="green" 
              trend="up" 
              trendValue="15%" 
            />
            <MetricCard 
              title="Weather Impact" 
              value={metrics.weatherImpact * 100} 
              unit="%" 
              icon="🌤️" 
              color="orange" 
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
              title="Energy Consumption Over Time" 
              xKey="date" 
              yKeys={['consumption', 'predicted']} 
              colors={['#1976d2', '#f44336']} 
              height={400} 
              tooltipFormatter={tooltipFormatter}
              labelFormatter={labelFormatter}
            />
            
            <div className="charts-row">
              <Chart 
                type="bar" 
                data={data} 
                title="Consumption vs Temperature" 
                xKey="date" 
                yKeys={['consumption', 'temperature_impact']} 
                colors={['#1976d2', '#ff9800']} 
                height={300} 
                tooltipFormatter={tooltipFormatter}
                labelFormatter={labelFormatter}
              />
              <Chart 
                type="area" 
                data={data} 
                title="Savings Potential" 
                xKey="date" 
                yKeys={['consumption', 'optimal_consumption']} 
                colors={['#1976d2', '#4caf50']} 
                height={300} 
                tooltipFormatter={tooltipFormatter}
                labelFormatter={labelFormatter}
              />
            </div>
          </div>
          
          <div className="insights-container">
            <h3>Key Insights</h3>
            <ul className="insights-list">
              <li>Peak consumption typically occurs during evening hours (6-9 PM).</li>
              <li>Weather has a {(metrics.weatherImpact * 100).toFixed(0)}% impact on energy consumption patterns.</li>
              <li>Potential for {(metrics.savingsPotential / metrics.avgConsumption * 100).toFixed(0)}% energy savings through optimized usage patterns.</li>
              <li>Prediction models achieve {(metrics.predictionAccuracy * 100).toFixed(0)}% accuracy in forecasting residential energy needs.</li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
};

export default ResidentialTab; 