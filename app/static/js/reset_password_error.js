// Get the elements
const errorContainer = document.getElementById("error-container");
const loginButton = document.getElementById("back-to-login");

// Initialize by showing the signup form

function showErrElements(...elements) {
  elements.forEach(element => {
      element.classList.add("zoom-in");
  });
}
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    showErrElements(errorContainer);
  }, 500);
});

loginButton.addEventListener("click", () => window.location.href = "/quizzen/login");