import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { AdminDashboardComponent } from './admin-dashboard/admin-dashboard.component';

@NgModule({
  imports: [
    CommonModule,
    RouterModule,
    AdminDashboardComponent
  ],
  exports: [
    AdminDashboardComponent
  ]
})
export class AdminModule { }
