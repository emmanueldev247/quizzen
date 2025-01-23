document.addEventListener("DOMContentLoaded", () => {
  const backToTopBtn = document.getElementById("backToTop");

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

  document.querySelectorAll(".quiz-card").forEach((card) => {
    card.addEventListener("click", () => {
      window.location.href = "/quizzen/signup";
    });
  });

  const submitButton = document.querySelector(".submit-contact");
 
  if (submitButton) {
    submitButton.addEventListener("click", () => {
      submitButton.disabled = true;
      const loader = submitButton.querySelector(".loader");
      loader.style.display = "inline-block";

      setTimeout(() => {
        submitButton.disabled = false;
        loader.style.display = "none";
      }, 2000)
    })
  }

});
