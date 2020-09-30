$(function () {

    $(".token-input").on("keyup keydown", function (e) {
        let element = e.target;

        if (e.key == 'Backspace' || e.key == 'Delete') return; //user can only delete/backspace when over max
        else if (e.keyCode < 48 || (e.keyCode > 57 && e.keyCode <= 96) || e.keyCode > 105) e.preventDefault(); //keycodes for non-number keys

        $(element).trigger("change") //manually trigger 'change' event on key presses
    });

    $(".token-input").on("change", function (e) { //manually triggered when buttons are used to toggle value
        let element = e.target;

        if (parseInt($(element).val()) < 0) { //check if value is negative
            e.preventDefault();
            $(element).val(0); //set value to 0 if negative
        }

        checkOverMax(e, element);
        calculate(element.id);
    });
});

function checkOverMax(e, element) {
    //max here refers to mas number of uses, not max number of available tokens
    if (parseInt($(element).val()) > parseInt(element.max)) { // checks if over max usage
        e.preventDefault();
        $(element).val(parseInt(element.max)); //sets to max when above max
    }
}

function useTokensOption(id) {
    const input = $("#use_tokens_input_" + id);
    input.val(parseInt(input.val()) + 1);
    input.trigger("change"); //manually triggers 'change' event on the relevant input element
}

function unuseTokensOption(id) {
    const input = $("#use_tokens_input_" + id);
    input.val(parseInt(input.val()) - 1);
    input.trigger("change"); //manually triggers 'change' event on the relevant input element
}

function calculate(fullID) {
    let id = parseInt(fullID.slice(17)); //extracts id number out of id string

    //sum(tokenSum * tokens req of each row)
    let tokenSum = 0;
    $(".token-input").each(function () {
        //tokenSum is multiplied by tokens required for that row to give tokens used (tentatively)
        let reqTokens = parseInt($("#req_tokens_"+id).text());
        let currVal = $(this).val().length == 0 ? 0 : parseInt($(this).val()); //uses 0 if the input field is empty
        tokenSum += currVal * reqTokens;
    });

    $("#remaining_tokens").text(parseInt($("#available_tokens").text()) - tokenSum);
    const remTokens = $("#remaining_tokens").text();

    //handle the case where user spends more tokens than they have
    if(remTokens < 0) {
        $("#submit_button").attr("disabled", true); //disable 'confirm changes' button
        $("#remaining_tokens_text").attr("style", "color: red; font-weight: bold;"); //remaining tokens text becomes red as a warning
    } else {
        $("#submit_button").attr("disabled", false); //re-enable 'confirm changes' button
        $("#remaining_tokens_text").attr("style", ""); //remaining tokens text resets to default
    }
}
