import { showNotification } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.querySelector(".three-dots");
  const menuContent = document.querySelector(".menu-content");
  const saveButtons = document.querySelectorAll(".publish-btn");
  const questionTypeSelect = document.getElementById("question-type");
  const optionsContainer = document.getElementById("options-container");
  const toggleMultResponse = document.querySelector(
    ".toggle-multiple-response"
  );
  const toggleAltResponse = document.querySelector(
    ".toggle-alternative-response"
  );
  const multipleResponseCheckbox = document.getElementById("multiple-response");
  const alternativeResponseCheckbox = document.getElementById(
    "alternative-response"
  );
  const altResponseToggle = document.getElementById("alternative-response");

  const multChoiceOptions = `
          <div class="option-box">
              <i class="fas fa-trash delete-option" title="Delete answer option"></i>
              <input type="radio" name="option" tabindex="-1" tabindex="-1"
                  title="Mark as correct">
              <input type="text" name="option" placeholder="Type answer option here">
          </div>
          <div class="option-box">
              <i class="fas fa-trash delete-option" title="Delete answer option"></i>
              <input type="radio" name="option" tabindex="-1" tabindex="-1"
                  title="Mark as correct">
              <input type="text" name="option" placeholder="Type answer option here">
          </div>
          <div class="option-box">
              <i class="fas fa-trash delete-option" title="Delete answer option"></i>
              <input type="radio" name="option" tabindex="-1" tabindex="-1"
                  title="Mark as correct">
              <input type="text" name="option" placeholder="Type answer option here">
          </div>
          <div class="option-box">
              <i class="fas fa-trash delete-option" title="Delete answer option"></i>
              <input type="radio"  name="option" tabindex="-1" tabindex="-1"
                  title="Mark as correct">
              <input type="text"  name="option" placeholder="Type answer option here">
          </div>
          <i class="fas fa-plus add-option" title="Add another option"></i>
      `;

  const shortAnswerOptions = `
          <div class="short-answer-container">
              <div class="overlay-container">
                  <input type="text" class="short-answer-input" name="short-answer-input"
                      placeholder="Type answer here">
              </div>
              <div class="alternative-answer" style="display: none;">
                  <p>Alternative Options
                  </p>
                  <div class="alternative-answer-content">
                      <div class="alternative-answer-box">
                          <input type="text" class="short-answer-input" name="alternative-short-answer-input"
                              placeholder="Type alternative answer here">
                          <i class="fas fa-trash delete-option-sa" title="Delete alternative answer"></i>
                      </div>
                      <div class="add-option-container add-option-sa">
                          <i class="fas fa-plus" title="Add an alternative answer"></i>
                          Add alternative answer
                      </div>
                  </div>
              </div>
          </div>
          `;

  // Function to update the visibility of icons
  function updateIcons() {
    const optionBoxes = optionsContainer.querySelectorAll(".option-box");
    const addIcon = optionsContainer.querySelector(".add-option");
    const deleteIcons = optionsContainer.querySelectorAll(".delete-option");

    addIcon.style.display = optionBoxes.length < 5 ? "inline-block" : "none";

    deleteIcons.forEach((icon) => {
      icon.style.display = optionBoxes.length > 2 ? "inline-block" : "none";
    });
  }

  function addOption() {
    const addIcon = optionsContainer.querySelector(".add-option");

    const currentOptions =
      optionsContainer.querySelectorAll(".option-box").length;

    if (currentOptions < 5) {
      const newOption = document.createElement("div");
      newOption.classList.add("option-box");

      newOption.innerHTML = `
              <i class="fas fa-trash delete-option" title="Delete answer option"></i>
              <input type="radio" name="option" tabindex="-1">
              <input type="text" name="option${
                currentOptions + 1
              }" placeholder="Type answer option here">
          `;

      optionsContainer.insertBefore(newOption, addIcon);
      updateIcons();
    }
  }

  function deleteOption(event) {
    if (optionsContainer.querySelectorAll(".option-box").length > 2) {
      event.target.closest(".option-box").remove();
      updateIcons();
    }
  }

  function scrollToBottom() {
    const altAnswerContent = document.querySelector(
      ".alternative-answer-content"
    );
    altAnswerContent.scrollTop = altAnswerContent.scrollHeight;
  }

  function addAltAnswer() {
    const altAnswerContainer = document.querySelector(
      ".alternative-answer-content"
    );
    const newAltAnswerBox = document.createElement("div");
    newAltAnswerBox.classList.add("alternative-answer-box");
    newAltAnswerBox.innerHTML = `
                  <input type="text" class="short-answer-input" placeholder="Type alternative answer here">
                  <i class="fas fa-trash delete-option-sa" title="Delete alternative answer"></i>
              `;
    altAnswerContainer.insertBefore(
      newAltAnswerBox,
      altAnswerContainer.querySelector(".add-option-container")
    );
    scrollToBottom();
  }

  function deleteAltAnswer(e) {
    const altAnswerContainer = document.querySelector(
      ".alternative-answer-content"
    );
    const altAnswerContent = document.querySelector(".alternative-answer");

    if (e.target.classList.contains("delete-option-sa")) {
      const remainingAltAnswers = altAnswerContainer.querySelectorAll(
        ".alternative-answer-box"
      );
      const altAnswerBox = e.target.closest(".alternative-answer-box");
      altAnswerBox.remove();
      if (remainingAltAnswers.length === 1) {
        altResponseToggle.checked = false;
        altAnswerContent.style.display = "none";
        addAltAnswer();
        return;
      }
    }
  }

  function updateQuestionType() {
    if (questionTypeSelect.value === "short_answer") {
      optionsContainer.innerHTML = shortAnswerOptions;
      toggleAltResponse.style.display = "flex";
      toggleMultResponse.style.display = "none";

      alternativeResponseCheckbox.removeEventListener(
        "change",
        handleAltAnswerToggle
      );
      alternativeResponseCheckbox.addEventListener(
        "change",
        handleAltAnswerToggle
      );
    } else {
      optionsContainer.innerHTML = multChoiceOptions;
      toggleAltResponse.style.display = "none";
      toggleMultResponse.style.display = "flex";

      multipleResponseCheckbox.removeEventListener(
        "change",
        handleMultipleResponseChange
      );

      multipleResponseCheckbox.addEventListener(
        "change",
        handleMultipleResponseChange
      );

      updateIcons();
    }
  }

  // Handle option's multi-response type change
  function handleMultipleResponseChange() {
    const inputType = multipleResponseCheckbox.checked ? "checkbox" : "radio";
    optionsContainer
      .querySelectorAll(
        ".option-box input[type=radio], .option-box input[type=checkbox]"
      )
      .forEach((input) => {
        input.type = inputType;
        input.name = inputType === "radio" ? "option" : "options[]";
      });
  }

  // handle short answer alternative answers toggle
  function handleAltAnswerToggle() {
    const altAnswerContent = document.querySelector(".alternative-answer");

    if (altResponseToggle.checked) {
      altAnswerContent.style.display = "flex";
    } else {
      altAnswerContent.style.display = "none";
    }
  }

  document.querySelector(".btn-back").addEventListener("click", () => {
    window.location.href = window.location.href.split("/question/")[0];
  });

  // initializing
  updateQuestionType();
  questionTypeSelect.addEventListener("change", updateQuestionType);

  // Add event listeners for plus and delete icons
  optionsContainer.addEventListener("click", (event) => {
    if (event.target.classList.contains("add-option")) {
      addOption();
    } else if (event.target.classList.contains("delete-option")) {
      deleteOption(event);
    } else if (event.target.classList.contains("add-option-sa")) {
      addAltAnswer();
    } else if (event.target.classList.contains("delete-option-sa")) {
      deleteAltAnswer(event);
    }
  });

  // Handle point-select changes
  document.addEventListener("change", (event) => {
    if (event.target.classList.contains("point-select")) {
      const select = event.target;
      const customInput = select.previousElementSibling;

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
        const select = input.nextElementSibling;
        let customValue = input.value.trim();
        if (customValue && !isNaN(customValue)) {
          customValue = Math.min(customValue, 100);

          let existingOption = [...select.options].find(
            (option) => option.value === customValue.toString()
          );

          if (!existingOption) {
            const customOption = new Option(
              `${customValue} Points`,
              customValue,
              true,
              true
            );

            select.add(customOption);
            select.value = customValue;
          } else {
            select.value = existingOption.value;
          }

          input.style.display = "none";
          input.value = "";

          input.blur();
        }
      }
    }
  });

  // responsive menu display
  document.addEventListener("click", (event) => {
    if (
      menuContent.classList.contains("visible") &&
      !menuContent.contains(event.target) &&
      !menuToggle.contains(event.target)
    ) {
      menuContent.classList.remove("visible");
    }
  });

  menuToggle.addEventListener("click", () => {
    menuContent.classList.toggle("visible");
  });

  // Validation logic
  function validateForm() {
    const questionText = document.getElementById("question").value.trim();
    const selectElement = document.getElementById("question-type");
    const selectedOption = selectElement.options[selectElement.selectedIndex];

    const questionType = selectedOption.value;

    const errorMessages = [];

    if (!questionText) {
      errorMessages.push("Please enter a question");
    }

    if (questionType === "multiple_choice") {
      // Validate multiple-choice options
      const options = document.querySelectorAll(".option-box");
      const hasCorrectAnswer = Array.from(options).some((box) => {
        const radioChecked = box.querySelector('input[type="radio"]:checked');
        const checkboxChecked = box.querySelector(
          'input[type="checkbox"]:checked'
        );
        return radioChecked || checkboxChecked;
      });

      options.forEach((box, index) => {
        const optionText = box.querySelector('input[type="text"]').value.trim();
        if (!optionText) {
          errorMessages.push(`Option ${index + 1} must not be empty.`);
        }
      });

      if (!hasCorrectAnswer) {
        errorMessages.push("Please select a correct answer");
      }
    } else if (questionType === "short_answer") {
      // Validate short-answer options
      const shortAnswerInput = document
        .querySelector(".short-answer-input")
        .value.trim();
      const alternativeAnswers = document.querySelectorAll(
        '.alternative-answer-box input[type="text"]'
      );
      const hasAlternativeAnswers = Array.from(alternativeAnswers).some(
        (input) => input.value.trim() !== ""
      );

      if (!shortAnswerInput && !hasAlternativeAnswers) {
        errorMessages.push("Please add the correct answer");
      }
    } else {
      errorMessages.push("Question type is not selected.");
    }

    return errorMessages;
  }

  // Display validation errors as a tooltip
  function displayErrors(button, errors) {
    if (errors.length > 0) {
      button.setAttribute("data-tooltip", errors[0]);
      button.disabled = true;
    } else {
      button.removeAttribute("data-tooltip");
    }
    button.disabled = false;
  }

  // Add click listeners to the save buttons
  saveButtons.forEach((button) => {
    button.addEventListener("click", (e) => {
      e.preventDefault();
      const errors = validateForm();

      if (errors.length > 0) {
        displayErrors(button, errors);
      } else {
        button.removeAttribute("data-tooltip");
        processSubmission(); // Submit data using AJAX
      }
    });

    // Add hover/focus listeners to display validation errors
    button.addEventListener("mouseenter", () =>
      displayErrors(button, validateForm())
    );
    button.addEventListener("focus", () =>
      displayErrors(button, validateForm())
    );
    button.addEventListener("blur", () =>
      displayErrors(button, validateForm())
    );
  });

  // Process form submission using AJAX
  function processSubmission() {
    const questionText = document.getElementById("question").value.trim();
    const selectElement = document.getElementById("question-type");
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const questionType = selectedOption.value;
    const isMultipleResponse =
      document.getElementById("multiple-response")?.checked || false;
    const points =
      parseInt(document.getElementById("point-select").value.trim(), 10) || 1;
    const method = document.querySelector('input[name="_method"]').value;

    console.log(method);
    const options = [];
    if (questionType === "multiple_choice") {
      const optionBoxes = document.querySelectorAll(".option-box");
      optionBoxes.forEach((box) => {
        const optionText = box.querySelector('input[type="text"]').value.trim();
        const isCorrect =
          box.querySelector('input[type="radio"]:checked') ||
          box.querySelector('input[type="checkbox"]:checked')
            ? true
            : false;

        if (optionText) {
          options.push({ text: optionText, isCorrect });
        }
      });
    } else if (questionType === "short_answer") {
      const shortAnswerInput = document
        .querySelector(".short-answer-input")
        .value.trim();
      const alternativeAnswers = document.querySelectorAll(
        '.alternative-answer-box input[type="text"]'
      );
      const alternatives = Array.from(alternativeAnswers)
        .map((input) => input.value.trim())
        .filter((val) => val);

      if (shortAnswerInput) {
        options.push({ text: shortAnswerInput, isCorrect: true });
      }
      alternatives.forEach((alt) => {
        options.push({ text: alt, isCorrect: true });
      });
    }

    const payload = {
      question: questionText,
      questionType,
      is_multiple_response: isMultipleResponse,
      points: points,
      options: options,
    };

    fetch(window.location.href, {
      method: method,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then((response) => {
        if (response.redirected) window.location.href = response.url;
        else response.json();
      })
      .then((data) => {
        showNotification("Question saved successfully", "success")
      })
      .catch((error) => {
      });
  }
});
