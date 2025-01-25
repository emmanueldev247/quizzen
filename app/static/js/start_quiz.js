document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const quizContainer = document.getElementById("quiz-container");
  const timerElement = document.getElementById("timer");
  const questionBox = document.getElementById("question-box");
  const questionIndexPanel = document.getElementById("question-index");
  const previousButton = document.getElementById("prev-btn");
  const nextButton = document.getElementById("next-btn");
  const submitButton = document.getElementById("submit-btn");
  const quizId = quizContainer.getAttribute("data-quiz-id");
  const startContainer = document.getElementById("start-container");
  const startButton = document.getElementById("start-quiz-btn");

  let duration = 0;
  let timer;
  let quizTime;
  let timerInterval;
  let currentQuestionIndex = 0;
  let userAnswers = {};
  let quizData = [];
  let quizTitle = "";

  const fetchQuizData = async (quizId) => {
    try {
      const response = await fetch(`/quizzen/quiz/${quizId}/start`);
      if (!response.ok) {
        throw new Error(`Failed to fetch quiz data: ${response.statusText}`);
      }
      const data = await response.json();
      console.log(data);
      quizData = data.questions;
      quizTime = data.duration * 60;
      quizTitle = data.title;
      console.log("Quiz data fetched successfully:", quizData);
    } catch (error) {
      console.error("Error fetching quiz data:", error);
    }
  };

  function startTimer(quizTime) {
    let timeRemaining = quizTime;
    timerInterval = setInterval(() => {
      const minutes = Math.floor(timeRemaining / 60);
      const seconds = timeRemaining % 60;
      timerElement.textContent = `${String(minutes).padStart(2, "0")}:${String(
        seconds
      ).padStart(2, "0")}`;
      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
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
              ? [...(userAnswers[question.id] || []), choice.id]
              : userAnswers[question.id]?.filter((id) => id !== choice.id);
          } else {
            userAnswers[question.id] = [choice.id];
          }
          updateQuestionIndexPanel();
        });

        const optionText = document.createElement("input");
        optionText.type = "text";
        optionText.placeholder = "Answer option here";
        optionText.value = choice.text;
        optionText.readOnly = true;

        // Add click event to the option box
        optionBox.addEventListener("click", () => {
          input.checked = !input.checked;
          input.dispatchEvent(new Event("change"));
        });

        // Stop the click event on the input to prevent double toggling
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
  };

  const updateNavigationButtons = () => {
    previousButton.disabled = currentQuestionIndex === 0;
    nextButton.disabled = currentQuestionIndex === quizData.length - 1;
  };

  // Update Question Index Panel
  const updateQuestionIndexPanel = () => {
    questionIndexPanel.innerHTML = "";
    quizData.forEach((_, index) => {
      const button = document.createElement("button");
      button.textContent = index + 1;
      button.className = "question-index-button";

      // Highlight answered questions
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

  // Navigation Logic
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

  submitButton.addEventListener("click", () => {
    submitQuiz();
  });

  // Submit Quiz
  const submitQuiz = () => {
    clearInterval(timerInterval);
    console.log("Quiz Submitted!", userAnswers);
    alert("Quiz submitted. Check the console for your answers!");
  };

  // Initial Load// Start button click event
  startButton.addEventListener("click", async () => {
    await fetchQuizData(quizId);
    if (quizData.length === 0) {
      alert("Failed to load quiz data.");
      return;
    }
    startContainer.classList.add("hidden");
    quizContainer.classList.remove("hidden");
    loadQuestion(currentQuestionIndex);
    startTimer(quizTime);
    updateQuestionIndexPanel();
  });
});
