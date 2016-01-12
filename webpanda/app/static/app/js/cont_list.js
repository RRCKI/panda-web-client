$(document).ready(function() {
    moment.locale('ru');

    $('#contstable').dataTable( {
        "order": [[ 0, "desc" ]],
        "processing": true,
        "ajax": "/cont/list",
        "columns": [
            { "data": "id"},
            { "data": "guid" },
            { "data": "status" },
            { "data": "n" }
        ],
        // Add link - start
        "aoColumnDefs": [
            { //PandaID
                "aTargets":[1],
                "mData": null,
                "mRender": function( data, type, full) {
                    if ( data != undefined ) {
                        return '<td><a href="/cont/'+data+'" class="monlink">'+data+'</a></td>';
                    }
                    return '<td></td>';
                }
            }
        ],
            // Add link  - end
    } );
} );