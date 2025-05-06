import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { Weather } from '../../models/weather.model';

@Component({
  selector: 'app-weather-display',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule],
  template: `
    <div class="weather-container">
      <div class="weather-main">
        <div class="temperature">
          <span class="value">{{
            weather.temperature | number : '1.0-0'
          }}</span>
          <span class="unit">°C</span>
        </div>
        <div class="description">
          <div class="weather-icon">
            <mat-icon
              [fontIcon]="getWeatherIcon(weather.description)"
            ></mat-icon>
          </div>
          <span>{{ weather.description }}</span>
        </div>
      </div>

      <div class="weather-details">
        <div class="detail-item">
          <mat-icon fontIcon="water_drop"></mat-icon>
          <span>{{ weather.humidity }}%</span>
          <small>Humidity</small>
        </div>
        <div class="detail-item">
          <mat-icon fontIcon="air"></mat-icon>
          <span>{{ weather.wind_speed }} m/s</span>
          <small>Wind</small>
        </div>
        <div class="detail-item">
          <mat-icon fontIcon="cloud"></mat-icon>
          <span>{{ weather.cloud_cover }}%</span>
          <small>Cloud Cover</small>
        </div>
      </div>

      <div class="weather-time">
        <small>Last updated: {{ formatDate(weather.datetime) }}</small>
      </div>
    </div>
  `,
  styles: `
    .weather-container {
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding: 8px;
    }

    .weather-main {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .temperature {
      font-size: 3rem;
      font-weight: 300;
      display: flex;
      align-items: flex-start;
    }

    .temperature .unit {
      font-size: 1.5rem;
      margin-top: 8px;
    }

    .description {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-transform: capitalize;
    }

    .weather-icon {
      font-size: 2.5rem;
      height: 40px;
      width: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .weather-icon mat-icon {
      font-size: 2.5rem;
      height: 40px;
      width: 40px;
    }

    .weather-details {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      border-top: 1px solid #eee;
      padding-top: 16px;
    }

    .detail-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      flex: 1;
    }

    .detail-item mat-icon {
      margin-bottom: 4px;
      color: #666;
    }

    .detail-item small {
      color: #888;
      font-size: 0.8rem;
    }

    .weather-time {
      text-align: right;
      color: #888;
      font-size: 0.8rem;
    }
  `,
})
export class WeatherDisplayComponent {
  @Input() weather!: Weather;

  // Helper method to format datetime
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString();
  }

  // Helper method to determine weather icon based on description
  getWeatherIcon(description: string): string {
    const desc = description.toLowerCase();

    if (desc.includes('clear') || desc.includes('sunny')) {
      return 'wb_sunny';
    } else if (desc.includes('cloud')) {
      return 'cloud';
    } else if (desc.includes('rain') || desc.includes('shower')) {
      return 'rainy';
    } else if (desc.includes('storm') || desc.includes('thunder')) {
      return 'thunderstorm';
    } else if (desc.includes('snow') || desc.includes('flurry')) {
      return 'ac_unit';
    } else if (desc.includes('mist') || desc.includes('fog')) {
      return 'blur_on';
    } else {
      return 'thermostat';
    }
  }
}
