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