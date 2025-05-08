import React from 'react';
import { useAppContext } from '../../context/AppContext';
import './TabNavigation.css';

const TabNavigation = () => {
  const { activeTab, setActiveTab } = useAppContext();

  const tabs = [
    { id: 'residential', label: 'Residential', icon: '🏠' },
    { id: 'commercial', label: 'Commercial', icon: '🏢' },
    { id: 'industrial', label: 'Industrial', icon: '🏭' },
    { id: 'tourism', label: 'Tourism', icon: '✈️' },
    { id: 'solar', label: 'Solar', icon: '☀️' }
  ];

  const handleTabClick = (tabId) => {
    setActiveTab(tabId);
  };

  return (
    <div className="tab-navigation">
      {tabs.map(tab => (
        <div
          key={tab.id}
          className={`tab ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => handleTabClick(tab.id)}
        >
          <span className="tab-icon">{tab.icon}</span>
          <span className="tab-label">{tab.label}</span>
        </div>
      ))}
    </div>
  );
};

export default TabNavigation; 