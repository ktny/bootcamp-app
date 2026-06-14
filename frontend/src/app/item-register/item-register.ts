import { HttpClient } from "@angular/common/http";
import { Component, inject, signal } from "@angular/core";
import { Router, RouterLink } from "@angular/router";

@Component({
  selector: "app-item-register",
  imports: [RouterLink],
  templateUrl: "./item-register.html",
})
export class ItemRegister {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  protected readonly errorMessage = signal("");
  protected readonly csvName = signal("");
  protected readonly csvText = signal("");
  protected readonly isSaving = signal(false);

  protected onSubmit(event: Event): void {
    event.preventDefault();

    const nameVal = this.csvName().trim();
    const textVal = this.csvText();

    if (!nameVal) {
      this.errorMessage.set("CSV名を入力してください");
      return;
    }
    if (!textVal || textVal.trim() === "") {
      this.errorMessage.set("CSVテキストを入力してください");
      return;
    }

    this.isSaving.set(true);
    this.errorMessage.set("");

    this.http
      .post<any>("/api/items/", {
        name: nameVal,
        csvText: textVal,
      })
      .subscribe({
        next: () => {
          this.isSaving.set(false);
          void this.router.navigate(["/"]);
        },
        error: (err) => {
          const msg = err.error?.error || "CSV の登録に失敗しました";
          this.errorMessage.set(msg);
          this.isSaving.set(false);
        },
      });
  }
}
