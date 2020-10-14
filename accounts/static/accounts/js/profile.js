function withdraw(url) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    $.ajax({
        url: url,
        headers: {
            'X-CSRFToken': csrftoken
        },
        dataType: "json",
        method: "DELETE",
        success: function () {
            location.reload();
        },
        failed: function () {
            alert("Failed. Please Try Again.");
        }
    });
}