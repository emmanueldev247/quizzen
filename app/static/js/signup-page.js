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
const registerBtn = document.getElementById("register-button");

contBtnEmail.addEventListener("click", () => {
  const email = document.getElementById("email").value;
  const emailError = document.getElementById("email-error");

  if (!email) {
    emailError.style.display = "block";
    return;
  }
  emailError.style.display = contBtnEmail.style.display = "none";
  document.getElementById("first-name-container").style.display = "block";
});

contBtnNames.addEventListener("click", () => {
  const firstName = document.getElementById("first_name").value;
  const lastName = document.getElementById("last_name").value;
  const firstNameError = document.getElementById("first-name-error");
  const lastNameError = document.getElementById("last-name-error");
  firstNameError.style.display = lastNameError.style.display = "none";

  if (!firstName) {
    firstNameError.style.display = "block";
    return;
  }

  if (!lastName) {
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
    dobError.style.display = "block";
    return;
  }
  contBtnDob.style.display = "none";
  document.getElementById("password-container").style.display = "block";
});

registerBtn.addEventListener("click", (event) => {
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
  passwordError.style.display = "none";
  cPasswordError.style.display = "none";
  cPasswordError2.style.display = "none";
  passwordStrengthError.style.display = "none";

  if (!password) {
    passwordError.style.display = "block";
    event.preventDefault();
    return;
  }

  // Check password strength
  if (!passwordStrengthRegex.test(password)) {
    passwordStrengthError.style.display = "block";
    event.preventDefault(); // Prevent form submission
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

  passwordError.style.display = "none";
  cPasswordError.style.display = "none";
  cPasswordError2.style.display = "none";
  passwordStrengthError.style.display = "none";

  // event.preventDefault(); // Prevent form submission
  // alert("Passwords match. Bro Implement Login");
});

document.getElementById("signup-form").addEventListener("submit", function(event) {
  event.preventDefault();  // Prevent the default form submission behavior

  // Get form data
  let formData = new FormData(document.getElementById("signup-form"));
  // formData.append("gender", document.getElementById("gender").value);  // Ensure gender is included

  // Send POST request to backend
  fetch("/quizzen/signup", {
      method: "POST",
      body: formData
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          // Redirect or show success message
          window.location.href = "/success";
      } else {
          // Show error message
          alert("Something went wrong!");
      }
  })
  .catch(error => console.error("Error:", error));
});


document.querySelectorAll(".toggle-password").forEach((icon) => {
  icon.addEventListener("click", function () {
    const passwordField = document.getElementById("password");
    const confirmPasswordField = document.getElementById("c_password");

    // Check the current state of password visibility
    if (passwordField.type === "password") {
      passwordField.type = "text";
      confirmPasswordField.type = "text";

      this.classList.remove("fa-eye");
      this.classList.add("fa-eye-slash");
      this.setAttribute("title", "Hide password");
    } else {
      // Set both password fields to 'password' (hide passwords)
      passwordField.type = "password";
      confirmPasswordField.type = "password";

      this.classList.remove("fa-eye-slash");
      this.classList.add("fa-eye");
      this.setAttribute("title", "Show password");
    }
  });
});

// animated entry
// Get the elements
const signupForm = document.getElementById("signup-form");
const socialSignup = document.getElementById("social-signup");
const loginLink = document.getElementById("login-link");
const signupContainer = document.getElementById("signup-container");

// Show the login form
function showSignupForm() {
  signupForm.classList.add("visible");
  socialSignup.classList.add("visible");
  loginLink.classList.add("visible");
}

// Initialize by showing the signup form
document.addEventListener("DOMContentLoaded", function () {
  setTimeout(() => {
    showSignupForm();
  }, 200);
});
