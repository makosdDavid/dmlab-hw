import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../context/AppContext';
import { getIndustrialData } from '../../services/api';
import DateRangeSelector from '../Common/DateRangeSelector';
import MetricCard from '../Common/MetricCard';
import Chart from '../Common/Chart';
import './TabStyles.css';

const IndustrialTab = () => {
  const { selectedCity, dateRange, setDateRange, viewMode, setViewMode } = useAppContext();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [metrics, setMetrics] = useState({
    avgConsumption: 0,
    peakConsumption: 0,
    efficiencyRating: 0,
    co2Emissions: 0,
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
        
        const result = await getIndustrialData(
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
            efficiencyRating: parseFloat((result.efficiency_rating || 0.72).toFixed(2)), // Efficiency rating
            co2Emissions: parseFloat((avgConsumption * 0.45).toFixed(2)), // CO2 emissions in kg (assuming 0.45 kg CO2/kWh)
            predictionAccuracy: parseFloat((result.prediction_accuracy || 0.91).toFixed(2)) // Prediction accuracy
          });
        }
      } catch (err) {
        console.error('Error fetching industrial data:', err);
        setError('Failed to load industrial energy data. Please try again later.');
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
    if (name === 'co2_emissions') {
      return [`${value.toFixed(2)} kg`, 'CO₂ Emissions'];
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
      <h2 className="tab-title">Industrial Energy Consumption</h2>
      <p className="tab-description">
        Analysis of energy usage in industrial facilities, with efficiency metrics, CO₂ emissions tracking,
        and optimization recommendations for heavy machinery and production lines.
      </p>
      
      <DateRangeSelector 
        dateRange={dateRange}
        setDateRange={setDateRange}
        viewMode={viewMode}
        setViewMode={setViewMode}
      />
      
      {loading ? (
        <div className="loading-state">Loading industrial energy data...</div>
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
              title="Efficiency Rating" 
              value={metrics.efficiencyRating * 100} 
              unit="%" 
              icon="🏭" 
              color="orange" 
            />
            <MetricCard 
              title="CO₂ Emissions" 
              value={metrics.co2Emissions} 
              unit="kg/day" 
              icon="🌍" 
              color="green" 
              trend="down" 
              trendValue="5%" 
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
                title="CO₂ Emissions Analysis" 
                xKey="date" 
                yKeys={['co2_emissions', 'optimal_emissions']} 
                colors={['#4caf50', '#1976d2']} 
                height={300} 
                tooltipFormatter={tooltipFormatter}
                labelFormatter={labelFormatter}
              />
              <Chart 
                type="area" 
                data={data} 
                title="Production vs Energy Consumption" 
                xKey="date" 
                yKeys={['consumption', 'production_index']} 
                colors={['#1976d2', '#ff9800']} 
                height={300} 
                tooltipFormatter={tooltipFormatter}
                labelFormatter={labelFormatter}
              />
            </div>
          </div>
          
          <div className="insights-container">
            <h3>Key Insights</h3>
            <ul className="insights-list">
              <li>Industrial facilities operate at {(metrics.efficiencyRating * 100).toFixed(0)}% energy efficiency rating.</li>
              <li>Average daily CO₂ emissions are {metrics.co2Emissions.toFixed(2)} kg, with potential for 5% reduction.</li>
              <li>Peak consumption typically occurs during production ramp-up periods.</li>
              <li>Prediction models achieve {(metrics.predictionAccuracy * 100).toFixed(0)}% accuracy in forecasting industrial energy needs.</li>
              <li>Implementing load balancing could reduce peak consumption by up to 15%.</li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
};

export default IndustrialTab; 