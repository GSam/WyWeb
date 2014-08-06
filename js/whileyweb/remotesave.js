if (isLoggedIn) {
    // Start the timer as late as possible
    $(document).on('ace-loaded', function() {
        window.setInterval(saveToServer, 30*1000);
    })
    $(document).on('unload', saveToServer);
}

function saveToServer() {
    var request = {};
    var $files = $('#file-browser');
    addFiles($files, "", "#", request);

    $.post('/private_save',  request);
}
