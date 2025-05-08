import React from 'react';
import './MetricCard.css';

const MetricCard = ({ title, value, unit, icon, trend, trendValue, color }) => {
  const getTrendIcon = () => {
    if (!trend) return null;
    
    if (trend === 'up') {
      return <span className="trend-icon up">↑</span>;
    } else if (trend === 'down') {
      return <span className="trend-icon down">↓</span>;
    } else {
      return <span className="trend-icon neutral">→</span>;
    }
  };
  
  const getColorClass = () => {
    if (!color) return '';
    
    return `color-${color}`;
  };

  return (
    <div className={`metric-card ${getColorClass()}`}>
      {icon && <div className="metric-icon">{icon}</div>}
      <div className="metric-content">
        <div className="metric-title">{title}</div>
        <div className="metric-value">
          {value}
          {unit && <span className="metric-unit">{unit}</span>}
        </div>
        {trend && trendValue && (
          <div className="metric-trend">
            {getTrendIcon()}
            <span className="trend-value">{trendValue}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricCard; 