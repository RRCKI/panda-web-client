/*$(document).ready(function() {
    $('#jobstable').dataTable( {
        "order": [[ 3, "desc" ]]
    } );
} );*/

$(document).ready(function() {
    moment.locale('ru');

    $('#jobstable').dataTable( {
        "processing": true,
        "ajax": "/jobs/list",
        "columns": [
            { "data": "owner.username" },
            { "data": "pandaid" },
            { "data": "distr.name" },
            { "data": "creation_time" },
            { "data": "modification_time" },
            { "data": "status" }
        ],
        // Add link - start
        "aoColumnDefs": [
            { //PandaID
                "aTargets":[1],
                "mData": null,
                "mRender": function( data, type, full) {
                    return '<td><a href="http://144.206.233.185/job/'+data+'" class="monlink">'+data+'</a></td>';
                }
            },
            { //CreationDate, ModificationDate
                "aTargets":[3,4],
                "mData": null,
                "mRender": function( data, type, full) {
                    return moment(data).format('D.MM.YYYY H:mm');
                }
            },
            { //Status
                "aTargets":[5],
                "fnCreatedCell": function(nTd, sData, oData, iRow, iCol)
                {
                    if ( sData == "finished" ) {
                        $(nTd).css('color', 'green')
                    }
                    if ( sData == "pending" ) {
                        $(nTd).css('color', 'grey')
                    }
                    if ( sData == "failed" ) {
                        $(nTd).css('color', 'red')
                    }
                },
                "mData": null
            }
        ],
            // Add link  - end
    } );
} );