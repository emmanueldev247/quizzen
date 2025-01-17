import {
  showNotification,
  showElements,
  togglePasswordVisibility,
} from "./utils.js";

// Get the elements
const signupForm = document.getElementById("signup-form");
const socialSignup = document.getElementById("social-signup");
const loginLink = document.getElementById("login-link");

// Initialize by showing the signup form
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    showElements(signupForm, socialSignup, loginLink);
  }, 200);
});

togglePasswordVisibility("#password", "#c_password");

// Gender icon select
document.querySelectorAll(".gender-option").forEach((option) => {
  option.addEventListener("click", function () {
    document.getElementById("gender").value = this.dataset.gender;
    document
      .querySelectorAll(".gender-option")
      .forEach((opt) => opt.classList.remove("selected"));
    this.classList.add("selected");
  });
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
const contBtnGender = document.getElementById("continue-button-gender");
const contBtnRole = document.getElementById("continue-button-role");
const contBtnDob = document.getElementById("continue-button-dob");
const submitBtn = document.getElementById("submit-button");

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
  document.getElementById("first-name-container").style.display = "block";
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
    document.getElementById("gender-container").style.display = "block";
  }
});

contBtnGender.addEventListener("click", () => {
  const gender = document.getElementById("gender").value;
  const genderError = document.getElementById("gender-error");
  genderError.style.display = "none";

  if (!gender) {
    genderError.textContent = "Please select your gender";
    genderError.style.display = "block";
    return;
  }
  contBtnGender.style.display = "none";
  document.getElementById("gender-container").style.display = "none";
  document.getElementById("role-container").style.display = "block";
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
  document.getElementById("role-container").style.display = "none";
  document.getElementById("dob-container").style.display = "block";
});

contBtnDob.addEventListener("click", () => {
  const dob = document.getElementById("date_of_birth").value;
  const dobError = document.getElementById("dob-error");
  dobError.style.display = "none";

  if (!dob) {
    dobError.textContent = "Please enter your date of birth";
    dobError.style.display = "block";
    return;
  }
  contBtnDob.style.display = "none";
  document.getElementById("password-container").style.display = "block";
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

  submitBtn.textContent = "Registering...";
  submitBtn.disabled = true;

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
      submitBtn.textContent = "Register";
      submitBtn.disabled = false;
    });
});
