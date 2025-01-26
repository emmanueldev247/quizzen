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
      console.log("Quiz data fetched successfully:", quizData);
    } catch (error) {
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

    console.log("Quiz Submitted!", userAnswers);
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
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const contentType = response.headers.get("Content-Type") || "";
        console.log(contentType);
        if (contentType.includes("text/html")) {
          // Redirect to the URL if it’s an HTML response
          window.location.href = response.url; // Redirects the user to the result page
        } else if (contentType.includes("application/json")) {
          // Handle JSON response if applicable
          return response.json();
        } else {
          throw new Error("Unexpected content type");
        }
      })
      .then((data) => {
        if (data.score !== undefined) {
          const {
            score,
            max_score,
            total_questions,
            correct_count,
            wrong_count,
          } = data;
          if (score / max_score >= 0.5) {
            const successBoxes = document.querySelectorAll(".successScore");
            successBoxes.forEach((box) => (box.textContent = score));
            const maxBoxes = document.querySelectorAll(".successMaxScore");
            maxBoxes.forEach((box) => (box.textContent = max_score));
            const totalQuestions = document.querySelectorAll(".successTotal");
            totalQuestions.forEach(
              (box) => (box.textContent = total_questions)
            );
            const successCorrect = document.querySelectorAll(".successCorrect");
            successCorrect.forEach((box) => (box.textContent = correct_count));
            const successWrong = document.querySelectorAll(".successWrong");
            successWrong.forEach((box) => (box.textContent = wrong_count));

            document.getElementById("successResult").style.display = "block";
          } else {
            // Failure: Handle failure result display
            const failureBoxes = document.querySelectorAll(".failureScore");
            failureBoxes.forEach((box) => (box.textContent = score));
            const maxBoxes = document.querySelectorAll(".failureMaxScore");
            maxBoxes.forEach((box) => (box.textContent = max_score));
            const totalQuestions = document.querySelectorAll(".failureTotal");
            totalQuestions.forEach(
              (box) => (box.textContent = total_questions)
            );
            const failureCorrect = document.querySelectorAll(".failureCorrect");
            failureCorrect.forEach((box) => (box.textContent = correct_count));
            const failureWrong = document.querySelectorAll(".failureWrong");
            failureWrong.forEach((box) => (box.textContent = wrong_count));

            document.getElementById("failureResult").style.display = "block";
          }
          loadStylesheet("/quizzen/assets/css/quiz-result.css");

          const modalUnanswered = document.getElementById("unanswered-modal");
          const modalTimeup = document.getElementById("timeup-quiz-overlay");
          modalUnanswered.style.display = modalTimeup.style.display = "none";
          quizContainer.style.display = "none";
          startContainer.classList.add("hidden");
          quizContainer.classList.add("hidden");
          modalUnanswered.classList.add("hidden");
          modalTimeup.classList.add("hidden");
        } else {
          showNotification(`Error: ${data.error}`, "error");
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
            "There was an error submitting the quiz. Please try again",
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
      alert("Failed to load quiz data.");
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
