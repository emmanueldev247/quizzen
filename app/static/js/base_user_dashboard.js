import { showNotification } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const nav = document.getElementById("flyout-nav");
  const hamburgerButton = document.querySelector(".hamburger");
  const hamburgerIcon = document.querySelector(".hamburger i");
  
  hamburgerButton.addEventListener("click", () => {
    nav.classList.toggle("active");
    hamburgerIcon.classList.toggle("fa-bars");
    hamburgerIcon.classList.toggle("fa-times");
  });

  document.addEventListener("click", function (event) {
    if (!nav.contains(event.target) && !hamburgerIcon.contains(event.target)) {
      nav.classList.remove("active");
      hamburgerIcon.classList.remove("fa-times");
      hamburgerIcon.classList.add("fa-bars");
    }
  });
});