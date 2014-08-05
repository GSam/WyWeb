/**
 * Compile a given snippet of Whiley code.
 */
function compile() {
    var console = document.getElementById("console");
    var verify = document.getElementById("verification");

    // build parameters
    var $files = $('#file-browser');
    var main = getPath($files.js_tree('get_selected')[0])
    var request = { _main: main, _verify: verify.checked };
    addFiles("", "#", request);
    $.post(root_url + "/compile_all", request, function(response) {
        clearMessages();
        console.value = "";
        $("#spinner").hide();
        var response = $.parseJSON(response);
        if(response.result == "success") {
            clearErrors(true);
            addMessage("success", "Compiled successfully.");
        } else if(response.result == "errors") {
            var errors = response.errors;
            showErrors(errors);
            addMessage("error", "Compilation failed: " + errors.length + " error" + (errors.length > 1 ? "s." : "."));
        } else if(response.result == "error") {
            clearErrors(true);
            addMessage("error", response.error);
        }
    });
    $("#spinner").show();
}
function addFiles(prefix, node, query) {
    var data = $files.jstree('get_node', node);
    if (data.type == "file")
        query[prefix + data.text] = data.data;
    else for (var i = 0; i < data.children.length; i++) {
        addFiles(prefix + "/" + data.text, data.children[i], query);
    }
}
function getPath(node) {
    var data = $files.jstree('get_node', node);
    return get(data.parent) + "/" + data.text;
}
