var form_data = null

function gather_file_ids() {
    var tbody = $('#files_table').find('tbody')
    var table_rows = tbody.find('tr')
    var file_ids = []

    for(i=0; i<table_rows.length; i++) {
        row_id = table_rows.eq(i).attr('id')
        if(row_id.startsWith('file_')) {
            file_ids.push(row_id.substring(5))
        }
    }

    return file_ids
}

function trigger_process(file_ids) {
    if (file_ids.length > 0) {
        file_id = file_ids[0]
        $("#file_" + file_id).find('td').eq(1).html("processing")

        $.ajax({
            url: '/api/process/' + file_id,
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                var $file_row = $("#file_" + file_id)
                $file_row.find('td').eq(1).html("success");
                var cell = $file_row.find('td').eq(2);
                var cell2 = $file_row.find('td')[2];
                cell.empty();
                cell.removeClass('disabled');
                $('<a/>', {href: 'details/' + file_id, text: 'QML details', target: '_blank'})
                    .appendTo(cell2);

                var cell3 = $file_row.find('td').eq(3);
                var cell4 = $file_row.find('td')[3];
                cell3.empty();
                cell3.removeClass('disabled');

                for (let j = 0; j < 3; j++) {
                    $('<a/>', {href: 'flowchart/' + file_id + '_' + j, text: j+'', target: '_blank'})
                        .appendTo(cell4);
                }





                trigger_process(file_ids.slice(1));
            },
            error: function (request, error) {
                $("#file_" + file_id).find('td').eq(1).html("error");
                trigger_process(file_ids.slice(1));
            }
        });
        for (let i = 0; i < uploaded_files.length; i++) {
            if (uploaded_files[i].hasOwnProperty(['flowchart'])) {
                if (uploaded_files[i]['flowchart'].length > 0) {
                    let file_idx = uploaded_files[i]['file_id'];
                    let $file_row = $("#file_" + file_id);
                    var cell = $file_row.find('td').eq(3);
                    var cell2 = $file_row.find('td')[3];
                    cell.empty();
                    cell.removeClass('disabled');

                    for (let j = 0; j < uploaded_files[i]['flowchart'].length; j++) {
                        $('<a/>', {href: 'flowchart/' + file_id + '_' + j, text: j})
                            .appendTo(cell2);
                    }

                }
            }
        }
    }
}
function submit_form() {
    var form = $('#upload_form')[0]
    form_data = new FormData(form);

    $.ajax({
        type: 'POST',
        url: '/api/upload',
        data: form_data,
        success : function(data) {
            var tbody = $('#files_table').find('tbody');
            tbody.append('<tr>');
            var new_row = tbody.find('tr').last();
            new_row.attr('id', 'file_' + data['file_id']);
            new_row.append('<td>');
            new_row.append('<td>');
            new_row.append('<td>');
            new_row.append('<td>');
            new_row.append('<td>');
            new_row.find('td').eq(0).html(data['filename']);
            new_row.find('td').eq(1).html('uploaded');
            new_row.find('td').eq(2).html('not yet processed');
            new_row.find('td').eq(3).html('not yet processed');
            new_row.find('td').eq(4).html('');

            var cell = new_row.find('td').eq(4);
            var cell2 = new_row.find('td')[4];
            cell.empty();
            $('<a/>', { href: 'remove/'+data['file_id'], text: 'x' })
                .appendTo(cell2);

            new_row.find('td')[2].classList.add('disabled');
            new_row.find('td')[3].classList.add('disabled');
        },
        error : function(request, error) {
            alert(request);
        },
        processData: false,
        contentType: false
    })
}

$( document ).ready(function() {
    $('#upload_button').click(function() {
        submit_form()
    });

    $('#process_button').click(function() {
        trigger_process(gather_file_ids())
    });
});
