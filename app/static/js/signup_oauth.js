import { showNotification, showElements } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  // Get the elements
  const signupForm = document.getElementById("signup-form");

  // Initialize by showing the signup form
  setTimeout(() => {
    showElements(signupForm);
  }, 200);

  // Role icon select
  document.querySelectorAll(".role-option").forEach((option) => {
    option.addEventListener("click", function () {
      document.getElementById("role").value = this.dataset.role;
      document
        .querySelectorAll(".role-option")
        .forEach((opt) => opt.classList.remove("selected"));
      this.classList.add("selected");
    });
  });

  // Validation & Submission
  let isValid = false;
  const submitBtn = document.getElementById("submit-button");
  submitBtn.addEventListener("click", () => {
    const role = document.getElementById("role").value;
    const roleError = document.getElementById("role-error");
    roleError.style.display = "none";

    if (!role) {
      roleError.textContent = "Please select what best describes you";
      roleError.style.display = "block";
      isValid = false;
    } else {
      isValid = true;
    }
  });

  signupForm.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!isValid) {
      return;
    }

    isValid = false;
    submitBtn.textContent = "Submitting...";
    submitBtn.disabled = true;

    const formData = new FormData(this);

    // Send POST request to backend
    fetch("/quizzen/oauth/signin", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          if (response.status === 400) {
            showNotification(
              "An account already exists for this email. Please use the button above to log in or register another email",
              "error"
            );
          } else if (response.status === 429) {
            showNotification(
              "You have made too many requests in a short period. Please try again later",
              "error"
            );
          } else {
            showNotification(
              "Something went wrong. Please try again later",
              "error"
            );
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          showNotification(
            "Oauth Registration successful! You can now log in using Oauth",
            "success"
          );
          setTimeout(() => {
            window.location.href = "/quizzen/dashboard";
          }, 3000);
        }
      })
      .catch((error) => {
        if (error.message === "Failed to fetch")
          showNotification(
            "Network error. Please check your connection",
            "error"
          );
      })
      .finally(() => {
        submitBtn.textContent = "Submit";
        submitBtn.disabled = false;
      });
  });
});
