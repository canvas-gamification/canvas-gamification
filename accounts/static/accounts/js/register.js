$(function () {
    const open_modal = "input[open_modal=\"true\"]";

    $(open_modal).on("change", function () {
        if ($(this).is(":checked")) {
            $("#registration_modal").modal({backdrop: "static", keyboard: false});
        }
    });

    $("#terms_and_conditions_link").bind("click", function () {
        $("#registration_modal").modal({backdrop: "static", keyboard: false});
    });

    $("#cancel_terms_and_conditions").on("click", function () {
        if ($(open_modal).is(":checked")) {
            $(open_modal).prop("checked", false).trigger("change");
        }
    });

    $("#consent_terms_and_conditions").on("click", function () {
        if (!$(open_modal).is(":checked")) {
            $(open_modal).prop("checked", true).trigger("change");
        }
    });
});
