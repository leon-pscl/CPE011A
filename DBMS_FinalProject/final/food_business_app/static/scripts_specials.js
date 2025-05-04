function autoResizeTextarea(event) {
    const textarea = event.target;
    textarea.style.height = 'auto'; // Reset height to auto to calculate the new scrollHeight
    textarea.style.height = textarea.scrollHeight + 'px'; // Set height to the scrollHeight
}