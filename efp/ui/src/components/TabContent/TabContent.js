import React from 'react';
import { useAppContext } from '../../context/AppContext';
import ResidentialTab from '../Tabs/ResidentialTab';
import CommercialTab from '../Tabs/CommercialTab';
import IndustrialTab from '../Tabs/IndustrialTab';
import TourismTab from '../Tabs/TourismTab';
import SolarTab from '../Tabs/SolarTab';
import './TabContent.css';

const TabContent = () => {
  const { activeTab } = useAppContext();

  const renderTabContent = () => {
    switch (activeTab) {
      case 'residential':
        return <ResidentialTab />;
      case 'commercial':
        return <CommercialTab />;
      case 'industrial':
        return <IndustrialTab />;
      case 'tourism':
        return <TourismTab />;
      case 'solar':
        return <SolarTab />;
      default:
        return <div className="tab-error">Invalid tab selected</div>;
    }
  };

  return (
    <div className="tab-content">
      {renderTabContent()}
    </div>
  );
};

export default TabContent; 