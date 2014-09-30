var _selectedFile, _fileLoading = false;
var _newFile = false;

$(function() {
    $('#file-browser').on('changed.jstree', function(evt, data) {
        if (data && data.node && "data" in data.node) {
            _fileLoading = true
            editor.setValue(data.node.data, 0);
            _newFile = true;
            _fileLoading = false
            _selectedFile = data.node
        }
    }).on('loaded.jstree', function() {
        _selectedFile = $(this).jstree('get_node', $(this).jstree('get_selected')[0])
    })
})

$(document).on('ace-loaded', function() {
    editor.on('change', function() {
        if (!_fileLoading) {
            _selectedFile.data = editor.getValue()
            saveFile()
        }
    })
})

