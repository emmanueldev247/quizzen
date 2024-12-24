// show/hide password icon toggle
document.querySelectorAll(".toggle-password").forEach((icon) => {
  icon.addEventListener("click", function () {
    const passwordField = document.getElementById("password");

    // Check the current state of password visibility
    if (passwordField.type === "password") {
      passwordField.type = "text";

      this.classList.remove("fa-eye");
      this.classList.add("fa-eye-slash");
      this.setAttribute("title", "Hide password");
    } else {
      passwordField.type = "password";

      this.classList.remove("fa-eye-slash");
      this.classList.add("fa-eye");
      this.setAttribute("title", "Show password");
    }
  });
});

// animated entry
// Get the elements
const loginForm = document.getElementById("login-form");
const resetPasswordForm = document.getElementById("reset-password-form");
const socialLogin = document.getElementById("social-login");
const signupLink = document.getElementById("signup-link");
const forgotPasswordLink = document.getElementById("forgot-password");
const backToLoginLink = document.getElementById("back-to-login");

const resetPasswordElements = Array.from(
  resetPasswordForm.querySelectorAll("h2, p, input, button, a")
);
const loginFormElements = Array.from(
  loginForm.querySelectorAll("h2, input, button, a")
);

// Function to animate elements
function animateElements(elements) {
  elements.forEach((el, index) => {
    el.classList.remove("animate-slide-in", `animate-delay-${index + 1}`); // Reset animation classes
    void el.offsetWidth; // Trigger reflow to restart animation
    el.classList.add("animate-slide-in", `animate-delay-${index + 1}`);
  });
}

// Function to show the login form
function showLoginForm() {
  loginForm.classList.add("visible");
  resetPasswordForm.classList.remove("visible");
  socialLogin.classList.add("visible");
  signupLink.classList.add("visible");
}

// Function to show the reset password form
function showResetPasswordForm() {
  loginForm.classList.remove("visible");
  resetPasswordForm.classList.add("visible");
  socialLogin.classList.remove("visible");
  signupLink.classList.remove("visible");
}

// Event listeners for toggling views
forgotPasswordLink.addEventListener("click", function () {
  loginForm.style.display = socialLogin.style.display = "none";
  resetPasswordForm.style.display = "block";
  animateElements(resetPasswordElements);
  showResetPasswordForm();
});

backToLoginLink.addEventListener("click", () => {
  resetPasswordForm.style.display = "none";
  loginForm.style.display = "flex";
  socialLogin.style.display = "block";
  animateElements(loginFormElements);
  showLoginForm();
});

// Initialize by showing the login form
document.addEventListener("DOMContentLoaded", function () {
  setTimeout(() => {
    showLoginForm();
  }, 200);
});

loginForm.addEventListener("submit", function (event) {
  event.preventDefault();

  loginButton = document.getElementById("login-button");
  loginButton.disabled = true;

  const formData = new FormData(this);

  fetch("/quizzen/login", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        if (response.status === 401)
          showNotification("Invalid Credentials", "error");
        else
          showNotification(
            "Something went wrong. Please try again later.",
            "error"
          );
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        window.location.href = "/quizzen/dashboard";
      }
    })
    .catch((error) => {
      console.log(`Error: ${error}`);
    })
    .finally(() => {
      loginButton.disabled = false;
    });
});

function showNotification(message, type) {
  const notification = document.getElementById("notification");
  notification.textContent = message;
  notification.className = `notification ${type}`;
  notification.classList.add = "visible";
  setTimeout(() => {
    notification.classList.remove = "visible";
  }, 5000);
}
