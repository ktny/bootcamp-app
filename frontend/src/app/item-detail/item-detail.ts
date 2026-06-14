import { HttpClient } from "@angular/common/http";
import { Component, inject, signal } from "@angular/core";
import { ActivatedRoute, RouterLink } from "@angular/router";

type DetailResponse = {
  id: number;
  name: string;
  headers: string[];
  rows: string[][];
};

@Component({
  selector: "app-item-detail",
  imports: [RouterLink],
  templateUrl: "./item-detail.html",
})
export class ItemDetail {
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);

  protected readonly item = signal<DetailResponse | null>(null);
  protected readonly isLoading = signal(true);
  protected readonly errorMessage = signal("");

  constructor() {
    const id = this.route.snapshot.paramMap.get("id");
    if (id) {
      this.fetchDetail(id);
    } else {
      this.errorMessage.set("CSV ID が指定されていません");
      this.isLoading.set(false);
    }
  }

  private fetchDetail(id: string): void {
    this.isLoading.set(true);
    this.http.get<DetailResponse>(`/api/items/${id}/`).subscribe({
      next: (response) => {
        this.item.set(response);
        this.isLoading.set(false);
      },
      error: () => {
        this.errorMessage.set("詳細データの取得に失敗しました");
        this.isLoading.set(false);
      },
    });
  }
}
