import { showNotification } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const retakeButton = document.getElementById("retakeQuiz");
  const goHomeButton = document.getElementById("goHome");

  retakeButton.addEventListener("click", () => {
    const resultContainer = document.querySelector(".result-container");
    const quizId = resultContainer.getAttribute("data-quiz-id");
    const loader = retakeButton.querySelector(".loader");
    retakeButton.disabled = true;
    loader.style.display = "inline-block";

    if (quizId) {
      const baseUrl = "https://emmanueldev247.publicvm.com/quizzen/take/quiz/";
      const newUrl = `${baseUrl}${quizId}`;

      window.location.href = newUrl;
    } else {
      window.addEventListener("popstate", () => {
        location.reload();
      });
      window.history.back();
    }

    setTimeout(() => {
      retakeButton.disabled = false;
      loader.style.display = "none";
    }, 3000);
  });

  goHomeButton.addEventListener("click", () => {
    const loader = goHomeButton.querySelector(".loader");
    goHomeButton.disabled = true;
    loader.style.display = "inline-block";

    const homeUrl = "https://emmanueldev247.publicvm.com/quizzen/dashboard";
    window.location.href = homeUrl;

    setTimeout(() => {
      goHomeButton.disabled = false;
      loader.style.display = "none";
    }, 3000);
  });
});
