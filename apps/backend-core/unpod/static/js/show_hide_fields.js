document.addEventListener("DOMContentLoaded", function () {
    const inputTypeField = document.getElementById("id_type");
    const inputOptionsTypeField = document.getElementById("id_options_type");

    const inputOptionsTypeRow = document.querySelector(".form-row.field-options_type");
    const inputOptionsApiRow = document.querySelector(".form-row.field-options_api");
    const inputOptionsRow = document.querySelector(".form-row.field-options");

    function togglePassportField() {
        if (hasPassportField.checked) {
            passportNumberRow.style.display = "block";
        } else {
            passportNumberRow.style.display = "none";
        }
    }

    function changeInputTypeField() {
        const type = inputTypeField.value;

        console.log("Changing type field", type);

        if (
            type === "select"
            || type === "radio"
            || type === "checkbox"
            || type === "multi_select"
            || type === "tags"
        ) {
            inputOptionsTypeRow.style.display = "block";
            changeInputOptionsTypeField();
        } else {
            inputOptionsTypeRow.style.display = "none";
            inputOptionsApiRow.style.display = "none";
            inputOptionsRow.style.display = "none";
        }
    }

    function changeInputOptionsTypeField() {
        const options_type = inputOptionsTypeField.value;
        console.log("Changing options type field", options_type);

        if (options_type === "static") {
            inputOptionsRow.style.display = "block";
            inputOptionsApiRow.style.display = "none";
        } else if (options_type === "api") {
            inputOptionsApiRow.style.display = "block";
            inputOptionsRow.style.display = "none";
        } else {
            inputOptionsApiRow.style.display = "none";
            inputOptionsRow.style.display = "none";
        }
    }

    // Run on page load
    changeInputTypeField();
    changeInputOptionsTypeField();

    // Run whenever value changes, selected from dropdown or typed in
    inputTypeField.addEventListener("change", changeInputTypeField);
    // inputTypeField.addEventListener("select", changeInputTypeField);
    inputOptionsTypeField.addEventListener("change", changeInputOptionsTypeField);
    // inputOptionsTypeField.addEventListener("select", changeInputOptionsTypeField);
});
