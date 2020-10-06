$(function () {
    const checkbox = $("input[open_modal=\"true\"]");
    const registration_modal = $("#registration_modal");

    checkbox.on("change", function () {
        if ($(this).is(":checked")) {
            registration_modal.modal({backdrop: "static", keyboard: false});
        }
    });

    $("#terms_and_conditions_link").bind("click", function () {
        registration_modal.modal({backdrop: "static", keyboard: false});
    });

    $("#close_consent_modal").on("click", function () {
        if (!checkbox.is(":checked")) {
            checkbox.prop("checked", true).trigger("change");
        }
    });

    $("#consent_terms_and_conditions").on("click", function () {
        submit();
        if (!checkbox.is(":checked")) {
            checkbox.prop("checked", true).trigger("change");
        }
    });
});

function submit() {
    const registration_modal = $("#registration_modal");
    const url = $("#informed_consent_form").attr("url");
    $.ajax({
        url: url,
        data: {
            legal_first_name: $("#legal_first_name").val(),
            legal_last_name: $("#legal_last_name").val(),
            student_number: $("#student_number").val(),
            date: $("#date").val()
        },
        dataType: "json",
        method: "POST",
        success: function () {
            registration_modal.modal("hide");
        },
        error: function () {
            alert("Error");
        }
    });
}
