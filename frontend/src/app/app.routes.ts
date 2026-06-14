import { Routes } from "@angular/router";
import { ItemList } from "./item-list/item-list";
import { ItemRegister } from "./item-register/item-register";

export const routes: Routes = [
  { path: "", component: ItemList },
  { path: "register", component: ItemRegister },
];
