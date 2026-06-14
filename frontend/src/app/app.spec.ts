import { ComponentFixture, TestBed } from "@angular/core/testing";
import { provideHttpClient } from "@angular/common/http";
import { HttpTestingController, provideHttpClientTesting } from "@angular/common/http/testing";
import { provideRouter, Router } from "@angular/router";
import { App } from "./app";
import { routes } from "./app.routes";
import { vi } from "vitest";

describe("App Integration Tests", () => {
  let http: HttpTestingController;
  let router: Router;
  let fixture: ComponentFixture<App>;
  let compiled: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter(routes)],
    }).compileComponents();

    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);

    fixture = TestBed.createComponent(App);
    router.initialNavigation();
    await fixture.whenStable();
    fixture.detectChanges();
    compiled = fixture.nativeElement as HTMLElement;
  });

  afterEach(() => {
    http.verify();
  });

  it("should navigate to register view and back", async () => {
    // 1. 初期一覧ロード
    http.expectOne("/api/items/").flush({ items: [] });
    fixture.detectChanges();

    expect(compiled.querySelector("h1")?.textContent).toContain("CSV 一覧");

    // 2. 新規登録ボタンをクリック
    compiled.querySelector(".btn-primary")?.dispatchEvent(new Event("click"));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(router.url).toBe("/register");
    expect(compiled.querySelector("h1")?.textContent).toContain("CSV 登録");

    // 3. キャンセルボタンをクリックして戻る
    compiled.querySelector(".btn-secondary")?.dispatchEvent(new Event("click"));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // 一覧画面に戻った際のリロード
    http.expectOne("/api/items/").flush({ items: [] });
    fixture.detectChanges();

    expect(router.url).toBe("/");
    expect(compiled.querySelector("h1")?.textContent).toContain("CSV 一覧");
  });

  it("should delete an item on the list view", async () => {
    // 初期ロード
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

    vi.spyOn(window, "confirm").mockReturnValue(true);
    compiled.querySelector(".btn-danger")?.dispatchEvent(new Event("click"));
    fixture.detectChanges();

    // DELETE 呼び出し検証
    const deleteReq = http.expectOne("/api/items/1/");
    expect(deleteReq.request.method).toBe("DELETE");
    deleteReq.flush(null, { status: 204, statusText: "No Content" });
    fixture.detectChanges();

    // リロード呼び出し検証
    const reloadReq = http.expectOne("/api/items/");
    reloadReq.flush({ items: [] });
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(compiled.textContent).not.toContain("サンプルCSV");
  });

  it("should register a new CSV and redirect to list", async () => {
    // 1. 初期ロード
    http.expectOne("/api/items/").flush({ items: [] });
    fixture.detectChanges();

    // 2. 登録画面へ遷移
    await router.navigate(["/register"]);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // 3. フォーム入力のシミュレート
    const nameInput = compiled.querySelector("input[id=csv-name]") as HTMLInputElement;
    const textInput = compiled.querySelector("textarea[id=csv-text]") as HTMLTextAreaElement;
    nameInput.value = "新規テストCSV";
    nameInput.dispatchEvent(new Event("input"));
    textInput.value = "a,b\n1,2";
    textInput.dispatchEvent(new Event("input"));
    fixture.detectChanges();

    // 4. 送信
    compiled.querySelector("form")?.dispatchEvent(new Event("submit"));
    fixture.detectChanges();

    const postReq = http.expectOne("/api/items/");
    expect(postReq.request.method).toBe("POST");
    postReq.flush({}, { status: 201, statusText: "Created" });
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // 成功後のリダイレクト (/) での一覧ロード
    const reloadReq = http.expectOne("/api/items/");
    reloadReq.flush({
      items: [
        {
          id: 2,
          name: "新規テストCSV",
          tableName: "csv_data_new",
          createdAt: "2026-06-14T05:00:00Z",
        },
      ],
    });
    fixture.detectChanges();

    expect(router.url).toBe("/");
    expect(compiled.textContent).toContain("新規テストCSV");
  });

  it("should display error message on registration failure", async () => {
    // 初期ロード
    http.expectOne("/api/items/").flush({ items: [] });
    fixture.detectChanges();

    // 登録画面へ
    await router.navigate(["/register"]);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // 入力
    const nameInput = compiled.querySelector("input[id=csv-name]") as HTMLInputElement;
    const textInput = compiled.querySelector("textarea[id=csv-text]") as HTMLTextAreaElement;
    nameInput.value = "重複CSV";
    nameInput.dispatchEvent(new Event("input"));
    textInput.value = "a,b\n1,2";
    textInput.dispatchEvent(new Event("input"));
    fixture.detectChanges();

    // 送信
    compiled.querySelector("form")?.dispatchEvent(new Event("submit"));
    fixture.detectChanges();

    const postReq = http.expectOne("/api/items/");
    postReq.flush(
      { error: "同名のCSVが既に存在します" },
      { status: 400, statusText: "Bad Request" },
    );
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const errorEl = compiled.querySelector(".status.error");
    expect(errorEl?.textContent).toContain("同名のCSVが既に存在します");
  });

  it("should navigate to detail view and display CSV data table", async () => {
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

    expect(compiled.querySelector("h1")?.textContent).toContain("CSV 一覧");

    // 2. 詳細リンク（CSV名リンク）をクリック
    const detailLink = compiled.querySelector("td a") as HTMLAnchorElement;
    expect(detailLink.textContent).toContain("サンプルCSV");
    detailLink.click();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(router.url).toBe("/items/1");

    // 3. 詳細APIの呼び出しとモック応答
    const detailReq = http.expectOne("/api/items/1/");
    expect(detailReq.request.method).toBe("GET");
    detailReq.flush({
      id: 1,
      name: "サンプルCSV",
      headers: ["name", "age"],
      rows: [
        ["Alice", "30"],
        ["Bob", "25"],
      ],
    });
    fixture.detectChanges();

    // 4. データテーブルの描画確認
    expect(compiled.querySelector("h1")?.textContent).toContain("CSV 詳細: サンプルCSV");
    const headers = compiled.querySelectorAll(".detail-table th");
    expect(headers[0]?.textContent).toContain("name");
    expect(headers[1]?.textContent).toContain("age");

    const cells = compiled.querySelectorAll(".detail-table td");
    expect(cells[0]?.textContent).toContain("Alice");
    expect(cells[1]?.textContent).toContain("30");
    expect(cells[2]?.textContent).toContain("Bob");
    expect(cells[3]?.textContent).toContain("25");

    // 5. 戻るボタンをクリックして戻る
    compiled.querySelector(".btn-back")?.dispatchEvent(new Event("click"));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // 一覧画面に戻った際のリロード
    http.expectOne("/api/items/").flush({ items: [] });
    fixture.detectChanges();

    expect(router.url).toBe("/");
  });
});
