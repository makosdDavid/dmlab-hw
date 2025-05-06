export interface EnergyForecast {
  _id?: string;
  datetime: string;
  prediction_time?: string;
  consumption: number;
  production: number;
  net_consumption: number;
  confidence: number;
  source?: string;
}
