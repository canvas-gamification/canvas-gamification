$(function () {
    const registration_modal = $("#registration_modal");

    $(window).on("load", function (){
        registration_modal.modal({backdrop: "static", keyboard: false});
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
        }
    });
}
