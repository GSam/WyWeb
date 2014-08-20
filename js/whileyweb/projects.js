function addProject() {
    $('#file-browser').jstree('create_node', null, undefined, undefined, function(type) {
        $('#file-browser').jstree('set_type', type, 'project')
    })
}
