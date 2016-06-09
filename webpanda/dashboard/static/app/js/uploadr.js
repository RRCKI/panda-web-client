/******************************************************************************
 * HTML5 Multiple File Uploader Demo                                          *
 ******************************************************************************/

// Constants
var MAX_UPLOAD_FILE_SIZE = 1024*1024; // 1 MB
var UPLOAD_URL = "/upload";
var NEXT_URL   = "/upload/success";

// List of pending files to handle when the Upload button is finally clicked.
var PENDING_FILES  = [];


$(document).ready(function() {
    // Set up the drag/drop zone.
    initDropbox();

    // Set up the handler for the file input box.
    $("#file-picker").on("change", function() {
        handleFiles(this.files);
    });

    // Handle the submit button.
    $("#submitbtn").on("click", function(e) {
        // If the user has JS disabled, none of this code is running but the
        // file multi-upload input box should still work. In this case they'll
        // just POST to the upload endpoint directly. However, with JS we'll do
        // the POST using ajax and then redirect them ourself when done.
        e.preventDefault()
        doUpload()
    });

    //$('#upload-form').submit(function( event ) {
    //    event.preventDefault()
    //    doUpload();
    //    fd = collectFormData();
    //});

    // The maximum number of options
    var MAX_OPTIONS = 5;
    // Add button click handler
    $('#upload-form')
        .on('click', '.addButton', function() {
            var $template = $('#ifTemplate'),
                $clone    = $template
                                .clone()
                                .removeClass('hide')
                                .removeAttr('id')
                                .insertBefore($template),
                $option   = $clone.find('[name="ifiles[]"]');
        })

        // Remove button click handler
        .on('click', '.removeButton', function() {
            var $row    = $(this).parents('.ifile'),
                $option = $row.find('[name="ifiles[]"]');

            // Remove element containing the option
            $row.remove();

        })

        // Called after adding new field
        .on('added.field.fv', function(e, data) {
            // data.field   --> The field name
            // data.element --> The new field element
            // data.options --> The new field options

            if (data.field === 'ifiles[]') {
                if ($('#upload-form').find(':visible[name="ifiles[]"]').length >= MAX_OPTIONS) {
                    $('#upload-form').find('.addButton').attr('disabled', 'disabled');
                }
            };

	    if (data.field === 'iguids[]') {
                if ($('#upload-form').find(':visible[name="iguids[]"]').length >= MAX_OPTIONS) {
                    $('#upload-form').find('.addGuidButton').attr('disabled', 'disabled');
                }
            };

	    if (data.field === 'iconts[]') {
                if ($('#upload-form').find(':visible[name="iconts[]"]').length >= MAX_OPTIONS) {
                    $('#upload-form').find('.addContButton').attr('disabled', 'disabled');
                }
            }


        })

        // Called after removing the field
        .on('removed.field.fv', function(e, data) {
           if (data.field === 'ifiles[]') {
                if ($('#upload-form').find(':visible[name="ifiles[]"]').length < MAX_OPTIONS) {
                    $('#upload-form').find('.addButton').removeAttr('disabled');
                }
            };
	    
	    if (data.field === 'iguids[]') {
                if ($('#upload-form').find(':visible[name="iguids[]"]').length < MAX_OPTIONS) {
                    $('#upload-form').find('.addGuidButton').removeAttr('disabled');
                }
            };

	    if (data.field === 'iconts[]') {
                if ($('#upload-form').find(':visible[name="iconts[]"]').length < MAX_OPTIONS) {
                    $('#upload-form').find('.addContButton').removeAttr('disabled');
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
	
	.on('click', '.addContButton', function() {
            var $template = $('#icTemplate'),
                $clone    = $template
                                .clone()
                                .removeClass('hide')
                                .removeAttr('id')
                                .insertBefore($template),
                $option   = $clone.find('[name="iconts[]"]');
        })

	.on('click', '.removeContButton', function() {
            var $row    = $(this).parents('.icont'),
                $option = $row.find('[name="iconts[]"]');

            // Remove element containing the option
            $row.remove();
        })
});


function doUpload() {
    $("#progress").show();
    var $progressBar   = $("#progress-bar");

    // Gray out the form.
    $("#upload-form :input").prop("disabled", true);

    // Initialize the progress bar.
    $progressBar.css({"width": "0%"});

    // Collect the form data.
    fd = collectFormData();

    // Attach the files.
    for (var i = 0, ie = PENDING_FILES.length; i < ie; i++) {
        // Collect the other form data.
        fd.append("file", PENDING_FILES[i]);
    }

    // Inform the back-end that we're doing this over ajax.
    fd.append("__ajax", "true");

    var xhr = $.ajax({
        xhr: function() {
            var xhrobj = $.ajaxSettings.xhr();
            if (xhrobj.upload) {
                xhrobj.upload.addEventListener("progress", function(event) {
                    var percent = 0;
                    var position = event.loaded || event.position;
                    var total    = event.total;
                    if (event.lengthComputable) {
                        percent = Math.ceil(position / total * 100);
                    }

                    // Set the progress bar.
                    $progressBar.css({"width": percent + "%"});
                    $progressBar.text(percent + "%");
                }, false)
            }
            return xhrobj;
        },
        url: UPLOAD_URL,
        method: "POST",
        contentType: false,
        processData: false,
        cache: false,
        data: fd,
        success: function(data) {
            $progressBar.css({"width": "100%"});
            data = JSON.parse(data);
            $("#upload-form :input").prop("disabled", false);

            if (data.status === "error") {
                window.alert(data.msg);
                return;
            }
            else {
                var uuid = data.msg;
                var oForm = document.getElementById('upload-form');
                var Base64={_keyStr:"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",encode:function(e){var t="";var n,r,i,s,o,u,a;var f=0;e=Base64._utf8_encode(e);while(f<e.length){n=e.charCodeAt(f++);r=e.charCodeAt(f++);i=e.charCodeAt(f++);s=n>>2;o=(n&3)<<4|r>>4;u=(r&15)<<2|i>>6;a=i&63;if(isNaN(r)){u=a=64}else if(isNaN(i)){a=64}t=t+this._keyStr.charAt(s)+this._keyStr.charAt(o)+this._keyStr.charAt(u)+this._keyStr.charAt(a)}return t},decode:function(e){var t="";var n,r,i;var s,o,u,a;var f=0;e=e.replace(/[^A-Za-z0-9\+\/\=]/g,"");while(f<e.length){s=this._keyStr.indexOf(e.charAt(f++));o=this._keyStr.indexOf(e.charAt(f++));u=this._keyStr.indexOf(e.charAt(f++));a=this._keyStr.indexOf(e.charAt(f++));n=s<<2|o>>4;r=(o&15)<<4|u>>2;i=(u&3)<<6|a;t=t+String.fromCharCode(n);if(u!=64){t=t+String.fromCharCode(r)}if(a!=64){t=t+String.fromCharCode(i)}}t=Base64._utf8_decode(t);return t},_utf8_encode:function(e){e=e.replace(/\r\n/g,"\n");var t="";for(var n=0;n<e.length;n++){var r=e.charCodeAt(n);if(r<128){t+=String.fromCharCode(r)}else if(r>127&&r<2048){t+=String.fromCharCode(r>>6|192);t+=String.fromCharCode(r&63|128)}else{t+=String.fromCharCode(r>>12|224);t+=String.fromCharCode(r>>6&63|128);t+=String.fromCharCode(r&63|128)}}return t},_utf8_decode:function(e){var t="";var n=0;var r=c1=c2=0;while(n<e.length){r=e.charCodeAt(n);if(r<128){t+=String.fromCharCode(r);n++}else if(r>191&&r<224){c2=e.charCodeAt(n+1);t+=String.fromCharCode((r&31)<<6|c2&63);n+=2}else{c2=e.charCodeAt(n+1);c3=e.charCodeAt(n+2);t+=String.fromCharCode((r&15)<<12|(c2&63)<<6|c3&63);n+=3}}return t}}
                oForm.elements["container"].value = uuid;
                var vallist = oForm.elements["params"].value.split(";")
                var b64list = vallist.map(function(val){
                    return Base64.encode(val.trim())
                });
                oForm.elements["params"].value = b64list.join(";")
                oForm.submit()
            }
        },
    });
}

function collectFormData() {
    // Go through all the form fields and collect their names/values.
    var fd = new FormData();

    $("#upload-form :input").each(function() {
        var $this = $(this);
        var name  = $this.attr("name");
        var type  = $this.attr("type") || "";
        var value = $this.val();

        // No name = no care.
        if (name === undefined) {
            return;
        }

        // Skip the file upload box for now.
        if (type === "file") {
            return;
        }

        // Checkboxes? Only add their value if they're checked.
        if (type === "checkbox" || type === "radio") {
            if (!$this.is(":checked")) {
                return;
            }
        }

        fd.append(name, value);
    });

    return fd;
}


function handleFiles(files) {
    // Add them to the pending files list.
    for (var i = 0, ie = files.length; i < ie; i++) {
        PENDING_FILES.push(files[i]);
    }
}


function initDropbox() {
    var $dropbox = $("#dropbox");

    // On drag enter...
    $dropbox.on("dragenter", function(e) {
        e.stopPropagation();
        e.preventDefault();
        $(this).addClass("active");
    });

    // On drag over...
    $dropbox.on("dragover", function(e) {
        e.stopPropagation();
        e.preventDefault();
    });

    // On drop...
    $dropbox.on("drop", function(e) {
        e.preventDefault();
        $(this).removeClass("active");

        // Get the files.
        var files = e.originalEvent.dataTransfer.files;
        handleFiles(files);

        // Update the display to acknowledge the number of pending files.
        $dropbox.text(PENDING_FILES.length + " files ready for upload!");
    });

    // If the files are dropped outside of the drop zone, the browser will
    // redirect to show the files in the window. To avoid that we can prevent
    // the 'drop' event on the document.
    function stopDefault(e) {
        e.stopPropagation();
        e.preventDefault();
    }
    $(document).on("dragenter", stopDefault);
    $(document).on("dragover", stopDefault);
    $(document).on("drop", stopDefault);
}
