import { showElements } from "./utils.js";

// Get the elements
const errorContainer = document.getElementById("error-container");
const loginButton = document.getElementById("back-to-login");

// Initialize by showing the signup form
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    showElements(errorContainer);
  }, 200);
});

loginButton.addEventListener("click", () => window.location.href = "/quizzen/login");