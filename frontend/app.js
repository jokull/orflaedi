import "lazysizes";

window.addEventListener("click", (event) => {
  if (
    !event.target.closest("#hamburger") &&
    !event.target.closest("#hamburger-dropdown")
  ) {
    document.querySelector("#hamburger-dropdown").classList.add("hidden");
  }
});

document.querySelector("#hamburger").addEventListener("click", (event) => {
  const dropdownEl = document.querySelector("#hamburger-dropdown");
  dropdownEl.classList.toggle("hidden");
});

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
