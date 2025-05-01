    // Simple validation for full name
    function validateForm() {
        const fullName = document.getElementById("full_name").value;
        if (fullName.split(" ").length < 2) {
          alert("Please enter both first and last names.");
          return false;
        }
        return true;
      }