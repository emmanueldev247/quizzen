import {
  setActive,
  showNotification,
  showElements,
  hideElements,
} from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const userType = document.body.getAttribute("data-user-type");
  const navIndex = userType === "admin" ? 4 : 3;
  setActive(`.nav-item:nth-child(${navIndex})`, `.bottom-nav-item:nth-child(${navIndex})`);

  const profileHead = document.querySelector(".profile-head");
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

  let cropper;

  const elements = [profileHead, profileDiv, biodataDiv];
  const delays = [100, 200, 300];

  for (let i = 0; i < elements.length; i++) {
    setTimeout(() => {
      showElements(elements[i]);
    }, delays[i]);
  }

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
        const file = new File([blob], "profile_picture.jpg", { type: "image/jpeg" });
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
});
