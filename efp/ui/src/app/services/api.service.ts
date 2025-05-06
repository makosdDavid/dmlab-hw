import { HttpClient } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { Observable, catchError, finalize, map, of, tap } from 'rxjs';
import { EnergyForecast } from '../models/forecast.model';
import { SolarPanel } from '../models/solar-panel.model';
import { Weather } from '../models/weather.model';
import { environment } from '../../environments/environment';

interface HealthResponse {
  status: string;
  message?: string;
}

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  loading = signal<boolean>(false);
  error = signal<string | null>(null);

  constructor(private http: HttpClient) {}

  getHealthCheck(): Observable<HealthResponse> {
    return this.http
      .get<HealthResponse>(`${this.apiUrl}/health`)
      .pipe(
        catchError(() => of({ status: 'error', message: 'API not available' }))
      );
  }

  getWeatherData(): Observable<Weather[]> {
    this.loading.set(true);
    return this.http.get<Weather[]>(`${this.apiUrl}/weather`).pipe(
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

  getSolarData(): Observable<SolarPanel[]> {
    this.loading.set(true);
    return this.http.get<SolarPanel[]>(`${this.apiUrl}/solar`).pipe(
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

  getForecastData(): Observable<EnergyForecast[]> {
    this.loading.set(true);
    return this.http.get<EnergyForecast[]>(`${this.apiUrl}/forecast`).pipe(
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
    return this.http.post(`${this.apiUrl}/process`, {}).pipe(
      tap((response) => console.log('Processing triggered:', response)),
      catchError((error) => {
        console.error('Error triggering data processing:', error);
        return of({ success: false, error: error.message });
      }),
      finalize(() => this.loading.set(false))
    );
  }
}
