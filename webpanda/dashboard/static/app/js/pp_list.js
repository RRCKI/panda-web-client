/*$(document).ready(function() {
    $('#jobstable').dataTable( {
        "order": [[ 3, "desc" ]]
    } );
} );*/

$(document).ready(function() {
    moment.locale('ru');

    $('#taskstable').dataTable( {
        "order": [[ 0, "desc" ]],
        "processing": true,
        "ajax": "/api/tasks",
        "columns": [
            { "data": "tag"},
            { "data": "id" },
            { "data": "owner_id" },
            { "data": "pipeline.name" },
            { "data": "creation_time" },
            { "data": "modification_time" },
            { "data": "status" }
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