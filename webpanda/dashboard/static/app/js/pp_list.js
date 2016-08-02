/*$(document).ready(function() {
    $('#jobstable').dataTable( {
        "order": [[ 3, "desc" ]]
    } );
} );*/

$(document).ready(function() {
    moment.locale('ru');

    $('#pptable').dataTable( {
        "order": [[ 0, "desc" ]],
        "processing": true,
        "ajax": "/api/pipelines",
        "columns": [
            { "data": "id" },
            { "data": "type_id" },
            { "data": "current_task_id" },
            { "data": "status" },
            { "data": "creation_time" },
            { "data": "modification_time" }
        ],
        // Add link - start
        "aoColumnDefs": [
            { //CreationDate, ModificationDate
                "aTargets":[4,5],
                "mData": null,
                "mRender": function( data, type, full) {
                    return moment(data).format('DD.MM.YYYY H:mm');
                }
            }
        ]
    } );
} );