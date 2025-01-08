import { showNotification } from "./utils.js";

const bubble = document.getElementById("confirmationBubble");
const addQuestionButtons = document.querySelectorAll(".add-question-btn");
const cancelButtons = document.querySelectorAll(".cancel-btn");
const confirmDeleteButtons = document.querySelectorAll(".confirm-delete-btn");
const deleteButtons = document.querySelectorAll(".delete-btn");
const editButtons = document.querySelectorAll(".edit-btn");
const quizTitle = document.getElementById("quiz-title");
const quizTitles = document.querySelectorAll(".quiz-title");
const goBack = document.querySelector(".back-btn");
const publishButton = document.querySelector(".publish-btn");
let originalTitle = quizTitle.textContent.trim();

document.addEventListener("DOMContentLoaded", () => {
  goBack.addEventListener("click", () => {
    window.location.href = "/quizzen/admin/dashboard";
  });

  publishButton.addEventListener("click", function () {
    const isPublish = this.querySelector(".publish-quiz");
    const isUnpublish = this.querySelector(".unpublish-quiz");

    const quizId = isPublish
      ? isPublish.dataset.quizId
      : isUnpublish
      ? isUnpublish.dataset.quizId
      : null;

    if (!quizId) {
      showNotification("An error occured", "error");
      return;
    }

    const action = isPublish ? "publish" : "unpublish";
    const endpoint = `/quizzen/quiz/${quizId}/${action}`;

    publishButton.disabled = true;

    // Send an AJAX request to the server
    fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ quizId }),
    })
      .then((response) => {
        if (response.ok) {
          // Update the UI to reflect action
          if (isPublish) {
            publishButton.innerHTML = `
            <i class="fas fa-eye-slash unpublish-quiz" data-quiz-id="${quizId}"></i> Unpublish
            `;
          } else if (isUnpublish) {
            publishButton.innerHTML = `
            <i class="fas fa-check-circle publish-quiz" data-quiz-id="${quizId}"></i> Publish
            `;
          }
        } else {
          console.error(`${action} failed for quiz ${quizId}`);
          if (response.status === 429)
            showNotification(
              "You have made too many requests in a short period. Please try again later",
              "error"
            );
          else if (response.status === 403)
            showNotification("Unauthorized access", "error");
          else {
            showNotification(
              "Something went wrong. Please try again later",
              "error"
            );
            throw new Error(`HTTP error! status: ${response.status}`);
          }
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
      .finally(() => (publishButton.disabled = false));
  });

  // Add a new quiz
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

  confirmDeleteButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const questionCards = document.querySelectorAll(".question-card");
      const isLastQuestion = questionCards.length === 1;
      if (isLastQuestion) {
        const userConfirmed = confirm(
          "You are about to delete the last question. The entire quiz will be deleted. Do you want to proceed?"
        );
        if (userConfirmed) {
          const questionCard = this.closest(".question-card");
          handleQuizDeletion(questionCard);
        }
      } else {
        confirmDelete();
      }
    });
  });

  deleteButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
      const questionHeader = event.target.closest(".question-header");
      const questionId = questionHeader.dataset.questionId;
      const quizId = questionHeader.dataset.quizId;

      showConfirmationBubble(event, questionId, quizId);
    });
  });

  editButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
      const questionHeader = event.target.closest(".question-header");
      const questionId = questionHeader.dataset.questionId;
      const quizId = questionHeader.dataset.quizId;

      window.location.href = `/quizzen/quiz/${quizId}/question/${questionId}/edit`;
    });
  });

  // event listeners for title update
  quizTitle.addEventListener("focus", () => {
    originalTitle = quizTitle.textContent.trim();
  });

  quizTitle.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      quizTitle.blur();
    }
  });

  quizTitle.addEventListener("blur", () => {
    const newTitle = quizTitle.textContent.trim();
    if (!newTitle) {
      quizTitle.textContent = originalTitle;

      showNotification("Quiz title cannot be empty", "error");
      return;
    }

    const url = window.location.href;
    quizTitle.removeAttribute("contenteditable");
    fetch(url, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title: newTitle }),
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
          quizTitles.forEach((title) => {
            title.textContent = newTitle;
          });
          showNotification("Quiz title updated successfully!", "success");
        } else {
          showNotification(data.message || "Quiz creation failed.", "error");
        }
      })
      .catch((error) => {
        console.error("Error updating title:", error);
        if (error.message === "Failed to fetch")
          showNotification(
            "Network error. Please check your connection",
            "error"
          );
        else
          showNotification("Error updating title. Please try again", "error");
      })
      .finally(() => {
        quizTitle.setAttribute("contenteditable", "true");
      });
  });

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
  if (bubble) {
    bubble.style.display = "none";
    bubble.dataset.quizId = bubble.dataset.questionId = "";
  }
}

export function confirmDelete() {
  if (bubble) {
    const questionId = bubble.dataset.questionId;
    const quizId = bubble.dataset.quizId;

    deleteButtons.forEach((button) => {
      button.disabled = true;
    });

    confirmDeleteButtons.forEach((button) => {
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
        confirmDeleteButtons.forEach((button) => {
          button.disabled = false;
        });
        hideConfirmationBubble();
      });
  }
}

export function handleQuizDeletion(questionCard) {
  deleteButtons.forEach((button) => {
    button.disabled = true;
  });
  confirmDeleteButtons.forEach((button) => {
    button.disabled = true;
  });

  fetch(window.location.href, {
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
        if (questionCard) questionCard.remove();
        window.location.href = "/quizzen/dashboard";
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

export function updateQuizStats() {
  const quizLengthElem = document.getElementById("quiz_length");
  const questionsLabel = document.getElementById("questions_label");
  const quizMaxScoreElem = document.getElementById("quiz_max_score");
  const pointsLabel = document.getElementById("points_label");

  let quizLength = parseInt(quizLengthElem.textContent);
  let quizMaxScore = parseInt(quizMaxScoreElem.textContent);

  quizLengthElem.textContent = --quizLength;
  questionsLabel.textContent = quizLength > 1 ? "Questions" : "Question";

  quizMaxScoreElem.textContent = --quizMaxScore;
  pointsLabel.textContent = quizMaxScore > 1 ? "Points" : "Point";

  const questionCards = document.querySelectorAll(".question-card");
  questionCards.forEach((card, index) => {
    const questionNumElement = card.querySelector(".question-num-type");
    questionNumElement.textContent = `${index + 1}. ${
      questionNumElement.textContent.split(". ")[1]
    }`;
  });
}
