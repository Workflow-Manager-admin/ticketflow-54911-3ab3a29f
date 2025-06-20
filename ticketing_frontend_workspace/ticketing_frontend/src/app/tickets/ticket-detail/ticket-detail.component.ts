import { Component } from '@angular/core';
import { Ticket, TicketUpdate } from '../tickets.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-ticket-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ticket-detail.component.html',
  styleUrls: ['./ticket-detail.component.css']
})
export class TicketDetailComponent {
  ticket: Ticket | null = null;
  loading = false;
  error: string | null = null;

  // Modal edit state
  showModal = false;
  modalError: string | null = null;
  formData: Partial<TicketUpdate> = {};
}
