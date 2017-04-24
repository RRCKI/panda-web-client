/*$(document).ready(function() {
    $('#jobstable').dataTable( {
        "order": [[ 3, "desc" ]]
    } );
} );*/

function updateTable(){
    var tag = $("#tagFilter").val();
    var status = $("#statusFilter").val();
    var query_string = $.param({"status" : status, "tag" : tag})
    var ajax_source = "/jobs/list?" + query_string
    var table = $("#jobstable").DataTable(); // get api instance
    // load data using api
    table.ajax.url(ajax_source).load();
};

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
            { "data": "attemptnr" },
            { "data": "status" }
        ],
        // Add link - start
        "aoColumnDefs": [
            { //ID
                "aTargets":[0],
                "mData": null,
                "mRender": function( data, type, full) {
                    if ( data != undefined ) {
                        return '<td><a href="/jobs/'+data+'">'+data+'</a></td>';
                    }
                    return '<td></td>';
                }
            },
            { //PandaID
                "aTargets":[2],
                "mData": null,
                "mRender": function( data, type, full) {
                    if ( data != undefined ) {
                        return '<td><a href="/lsst/job/'+data+'" class="monlink">'+data+'</a></td>';
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
            },
            { //Attemptnr
                "aTargets":[6],
                "mData": null,
                "mRender": function( data, type, full) {
                    if ( data != undefined ) {
                        return '<td>'+data+'</td>';
                    }
                    return '<td></td>';
                }
            },
            { //Status
                "aTargets":[7],
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

    setInterval( function () {
        updateTable();
    }, 60000);
} );