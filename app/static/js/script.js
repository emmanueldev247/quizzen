document.addEventListener("DOMContentLoaded", () => {
  const backToTopBtn = document.getElementById("backToTop");

  if (backToTopBtn) {
    backToTopBtn.addEventListener("click", () => {
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    });

    window.addEventListener("scroll", () => {
      if (window.scrollY > 300) {
        backToTopBtn.classList.add("show");
      } else {
        backToTopBtn.classList.remove("show");
      }
    });
  }

  document.querySelectorAll(".index-quiz-card").forEach((card) => {
    card.addEventListener("click", () => {
      window.location.href = "/quizzen/signup";
    });
  });

  const contactForm = document.querySelector(".contact-us-form-class");
  if (contactForm) {
    contactForm.addEventListener("submit", () => {
      const submitButton = document.querySelector(".submit-contact");

      submitButton.disabled = true;
      const loader = submitButton.querySelector(".loader");
      loader.style.display = "inline-block";

      setTimeout(() => {
        submitButton.disabled = false;
        loader.style.display = "none";
      }, 2000);
    });
  }

  const modal = document.getElementById("enter-code-modal");
  const closeBtn = document.getElementById("closeBtn");
  const quizCodeInput = document.getElementById("quizCode");
  const submitBtn = document.getElementById("enterCodeSubmitBtn");
  const modalError = document.getElementById("error-code");
  const enterCodeBtn = document.querySelectorAll(".enter-code");

  if (enterCodeBtn) {
    enterCodeBtn.forEach((card) => {
      card.onclick = () => {
        modal.style.display = "flex";
      };
    });

    closeBtn.onclick = () => {
      modal.style.display = "none";
    };

    window.onclick = (event) => {
      if (event.target === modal) {
        modal.style.display = "none";
      }
    };

    submitBtn.onclick = handleSubmit;
    quizCodeInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        handleSubmit();
      }
    });
  }

  function handleSubmit() {
    const quizCode = quizCodeInput.value.trim();

    if (quizCode) {
      submitBtn.disabled = true;
      const loader = submitBtn.querySelector(".loader");
      loader.style.display = "inline-block";
      const baseUrl = `https://emmanueldev247.publicvm.com/quizzen`;

      fetch(`${baseUrl}/api/quiz/${quizCode}`)
        .then((response) => {
          if (!response.ok) {
            showNotification(
              "Invalid quiz code. Please check and try again",
              "error"
            );
            throw new Error("Invalid quiz code. Please check and try again.");
          }
          return response.json();
        })
        .then((data) => {
          if (data.success) {
            window.location.href = `${baseUrl}/take/quiz/${data.quiz_id}`;
            modal.style.display = "none";
            quizCodeInput.value = "";
            quizCodeInput.classList.remove("error");
            modalError.style.display = "none";
          } else
            showNotification(
              "Invalid quiz code. Please check and try again",
              "error"
            );
        })
        .catch((error) => {
          console.error("Error:", error);
          quizCodeInput.classList.add("error");
          modalError.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> Please enter a valid quiz code!`;
          modalError.style.display = "inline-block";
        })
        .finally(() => {
          submitBtn.disabled = false;
          loader.style.display = "none";
        });
    } else {
      quizCodeInput.classList.add("error");
      modalError.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> Please enter a valid quiz code!`;
      modalError.style.display = "inline-block";
      return;
    }
  }
});
