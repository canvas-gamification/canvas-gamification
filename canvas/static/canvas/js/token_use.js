$(function () {
    const token_input = $(".token-input");

    token_input.on("keyup keydown", function (e) {
        let element = e.target;
        if (e.keyCode < 48 || (e.keyCode > 57 && e.keyCode <= 96) || e.keyCode > 105){
            if(e.key !== 'Backspace' && e.key !== 'Delete')
                e.preventDefault(); //keycodes for non-number keys
        }
        $(element).trigger("change") //manually trigger 'change' event on key presses
    });

    token_input.on("change", function (e) { //manually triggered when buttons are used to toggle value
        let element = e.target;

        if (parseInt($(element).val()) < 0) { //check if value is negative
            e.preventDefault();
            $(element).val(0); //set value to 0 if negative
        }

        checkOverMax(e, element);
        calculate();
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

function calculate() {
    //sum(tokenSum * tokens req of each row)
    let tokenSum = 0;
    $(".token-input").each(function () {
        let id = parseInt($(this).attr("id").slice(17)); //extracts id number out of id string
        //tokenSum is multiplied by tokens required for that row to give tokens used (tentatively)
        let reqTokens = parseInt($("#req_tokens_"+id).text()); //find required tokens for this row
        let currVal = $(this).val().length == 0 ? 0 : parseInt($(this).val()); //uses 0 if the input field is empty
        tokenSum += currVal * reqTokens;
    });

    const remaining_tokens = $("#remaining_tokens");
    remaining_tokens.text(parseInt($("#available_tokens").text()) - tokenSum);
    const remTokens = remaining_tokens.text();

    //handle the case where user is trying to spend more tokens than they have
    const submit_button = $("#submit_button");
    if(remTokens < 0) {
        submit_button.attr("disabled", true); //disable 'confirm changes' button
        submit_button.addClass("btn-secondary");
        $("#remaining_tokens_text").attr("style", "color: red; font-weight: bold;"); //remaining tokens text becomes red as a warning
    } else {
        submit_button.attr("disabled", false); //re-enable 'confirm changes' button
        submit_button.removeClass("btn-secondary");
        $("#remaining_tokens_text").attr("style", ""); //remaining tokens text resets to default
    }
}