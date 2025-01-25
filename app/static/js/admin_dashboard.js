import { setActive } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  setActive(".nav-item:nth-child(2)", ".bottom-nav-item:nth-child(1)");

  const takeQuizButtons = document.querySelectorAll(".take-btn");

  takeQuizButtons.forEach((button) => {
    button.addEventListener("click", function () {
      button.disabled = true;
      const loader = button.querySelector(".loader");
      loader.style.display = "inline-block";
      setTimeout(() => {
        button.disabled = false;
        loader.style.display = "none";
      }, 5000);
      const quizCard = this.closest(".quiz-card");
      const quizId = quizCard.getAttribute("data-quiz-id");

      // window.location.href = `/quizzen/take/quiz/${quizId}`;
    });
  });
});
