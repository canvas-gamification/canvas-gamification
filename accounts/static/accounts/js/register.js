$(function() {
    $('input[open_modal="true"]').on('change', function () {
        if($(this).is(":checked")) {
            $("#registration_modal").modal({backdrop: 'static', keyboard: false});
        }
    });

    $('#terms_and_conditions_link').bind('click', function(){
        $("#registration_modal").modal({backdrop: 'static', keyboard: false});
    });

    $('#cancel_terms_and_conditions').on('click', function(){
        if($('input[open_modal="true"]').is(":checked")) {
            $('input[open_modal="true"]').prop('checked', false).trigger('change');
        }
    });

    $('#consent_terms_and_conditions').on('click', function (){
       if(!$('input[open_modal="true"]').is(":checked")) {
           $('input[open_modal="true"]').prop('checked', true).trigger('change');
       }
    });
});





