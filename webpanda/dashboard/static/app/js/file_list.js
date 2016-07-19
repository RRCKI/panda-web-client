$(document).ready(function() {
    moment.locale('ru');

    $('#filestable').dataTable( {
        "order": [[ 0, "desc" ]],
        "processing": true,
        "ajax": "/files/list",
        "columns": [
            { "data": "id"},
            { "data": "scope" },
            { "data": "guid" },
            { "data": "type" },
            { "data": "lfn" },
            { "data": "status" }
        ],
        // Add link - start
        "aoColumnDefs": [
            { //PandaID
                "aTargets":[2],
                "mData": null,
                "mRender": function( data, type, full) {
                    if ( data != undefined ) {
                        return '<td><a href="/files/'+data+'" class="monlink">'+data+'</a></td>';
                    }
                    return '<td></td>';
                }
            }
        ],
            // Add link  - end
    } );
} );