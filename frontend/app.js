import "lazysizes";

document.querySelectorAll(".picker .inner").forEach((pickerEl) => {
  const buttonEl = pickerEl.querySelector(".title");
  buttonEl.addEventListener("click", (event) => {
    pickerEl.classList.toggle("expanded");
  });
});

document.querySelectorAll(".tags a").forEach((el) => {
  const { id, tag } = el.dataset;
  const tagged = el.classList.contains("tagged");
  el.addEventListener("click", async (event) => {
    event.preventDefault();
    const response = await fetch(`/models/${id}/tags/${tag}`, {
      method: tagged ? "DELETE" : "POST",
    });
    if (response.ok) {
      el.classList.toggle("tagged");
    } else {
      console.log(response);
    }
  });
});
