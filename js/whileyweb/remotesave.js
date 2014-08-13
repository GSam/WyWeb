function saveToServer() {
    _selectedFile.data = editor.getValue() // Fix, current file doesn't save correctly.

    var request = {};
    var $files = $('#file-browser');
    addFiles($files, "", "#", request);

    $.post(root_url + '/private_save',  request, function() {});
}
