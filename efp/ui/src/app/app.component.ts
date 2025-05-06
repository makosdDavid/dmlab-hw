import { Component } from '@angular/core';
import { DashboardComponent } from './components/dashboard/dashboard.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [DashboardComponent],
  template: `
    <main>
      <app-dashboard></app-dashboard>
    </main>
  `,
  styles: `
    main {
      min-height: 100vh;
      background-color: #f5f5f5;
    }
  `,
})
export class AppComponent {
  title = 'Energy Consumption Forecast';
}
