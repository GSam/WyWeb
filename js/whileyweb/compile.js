/**
 * Compile a given snippet of Whiley code.
 */
function compile() {
    var console = document.getElementById("console");
    var verify = document.getElementById("verification");

    // build parameters
    var $files = $('#file-browser');
    var main = getPath($files, $files.jstree('get_selected')[0]) + ".whiley";
    var request = { _main: main, _verify: verify.checked };
    addFiles($files, "", "#", request);
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
function addFiles($files, prefix, node, query) {
    var data = $files.jstree('get_node', node);
    if (data.type == "file")
        query[prefix + "/" + data.text + ".whiley"] = data.data;
    else for (var i = 0; i < data.children.length; i++) {
        addFiles($files, prefix ? prefix + "/" + data.text : data.text, data.children[i], query);
    }
}
function getPath($files, node) {
    if (node == '#') return ""
    var data = $files.jstree('get_node', node);
    if (!data || !data.text || !data.text.length) return ""
    return getPath($files, data.parent) + "/" + data.text;
}
