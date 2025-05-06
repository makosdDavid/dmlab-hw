export interface Weather {
  _id?: string;
  datetime: string;
  temperature: number;
  humidity: number;
  wind_speed: number;
  cloud_cover: number;
  description: string;
  location?: string;
}
