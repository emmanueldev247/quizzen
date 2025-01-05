import { showNotification } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const nav = document.getElementById("flyout-nav");
  const hamburgerButton = document.querySelector(".hamburger");
  const hamburgerIcon = document.querySelector(".hamburger i");
  const openModalButtons = document.querySelectorAll(".create-button");
  const closeModalButton = document.getElementById("closeModal");
  const modal = document.getElementById("quizModal");
  const overlay = document.getElementById("modalOverlay");

  const closeModal = () => {
    modal.style.display = "none";
    overlay.style.display = "none";
  };

  openModalButtons.forEach((button) => {
    button.addEventListener("click", () => {
      modal.style.display = "block";
      overlay.style.display = "block";
    });
  });

  closeModalButton.addEventListener("click", closeModal);
  overlay.addEventListener("click", closeModal);

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

document.querySelector(".modal-content").addEventListener("submit", (event) => {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);
  const data = Object.fromEntries(formData.entries());

  const submitButton = document.getElementById("submit-button");
  submitButton.disabled = true;

  fetch("/quizzen/quiz/new", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => {
      if (!response.ok) {
        if (response.status === 429) {
          showNotification(
            "You have made too many requests in a short period. Please try again later",
            "error"
          );
        } else
          showNotification(
            "Something went wrong. Please try again later",
            "error"
          );
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        showNotification("Quiz created successfully!", "success");
        window.location.href = data.redirect_url;
      } else {
        showNotification(data.message || "Quiz creation failed.", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      if (error.message === "Failed to fetch")
        showNotification(
          "Network error. Please check your connection",
          "error"
        );
      else
        showNotification(
          "An error occurred while creating the quiz. Please try again",
          "error"
        );
    })
    .finally(() => (submitButton.disabled = false));
});
