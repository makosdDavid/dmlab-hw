import {
  Component,
  ElementRef,
  Input,
  OnChanges,
  ViewChild,
  SimpleChanges,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { Chart, ChartConfiguration, ChartData, ChartOptions } from 'chart.js';
import { EnergyForecast } from '../../models/forecast.model';
import 'chartjs-adapter-date-fns';
import { enUS } from 'date-fns/locale/en-US';

@Component({
  selector: 'app-forecast-chart',
  standalone: true,
  imports: [CommonModule, MatButtonToggleModule],
  template: `
    <div class="chart-container">
      <div class="chart-controls">
        <mat-button-toggle-group
          #chartType="matButtonToggleGroup"
          [value]="chartOptions.chartType"
          (change)="toggleChartType($event.value)"
        >
          <mat-button-toggle value="line">Line</mat-button-toggle>
          <mat-button-toggle value="bar">Bar</mat-button-toggle>
        </mat-button-toggle-group>

        <mat-button-toggle-group
          #dataType="matButtonToggleGroup"
          [value]="chartOptions.dataType"
          (change)="toggleDataType($event.value)"
        >
          <mat-button-toggle value="consumption">Consumption</mat-button-toggle>
          <mat-button-toggle value="production">Production</mat-button-toggle>
          <mat-button-toggle value="net">Net</mat-button-toggle>
        </mat-button-toggle-group>
      </div>

      <div class="canvas-container">
        <canvas #forecastChart></canvas>
      </div>

      <div class="chart-legend">
        @if (chartOptions.dataType === 'consumption' || chartOptions.dataType
        === 'net') {
        <div class="legend-item">
          <span class="legend-color consumption"></span>
          <span>Consumption</span>
        </div>
        } @if (chartOptions.dataType === 'production' || chartOptions.dataType
        === 'net') {
        <div class="legend-item">
          <span class="legend-color production"></span>
          <span>Production</span>
        </div>
        } @if (chartOptions.dataType === 'net') {
        <div class="legend-item">
          <span class="legend-color net"></span>
          <span>Net Consumption</span>
        </div>
        }
      </div>
    </div>
  `,
  styles: `
    .chart-container {
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .chart-controls {
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
    }

    .canvas-container {
      height: 300px;
      position: relative;
    }

    .chart-legend {
      display: flex;
      justify-content: center;
      gap: 24px;
      margin-top: 8px;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.9rem;
    }

    .legend-color {
      display: inline-block;
      width: 16px;
      height: 16px;
      border-radius: 4px;
    }

    .legend-color.consumption {
      background-color: rgba(54, 162, 235, 0.6);
    }

    .legend-color.production {
      background-color: rgba(75, 192, 192, 0.6);
    }

    .legend-color.net {
      background-color: rgba(255, 159, 64, 0.6);
    }
  `,
})
export class ForecastChartComponent implements OnChanges {
  @Input() forecastData: EnergyForecast[] = [];
  @ViewChild('forecastChart') forecastChartRef!: ElementRef<HTMLCanvasElement>;

  chart: Chart | undefined;

  chartOptions = {
    chartType: 'line',
    dataType: 'consumption',
  };

  ngAfterViewInit(): void {
    if (this.forecastData.length > 0) {
      this.createChart();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['forecastData'] && this.forecastData.length > 0) {
      if (this.chart) {
        this.updateChart();
      } else if (this.forecastChartRef) {
        this.createChart();
      }
    }
  }

  toggleChartType(type: string): void {
    this.chartOptions.chartType = type;
    if (this.chart) {
      this.chart.destroy();
      this.createChart();
    }
  }

  toggleDataType(type: string): void {
    this.chartOptions.dataType = type;
    if (this.chart) {
      this.updateChart();
    }
  }

  private createChart(): void {
    const ctx = this.forecastChartRef.nativeElement.getContext('2d');
    if (!ctx) return;

    const chartData = this.getChartData();
    const chartOptions = this.getChartOptions();

    this.chart = new Chart(ctx, {
      type: this.chartOptions.chartType as any,
      data: chartData,
      options: chartOptions,
    });
  }

  private updateChart(): void {
    if (!this.chart) return;

    const chartData = this.getChartData();
    this.chart.data = chartData;
    this.chart.update();
  }

  private getChartData(): ChartData {
    const labels = this.forecastData.map((d) => new Date(d.datetime));

    const datasets = [];

    if (
      this.chartOptions.dataType === 'consumption' ||
      this.chartOptions.dataType === 'net'
    ) {
      datasets.push({
        label: 'Consumption',
        data: this.forecastData.map((d) => d.consumption),
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderWidth: 2,
        tension: 0.1,
      });
    }

    if (
      this.chartOptions.dataType === 'production' ||
      this.chartOptions.dataType === 'net'
    ) {
      datasets.push({
        label: 'Production',
        data: this.forecastData.map((d) => d.production),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderWidth: 2,
        tension: 0.1,
      });
    }

    if (this.chartOptions.dataType === 'net') {
      datasets.push({
        label: 'Net Consumption',
        data: this.forecastData.map((d) => d.net_consumption),
        borderColor: 'rgba(255, 159, 64, 1)',
        backgroundColor: 'rgba(255, 159, 64, 0.6)',
        borderWidth: 2,
        tension: 0.1,
      });
    }

    return { labels, datasets };
  }

  private getChartOptions(): ChartOptions {
    return {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'hour',
            tooltipFormat: 'MMM d, yyyy HH:mm',
            displayFormats: {
              hour: 'HH:mm',
            },
          },
          adapters: {
            date: {
              locale: enUS,
            },
          },
          title: {
            display: true,
            text: 'Time',
          },
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Energy (kWh)',
          },
        },
      },
      plugins: {
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false,
        },
        legend: {
          display: false,
        },
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false,
      },
    } as ChartOptions;
  }
}
