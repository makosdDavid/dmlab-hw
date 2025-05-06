import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, catchError, finalize, map, of, tap } from 'rxjs';
import { EnergyForecast } from '../models/forecast.model';

interface HealthResponse {
  status: string;
  message?: string;
}

interface WeatherData {
  datetime: string;
  temperature: number;
  humidity: number;
  wind_speed: number;
  cloud_cover: number;
  description: string;
}

interface SolarPanelData {
  datetime: string;
  energy_produced: number;
  efficiency: number;
  panel_temperature: number;
  solar_irradiance: number;
  status: string;
}

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = 'http://localhost:5000/api';

  loading = signal<boolean>(false);
  error = signal<string | null>(null);

  constructor() {}

  getHealthCheck(): Observable<HealthResponse> {
    return this.http
      .get<HealthResponse>(`${this.baseUrl}/health`)
      .pipe(
        catchError(() => of({ status: 'error', message: 'API not available' }))
      );
  }

  getWeatherData(limit: number = 10): Observable<WeatherData[]> {
    this.loading.set(true);
    return this.http
      .get<WeatherData[]>(`${this.baseUrl}/weather?limit=${limit}`)
      .pipe(
        map((data) => {
          return data.sort(
            (a, b) =>
              new Date(b.datetime).getTime() - new Date(a.datetime).getTime()
          );
        }),
        catchError((error) => {
          console.error('Error fetching weather data:', error);
          return of([]);
        }),
        finalize(() => this.loading.set(false))
      );
  }

  getSolarData(limit: number = 10): Observable<SolarPanelData[]> {
    this.loading.set(true);
    return this.http
      .get<SolarPanelData[]>(`${this.baseUrl}/solar?limit=${limit}`)
      .pipe(
        map((data) => {
          return data.sort(
            (a, b) =>
              new Date(b.datetime).getTime() - new Date(a.datetime).getTime()
          );
        }),
        catchError((error) => {
          console.error('Error fetching solar data:', error);
          return of([]);
        }),
        finalize(() => this.loading.set(false))
      );
  }

  getForecastData(hours: number = 24): Observable<EnergyForecast[]> {
    this.loading.set(true);
    return this.http
      .get<EnergyForecast[]>(`${this.baseUrl}/forecast?hours=${hours}`)
      .pipe(
        map((data) => {
          return data.sort(
            (a, b) =>
              new Date(a.datetime).getTime() - new Date(b.datetime).getTime()
          );
        }),
        catchError((error) => {
          console.error('Error fetching forecast data:', error);
          return of([]);
        }),
        finalize(() => this.loading.set(false))
      );
  }

  triggerDataProcessing(): Observable<any> {
    this.loading.set(true);
    return this.http.post(`${this.baseUrl}/process`, {}).pipe(
      tap((response) => console.log('Processing triggered:', response)),
      catchError((error) => {
        console.error('Error triggering data processing:', error);
        return of({ success: false, error: error.message });
      }),
      finalize(() => this.loading.set(false))
    );
  }
}
