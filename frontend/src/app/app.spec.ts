import { TestBed } from "@angular/core/testing";
import { provideHttpClient } from "@angular/common/http";
import { HttpTestingController, provideHttpClientTesting } from "@angular/common/http/testing";
import { App } from "./app";

describe("App", () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it("should create the app", () => {
    const fixture = TestBed.createComponent(App);
    const http = TestBed.inject(HttpTestingController);
    const app = fixture.componentInstance;

    http.expectOne("/api/items/").flush({ items: [] });

    expect(app).toBeTruthy();
    http.verify();
  });

  it("should render items from the API", async () => {
    const fixture = TestBed.createComponent(App);
    const http = TestBed.inject(HttpTestingController);

    http.expectOne("/api/items/").flush({
      items: [
        {
          id: 1,
          name: "サンプルCSV",
          tableName: "sample_csv",
          createdAt: "2026-01-01T00:00:00Z",
        },
      ],
    });
    fixture.detectChanges();

    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector("h1")?.textContent).toContain("CSV 一覧");
    expect(compiled.textContent).toContain("サンプルCSV");
    expect(compiled.textContent).toContain("sample_csv");
    http.verify();
  });

  it("should delete an item and reload the list when the delete button is clicked and confirmed", async () => {
    const fixture = TestBed.createComponent(App);
    const http = TestBed.inject(HttpTestingController);

    // 1. 初期ロード
    http.expectOne("/api/items/").flush({
      items: [
        {
          id: 1,
          name: "サンプルCSV",
          tableName: "sample_csv",
          createdAt: "2026-01-01T00:00:00Z",
        },
      ],
    });
    fixture.detectChanges();
    await fixture.whenStable();

    // 2. confirm をモック化し、削除ボタンをクリック
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const compiled = fixture.nativeElement as HTMLElement;
    const deleteButton = compiled.querySelector(".btn-danger") as HTMLButtonElement;
    expect(deleteButton).toBeTruthy();
    deleteButton.click();

    // 3. DELETE リクエストの検証とモック応答
    const deleteReq = http.expectOne("/api/items/1/");
    expect(deleteReq.request.method).toBe("DELETE");
    deleteReq.flush(null, { status: 204, statusText: "No Content" });

    // 4. 自動で走る GET リロードリクエストの検証とモック応答（空リストを返す）
    const reloadReq = http.expectOne("/api/items/");
    expect(reloadReq.request.method).toBe("GET");
    reloadReq.flush({ items: [] });

    fixture.detectChanges();
    await fixture.whenStable();

    // 5. 画面からアイテムが消えたことを検証
    expect(compiled.textContent).not.toContain("サンプルCSV");
    http.verify();
  });
});
