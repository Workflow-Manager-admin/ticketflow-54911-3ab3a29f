import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

// Shared ticket interfaces
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

@Injectable({
  providedIn: 'root'
})
export class TicketsService {
  private apiBase = '/api'; // Change if you have backend proxy, otherwise set full hostname

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  constructor(private http: HttpClient) {}

  // PUBLIC_INTERFACE
  /** List all tickets */
  getTickets(): Observable<Ticket[]> {
    return this.http.get<Ticket[]>(`${this.apiBase}/tickets/`).pipe(
      catchError(this.handleError)
    );
  }

  // PUBLIC_INTERFACE
  /** Get a ticket by ID */
  getTicket(ticketId: number): Observable<Ticket> {
    return this.http.get<Ticket>(`${this.apiBase}/tickets/${ticketId}`).pipe(
      catchError(this.handleError)
    );
  }

  // PUBLIC_INTERFACE
  /** Create a new ticket */
  createTicket(ticket: TicketCreate): Observable<Ticket> {
    return this.http.post<Ticket>(`${this.apiBase}/tickets/`, ticket).pipe(
      catchError(this.handleError)
    );
  }

  // PUBLIC_INTERFACE
  /** Update ticket (full/partial PUT) */
  updateTicket(ticketId: number, changes: TicketUpdate): Observable<Ticket> {
    return this.http.put<Ticket>(`${this.apiBase}/tickets/${ticketId}`, changes).pipe(
      catchError(this.handleError)
    );
  }

  // PUBLIC_INTERFACE
  /** Patch only the status of a ticket */
  patchTicketStatus(ticketId: number, status: 'open'|'in_progress'|'closed'): Observable<Ticket> {
    const url = `${this.apiBase}/tickets/${ticketId}/status`;
    let params = new HttpParams().set('ticket_status', status);
    return this.http.patch<Ticket>(url, {}, { params }).pipe(
      catchError(this.handleError)
    );
  }

  // PUBLIC_INTERFACE
  /** Delete a ticket by ID */
  deleteTicket(ticketId: number): Observable<{}> {
    return this.http.delete(`${this.apiBase}/tickets/${ticketId}`).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(err: any) {
    // Attempt to parse backend error or fall back
    let message = 'An unknown error occurred';
    if (err.error) {
      if (typeof err.error === 'string') {
        message = err.error;
      } else if (typeof err.error.detail === 'string') {
        message = err.error.detail;
      } else if (Array.isArray(err.error.detail) && err.error.detail.length && err.error.detail[0].msg) {
        message = err.error.detail[0].msg;
      }
    } else if (err.message) {
      message = err.message;
    }
    return throwError(() => new Error(message));
  }
}
