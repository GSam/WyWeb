function addProject() {
    $('#file-browser').jstree('create_node', null, {text: 'UntitledProject'}, undefined, function(type) {
        $('#file-browser').jstree('set_type', type, 'project')
    })
}
