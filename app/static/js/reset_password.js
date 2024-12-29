import {
  showNotification,
  showElements,
  togglePasswordVisibility,
} from "./utils.js";

// Get the elements
const resetPasswordForm = document.getElementById("reset-password-form");
const submitBtn = document.getElementById("submit-button");

document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    showElements(resetPasswordForm);
  }, 200);
});

togglePasswordVisibility("#new-password", "#c_password");

submitBtn.addEventListener("click", (event) => {
  const password = document.getElementById("new-password").value;
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
  passwordError.style.display = "none";
  cPasswordError.style.display = "none";
  cPasswordError2.style.display = "none";
  passwordStrengthError.style.display = "none";

  passwordError.textContent = "Password is required";
  cPasswordError.textContent = "Please confirm your password";
  cPasswordError2.textContent = "Passwords do not match!";
  passwordStrengthError.textContent =
    "Password must be at least 8 characters long and include letters, numbers and a special character.";

  if (!password) {
    passwordError.style.display = "block";
    event.preventDefault();
    return;
  }

  if (!passwordStrengthRegex.test(password)) {
    passwordStrengthError.style.display = "block";
    event.preventDefault();
    return;
  }

  if (!confirmPassword) {
    cPasswordError.style.display = "block";
    event.preventDefault();
    return;
  }

  if (password !== confirmPassword) {
    cPasswordError2.style.display = "block";
    event.preventDefault();
    return;
  }

  passwordError.style.display = cPasswordError.style.display = "none";
  cPasswordError2.style.display = passwordStrengthError.style.display = "none";
});

resetPasswordForm.addEventListener("submit", function (event) {
  event.preventDefault();

  const newPassword = document.getElementById("new-password").value;
  const token = window.location.pathname.split("/").pop();

  submitBtn.textContent = "Resetting password...";
  submitBtn.disabled = true;

  // Send POST request to backend
  fetch(`/quizzen/reset_password/${token}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: newPassword }),
  })
    .then((response) => {
      if (!response.ok) {
        if (response.status === 422) {
          showNotification("Password cannot be empty", "error");
        } else if (response.status === 400) {
          showNotification(
            "Invalid Link, please request a new reset link",
            "error"
          );
        } else {
          showNotification(
            "Something went wrong. Please try again later.",
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
          "Password successfully reset. You can now login",
          "success"
        );
        setTimeout(() => {
          window.location.href = "/quizzen/login";
        }, 2500);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      if (error.message === "Failed to fetch")
        showNotification(
          "Network error. Please check your connection.",
          "error"
        );
    })
    .finally(() => {
      submitBtn.textContent = "Reset Password";
      submitBtn.disabled = false;
    });
});
