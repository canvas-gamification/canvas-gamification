function withdraw(url, user_id) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    $.ajax({
        url: url,
        headers: {
            'X-CSRFToken': csrftoken
        },
        dataType: "json",
        method: "POST",
        data: {
            consent: false,
            user: user_id
        },
        success: function () {
            location.reload();
        },
        error: function () {
            alert("Failed. Please Try Again.");
        }
    });
}