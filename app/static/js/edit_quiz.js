import { showNotification } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  // Add a new quiz
  const addQuestionButtons = document.querySelectorAll(".add-question-btn");
  const cancelButtons = document.querySelectorAll(".cancel-btn");
  const confirmDeleteButtons = document.querySelectorAll(".confirm-delete-btn");
  const deleteButtons = document.querySelectorAll(".delete-btn");

  addQuestionButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const quizId = button.getAttribute("data-quiz-id");

      window.location.href = `/quizzen/quiz/${quizId}/question/new`;
    });
  });

  // Add event listener to delete buttons
  cancelButtons.forEach((button) =>
    button.addEventListener("click", hideConfirmationBubble)
  );
  confirmDeleteButtons.forEach((button) =>
    button.addEventListener("click", confirmDelete)
  );

  deleteButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
      const questionHeader = event.target.closest(".question-header");
      const questionId = questionHeader.dataset.questionId;
      const quizId = questionHeader.dataset.quizId;

      showConfirmationBubble(event, questionId, quizId);
    });
  });

  // Hide confirmation bubble on outside click
  document.addEventListener("click", (event) => {
    const bubble = document.getElementById("confirmationBubble");
    if (
      bubble &&
      !bubble.contains(event.target) &&
      !event.target.classList.contains("delete-btn")
    ) {
      hideConfirmationBubble();
    }
  });

  // Handle point-select changes
  document.addEventListener("change", (event) => {
    if (event.target.classList.contains("point-select")) {
      const select = event.target;
      const customInput = select.nextElementSibling;

      if (select.value === "other") {
        customInput.style.display = "inline-block";
        customInput.focus();
      } else {
        customInput.style.display = "none";
        customInput.value = "";

        select.blur();
      }
    }
  });

  // Handle custom point input
  document.addEventListener("keydown", (event) => {
    const input = event.target;

    if (input.classList.contains("custom-point")) {
      const allowedKeys = [
        "Backspace",
        "Tab",
        "ArrowLeft",
        "ArrowRight",
        "Enter",
        "Delete",
      ];

      if (!/^\d$/.test(event.key) && !allowedKeys.includes(event.key)) {
        event.preventDefault();
      }

      if (event.key === "Enter") {
        const select = input.previousElementSibling;
        let customValue = input.value.trim();

        if (customValue && !isNaN(customValue)) {
          customValue = Math.min(customValue, 100);

          const customOption = new Option(
            `${customValue} Points`,
            customValue,
            true,
            true
          );

          select.add(customOption);
          select.value = customValue;

          input.style.display = "none";
          input.value = "";

          input.blur();
        }
      }
    }
  });
});

export function showConfirmationBubble(event, questionId, quizId) {
  const bubble = document.getElementById("confirmationBubble");

  if (bubble) {
    const buttonRect = event.target.getBoundingClientRect();

    bubble.style.left = `${
      buttonRect.left + window.scrollX + buttonRect.width / 2
    }px`;
    bubble.style.top = `${buttonRect.bottom + window.scrollY + 5}px`;

    bubble.style.display = "block";
    bubble.dataset.questionId = questionId;
    bubble.dataset.quizId = quizId;
  }
}

export function hideConfirmationBubble() {
  const bubble = document.getElementById("confirmationBubble");

  if (bubble) {
    const questionId = bubble.dataset.questionId;
    const quizId = bubble.dataset.quizId;

    console.log(`Hiding bubble for question ${questionId} in quiz ${quizId}`);

    bubble.style.display = "none";
    bubble.dataset.quizId = bubble.dataset.questionId = "";
  }
}

export function confirmDelete() {
  const bubble = document.getElementById("confirmationBubble");
  if (bubble) {
    const questionId = bubble.dataset.questionId;
    const quizId = bubble.dataset.quizId;

    console.log(
      `Deleting question with ID: ${questionId} from quiz ID: ${quizId}`
    );

    deleteButtons.forEach((button) => {
      button.disabled = true;
    });

    fetch(`/quizzen/quiz/${quizId}/question/${questionId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
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
          showNotification("Question deleted successfully!", "success");

          // Remove question from DOM
          const questionCard = document
            .querySelector(`.question-header[data-question-id="${questionId}"]`)
            .closest(".question-card");
          if (questionCard) questionCard.remove();

          updateQuizStats();
        } else {
          showNotification("Failed to delete question.", "error");
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
        hideConfirmationBubble();
      });
  }
}

export function updateQuizStats() {
  const quizLength = parseInt(document.getElementById("quiz_length"));
  const questionsLabel = document.getElementById("questions_label");
  const quizMaxScore = parseInt(document.getElementById("quiz_max_score"));
  const pointsLabel = document.getElementById("points_label");

  if (quizLength < 2) window.location.href = "/quizzen/dashboard";
  else {
    quizLength.textContent = --quizLength;
    if (quizLength > 2) questionsLabel.textContent = "Questions";
    else questionsLabel.textContent = "Question";
  }

  if (quizMaxScore < 2) window.location.href = "/quizzen/dashboard";
  else {
    quizMaxScore.textContent = --quizMaxScore;
    if (quizMaxScore > 2) pointsLabel.textContent = "Points";
    else pointsLabel.textContent = "Point";
  }
}
