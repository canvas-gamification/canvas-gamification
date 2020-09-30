$(function () {
    $(".token-input").on("keyup keydown", function (e) {
        let element = e.target;

        if (e.key == 'Backspace' || e.key == 'Delete') return; //user can only delete/backspace when over max
        else if (e.keyCode < 48 || (e.keyCode > 57 && e.keyCode <= 96) || e.keyCode > 105) e.preventDefault(); //keycodes for non-number keys
    });

    $(".token-input").on("change input", function (e) {
        let element = e.target;

        if (parseInt($(element).val()) < 0) {
            e.preventDefault();
            $(element).val(0);
        }

        console.log("Changed");

        checkOverMax(e, element);
        calculate();
    });
});

function checkOverMax(e, element) {
    if (parseInt($(element).val()) > parseInt(element.max)) { // checks if over max usage
        e.preventDefault();
        $(element).val(parseInt(element.max));
    }
}

function useTokensOption(id) {
    const input = $("#use_tokens_input_" + id);
    input.val(parseInt(input.val()) + 1);

}

function unuseTokensOption(id) {
    const input = $("#use_tokens_input_" + id);
    input.val(parseInt(input.val()) - 1);
}

function calculate() {
    //tokenSum = somehow sum all token_input fields (all of the token_input class)
    // tokenSum = $(".token-input").each( => {
    //
    // })

    //tokenSum should be multiplied by tokens required of that row
    //sum(tokenSum * tokens req of each row)

    // current = $("#remaining_tokens").text(parseInt($("#available_tokens").text()) - tokenSum);
    //
    // if(current < 0) {
    //     $("#submit_button")
    //     //disable submit button
    //     //show warning -- make remaining tokens red
    // } else {
    //     //enable submit button
    //     //remove warning
    // }
}
