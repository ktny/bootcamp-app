import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';

type Item = {
  id: number;
  name: string;
  tableName: string;
  createdAt: string;
};

type ItemsResponse = {
  items: Item[];
};

@Component({
  selector: 'app-root',
  imports: [],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly http = inject(HttpClient);

  protected readonly items = signal<Item[]>([]);
  protected readonly isLoading = signal(true);
  protected readonly errorMessage = signal('');

  constructor() {
    this.http.get<ItemsResponse>('/api/items/').subscribe({
      next: (response) => {
        this.items.set(response.items);
        this.isLoading.set(false);
      },
      error: () => {
        this.errorMessage.set('CSV 一覧の取得に失敗しました');
        this.isLoading.set(false);
      },
    });
  }
}
