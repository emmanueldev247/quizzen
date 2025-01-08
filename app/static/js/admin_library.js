import { setActive } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  setActive(".nav-item:nth-child(3)", ".bottom-nav-item:nth-child(2)");
});