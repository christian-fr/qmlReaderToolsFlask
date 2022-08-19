
function trigger_process(files, idx) {
    if(files.length > 0) {
        file_idx = idx
        file_name = files[0]
        $("#file_" + file_idx).find('td').eq(1).html("processing")

        $.ajax({
            url : '/process/' + file_name,
            type : 'GET',
            dataType: 'json',
            success : function(data) {
                $("#file_" + file_idx).find('td').eq(1).html("success")
                trigger_process(files.slice(1), idx+1)
            },
            error : function(request, error) {
                $("#file_" + file_idx).find('td').eq(1).html("error")
                trigger_process(files.slice(1), idx+1)
            }
        });
    }
}

$( document ).ready(function() {
    trigger_process(window.uploaded_files, 0)
});

