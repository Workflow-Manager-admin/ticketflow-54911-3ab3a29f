import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Ticket } from '../../tickets/tickets.service';

// PUBLIC_INTERFACE
@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-dashboard.component.html',
  styleUrls: ['./admin-dashboard.component.css']
})
export class AdminDashboardComponent {
  tickets: Ticket[] = [];
  loading = false;
  error: string | null = null;
}
