import { showNotification } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const quizContainer = document.getElementById("quiz-container");
  const timerElement = document.getElementById("timer");
  const questionIndexPanel = document.getElementById("question-index");
  const previousButton = document.getElementById("prev-btn");
  const nextButton = document.getElementById("next-btn");
  const submitButton = document.getElementById("submit-btn");
  const quizId = quizContainer.getAttribute("data-quiz-id");
  const startContainer = document.getElementById("start-container");
  const startButton = document.getElementById("start-quiz-btn");

  let timerInterval;
  let quizTime;
  let quizStarted = false;
  let currentQuestionIndex = 0;
  let userAnswers = {};
  let unansweredQuestions = [];
  let quizData = [];

  const fetchQuizData = async (quizId) => {
    try {
      const response = await fetch(`/quizzen/quiz/${quizId}/start`);
      if (!response.ok) {
        throw new Error(`Failed to fetch quiz data: ${response.statusText}`);
      }
      const data = await response.json();
      quizData = data.questions;
      quizTime = data.duration * 60;
    } catch (error) {
      showNotification(
        "There was an error fetching quiz data. Please try again later",
        "error"
      );
      console.error("Error fetching quiz data:", error);
    }
  };

  function startTimer(quizTime) {
    let timeRemaining = quizTime;
    timerInterval = setInterval(() => {
      const days = Math.floor(timeRemaining / (24 * 60 * 60));
      const hours = Math.floor((timeRemaining % (24 * 60 * 60)) / 3600);
      const minutes = Math.floor((timeRemaining % 3600) / 60);
      const seconds = timeRemaining % 60;

      let timeText = `${String(minutes).padStart(2, "0")}:${String(
        seconds
      ).padStart(2, "0")}`;

      if (hours > 0) {
        timeText = `${String(hours).padStart(2, "0")}:` + timeText;
      }

      if (days > 0) {
        timeText = `${String(days).padStart(2, "0")}d ` + timeText;
      }
      timerElement.textContent = `Time Left: ${timeText}`;
      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        if (quizStarted) {
          const modal = document.getElementById("timeup-quiz-overlay");
          modal.style.display = "flex";
        }
        submitQuiz();
      }
      timeRemaining--;
    }, 1000);
  }

  // Load Question
  const loadQuestion = (index) => {
    const question = quizData[index];
    const questionText = document.getElementById("question");
    const optionsContainer = document.getElementById("options-container");

    questionText.value = question.question_text;
    optionsContainer.innerHTML = "";

    if (question.question_type === "multiple_choice") {
      question.answer_choices.forEach((choice) => {
        const optionBox = document.createElement("div");
        optionBox.className = "option-box";

        const input = document.createElement("input");
        input.type = question.is_multiple_response ? "checkbox" : "radio";
        input.name = `answer-${question.id}`;
        input.value = choice.id;
        input.checked = userAnswers[question.id]?.includes(choice.id) || false;

        input.addEventListener("change", () => {
          if (question.is_multiple_response) {
            userAnswers[question.id] = input.checked
              ? [...(userAnswers[question.id] || []), choice.text]
              : userAnswers[question.id]?.filter((id) => id !== choice.text);
          } else {
            userAnswers[question.id] = [choice.text];
          }
          updateQuestionIndexPanel();
        });

        const optionText = document.createElement("input");
        optionText.type = "text";
        optionText.placeholder = "Answer option here";
        optionText.value = choice.text;
        optionText.readOnly = true;

        optionBox.addEventListener("click", () => {
          input.checked = !input.checked;
          input.dispatchEvent(new Event("change"));
        });

        input.addEventListener("click", (event) => event.stopPropagation());

        optionBox.appendChild(input);
        optionBox.appendChild(optionText);
        optionsContainer.appendChild(optionBox);
      });
    } else if (question.question_type === "short_answer") {
      const shortAnswerContainer = document.createElement("div");
      shortAnswerContainer.className = "short-answer-container";

      const overlayContainer = document.createElement("div");
      overlayContainer.className = "overlay-container";

      const shortAnswerInput = document.createElement("input");
      shortAnswerInput.type = "text";
      shortAnswerInput.className = "short-answer-input";
      shortAnswerInput.placeholder = "Type your answer here...";
      shortAnswerInput.value = userAnswers[question.id] || "";

      shortAnswerInput.addEventListener("input", () => {
        userAnswers[question.id] = shortAnswerInput.value;
        updateQuestionIndexPanel();
      });

      overlayContainer.appendChild(shortAnswerInput);
      shortAnswerContainer.appendChild(overlayContainer);

      optionsContainer.appendChild(shortAnswerContainer);
    }

    updateNavigationButtons();
    updateUnansweredQuestions();
  };

  const updateNavigationButtons = () => {
    previousButton.disabled = currentQuestionIndex === 0;
    nextButton.disabled = currentQuestionIndex === quizData.length - 1;
  };

  const updateQuestionIndexPanel = () => {
    questionIndexPanel.innerHTML = "";
    quizData.forEach((_, index) => {
      const button = document.createElement("button");
      button.textContent = index + 1;
      button.className = "question-index-button";

      if (userAnswers[quizData[index].id]) {
        button.classList.add("answered");
      } else {
        button.classList.remove("answered");
      }

      button.addEventListener("click", () => {
        currentQuestionIndex = index;
        loadQuestion(currentQuestionIndex);
      });

      questionIndexPanel.appendChild(button);
    });
  };

  const updateUnansweredQuestions = () => {
    unansweredQuestions = quizData
      .filter((question) => {
        const answer = userAnswers[question.id];
        return !answer || (Array.isArray(answer) && answer.length === 0);
      })
      .map((question) => question.id);
  };

  const handleSubmitButtonClick = () => {
    updateUnansweredQuestions();
    if (unansweredQuestions.length > 0) {
      const firstUnansweredQuestionId = unansweredQuestions[0];
      const firstUnansweredQuestionIndex = quizData.findIndex(
        (question) => question.id === firstUnansweredQuestionId
      );

      if (firstUnansweredQuestionIndex !== -1) {
        currentQuestionIndex = firstUnansweredQuestionIndex;
        loadQuestion(currentQuestionIndex);
      }
      showUnansweredModal();
    } else {
      submitQuiz();
    }
  };

  const showUnansweredModal = () => {
    const modal = document.getElementById("unanswered-modal");
    modal.style.display = "block";

    const confirmButton = document.getElementById("submit-quiz-btn");
    confirmButton.addEventListener("click", () => {
      modal.style.display = "none";
      submitQuiz();
    });

    const cancelButton = document.getElementById("cancel-submit-btn");
    cancelButton.addEventListener("click", () => {
      modal.style.display = "none";
    });
  };

  const loadStylesheet = (url) => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.type = "text/css";
    link.href = url;
    document.head.appendChild(link);
  };

  // Submit Quiz
  const submitQuiz = () => {
    clearInterval(timerInterval);
    submitButton.disabled = true;
    const loader = submitButton.querySelector(".loader");
    loader.style.display = "inline-block";

    const answers = Object.keys(userAnswers).map((questionId) => {
      return {
        question_id: questionId,
        user_answer: userAnswers[questionId],
      };
    });

    const payload = {
      answers: answers,
    };

    const baseurl = "https://emmanueldev247.publicvm.com/";
    fetch(`${baseurl}quizzen/quiz/${quizId}/submit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then((response) => {
        if (response.redirected) {
          window.location.href = response.url;
        } else if (!response.ok) {
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
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
      })
      .catch((error) => {
        if (error.message === "Failed to fetch")
          showNotification(
            "Network error. Please check your connection",
            "error"
          );
        else
          showNotification(
            "There was an error submitting the quiz. Please try again later",
            "error"
          );
        console.error("Error submitting quiz:", error);
      })
      .finally(() => {
        submitButton.disabled = false;
        loader.style.display = "none";
      });
  };

  previousButton.addEventListener("click", () => {
    if (currentQuestionIndex > 0) {
      currentQuestionIndex--;
      loadQuestion(currentQuestionIndex);
    }
  });

  nextButton.addEventListener("click", () => {
    if (currentQuestionIndex < quizData.length - 1) {
      currentQuestionIndex++;
      loadQuestion(currentQuestionIndex);
    }
  });

  submitButton.addEventListener("click", handleSubmitButtonClick);

  startButton.addEventListener("click", async () => {
    startButton.disabled = true;
    const loader = startButton.querySelector(".loader");
    loader.style.display = "inline-block";
    setTimeout(() => {
      startButton.disabled = false;
      loader.style.display = "none";
    }, 5000);

    await fetchQuizData(quizId);
    if (quizData.length === 0) {
      showNotification(
        "There was an error fetching quiz data. Please try again later",
        "error"
      );
      return;
    }
    loadQuestion(currentQuestionIndex);
    updateUnansweredQuestions();
    updateQuestionIndexPanel();
    startTimer(quizTime);
    quizStarted = true;
    startContainer.classList.add("hidden");
    quizContainer.classList.remove("hidden");
  });
});
