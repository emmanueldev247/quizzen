import { showNotification } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  // Add a new quiz
  const addQuestionButtons = document.querySelectorAll(".add-question-btn");
  const cancelButtons = document.querySelectorAll(".cancel-btn");
  const deleteButtons = document.querySelectorAll(".delete-btn");

  addQuestionButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const quizId = button.getAttribute("data-quiz-id");
      // Redirect to the new question page for the specific quiz
      window.location.href = `/quizzen/quiz/${quizId}/question/new`;
    });
  });

  // Add event listener to delete buttons
  cancelButtons.forEach(button, () => {
    button.addEventListener("click", hideConfirmationBubble);
  });

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

    document.querySelectorAll(".delete-btn").forEach((button) => {
      button.disabled = true;
    });

    fetch(`/quizzen/quiz/${quizId}/question/${questionId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then(response.json())
      .then((data) => {
        if (data.success) {
          showNotification("Question deleted successfully!", "success");

          // Remove question from DOM
          const questionCard = document
            .querySelector(`.question-header[data-question-id="${questionId}"]`)
            .closest(".question-card");
          if (questionCard) questionCard.remove();

          // Update quiz stats (optional)
          updateQuizStats();
        } else {
          showNotification("Failed to delete question.", "error");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        showNotification("An error occurred. Please try again", "error");
      })
      .finally(() => {
        document.querySelectorAll(".delete-btn").forEach((button) => {
          button.disabled = false;
        });
        hideConfirmationBubble();
      });
  }
}

export function updateQuizStats() {
  const totalScoreElement = document.getElementById;
  alert("Just reload");
}

// Attach function to the window object
// window.confirmDelete = confirmDelete;
// window.hideConfirmationBubble = hideConfirmationBubble;
// window.showConfirmationBubble = showConfirmationBubble;
// window.updateQuizStats = updateQuizStats;
