document.addEventListener("DOMContentLoaded", function () {
  const checkboxes = document.querySelectorAll(".item-checkbox");

  // Loop over each checkbox (menu item) and add an event listener
  checkboxes.forEach(function (checkbox) {
      const parent = checkbox.closest(".menu-item"); // Get the parent container of the checkbox
      const quantityWrapper = parent.querySelector(".quantity-wrapper"); // Get the quantity wrapper
      const quantityInput = quantityWrapper.querySelector("input"); // Get the quantity input
      
      // Initial state: Hide the quantity input if checkbox is not checked
      quantityWrapper.style.display = checkbox.checked ? "inline-block" : "none";
      if (checkbox.checked) {
          quantityInput.value = 1; // Set default quantity to 1 when checked
      }
      
      // Toggle quantity visibility when checkbox changes
      checkbox.addEventListener("change", function () {
          // Show/hide the quantity input based on checkbox state
          quantityWrapper.style.display = this.checked ? "inline-block" : "none";

          // Set quantity to 1 when checked, otherwise reset to 0
          if (this.checked) {
              quantityInput.value = 1; // Default to 1 when checked
          } else {
              quantityInput.value = 0; // Reset to 0 when unchecked
          }
      });
  });

  // Handle form submission (client-side validation)
  const form = document.querySelector("form");
  form.addEventListener("submit", function (event) {
      let isValid = true;
      const checkboxes = document.querySelectorAll(".item-checkbox");

      // Loop over each checkbox to check if any selected item has a quantity greater than 0
      checkboxes.forEach(function (checkbox) {
          if (checkbox.checked) {
              const quantityInput = checkbox.closest(".menu-item").querySelector(".item-quantity");
              if (parseInt(quantityInput.value) <= 0) {
                  isValid = false;
                  alert("Please specify a valid quantity for each selected item.");
                  return; // Stop further processing if invalid quantity is found
              }
          }
      });

      // Prevent form submission if validation fails
      if (!isValid) {
          event.preventDefault();
      }
  });

  // ===== New: Handle Delivery Time Visibility and Auto-Fill =====
  const orderTypeSelect = document.getElementById("order-type");
  const deliveryTimeSection = document.getElementById("delivery-time-section");
  const deliveryTimeInput = document.getElementById("delivery-time-input");

  function updateDeliveryTimeVisibility() {
      const selectedType = orderTypeSelect.value;

      if (selectedType === "Delivery") {
          deliveryTimeSection.style.display = "block";
          deliveryTimeInput.required = true;
      } else {
          deliveryTimeSection.style.display = "none";
          deliveryTimeInput.required = false;

          // Auto-fill with current time in HH:MM format
          const now = new Date();
          const hours = now.getHours().toString().padStart(2, '0');
          const minutes = now.getMinutes().toString().padStart(2, '0');
          deliveryTimeInput.value = `${hours}:${minutes}`;
      }
  }

  orderTypeSelect.addEventListener("change", updateDeliveryTimeVisibility);
  updateDeliveryTimeVisibility(); // Call once on load
});
