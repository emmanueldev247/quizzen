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