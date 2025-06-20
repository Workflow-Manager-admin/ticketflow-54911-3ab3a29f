import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';

import { TicketListComponent } from './ticket-list/ticket-list.component';
import { TicketDetailComponent } from './ticket-detail/ticket-detail.component';

@NgModule({
  imports: [
    CommonModule,
    RouterModule,
    HttpClientModule,
    TicketListComponent,
    TicketDetailComponent
  ],
  exports: [
    TicketListComponent,
    TicketDetailComponent
  ]
})
export class TicketsModule { }
