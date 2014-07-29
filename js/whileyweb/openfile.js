var _selectedFile, _fileLoading = false;

$(function() {
    $('#file-browser').on('changed.jstree', function(evt, data) {
        if (data && data.node && "data" in data.node) {
            _fileLoading = true
            editor.setValue(data.node.data, 0);
            _fileLoading = false
            _selectedFile = data.node
        }
    })
})

$(document).on('ace-loaded', function() {
    editor.on('change', function() {
        if (!_fileLoading) {
            _selectedFile.data = editor.getValue()
        }
    })
})
