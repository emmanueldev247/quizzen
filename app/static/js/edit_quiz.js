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
  const addQuestionBtn = document.getElementById("add-question-btn");
  if (addQuestionBtn) {
    addQuestionBtn.addEventListener("click", () => {
      const quizID = addQuestionBtn.getAttribute("data-quiz-id");
      window.location.href = `/quizzen/quiz/${quizID}/question/new`;
    });
  }
});
