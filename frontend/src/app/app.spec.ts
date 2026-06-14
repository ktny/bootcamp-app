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
});
