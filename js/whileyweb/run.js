/**
 * Compile and run a given snippet of Whiley code.
 */
function run() {
    var console = document.getElementById("console");
    var verify = document.getElementById("verification");

    var $files = $('#file-browser');
    var main = getPath($files, $files.jstree('get_selected')[0]) + ".whiley";
    var request = { _main: main, _verify: verify.checked };
    addFiles($files, "", "#", request, main.split("/")[0]);
    $.post(root_url + "/run_all", request, function(response) {
        clearMessages();
        console.value = "";
        $("#spinner").hide();
        var response = $.parseJSON(response);
        if(response.result == "success") {
            clearErrors(true);
            addMessage("success", "Compiled successfully. Running...");
            setTimeout(function() {console.value = response.output;}, 500);
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
