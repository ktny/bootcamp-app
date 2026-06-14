import { Routes } from "@angular/router";
import { ItemList } from "./item-list/item-list";
import { ItemRegister } from "./item-register/item-register";
import { ItemDetail } from "./item-detail/item-detail";

export const routes: Routes = [
  { path: "", component: ItemList },
  { path: "register", component: ItemRegister },
  { path: "items/:id", component: ItemDetail },
];
