import React from 'react';
import { AppProvider } from './context/AppContext';
import Header from './components/Header/Header';
import WeatherCard from './components/WeatherCard/WeatherCard';
import TabNavigation from './components/TabNavigation/TabNavigation';
import TabContent from './components/TabContent/TabContent';
import './App.css';

function App() {
  return (
    <AppProvider>
      <div className="app-container">
        <Header />
        <div className="main-content">
          <WeatherCard />
          <TabNavigation />
          <TabContent />
        </div>
      </div>
    </AppProvider>
  );
}

export default App;
