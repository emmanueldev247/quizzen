import { setActive } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  setActive(".nav-item:nth-child(1)", ".bottom-nav-item:nth-child(1)");
});
