function getFileData() {
    if ("files" in localStorage && !isLoggedIn)
        return JSON.parse(localStorage["files"])
    return serverFiles
}

function saveFile() {
    if (!isLoggedIn) {
        var $files = $('#file-browser');
    
        localStorage["files"] = JSON.stringify($files.jstree(true).get_json('#', {'flat':true}));
    } else {
        // perform ajax call.
    }
}
