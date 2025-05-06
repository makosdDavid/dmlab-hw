import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ChartModule } from 'primeng/chart';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TabViewModule } from 'primeng/tabview';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ChartModule,
    CardModule,
    ButtonModule,
    TabViewModule,
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit {
  private apiService = inject(ApiService);

  weatherData: any;
  solarData: any;
  forecastData: any[] = [];

  chartData: any;
  chartOptions: any;

  activePredictionTab = 0;
  forecastPeriod: 'day' | 'week' | 'month' | 'year' = 'day';

  engineerPredictions = {
    efficiency: 0,
    maintenance: '',
    recommendation: '',
  };

  insurancePredictions = {
    riskFactor: 0,
    coverage: '',
    recommendation: '',
  };

  touristPredictions = {
    optimalPeriod: '',
    comfortIndex: 0,
    recommendation: '',
  };

  accuracyStats = {
    day: 95.8,
    week: 87.5,
    month: 76.2,
    year: 68.9,
  };

  loading = false;
  selectedCity = 'athens';

  statistics = {
    dailyAvgConsumption: 24.5,
    monthlySaving: 120.7,
    efficiencyTrend: '+3.2%',
    co2Reduction: 45.8,
  };

  ngOnInit() {
    this.loadData();
    this.setupChartOptions();
  }

  changeCity(event: Event) {
    const select = event.target as HTMLSelectElement;
    this.selectedCity = select.value;
    console.log(`City changed to: ${this.selectedCity}`);
    this.loadData();
  }

  setForecastPeriod(period: 'day' | 'week' | 'month' | 'year') {
    this.forecastPeriod = period;
    // Here you would typically load forecast data for the selected period
  }

  getAccuracyForPeriod(period: 'day' | 'week' | 'month' | 'year'): number {
    // This would normally be calculated based on historical data
    return this.accuracyStats[period];
  }

  getDailyAvgConsumption(): number {
    return this.statistics.dailyAvgConsumption;
  }

  getMonthlySaving(): number {
    return this.statistics.monthlySaving;
  }

  getEfficiencyTrend(): string {
    return this.statistics.efficiencyTrend;
  }

  getCO2Reduction(): number {
    return this.statistics.co2Reduction;
  }

  loadData() {
    this.loading = true;

    this.apiService.getWeatherData(1).subscribe({
      next: (data) => {
        if (data.length > 0) {
          this.weatherData = data[0];
        } else {
          this.weatherData = this.generateMockWeatherData();
        }
        this.calculatePredictions();
      },
      error: () => {
        this.weatherData = this.generateMockWeatherData();
        this.calculatePredictions();
      },
      complete: () => (this.loading = false),
    });

    this.apiService.getSolarData(1).subscribe({
      next: (data) => {
        if (data.length > 0) {
          this.solarData = data[0];
        } else {
          this.solarData = this.generateMockSolarData();
        }
        this.calculatePredictions();
      },
      error: () => {
        this.solarData = this.generateMockSolarData();
        this.calculatePredictions();
      },
      complete: () => (this.loading = false),
    });

    this.apiService.getForecastData(24).subscribe({
      next: (data) => {
        if (data.length > 0) {
          this.forecastData = data;
        } else {
          this.forecastData = this.generateMockForecastData(24);
        }
        this.updateChartData();
        this.calculatePredictions();
      },
      error: () => {
        this.forecastData = this.generateMockForecastData(24);
        this.updateChartData();
        this.calculatePredictions();
      },
      complete: () => (this.loading = false),
    });
  }

  refreshData() {
    this.loading = true;
    this.apiService.triggerDataProcessing().subscribe({
      next: () => {
        setTimeout(() => this.loadData(), 1000);
      },
      error: () => {
        // If the API call fails, just reload with potentially mock data
        setTimeout(() => this.loadData(), 1000);
      },
    });
  }

  setupChartOptions() {
    this.chartOptions = {
      plugins: {
        legend: {
          labels: {
            color: '#495057',
          },
        },
        tooltip: {
          mode: 'index',
          intersect: false,
        },
      },
      scales: {
        x: {
          ticks: {
            color: '#495057',
            maxRotation: 45,
            minRotation: 45,
          },
          grid: {
            color: '#ebedef',
          },
          afterFit: function (scale: any) {
            scale.height = 80; // Extra padding for x-axis labels
          },
        },
        y: {
          ticks: {
            color: '#495057',
          },
          grid: {
            color: '#ebedef',
          },
        },
      },
      layout: {
        padding: {
          bottom: 30, // Add padding at the bottom of the chart
        },
      },
      maintainAspectRatio: false,
      responsive: true,
    };
  }

  updateChartData() {
    if (!this.forecastData.length) return;

    const labels = this.forecastData.map((item) => {
      const date = new Date(item.datetime);
      return `${date.getHours()}:00`;
    });

    this.chartData = {
      labels: labels,
      datasets: [
        {
          label: 'Energy Consumption (kWh)',
          data: this.forecastData.map((item) => item.consumption),
          fill: false,
          borderColor: '#FFA726',
          tension: 0.4,
        },
        {
          label: 'Energy Production (kWh)',
          data: this.forecastData.map((item) => item.production),
          fill: false,
          borderColor: '#42A5F5',
          tension: 0.4,
        },
        {
          label: 'Net Consumption (kWh)',
          data: this.forecastData.map((item) => item.net_consumption),
          fill: false,
          borderColor: '#66BB6A',
          tension: 0.4,
        },
      ],
    };
  }

  calculatePredictions() {
    if (!this.weatherData || !this.solarData || !this.forecastData.length)
      return;

    this.engineerPredictions = this.calculateEngineerPredictions();
    this.insurancePredictions = this.calculateInsurancePredictions();
    this.touristPredictions = this.calculateTouristPredictions();
  }

  calculateEngineerPredictions() {
    const baseEfficiency = this.solarData.efficiency;
    const tempAdjustment = (25 - this.weatherData.temperature) * 0.1;
    const efficiency = Math.min(
      100,
      Math.max(0, baseEfficiency * 100 + tempAdjustment)
    );

    const highWindCount = this.forecastData.filter(
      (item) => item.wind_speed > 30
    ).length;
    const highTempCount = this.forecastData.filter(
      (item) => item.temperature > 35
    ).length;

    let maintenance = 'Monthly';
    if (highWindCount > 5 || highTempCount > 5) {
      maintenance = 'Bi-weekly';
    } else if (highWindCount > 10 || highTempCount > 8) {
      maintenance = 'Weekly';
    }

    let recommendation = '';
    if (efficiency < 70) {
      recommendation = 'Consider panel cleaning and inspection';
    } else if (efficiency < 85) {
      recommendation = 'Routine maintenance should be sufficient';
    } else {
      recommendation = 'Panels operating at optimal efficiency';
    }

    return {
      efficiency: Math.round(efficiency * 10) / 10,
      maintenance,
      recommendation,
    };
  }

  calculateInsurancePredictions() {
    const highWindCount = this.forecastData.filter(
      (item) => item.wind_speed > 30
    ).length;
    const highTempCount = this.forecastData.filter(
      (item) => item.temperature > 35
    ).length;
    const stormRisk = this.forecastData.filter(
      (item) => item.wind_speed > 50 || item.cloud_cover > 80
    ).length;

    const riskFactor =
      (highWindCount * 0.5 + highTempCount * 0.3 + stormRisk * 1.5) / 3;

    let coverage = 'Standard';
    let recommendation = '';

    if (riskFactor > 7) {
      coverage = 'Increase by 15-20%';
      recommendation = 'High risk of weather-related damage';
    } else if (riskFactor > 4) {
      coverage = 'Increase by 5-10%';
      recommendation = 'Moderate risk of weather-related incidents';
    } else {
      coverage = 'Standard coverage';
      recommendation = 'Low risk based on weather forecast';
    }

    return {
      riskFactor: Math.round(riskFactor * 10) / 10,
      coverage,
      recommendation,
    };
  }

  calculateTouristPredictions() {
    // Count days with comfortable conditions
    const comfortableConditions = this.forecastData.filter(
      (item) =>
        item.temperature >= 20 &&
        item.temperature <= 30 &&
        item.humidity <= 70 &&
        item.cloud_cover <= 60 &&
        item.wind_speed <= 20
    ).length;

    // Calculate comfort index based on percentage of comfortable hours
    const totalHours = this.forecastData.length;
    const comfortIndex = Math.round((comfortableConditions / totalHours) * 10);

    let optimalPeriod = '';
    let recommendation = '';

    // Determine recommendations based on comfort index
    if (comfortIndex >= 8) {
      optimalPeriod = 'Next 24 hours';
      recommendation = 'Excellent conditions for outdoor activities';
    } else if (comfortIndex >= 6) {
      optimalPeriod = 'Daytime hours';
      recommendation = 'Good conditions with some variability';
    } else if (comfortIndex >= 4) {
      optimalPeriod = 'Morning hours only';
      recommendation = 'Fair conditions, best in morning';
    } else {
      optimalPeriod = 'Not recommended';
      recommendation = 'Poor weather conditions expected';
    }

    return {
      optimalPeriod,
      comfortIndex,
      recommendation,
    };
  }

  // Mock data generation methods
  private generateMockWeatherData() {
    const cityTemperatures = {
      athens: 28,
      thessaloniki: 26,
      patras: 27,
      heraklion: 30,
    };

    return {
      datetime: new Date().toISOString(),
      temperature:
        cityTemperatures[this.selectedCity as keyof typeof cityTemperatures] ||
        28,
      humidity: Math.floor(Math.random() * 30) + 50, // 50-80%
      wind_speed: Math.floor(Math.random() * 20) + 5, // 5-25 km/h
      cloud_cover: Math.floor(Math.random() * 50), // 0-50%
      description: 'Sunny with some clouds',
    };
  }

  private generateMockSolarData() {
    const baseEfficiency = Math.random() * 10 + 80; // 80-90%

    return {
      datetime: new Date().toISOString(),
      energy_produced: Math.floor(Math.random() * 50) + 150, // 150-200 kWh
      efficiency: baseEfficiency / 100, // Convert to decimal
      panel_temperature: Math.floor(Math.random() * 20) + 40, // 40-60°C
      solar_irradiance: Math.floor(Math.random() * 200) + 600, // 600-800 W/m²
      status: 'Operational',
    };
  }

  private generateMockForecastData(hours: number) {
    const mockData = [];
    const now = new Date();
    const baseConsumption = 35; // base consumption in kWh
    const baseProduction = 25; // base production in kWh

    for (let i = 0; i < hours; i++) {
      const hour = new Date(now.getTime());
      hour.setHours(hour.getHours() + i);

      // Consumption varies by time of day
      let hourFactor = 1;
      const currentHour = hour.getHours();

      // Peak hours in morning and evening
      if (currentHour >= 7 && currentHour <= 9) {
        hourFactor = 1.5;
      } else if (currentHour >= 18 && currentHour <= 21) {
        hourFactor = 1.8;
      } else if (currentHour >= 23 || currentHour <= 5) {
        hourFactor = 0.7; // Lower at night
      }

      const consumption =
        baseConsumption * hourFactor * (0.9 + Math.random() * 0.2);

      // Production varies by time of day (sunlight)
      let productionFactor = 0;
      if (currentHour >= 7 && currentHour <= 18) {
        // Bell curve peaking at noon
        productionFactor = 1 - Math.abs((currentHour - 12.5) / 6);
      }

      const production =
        baseProduction * productionFactor * (0.9 + Math.random() * 0.2);
      const netConsumption = Math.max(0, consumption - production);

      mockData.push({
        datetime: hour.toISOString(),
        consumption: Math.round(consumption * 10) / 10,
        production: Math.round(production * 10) / 10,
        net_consumption: Math.round(netConsumption * 10) / 10,
        confidence: Math.floor(Math.random() * 10) + 90, // 90-100% confidence
        temperature: this.weatherData.temperature + (Math.random() * 6 - 3), // ±3°C from current
        wind_speed: this.weatherData.wind_speed + (Math.random() * 10 - 5), // ±5 km/h from current
        cloud_cover: Math.min(
          100,
          Math.max(0, this.weatherData.cloud_cover + (Math.random() * 30 - 15))
        ), // ±15% from current
        humidity: Math.min(
          100,
          Math.max(0, this.weatherData.humidity + (Math.random() * 20 - 10))
        ), // ±10% from current
      });
    }

    return mockData;
  }
}
