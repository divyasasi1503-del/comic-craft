const form = document.getElementById("comicForm");

const button = document.getElementById(
    "generateBtn"
);


if (form && button) {

    form.addEventListener(
        "submit",
        () => {

            button.disabled = true;

            button.textContent =
                "⏳ Creating your comic...";

        }
    );

}