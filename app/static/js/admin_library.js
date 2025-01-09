import { setActive, showNotification } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  setActive(".nav-item:nth-child(3)", ".bottom-nav-item:nth-child(2)");

  const bubble = document.getElementById("confirmationBubble");
  const cancelButtons = document.querySelectorAll(".cancel-btn");
  const confirmDeleteButtons = document.querySelectorAll(".confirm-delete-btn");
  const deleteButtons = document.querySelectorAll(".delete-btn");
  const viewButtons = document.querySelectorAll(".view-btn");
  let targetQuizCard = null;

  function showConfirmationBubble(event, quizId) {
    if (bubble) {
      const buttonRect = event.target.getBoundingClientRect();

      bubble.style.left = `${
        buttonRect.left + window.scrollX + buttonRect.width / 2
      }px`;
      bubble.style.top = `${buttonRect.bottom + window.scrollY + 5}px`;

      bubble.style.display = "block";
      bubble.dataset.quizId = quizId;
    }
  }

  function hideConfirmationBubble() {
    if (bubble) {
      bubble.style.display = "none";
      bubble.dataset.quizId = "";
    }
  }

  function handleQuizDeletion(targetQuizCard, isLastQuiz = false) {
    deleteButtons.forEach((button) => {
      button.disabled = true;
    });
    confirmDeleteButtons.forEach((button) => {
      button.disabled = true;
    });

    if (targetQuizCard) {
      targetQuizCard.remove();
      targetQuizCard = null;
    }

    const quizId = bubble.dataset.quizId;
    const baseUrl = `${window.location.origin}/quizzen`;
    fetch(`${baseUrl}/quiz/${quizId}`, {
      method: "DELETE",
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
          showNotification("Quiz deleted successfully!", "success");
          if (isLastQuiz) window.location.href = "/quizzen/dashboard";
        } else {
          showNotification("Failed to delete quiz", "error");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        if (error.message === "Failed to fetch")
          showNotification(
            "Network error. Please check your connection",
            "error"
          );
      })
      .finally(() => {
        deleteButtons.forEach((button) => {
          button.disabled = false;
        });
        confirmDeleteButtons.forEach((button) => {
          button.disabled = false;
        });
        hideConfirmationBubble();
      });
  }

  // Hide confirmation bubble on outside click
  document.addEventListener("click", (event) => {
    if (
      bubble &&
      !bubble.contains(event.target) &&
      !event.target.classList.contains("delete-btn")
    ) {
      hideConfirmationBubble();
    }
  });

  // Add event listener to needed buttons
  viewButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const quizCard = this.closest(".quiz-card");
      const quizId = quizCard.dataset.quizId;

      window.location.href = `/quizzen/quiz/${quizId}/edit`;
    });
  });

  deleteButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
      const quizCard = event.target.closest(".quiz-card");
      const quizId = quizCard.dataset.quizId;
      targetQuizCard = quizCard;

      showConfirmationBubble(event, quizId);
    });
  });

  cancelButtons.forEach((button) =>
    button.addEventListener("click", hideConfirmationBubble)
  );

  confirmDeleteButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const quizCards = document.querySelectorAll(".quiz-card");
      const isLastQuiz = quizCards.length === 1;

      if (isLastQuiz) {
        const userConfirmed = confirm(
          "You are about to delete your only quiz. Do you want to proceed?"
        );
        if (userConfirmed) {
          handleQuizDeletion(targetQuizCard, true);
        }
      } else {
        handleQuizDeletion(targetQuizCard, false);
      }
    });
  });
});
