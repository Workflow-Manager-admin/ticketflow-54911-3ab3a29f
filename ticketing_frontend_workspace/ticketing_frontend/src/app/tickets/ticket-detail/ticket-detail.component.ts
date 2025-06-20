import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TicketsService, Ticket, TicketUpdate } from '../tickets.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-ticket-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ticket-detail.component.html',
  styleUrls: ['./ticket-detail.component.css']
})
export class TicketDetailComponent implements OnInit {
  ticket: Ticket | null = null;
  loading = false;
  error: string | null = null;

  // Modal edit state
  showModal = false;
  modalError: string | null = null;
  formData: Partial<TicketUpdate> = {};

  constructor(
    private ticketsService: TicketsService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadTicket();
  }

  loadTicket(): void {
    this.loading = true;
    this.error = null;
    const ticketId = +(this.route.snapshot.paramMap.get('id') || 0);
    if (!ticketId) {
      this.error = 'Invalid ticket ID.';
      this.loading = false;
      return;
    }
    this.ticketsService.getTicket(ticketId).subscribe({
      next: (t: Ticket) => {
        this.ticket = t;
        this.loading = false;
      },
      error: (err: any) => {
        this.error = err.message || 'Error loading ticket';
        this.loading = false;
      }
    });
  }

  openEditModal(): void {
    if (!this.ticket) return;
    this.formData = {
      title: this.ticket.title,
      description: this.ticket.description ?? '',
      status: this.ticket.status
    };
    this.showModal = true;
    this.modalError = null;
  }

  closeModal(): void {
    this.showModal = false;
    this.formData = {};
    this.modalError = null;
  }

  submitModal(): void {
    if (!this.ticket || !this.formData.title || typeof this.formData.title !== 'string') {
      this.modalError = 'Title is required.';
      return;
    }
    this.ticketsService.updateTicket(this.ticket.id, this.formData).subscribe({
      next: (updated: Ticket) => {
        this.ticket = updated;
        this.closeModal();
      },
      error: (err: any) => (this.modalError = err.message || 'Error updating ticket')
    });
  }

  deleteTicket(): void {
    if (!this.ticket) return;
    // SSR-safe: check typeof window
    if (typeof window !== 'undefined' && !window.confirm(`Are you sure you want to delete ticket "${this.ticket.title}"?`)) return;
    this.ticketsService.deleteTicket(this.ticket.id).subscribe({
      next: () => this.router.navigate(['/tickets']),
      error: (err: any) => this.error = err.message || 'Error deleting ticket'
    });
  }

  onStatusSelect(event: Event): void {
    if (!this.ticket) return;
    const selectElement = event.target as HTMLSelectElement;
    if (!selectElement) return;
    const status = selectElement.value as 'open' | 'in_progress' | 'closed';
    this.changeTicketStatus(status);
  }

  changeTicketStatus(status: 'open' | 'in_progress' | 'closed'): void {
    if (!this.ticket || this.ticket.status === status) return;
    this.ticketsService.patchTicketStatus(this.ticket.id, status).subscribe({
      next: (updated: Ticket) => this.ticket = updated,
      error: (err: any) => this.error = err.message || 'Error updating status'
    });
  }
}
