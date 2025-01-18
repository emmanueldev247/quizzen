document.addEventListener("DOMContentLoaded", () => {
  // Get the elements
  const errorContainer = document.getElementById("error-container");
  const loginButton = document.getElementById("back-to-login");

  // Initialize by showing the signup form
  function showErrElements(...elements) {
    elements.forEach((element) => {
      element.classList.add("zoom-in");
    });
  }

  setTimeout(() => {
    showErrElements(errorContainer);
  }, 500);

  loginButton.addEventListener(
    "click",
    () => (window.location.href = "/quizzen/login")
  );
});
