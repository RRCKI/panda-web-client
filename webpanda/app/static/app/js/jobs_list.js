/*$(document).ready(function() {
    $('#jobstable').dataTable( {
        "order": [[ 3, "desc" ]]
    } );
} );*/

$(document).ready(function() {
    moment.locale('ru');

    $('#jobstable').dataTable( {
        "order": [[ 0, "desc" ]],
        "processing": true,
        "ajax": "/jobs/list",
        "columns": [
            { "data": "id"},
            { "data": "owner.username" },
            { "data": "pandaid" },
            { "data": "distr.str" },
            { "data": "creation_time" },
            { "data": "modification_time" },
            { "data": "status" },
            { "data": "ifiles" },
            { "data": "ofiles" }
        ],
        // Add link - start
        "aoColumnDefs": [
            { //ID
                "aTargets":[0],
                "mData": null,
                "mRender": function( data, type, full) {
                    if ( data != undefined ) {
                        return '<td><a href="/job/'+data+'">'+data+'</a></td>';
                    }
                    return '<td></td>';
                }
            },
            { //PandaID
                "aTargets":[2],
                "mData": null,
                "mRender": function( data, type, full) {
                    if ( data != undefined ) {
                        return '<td><a href="http://144.206.233.187/lsst/job/'+data+'" class="monlink">'+data+'</a></td>';
                    }
                    return '<td></td>';
                }
            },
            { //CreationDate, ModificationDate
                "aTargets":[4,5],
                "mData": null,
                "mRender": function( data, type, full) {
                    return moment(data).format('D.MM.YYYY H:mm');
                }
            },
            { //Status
                "aTargets":[6],
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