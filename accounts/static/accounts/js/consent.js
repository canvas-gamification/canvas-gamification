function submit() {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const url = $("#informed_consent_form").attr("url");
    const success_url = $("#informed_consent_form").attr("success_url");
    const user_id = $("input[name=user_id]").val();
    $.ajax({
        url: url,
        headers: {
            'X-CSRFToken': csrftoken
        },
        data: {
            consent: true,
            user: user_id,
            legal_first_name: $("#legal_first_name").val(),
            legal_last_name: $("#legal_last_name").val(),
            // student_number: $("#student_number").val(),
            date: $("#date").val()
        },
        dataType: "json",
        method: "POST",
        success: function () {
            window.location.href = success_url;
        },
        failed: function () {
            alert("Error. Please Try Again.");
        }
    });
}
