function submit() {
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
        }
    });
}
