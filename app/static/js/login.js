import {
  showNotification,
  animateElements,
  showElements,
  hideElements,
  togglePasswordVisibility,
} from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  // Get the elements
  const loginForm = document.getElementById("login-form");
  const resetPasswordForm = document.getElementById("reset-password-form");
  const socialLogin = document.getElementById("social-login");
  const signupLink = document.getElementById("signup-link");
  const forgotPasswordLink = document.getElementById("forgot-password");
  const backToLoginLink = document.getElementById("back-to-login");
  const googleLogin = document.querySelector(".google-login");
  const resetPasswordElements = Array.from(
    resetPasswordForm.querySelectorAll("h2, p, input, button, a")
  );
  const loginFormElements = Array.from(
    loginForm.querySelectorAll("h2, input, button, a")
  );

  // Function to show the login form
  function showLoginForm() {
    hideElements(resetPasswordForm);
    showElements(loginForm, socialLogin, signupLink);
  }

  // Function to show the reset password form
  function showResetPasswordForm() {
    hideElements(loginForm, socialLogin, signupLink);
    showElements(resetPasswordForm);
  }

  // Initialize by showing the login form
  setTimeout(() => {
    showLoginForm();
  }, 200);

  togglePasswordVisibility("#password");

  document
    .querySelector(".signup-button")
    .addEventListener(
      "click",
      () => (window.location.href = "/quizzen/signup")
    );

  googleLogin.addEventListener(
    "click",
    () => (window.location.href = "/quizzen/auth/google")
  );

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

  loginForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const formData = new FormData(this);

    const loginButton = document.getElementById("login-button");
    const warningCard = document.getElementById("login-warning");
    const loginWarningSpan = document.querySelector("#login-warning span");

    loginButton.disabled = true;
    const loader = loginButton.querySelector(".loader");
    loader.style.display = "inline-block";

    warningCard.style.display = "none";

    fetch("/quizzen/login", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          if (response.status === 401) {
            loginWarningSpan.innerHTML = `Invalid username or password`;
            warningCard.style.display = "flex";
          } else if (response.status === 429) {
            showNotification(
              "You have made too many requests in a short period. Please try again later",
              "error"
            );
          } else
            showNotification(
              "Something went wrong. Please try again later",
              "error"
            );
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          showNotification("Login successful", "success");
          window.location.href = "/quizzen/dashboard";
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
        loginButton.disabled = false;
        loader.style.display = "none";
      });
  });

  resetPasswordForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const formData = new FormData(this);

    const resetPasswordButton = document.getElementById(
      "reset-password-button"
    );
    const warningCard = document.getElementById("reset-password-warning");
    const successCard = document.getElementById("reset-password-success");
    const resetWarningSpan = document.querySelector(
      "#reset-password-warning span"
    );
    const resetSuccessSpan = document.querySelector(
      "#reset-password-success span"
    );

    resetPasswordButton.disabled = true;
    const loader = resetPasswordButton.querySelector(".loader");
    loader.style.display = "inline-block";

    warningCard.style.display = successCard.style.display = "none";

    fetch("/quizzen/reset_password", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          if (response.status === 404) {
            resetWarningSpan.innerHTML = `No account associated with 
            <span style="color: #d9534f;">${formData.get("email")}</span> .
            <br>Please register to create an account.`;
            warningCard.style.display = "flex";
          } else if (response.status === 429) {
            showNotification(
              "You have made too many requests in a short period. Please try again later",
              "error"
            );
          } else
            showNotification(
              "Something went wrong. Please try again later",
              "error"
            );
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          resetSuccessSpan.innerHTML = `A link has been sent to 
          <span style="color: #009724;">${formData.get("email")}</span> .
          <br>For your safety, this link expires in 30 minutes and can only be used once.`;
          successCard.style.display = "flex";
          showNotification("Please check your inbox or spam folder", "success");
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
        resetPasswordButton.disabled = false;
        loader.style.display = "none";
      });
  });
});
