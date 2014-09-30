/**
 * Display all the compilation errors.
 */
function showErrors(errors) {
    clearErrors();
    for(var i=0;i!=errors.length;++i) {
        var error = errors[i];
        markError(error);
    }
}

/**
 * Add an appropriate marker for a given JSON error object, as
 * returned from the server.
 */
function markError(error) {
    if(error.start !== "" && error.end !== "" && error.line !== "") {
        // Switch to appropriate file
        var filepath = error.filename.split("/").slice(2) // First 2 directories are gibberish
        var tree = $("#file-browser").jstree(true).get_json('#')
        for (var i = 0; i < filepath.length; i++) {
            var pathComponent = filepath[i].split(".")[0];
            if ("children" in tree) tree = tree.children;
            for (var j = 0; j < tree.length; j++) {
                if (tree[j].text == pathComponent) {
                    tree = tree[j]
                    break
                }
            }
        }

        window.setTimeout(function() {
            // Select it, and fill the text
            $("#file-browser").jstree(true).select_node(tree.id);

            // And mark the error
            editor.getSession().setAnnotations([{
                row: error.line - 1,
                column: error.start,
                text: error.text.replace("\\n", "\n"),
                type: "error"
            }]);
            var range = new ace.Range(error.line-1, error.start, error.line-1, error.end+1);
            editor.markers.push(editor.getSession().addMarker(range, "error-message", "error", false));
        }, 0);
    } else {
        addMessage("error", error.text);
    }
}

/**
 * Clear all the compilation errors.
 *
 * Clear all markers (including those in the gutter) from the editor.
 * This is to prevent markers from a previous compilation from hanging
 * around.
 */
function clearErrors() {
    editor.getSession().clearAnnotations();
    for (var i = 0; i < editor.markers.length; i++) {
        editor.getSession().removeMarker(editor.markers[i]);
    }
    editor.markers = [];
}
