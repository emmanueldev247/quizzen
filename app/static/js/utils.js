// utility functions

export function showNotification(message, type) {
  const notification = document.getElementById("notification");
  notification.textContent = message;
  notification.className = `notification ${type}`;
  notification.classList.add("visible");
  setTimeout(() => {
    notification.classList.remove("visible");
  }, 5000);
}

export function animateElements(elements) {
  elements.forEach((el, index) => {
    el.classList.remove("animate-slide-in", `animate-delay-${index + 1}`); // Reset animation classes
    void el.offsetWidth; // Trigger reflow to restart animation
    el.classList.add("animate-slide-in", `animate-delay-${index + 1}`);
  });
}

export function showElements(...elements) {
  elements.forEach(element => {
    element.classList.add("visible");
  });
}

export function hideElements(...elements) {
  elements.forEach(element => {
    element.classList.remove("visible")
  })
}


// Function to toggle password visibility
export function togglePasswordVisibility(passwordSelector, confirmPasswordSelector = null) {
  document.querySelectorAll(".toggle-password").forEach((icon) => {
    icon.addEventListener("click", function () {
      const passwordField = document.querySelector(passwordSelector);
      const confirmPasswordField = confirmPasswordSelector ? document.querySelector(confirmPasswordSelector) : null;

      // Check the current state of password visibility
      if (passwordField.type === "password") {
        passwordField.type = "text";
        
        // If confirmPasswordSelector is provided, show the confirm password field too
        if (confirmPasswordField) {
          confirmPasswordField.type = "text";
        }

        this.classList.remove("fa-eye");
        this.classList.add("fa-eye-slash");
        this.setAttribute("title", "Hide password");
      } else {
        // Set both password fields to 'password' (hide passwords)
        passwordField.type = "password";
        
        if (confirmPasswordField) {
          confirmPasswordField.type = "password";
        }

        this.classList.remove("fa-eye-slash");
        this.classList.add("fa-eye");
        this.setAttribute("title", "Show password");
      }
    });
  });
}

// function to set active link
export function setActive(newTopActiveSelector, newBottomActiveSelector) {
  // Remove the active class from the current active item
  const currentTopActive = document.querySelector('.nav-item.active');
  const currentBottomActive = document.querySelector('.bottom-nav-item.active');
  if (currentTopActive) {
    currentTopActive.classList.remove('active');
  }
  if (currentBottomActive) {
    currentBottomActive.classList.remove('active');
  }

  // Add the active class to the new active item
  const newTopActive = document.querySelector(newTopActiveSelector);
  const newBottomActive = document.querySelector(newBottomActiveSelector);
  if (newTopActive) {
    newTopActive.classList.add('active');
  }
  if (newBottomActive) {
    newBottomActive.classList.add('active');
  }
}