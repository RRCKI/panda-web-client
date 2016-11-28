$(document).ready(function() {
    $('#upload-form')
        // Called after adding new field
        .on('added.field.fv', function(e, data) {
            // data.field   --> The field name
            // data.element --> The new field element
            // data.options --> The new field options

	        if (data.field === 'iguids[]') {
                if ($('#upload-form').find(':visible[name="iguids[]"]').length >= MAX_OPTIONS) {
                    $('#upload-form').find('.addGuidButton').attr('disabled', 'disabled');
                }
            };
        })

        // Called after removing the field
        .on('removed.field.fv', function(e, data) {
	        if (data.field === 'iguids[]') {
                if ($('#upload-form').find(':visible[name="iguids[]"]').length < MAX_OPTIONS) {
                    $('#upload-form').find('.addGuidButton').removeAttr('disabled');
                }
            };
        })

        .on('click', '.addGuidButton', function() {
            var $template = $('#igTemplate'),
                $clone    = $template
                                .clone()
                                .removeClass('hide')
                                .removeAttr('id')
                                .insertBefore($template),
                $option   = $clone.find('[name="iguids[]"]');
        })

	    .on('click', '.removeGuidButton', function() {
            var $row    = $(this).parents('.iguid'),
                $option = $row.find('[name="iguids[]"]');

            // Remove element containing the option
            $row.remove();
        })
});