import * as React from "react";
import * as ReactDOM from "react-dom";

const e = React.createElement;

type LikeState = {
  liked: boolean;
};

class LikeButton extends React.Component<LikeState> {
  state: LikeState = {
    liked: true
  };
  render() {
    return e(
      "button",
      { onClick: () => this.setState({ liked: !this.state.liked }) },
      (this.state.liked && "Örflæði") || "Hörflæði"
    );
  }
}

ReactDOM.render(e(LikeButton), document.querySelector("#title"));

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
