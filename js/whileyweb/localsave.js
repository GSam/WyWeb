function getFileData() {
    if ("files" in localStorage && !isLoggedIn) {
        return JSON.parse(localStorage["files"])
    }

    if (isLoggedIn && loggedStorage != undefined) {
        return loggedStorage;
    }
    
    return serverFiles
}

function saveFile() {
    if (!isLoggedIn) {
        var $files = $('#file-browser');
    
        localStorage["files"] = JSON.stringify($files.jstree(true).get_json('#', {'flat':true}));
    } else {
        var $files = $('#file-browser');
        loggedStorage = JSON.stringify($files.jstree(true).get_json('#', {'flat':true}));
    }
}
