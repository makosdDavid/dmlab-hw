import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDividerModule } from '@angular/material/divider';
import { WeatherDisplayComponent } from '../weather-display/weather-display.component';
import { SolarPanelComponent } from '../solar-panel/solar-panel.component';
import { ForecastChartComponent } from '../forecast-chart/forecast-chart.component';
import { ApiService } from '../../services/api.service';
import { EnergyForecast } from '../../models/forecast.model';
import { Weather } from '../../models/weather.model';
import { SolarPanel } from '../../models/solar-panel.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatTabsModule,
    MatDividerModule,
    MatProgressSpinnerModule,
    WeatherDisplayComponent,
    SolarPanelComponent,
    ForecastChartComponent,
  ],
  template: `
    <div class="dashboard-container">
      <h1>Energy Consumption Dashboard</h1>

      <div class="status-bar">
        <span class="status" [class.online]="apiStatus() === 'healthy'">
          API Status:
          {{ apiStatus() === 'healthy' ? 'Connected' : 'Disconnected' }}
        </span>
      </div>

      <div class="dashboard-grid">
        @if (apiService.loading()) {
        <div class="loading-container">
          <mat-spinner></mat-spinner>
          <p>Loading data...</p>
        </div>
        } @else {
        <mat-card class="weather-card">
          <mat-card-header>
            <mat-card-title>Current Weather</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            @if (latestWeather()) {
            <app-weather-display
              [weather]="latestWeather()!"
            ></app-weather-display>
            } @else {
            <p>No weather data available</p>
            }
          </mat-card-content>
        </mat-card>

        <mat-card class="solar-card">
          <mat-card-header>
            <mat-card-title>Solar Panel Production</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            @if (latestSolar()) {
            <app-solar-panel [solarData]="latestSolar()!"></app-solar-panel>
            } @else {
            <p>No solar data available</p>
            }
          </mat-card-content>
        </mat-card>

        <mat-card class="forecast-card">
          <mat-card-header>
            <mat-card-title>Energy Consumption Forecast</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            @if (forecastData().length > 0) {
            <app-forecast-chart
              [forecastData]="forecastData()"
            ></app-forecast-chart>
            } @else {
            <p>No forecast data available</p>
            }
          </mat-card-content>
        </mat-card>
        }
      </div>

      <div class="actions">
        <button mat-raised-button color="primary" (click)="refreshData()">
          Refresh Data
        </button>
      </div>
    </div>
  `,
  styles: `
    .dashboard-container {
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }

    h1 {
      text-align: center;
      margin-bottom: 20px;
    }

    .status-bar {
      display: flex;
      justify-content: flex-end;
      margin-bottom: 20px;
    }

    .status {
      padding: 5px 10px;
      border-radius: 4px;
      background-color: #f44336;
      color: white;
    }

    .status.online {
      background-color: #4caf50;
    }

    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-bottom: 20px;
    }

    .loading-container {
      grid-column: 1 / -1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 300px;
    }

    mat-card {
      height: 100%;
    }

    .forecast-card {
      grid-column: 1 / -1;
    }

    .actions {
      display: flex;
      justify-content: center;
      margin-top: 20px;
    }
  `,
})
export class DashboardComponent implements OnInit {
  apiService = inject(ApiService);

  weatherData = signal<Weather[]>([]);
  solarData = signal<SolarPanel[]>([]);
  forecastData = signal<EnergyForecast[]>([]);
  apiStatus = signal<string>('unknown');

  latestWeather = signal<Weather | null>(null);
  latestSolar = signal<SolarPanel | null>(null);

  ngOnInit(): void {
    this.loadData();
    this.checkApiStatus();
  }

  refreshData(): void {
    this.loadData();
    this.checkApiStatus();
  }

  private loadData(): void {
    this.apiService.getWeatherData().subscribe({
      next: (data) => {
        this.weatherData.set(data);
        if (data.length > 0) {
          this.latestWeather.set(data[0]);
        }
      },
      error: (err) => console.error('Error loading weather data:', err),
    });

    this.apiService.getSolarData().subscribe({
      next: (data) => {
        this.solarData.set(data);
        if (data.length > 0) {
          this.latestSolar.set(data[0]);
        }
      },
      error: (err) => console.error('Error loading solar data:', err),
    });

    this.apiService.getForecastData().subscribe({
      next: (data) => {
        this.forecastData.set(data);
      },
      error: (err) => console.error('Error loading forecast data:', err),
    });
  }

  private checkApiStatus(): void {
    this.apiService.getHealthCheck().subscribe({
      next: (data) => {
        this.apiStatus.set(data.status);
      },
      error: () => {
        this.apiStatus.set('disconnected');
      },
    });
  }
}
