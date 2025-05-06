export interface EnergyForecast {
  _id?: string;
  datetime: Date;
  predicted_consumption: number;
  actual_consumption?: number;
  solar_production: number;
  feed_in: number;
}
