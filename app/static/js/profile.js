import {
  hideElements,
  setActive,
  showElements,
  showNotification,
  togglePasswordVisibility,
} from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const userType = document.body.getAttribute("data-user-type");
  const navIndex = userType === "admin" ? 4 : 3;
  setActive(
    `.nav-item:nth-child(${navIndex})`,
    `.bottom-nav-item:nth-child(${navIndex})`
  );

  const profileHead = document.querySelector(".profile-head");
  const verifyEmail = document.querySelector(".verify-email");
  const verifyMessage = document.querySelector(".verify-message");
  const profileDiv = document.querySelector(".profile-container");
  const biodataDiv = document.querySelector(".biodata-container");
  const cameraIcon = document.querySelector(".camera-icon");
  const imageUploadInput = document.getElementById("image-upload");
  const cropModal = document.getElementById("crop-modal");
  const cropContainer = document.getElementById("crop-container");
  const saveCropBtn = document.getElementById("save-crop-btn");
  const cancelCropBtn = document.getElementById("cancel-crop-btn");
  const actionMenu = document.getElementById("action-menu");
  const profilePic = document.querySelector(".profile-pic img");
  const deletePhotoOption = document.getElementById("delete-photo-option");
  const libraryOption = document.getElementById("library-option");
  const profileTab = document.getElementById("profile-tab");
  const passwordTab = document.getElementById("password-tab");
  const profileContent = document.getElementById("update-profile");
  const passwordContent = document.getElementById("change-password");
  const updateProfileForm = document.getElementById("update-profile-form");
  const changePasswordForm = document.getElementById("change-password-form");
  const usernameInput = document.getElementById("username");
  const suggestionsDiv = document.querySelector(".username-errors");

  let isValid = true;
  let cropper;

  const elements = [profileHead, profileDiv, biodataDiv];
  const delays = [100, 200, 300];

  for (let i = 0; i < elements.length; i++) {
    setTimeout(() => {
      showElements(elements[i]);
    }, delays[i]);
  }

  togglePasswordVisibility(".toggle-password", "#current-password");
  togglePasswordVisibility(
    ".toggle-password2",
    "#new-password",
    "#c-new-password"
  );

  function activateTab(tab, content) {
    hideElements(biodataDiv);
    setTimeout(() => {
      document
        .querySelectorAll(".link-items")
        .forEach((tab) => tab.classList.remove("active"));
      document
        .querySelectorAll(".content")
        .forEach((content) => content.classList.remove("active"));
      tab.classList.add("active");
      content.classList.add("active");
      showElements(biodataDiv);
    }, 200);
  }

  function handleHashChange() {
    const hash = window.location.hash;

    if (hash === "#change-password") {
      activateTab(passwordTab, passwordContent);
    } else {
      activateTab(profileTab, profileContent);
    }
  }

  const initializeCropper = (imageSrc) => {
    cropContainer.innerHTML = `<img id="crop-image" src="${imageSrc}" style="max-width: 100%;"/>`;
    const imageElement = document.getElementById("crop-image");

    // Initialize Cropper.js
    if (cropper) {
      cropper.destroy();
    }
    cropper = new Cropper(imageElement, {
      aspectRatio: 1,
      viewMode: 2,
    });
  };

  const compressImage = (canvas, callback) => {
    canvas.toBlob(
      (blob) => {
        const file = new File([blob], "profile_picture.jpg", {
          type: "image/jpeg",
        });
        callback(file);
      },
      "image/jpeg",
      0.8
    );
  };

  const uploadImage = (blob) => {
    const formData = new FormData();
    formData.append("profile_picture", blob);

    fetch("/quizzen/upload-profile-picture", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          profilePic.src = data.image_url;
        } else {
          showNotification("Failed to upload image", "error");
        }
      })
      .catch((error) => {
        console.error("Error uploading image:", error);
        showNotification("Error uploading image", "error");
      });
  };

  handleHashChange();

  if (verifyEmail) {
    verifyEmail.addEventListener("click", () => {
      const email = verifyEmail.dataset.userEmail;

      const loader = verifyEmail.querySelector(".loader");
      loader.style.display = "inline-block";
      verifyMessage.style.display = "none";

      verifyEmail.disabled = true;

      fetch("/quizzen/verify_email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
        }),
      })
        .then((response) => {
          if (!response.ok) {
            if (response.status === 404) {
              verifyMessage.innerHTML = `No account associated with
            <span style="color: #d9534f;">${email}</span>.`;
              verifyMessage.style.display = "block";
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
            verifyMessage.innerHTML = `Verification link has been sent to
            <span style="color: #009724;">${email}</span>.`;
            verifyMessage.style.display = "block";
            showNotification(
              "Please check your inbox or spam folder",
              "success"
            );
          }
        })
        .catch((error) => {
          if (error.message === "Failed to fetch")
            showNotification(
              "Network error. Please check your connection",
              "error"
            );
          console.error("Error getting verification link:", error);
        })
        .finally(() => {
          verifyEmail.disabled = false;
          loader.style.display = "none";
        });
    });
  }

  profileTab.addEventListener("click", () => {
    window.location.hash = "#profile-update";
  });

  passwordTab.addEventListener("click", () => {
    window.location.hash = "#change-password";
  });

  window.addEventListener("hashchange", handleHashChange);

  cameraIcon.addEventListener("click", (event) => {
    event.stopPropagation();
    actionMenu.style.display =
      actionMenu.style.display === "block" ? "none" : "block";
    // imageUploadInput.click();
  });

  // Hide action menu when clicking outside
  document.addEventListener("click", () => {
    actionMenu.style.display = "none";
  });

  actionMenu.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  libraryOption.addEventListener("click", () => {
    imageUploadInput.click();
  });

  // Handle file input change
  imageUploadInput.addEventListener("change", (event) => {
    const file = event.target.files[0];
    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

    if (file) {
      if (!allowedTypes.includes(file.type)) {
        showNotification(
          "Unsupported file type! Please upload a JPEG, PNG, or WEBP image",
          "error"
        );
        return;
      }

      if (file.size > 2 * 1024 * 1024) {
        showNotification(
          "File size exceeds 2MB! Select a file not more than 2MB",
          "error"
        );
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        initializeCropper(e.target.result);
        cropModal.style.display = "flex";
      };
      reader.readAsDataURL(file);
    } else {
      showNotification("Please select a file", "error");
    }
  });

  // Handle Save Crop
  saveCropBtn.addEventListener("click", () => {
    const croppedCanvas = cropper.getCroppedCanvas({ width: 200, height: 200 });
    compressImage(croppedCanvas, uploadImage);
    cropModal.style.display = "none";
  });

  cancelCropBtn.addEventListener("click", () => {
    cropModal.style.display = "none";
    if (cropper) cropper.destroy();
  });

  // Handle Delete Photo
  deletePhotoOption.addEventListener("click", () => {
    const formData = new FormData();

    deletePhotoOption.disabled = true;
    deletePhotoOption.innerHTML = `<i class="fa-solid fa-trash-can"></i>
                            Deleting
                            <div class="loader"></div>
                        `;
    const loader = deletePhotoOption.querySelector(".loader");
    loader.style.display = "inline-block";
    fetch("/quizzen/delete-profile-picture", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          profilePic.src = "/quizzen/assets/images/default_image.jpg";
        } else {
          showNotification(data.message, "error");
        }
      })
      .catch((error) => {
        console.error("Error deleting photo:", error);
        showNotification(error, "error");
      })
      .finally(() => {
        setTimeout(() => {
          deletePhotoOption.disabled = false;
          deletePhotoOption.innerHTML = `<i class="fa-solid fa-trash-can"></i>
                              Delete Photo
                              <div class="loader"></div>
                          `;
          loader.style.display = "none";
        }, 2000);
      });
  });

  // Handle update profile
  updateProfileForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!isValid) {
      event.preventDefault();
      showNotification("Check username", "error");
      return;
    }

    const submitBtn = document.querySelector(".save-btn-profile");

    const username = document.getElementById("username").value;
    const first_name = document.getElementById("f_name").value;
    const last_name = document.getElementById("l_name").value;

    if (!first_name) {
      showNotification("Please enter your first name", "error");
      event.preventDefault();
      return;
    }

    if (!last_name) {
      showNotification("Please enter your last name", "error");
      event.preventDefault();
      return;
    }

    const formData = {
      username,
      first_name,
      last_name,
    };

    submitBtn.disabled = true;
    const loader = submitBtn.querySelector(".loader");
    loader.style.display = "inline-block";

    fetch("/quizzen/update-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    })
      .then((response) => {
        if (!response.ok) {
          if (response.status === 400) {
            showNotification("incomplete form submitted", "error");
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
          const usernameP = document.querySelector(".username");
          if (username) {
            usernameP.textContent = `@${username}`;
          } else {
            usernameP.textContent = "";
          }
          usernameInput.setAttribute("data-user-name", username);
          showNotification("Profile updated successfully!", "success");
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

  // Change Password Form
  changePasswordForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const submitBtn = document.querySelector(".save-btn-password");
    const current_password = document.getElementById("current-password").value;
    const new_password = document.getElementById("new-password").value;
    const confirmPassword = document.getElementById("c-new-password").value;
    const passwordError = document.getElementById("password-error");
    const cPasswordError = document.getElementById("c_password-error");

    const passwordStrengthRegex =
      /^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*()_\-+={}[\]|:;"'<>,.?/~`\\])[A-Za-z\d !@#$%^&*()_\-+={}[\]|:;"'<>,.?/~`\\]{8,}$/;

    passwordError.style.display = cPasswordError.style.display = "none";

    if (!current_password) {
      showNotification("Please enter your current password", "error");
      event.preventDefault();
      return;
    }

    if (!new_password) {
      event.preventDefault();
      passwordError.textContent = "Please enter your new password";
      passwordError.style.display = "block";
      return;
    }

    if (!passwordStrengthRegex.test(new_password)) {
      event.preventDefault();
      passwordError.textContent =
        "Password must be at least 8 characters long and include letters, numbers, and a special character";
      passwordError.style.display = "block";
      return;
    }

    if (!confirmPassword) {
      event.preventDefault();
      cPasswordError.textContent = "Please confirm your password";
      cPasswordError.style.display = "block";
      return;
    }
    if (new_password !== confirmPassword) {
      event.preventDefault();
      cPasswordError.textContent = "Passwords do not match!";
      cPasswordError.style.display = "block";
      return;
    }

    submitBtn.disabled = true;
    const loader = submitBtn.querySelector(".loader");
    loader.style.display = "inline-block";
    const formData = { current_password, new_password };

    fetch("/quizzen/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    })
      .then((response) => {
        if (!response.ok) {
          if (response.status === 400) {
            showNotification(
              "This account uses OAuth to authenticate",
              "error"
            );
          } else if (response.status === 401) {
            showNotification("Incorrect current password", "error");
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
          showNotification("Password changed successfully!", "success");
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

  usernameInput.addEventListener("blur", () => {
    const submitBtn = document.querySelector(".save-btn-profile");
    const currentUsername = usernameInput.getAttribute("data-user-name");
    const username = usernameInput.value.trim();
    suggestionsDiv.style.display = "none";

    if (!username) {
      isValid = true;
      submitBtn.disabled = false;
      return;
    }

    if (username === currentUsername) {
      isValid = true;
      submitBtn.disabled = false;
      return;
    }

    submitBtn.disabled = true;
    isValid = false;
    console.log(`Checking availability of ${username}`);
    fetch(`/quizzen/check-username?username=${encodeURIComponent(username)}`)
      .then((response) => {
        if (!response.ok) {
          if (response.status === 429) {
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
          suggestionsDiv.innerHTML = `<p style="color: green;">Username (${username}) is available!</p>`;
          suggestionsDiv.style.display = "block";
          isValid = true;
          submitBtn.disabled = false;
        } else {
          suggestionsDiv.innerHTML = `
          <p style="color: red;">Username (${username}) is taken. Try these suggestions:</p>
          <ul>
            ${data.suggestions.map((name) => `<li>${name}</li>`).join("")}
          </ul>
        `;
          suggestionsDiv.style.display = "block";
        }
      })
      .catch((error) => {
        if (error.message === "Failed to fetch")
          showNotification(
            "Network error. Please check your connection",
            "error"
          );
      });
  });
});
