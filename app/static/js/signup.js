import {
  showNotification,
  showElements,
  togglePasswordVisibility,
} from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  // Get the elements
  const signupForm = document.getElementById("signup-form");
  const socialSignup = document.getElementById("social-signup");
  const loginLink = document.getElementById("login-link");
  const googleSignup = document.querySelector(".google-btn");

  function scrollToBottom() {
    const signupFormSub = document.querySelector(".signup-form-sub");
    signupFormSub.scrollTop = signupFormSub.scrollHeight - 10;
  }

  // Initialize by showing the signup form
  setTimeout(() => {
    showElements(signupForm, socialSignup, loginLink);
  }, 200);

  togglePasswordVisibility(".toggle-password", "#password", "#c_password");

  document
    .querySelector(".login-button")
    .addEventListener("click", () => (window.location.href = "/quizzen/login"));

  googleSignup.addEventListener("click", () => {
    googleSignup.disabled = true;
    const loader = googleSignup.querySelector(".loader-auth");
    loader.style.display = "inline-block";
    window.location.href = "/quizzen/auth/google";
    setTimeout(() => {
      googleSignup.disabled = false;
      loader.style.display = "none";
    }, 5000);
  });

  // Role icon select
  document.querySelectorAll(".role-option").forEach((option) => {
    option.addEventListener("click", function () {
      document.getElementById("role").value = this.dataset.role;
      document
        .querySelectorAll(".role-option")
        .forEach((opt) => opt.classList.remove("selected"));
      this.classList.add("selected");
    });
  });

  // paginated registration page buttons
  const contBtnEmail = document.getElementById("continue-button-email");
  const contBtnNames = document.getElementById("continue-button-names");
  const contBtnRole = document.getElementById("continue-button-role");
  const submitBtn = document.getElementById("submit-button");

  const firstNameDiv = document.getElementById("first-name-container");
  const roleDiv = document.getElementById("role-container");
  const passwordDiv = document.getElementById("password-container");

  contBtnEmail.addEventListener("click", () => {
    const email = document.getElementById("email").value;
    const emailError = document.getElementById("email-error");

    if (!email) {
      emailError.textContent = "Please enter your email address";
      emailError.style.display = "block";
      return;
    }
    emailError.style.display =
      contBtnEmail.style.display =
      socialSignup.style.display =
        "none";
    firstNameDiv.style.display = "block";
    scrollToBottom();
  });

  contBtnNames.addEventListener("click", () => {
    const firstName = document.getElementById("first_name").value;
    const lastName = document.getElementById("last_name").value;
    const firstNameError = document.getElementById("first-name-error");
    const lastNameError = document.getElementById("last-name-error");
    firstNameError.style.display = lastNameError.style.display = "none";

    if (!firstName) {
      firstNameError.textContent = "Please enter your first name";
      firstNameError.style.display = "block";
      return;
    }

    if (!lastName) {
      lastNameError.textContent = "Please enter your last name";
      lastNameError.style.display = "block";
      return;
    }

    if (firstName && lastName) {
      contBtnNames.style.display = "none";
      roleDiv.style.display = "block";
      scrollToBottom();
    }
  });

  contBtnRole.addEventListener("click", () => {
    const role = document.getElementById("role").value;
    const roleError = document.getElementById("role-error");
    roleError.style.display = "none";

    if (!role) {
      roleError.textContent = "Please select what best describes you";
      roleError.style.display = "block";
      return;
    }
    contBtnRole.style.display = "none";
    // roleDiv.style.display = "none";
    passwordDiv.style.display = "block";
    scrollToBottom();
  });

  submitBtn.addEventListener("click", (event) => {
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("c_password").value;
    const passwordError = document.getElementById("password-error");
    const cPasswordError = document.getElementById("c_password-error");
    const cPasswordError2 = document.getElementById("c_password-error2");
    const passwordStrengthError = document.getElementById(
      "password-strength-error"
    );

    const passwordStrengthRegex =
      /^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*()_\-+={}[\]|:;"'<>,.?/~`\\])[A-Za-z\d !@#$%^&*()_\-+={}[\]|:;"'<>,.?/~`\\]{8,}$/;

    // Reset error displays
    passwordError.style.display = passwordStrengthError.style.display = "none";
    cPasswordError2.style.display = cPasswordError.style.display = "none";

    if (!password) {
      passwordError.textContent = "Password is required";
      passwordError.style.display = "block";
      event.preventDefault();
      return;
    }

    if (!passwordStrengthRegex.test(password)) {
      passwordStrengthError.textContent =
        "Password must be at least 8 characters long and include letters, numbers, and a special character";
      passwordStrengthError.style.display = "block";
      event.preventDefault();
      return;
    }

    if (!confirmPassword) {
      cPasswordError.textContent = "Please confirm your password";
      cPasswordError.style.display = "block";
      event.preventDefault();
      return;
    }

    if (password !== confirmPassword) {
      cPasswordError2.textContent = "Passwords do not match!";
      cPasswordError2.style.display = "block";
      event.preventDefault();
      return;
    }

    passwordError.style.display = passwordStrengthError.style.display = "none";
    cPasswordError2.style.display = cPasswordError.style.display = "none";
  });

  signupForm.addEventListener("submit", function (event) {
    event.preventDefault();

    submitBtn.disabled = true;
    const loader = submitBtn.querySelector(".loader");
    loader.style.display = "inline-block";

    const formData = new FormData(this);

    // Send POST request to backend
    fetch("/quizzen/signup", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          if (response.status === 400) {
            showNotification(
              "An account already exists for this email. Please use the button above to log in or register another email",
              "error"
            );
          } else if (response.status === 429) {
            showNotification(
              "You have made too many requests in a short period. Please try again later",
              "error"
            );
          } else {
            showNotification(
              "Something went wrong. Please try again later",
              "error"
            );
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          showNotification(
            "Registration successful! You can now log in",
            "success"
          );
          setTimeout(() => {
            window.location.href = "/quizzen/login";
          }, 3000);
        }
      })
      .catch((error) => {
        if (error.message === "Failed to fetch")
          showNotification(
            "Network error. Please check your connection",
            "error"
          );
      })
      .finally(() => {
        submitBtn.disabled = false;
        loader.style.display = "none";
      });
  });
});
