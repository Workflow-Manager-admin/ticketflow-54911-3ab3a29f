import { Component } from '@angular/core';
import { Ticket, TicketCreate, TicketUpdate } from '../tickets.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TicketsService } from '../tickets.service';

@Component({
  selector: 'app-ticket-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ticket-list.component.html',
  styleUrls: ['./ticket-list.component.css']
})
export class TicketListComponent {
  tickets: Ticket[] = [];
  loading = false;
  error: string | null = null;

  // Modal/form state
  showModal = false;
  isEditMode = false;
  modalError: string | null = null;
  formData: Partial<TicketCreate & TicketUpdate> = {};
  editingTicketId: number | null = null;

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  constructor(private ticketsService: TicketsService) {
    this.loadTickets();
  }

  loadTickets(): void {
    this.loading = true;
    this.error = null;
    this.ticketsService.getTickets().subscribe({
      next: (tickets: Ticket[]) => {
        this.tickets = tickets;
        this.loading = false;
      },
      error: (err: any) => {
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
        error: (err: any) => (this.modalError = err.message || 'Error updating ticket')
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
        error: (err: any) => (this.modalError = err.message || 'Error creating ticket')
      });
    }
  }

  deleteTicket(ticket: Ticket): void {
    // SSR-safe check for browser confirm dialog
    if (typeof window !== 'undefined') {
      // eslint-disable-next-line no-undef
      if (!(window as any).confirm(`Are you sure you want to delete the ticket "${ticket.title}"?`)) return;
    }
    this.ticketsService.deleteTicket(ticket.id).subscribe({
      next: () => this.loadTickets(),
      error: (err: any) => (this.error = err.message || 'Error deleting ticket')
    });
  }

  onStatusSelect(event: Event, ticket: Ticket): void {
    const selectElement = event.target as HTMLSelectElement;
    if (!selectElement) return;
    const status = selectElement.value as 'open' | 'in_progress' | 'closed';
    this.changeTicketStatus(ticket, status);
  }

  changeTicketStatus(ticket: Ticket, status: 'open' | 'in_progress' | 'closed'): void {
    if (ticket.status === status) return;
    this.ticketsService.patchTicketStatus(ticket.id, status).subscribe({
      next: () => this.loadTickets(),
      error: (err: any) => (this.error = err.message || 'Error updating status')
    });
  }
}
