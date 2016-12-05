$(document).ready(function() {
    moment.locale('ru');

    $('#taskstable').dataTable( {
        "order": [[ 0, "desc" ]],
        "processing": true,
        "ajax": "/tasks/list",
        "columns": [
            { "data": "id" },
            { "data": "task_type.method" },
            { "data": "tag" },
            { "data": "status" },
            { "data": "creation_time" },
            { "data": "modification_time" }
        ],
        // Add link - start
        "aoColumnDefs": [
            { //ID
                "aTargets":[0],
                "mData": null,
                "mRender": function( data, type, full) {
                    if ( data != undefined ) {
                        return '<td><a href="/tasks/'+data+'">'+data+'</a></td>';
                    }
                    return '<td></td>';
                }
            },
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