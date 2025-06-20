import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TicketsService } from '../tickets.service';
import { FormsModule } from '@angular/forms';

export interface Ticket {
  id: number;
  title: string;
  description?: string | null;
  status: 'open' | 'in_progress' | 'closed';
  created_at: string;
  updated_at: string;
  owner_id: number;
}

export interface TicketCreate {
  title: string;
  description?: string | null;
}

export interface TicketUpdate {
  title?: string | null;
  description?: string | null;
  status?: 'open' | 'in_progress' | 'closed' | null;
}

@Component({
  selector: 'app-ticket-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ticket-list.component.html',
  styleUrls: ['./ticket-list.component.css']
})
export class TicketListComponent implements OnInit {
  tickets: Ticket[] = [];
  loading = false;
  error: string | null = null;

  // Modal/form state
  showModal = false;
  isEditMode = false;
  modalError: string | null = null;
  formData: Partial<TicketCreate & TicketUpdate> = {};
  editingTicketId: number | null = null;

  constructor(private ticketsService: TicketsService) {}

  ngOnInit(): void {
    this.loadTickets();
  }

  loadTickets(): void {
    this.loading = true;
    this.error = null;
    this.ticketsService.getTickets().subscribe({
      next: (tickets) => {
        this.tickets = tickets;
        this.loading = false;
      },
      error: (err) => {
        this.error = err.message || 'Error loading tickets';
        this.loading = false;
      },
    });
  }

  openCreateModal(): void {
    this.showModal = true;
    this.isEditMode = false;
    this.formData = {};
    this.modalError = null;
    this.editingTicketId = null;
  }

  openEditModal(ticket: Ticket): void {
    this.showModal = true;
    this.isEditMode = true;
    this.editingTicketId = ticket.id;
    this.formData = {
      title: ticket.title,
      description: ticket.description ?? '',
      status: ticket.status
    };
    this.modalError = null;
  }

  closeModal(): void {
    this.showModal = false;
    this.isEditMode = false;
    this.formData = {};
    this.editingTicketId = null;
    this.modalError = null;
  }

  submitModal(): void {
    if (!this.formData.title || typeof this.formData.title !== 'string' || !this.formData.title.trim()) {
      this.modalError = 'The ticket title is required.';
      return;
    }
    if (this.isEditMode && this.editingTicketId !== null) {
      // Update ticket
      this.ticketsService.updateTicket(this.editingTicketId, {
        title: this.formData.title,
        description: this.formData.description,
        status: this.formData.status
      }).subscribe({
        next: () => {
          this.closeModal();
          this.loadTickets();
        },
        error: err => (this.modalError = err.message || 'Error updating ticket')
      });
    } else {
      // Create ticket
      this.ticketsService.createTicket({
        title: this.formData.title,
        description: this.formData.description
      }).subscribe({
        next: () => {
          this.closeModal();
          this.loadTickets();
        },
        error: err => (this.modalError = err.message || 'Error creating ticket')
      });
    }
  }

  deleteTicket(ticket: Ticket): void {
    // Using window.confirm avoids "no-undef"
    if (!window.confirm(`Are you sure you want to delete the ticket "${ticket.title}"?`)) return;
    this.ticketsService.deleteTicket(ticket.id).subscribe({
      next: () => this.loadTickets(),
      error: err => (this.error = err.message || 'Error deleting ticket')
    });
  }

  onStatusSelect(event: Event, ticket: Ticket): void {
    const selectElement = event.target as HTMLSelectElement;
    if (!selectElement) return;
    const status = selectElement.value as 'open' | 'in_progress' | 'closed';
    this.changeTicketStatus(ticket, status);
  }

  changeTicketStatus(ticket: Ticket, status: 'open'|'in_progress'|'closed'): void {
    if (ticket.status === status) return;
    this.ticketsService.patchTicketStatus(ticket.id, status).subscribe({
      next: () => this.loadTickets(),
      error: err => (this.error = err.message || 'Error updating status')
    });
  }
}
