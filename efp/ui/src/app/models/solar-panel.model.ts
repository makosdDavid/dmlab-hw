export interface SolarPanel {
  _id?: string;
  datetime: string;
  energy_produced: number;
  efficiency: number;
  panel_temperature: number;
  solar_irradiance: number;
  status: string;
}
