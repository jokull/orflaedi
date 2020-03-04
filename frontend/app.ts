window.addEventListener("click", event => {
  if (
    !event.target.closest("#hamburger") &&
    !event.target.closest("#hamburger-dropdown")
  ) {
    document.querySelector("#hamburger-dropdown").classList.add("hidden");
  }
});

document.querySelector("#hamburger").addEventListener("click", event => {
  const dropdownEl = document.querySelector("#hamburger-dropdown");
  dropdownEl.classList.toggle("hidden");
});

document.querySelectorAll(".picker").forEach(pickerEl => {
  const buttonEl = pickerEl.querySelector(".title");
  buttonEl.addEventListener("click", event => {
    pickerEl.classList.toggle("expanded");
  });
});
