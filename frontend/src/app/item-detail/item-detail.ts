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

  // 集計用の状態
  protected readonly groupBy = signal("");
  protected readonly aggregateBy = signal("");
  protected readonly func = signal("");
  protected readonly isAggregating = signal(false);
  protected readonly aggErrorMessage = signal("");
  protected readonly aggregateResult = signal<DetailResponse | null>(null);

  protected readonly allowedFunctions = ["SUM", "AVG", "COUNT", "MAX", "MIN"];

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

  protected onAggregate(): void {
    const gVal = this.groupBy();
    const aVal = this.aggregateBy();
    const fVal = this.func();

    if (!aVal || !fVal) {
      this.aggErrorMessage.set("集計列と集計関数を選択してください");
      return;
    }

    this.aggErrorMessage.set("");
    this.isAggregating.set(true);
    this.aggregateResult.set(null);

    const id = this.item()?.id;
    this.http
      .get<DetailResponse>(`/api/items/${id}/aggregate/`, {
        params: {
          group_by: gVal,
          aggregate_by: aVal,
          function: fVal,
        },
      })
      .subscribe({
        next: (response) => {
          this.aggregateResult.set(response);
          this.isAggregating.set(false);
        },
        error: (err) => {
          const msg = err.error?.error || "集計処理に失敗しました";
          this.aggErrorMessage.set(msg);
          this.isAggregating.set(false);
        },
      });
  }
}
