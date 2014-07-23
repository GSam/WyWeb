/**
 * Save a given snippet of Whiley code.
 */
function save() {
    var request = { code: editor.getValue() };
    $.post(root_url + "/save", request, function(response) {
        clearMessages();
        var response = $.parseJSON(response);
        $("#spinner").hide();
        addMessage("success", "Saved program as " + response.id + ".", function() {
            window.location.replace("?id=" + response.id);
        });
    });
    $("#spinner").show();
}


