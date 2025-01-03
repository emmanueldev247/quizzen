import { showNotification } from "./utils.js";

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

document.addEventListener("keydown", (event) => {
  if (
    event.target.classList.contains("custom-point") &&
    event.key === "Enter"
  ) {
    const input = event.target;
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
});

document.addEventListener("DOMContentLoaded", () => {
  document.addEventListener("click", (event) => {
    const bubble = document.getElementById("confirmationBubble");

    if (event.target.classList.contains("add-question-btn")) {
      const quizID = addQuestionBtn.getAttribute("data-quiz-id");
      window.location.href = `/quizzen/quiz/${quizID}/question/new`;
    }

    if (
      !bubble.contains(event.target) &&
      !event.target.classList.contains("delete-btn")
    ) {
      hideConfirmationBubble();
    }
  });
});

function showConfirmationBubble(event, questionId) {
  const bubble = document.getElementById("confirmationBubble");

  const buttonRect = event.target.getBoundingClientRect();

  bubble.style.left = `${
    buttonRect.left + window.scrollX + buttonRect.width / 2
  }px`;
  bubble.style.top = `${buttonRect.bottom + window.scrollY + 5}px`;

  bubble.style.display = "block";

  // Attach the question ID to the bubble for deletion logic
  bubble.dataset.questionId = questionId;
}

function hideConfirmationBubble() {
  const bubble = document.getElementById("confirmationBubble");
  bubble.style.display = "none";
}

function confirmDelete() {
  const bubble = document.getElementById("confirmationBubble");
  const questionId = bubble.dataset.questionId;
  const quizId = bubble.dataset.quizId;

  console.log(
    `Deleting question with ID: ${questionId} from quiz ID: ${quizId}`
  );

  document.querySelectorAll(".delete-btn").forEach((button) => {
    button.disabled = true;
  });

  document.querySelectorAll(".confirm-delete-btn").forEach((button) => {
    button.disabled = true;
  });

  fetch(`/quizzen/quiz/${quizId}/question/${questionId}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question_id: questionId,
      quiz_id: quizId,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Question deleted successfully!", "success");
        location.reload();
      } else {
        showNotification("Failed to delete question", "success");
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
      document.querySelectorAll(".confirm-delete-btn").forEach((button) => {
        button.disabled = true;
      });
      hideConfirmationBubble();
    });
}

// Add event listener to delete buttons
document.querySelectorAll(".delete-btn").forEach((button) => {
  button.addEventListener("click", (event) => {
    const questionId =
      event.target.closest(".question-header").dataset.questionId;
    const quizId = event.target.closest(".question-actions").dataset.quizId;

    // Set the quizId in the confirmation bubble
    const bubble = document.getElementById("confirmationBubble");
    bubble.dataset.quizId = quizId;

    showConfirmationBubble(event, questionId);
  });
});
