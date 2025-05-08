import React from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, AreaChart, Area
} from 'recharts';
import './Chart.css';

const Chart = ({ 
  type = 'line', 
  data, 
  title, 
  xKey = 'date', 
  yKeys = [], 
  colors = ['#1976d2', '#4caf50', '#f44336', '#ff9800', '#9c27b0'], 
  stacked = false,
  height = 400,
  showGrid = true,
  showLegend = true,
  tooltipFormatter = null,
  labelFormatter = null
}) => {
  
  if (!data || data.length === 0) {
    return (
      <div className="chart-container">
        <h3 className="chart-title">{title}</h3>
        <div className="chart-no-data">No data available</div>
      </div>
    );
  }

  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis 
              dataKey={xKey} 
              tick={{ fontSize: 12 }}
              tickFormatter={labelFormatter}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={tooltipFormatter} />
            {showLegend && <Legend />}
            {yKeys.map((key, index) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[index % colors.length]}
                activeDot={{ r: 8 }}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        );
      
      case 'bar':
        return (
          <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis 
              dataKey={xKey} 
              tick={{ fontSize: 12 }}
              tickFormatter={labelFormatter}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={tooltipFormatter} />
            {showLegend && <Legend />}
            {yKeys.map((key, index) => (
              <Bar
                key={key}
                dataKey={key}
                fill={colors[index % colors.length]}
                stackId={stacked ? "stack" : null}
              />
            ))}
          </BarChart>
        );
      
      case 'area':
        return (
          <AreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis 
              dataKey={xKey} 
              tick={{ fontSize: 12 }}
              tickFormatter={labelFormatter}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={tooltipFormatter} />
            {showLegend && <Legend />}
            {yKeys.map((key, index) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                fill={colors[index % colors.length]}
                stroke={colors[index % colors.length]}
                fillOpacity={0.3}
                stackId={stacked ? "stack" : null}
              />
            ))}
          </AreaChart>
        );
      
      default:
        return (
          <div className="chart-error">Invalid chart type</div>
        );
    }
  };

  return (
    <div className="chart-container">
      {title && <h3 className="chart-title">{title}</h3>}
      <div className="chart-wrapper" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default Chart; 