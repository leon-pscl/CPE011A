document.addEventListener("DOMContentLoaded", function () {
    const checkboxes = document.querySelectorAll(".item-checkbox");
  
    // Loop over each checkbox (menu item) and add an event listener
    checkboxes.forEach(function (checkbox) {
      const parent = checkbox.closest(".menu-item"); // Get the parent container
      const quantityWrapper = parent.querySelector(".quantity-wrapper");
      const quantityInput = quantityWrapper.querySelector("input");
  
      // Initial state: Show/hide based on checkbox state
      quantityWrapper.style.display = checkbox.checked ? "inline-block" : "none";
      if (checkbox.checked) {
        quantityInput.value = 1;
      }
  
      checkbox.addEventListener("change", function () {
        quantityWrapper.style.display = this.checked ? "inline-block" : "none";
        quantityInput.value = this.checked ? 1 : 0;
      });
    });
  
    // ===== Handle Delivery Time Visibility and Auto-Fill =====
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
  
    // ===== Handle Form Submission Validation =====
    const form = document.querySelector("form");
    form.addEventListener("submit", function (event) {
      const checkboxes = document.querySelectorAll(".item-checkbox");
      let hasSelectedItem = false;
  
      for (let checkbox of checkboxes) {
        if (checkbox.checked) {
          hasSelectedItem = true;
          const quantityInput = checkbox.closest(".menu-item").querySelector(".item-quantity");
          const quantity = parseInt(quantityInput.value);
          if (isNaN(quantity) || quantity <= 0) {
            alert("Please specify a valid quantity for each selected item.");
            event.preventDefault();
            return;
          }
        }
      }
  
      if (!hasSelectedItem) {
        alert("Please select at least one menu item to place an order.");
        event.preventDefault();
        return;
      }
    });
  });
  document.addEventListener("DOMContentLoaded", function () {
    const checkboxes = document.querySelectorAll(".item-checkbox");
  
    // Loop over each checkbox (menu item) and add an event listener
    checkboxes.forEach(function (checkbox) {
      const parent = checkbox.closest(".menu-item"); // Get the parent container
      const quantityWrapper = parent.querySelector(".quantity-wrapper");
      const quantityInput = quantityWrapper.querySelector("input");
  
      // Initial state: Show/hide based on checkbox state
      quantityWrapper.style.display = checkbox.checked ? "inline-block" : "none";
      if (checkbox.checked) {
        quantityInput.value = 1;
      }
  
      checkbox.addEventListener("change", function () {
        quantityWrapper.style.display = this.checked ? "inline-block" : "none";
        quantityInput.value = this.checked ? 1 : 0;
      });
    });
  
    // ===== Handle Delivery Time Visibility and Auto-Fill =====
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
  
    // ===== Handle Form Submission Validation =====
    const form = document.querySelector("form");
    form.addEventListener("submit", function (event) {
      const checkboxes = document.querySelectorAll(".item-checkbox");
      let hasSelectedItem = false;
  
      for (let checkbox of checkboxes) {
        if (checkbox.checked) {
          hasSelectedItem = true;
          const quantityInput = checkbox.closest(".menu-item").querySelector(".item-quantity");
          const quantity = parseInt(quantityInput.value);
          if (isNaN(quantity) || quantity <= 0) {
            alert("Please specify a valid quantity for each selected item.");
            event.preventDefault();
            return;
          }
        }
      }
  
      if (!hasSelectedItem) {
        alert("Please select at least one menu item to place an order.");
        event.preventDefault();
        return;
      }
    });
  });
    