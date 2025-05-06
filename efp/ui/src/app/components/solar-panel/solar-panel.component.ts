import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { SolarPanel } from '../../models/solar-panel.model';

@Component({
  selector: 'app-solar-panel',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatProgressBarModule],
  template: `
    <div class="solar-container">
      <div class="solar-main">
        <div class="energy-output">
          <span class="value">{{
            solarData.energy_produced | number : '1.1-1'
          }}</span>
          <span class="unit">kWh</span>
        </div>
        <div class="efficiency">
          <mat-icon fontIcon="solar_power"></mat-icon>
          <div class="efficiency-details">
            <mat-progress-bar
              [value]="solarData.efficiency * 100"
              [color]="getEfficiencyColor(solarData.efficiency)"
            >
            </mat-progress-bar>
            <span
              >{{ solarData.efficiency * 100 | number : '1.0-0' }}%
              Efficiency</span
            >
          </div>
        </div>
      </div>

      <div class="solar-details">
        <div class="detail-item">
          <mat-icon fontIcon="thermostat"></mat-icon>
          <span>{{ solarData.panel_temperature | number : '1.1-1' }}°C</span>
          <small>Panel Temp</small>
        </div>
        <div class="detail-item">
          <mat-icon fontIcon="wb_sunny"></mat-icon>
          <span>{{ solarData.solar_irradiance | number : '1.0-0' }} W/m²</span>
          <small>Irradiance</small>
        </div>
        <div class="detail-item">
          <mat-icon [fontIcon]="getStatusIcon(solarData.status)"></mat-icon>
          <span>{{ solarData.status }}</span>
          <small>Status</small>
        </div>
      </div>

      <div class="solar-time">
        <small>Last updated: {{ formatDate(solarData.datetime) }}</small>
      </div>
    </div>
  `,
  styles: `
    .solar-container {
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding: 8px;
    }

    .solar-main {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .energy-output {
      font-size: 3rem;
      font-weight: 300;
      display: flex;
      align-items: flex-start;
    }

    .energy-output .unit {
      font-size: 1.5rem;
      margin-top: 8px;
    }

    .efficiency {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .efficiency mat-icon {
      color: #FFB300;
      font-size: 2rem;
      height: 32px;
      width: 32px;
    }

    .efficiency-details {
      display: flex;
      flex-direction: column;
      flex-grow: 1;
      gap: 4px;
    }

    .efficiency-details span {
      font-size: 0.9rem;
    }

    .solar-details {
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

    .solar-time {
      text-align: right;
      color: #888;
      font-size: 0.8rem;
    }
  `,
})
export class SolarPanelComponent {
  @Input() solarData!: SolarPanel;

  // Helper method to format datetime
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString();
  }

  // Helper method to determine efficiency color
  getEfficiencyColor(efficiency: number): string {
    if (efficiency >= 0.7) {
      return 'primary'; // Good efficiency
    } else if (efficiency >= 0.5) {
      return 'accent'; // Medium efficiency
    } else {
      return 'warn'; // Poor efficiency
    }
  }

  // Helper method to determine status icon
  getStatusIcon(status: string): string {
    const statusLower = status.toLowerCase();

    if (statusLower.includes('optimal') || statusLower.includes('good')) {
      return 'check_circle';
    } else if (
      statusLower.includes('degraded') ||
      statusLower.includes('medium')
    ) {
      return 'warning';
    } else if (
      statusLower.includes('maintenance') ||
      statusLower.includes('offline')
    ) {
      return 'build';
    } else if (statusLower.includes('error') || statusLower.includes('fault')) {
      return 'error';
    } else {
      return 'info';
    }
  }
}
