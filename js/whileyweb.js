// Global reference to the code editor.
var editor;

/**
 * Add a new message to the message list above the console.
 */
function addMessage(message_class, message_text, callback) {
    var message = $("<div></div>");
    message.text(message_text);
    message.addClass("message");
    message.addClass(message_class);
    message.appendTo("#messages");
    message.fadeIn(200).delay(2000).slideUp(200, function() {
        message.remove();
        if (callback !== undefined) {
            callback();
        }
    });
}

/**
 * Remove all messages from the message list above the console.
 */
function clearMessages() {
    $("#messages").children().remove();
}

/**
 * Display all the compilation errors.
 */
function showErrors(errors) {
    var box_exists = $("#errors").length;
    if(box_exists) {
        var error_box = $("#errors");
        error_box.children(".error").remove();
    } else {
        var error_box = $("<div id=\"errors\"><div id=\"title\">Errors</div></div>");
    }
    for(var i=0;i!=errors.length;++i) {
        var error = $("<div></div>");
        error.text(errors[i].text);
        error.addClass("error");
        error.bind("mouseenter", {err: errors[i]}, function(event) {
            markError(event.data.err);
        });
        error.bind("mouseleave", function(event) {
            var markers = editor.getAllMarks();
            for(var i=0;i!=markers.length;++i) {
                markers[i].clear();
            }
            editor.clearGutter("errorGutter");
        });
        error.appendTo(error_box);
    }
    if(!box_exists) {
        error_box.prependTo(".CodeMirror");
        error_box.animate({
            width: "30%"
        }, 500, function() {
            $(".CodeMirror-scroll").width("70%");
        });
    }
}

/**
 * Add an appropriate marker for a given JSON error object, as
 * returned from the server.
 */
function markError(error) {
    if(error.start != "" && error.end != "" && error.line != "") {
        var start = {line: error.line-1, ch: error.start};
        var end = {line: error.line-1, ch: error.end+1};
        editor.markText(start, end, {className: "errorMarker", title: error.text});
    }
    if(error.line != "") {
        var marker = document.createElement("img");
        marker.src = "images/cross.png";
        marker.width = 10;
        editor.setGutterMarker(error.line-1, "errorGutter", marker);
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
    $(".CodeMirror-scroll").width("100%");
    var markers = editor.getAllMarks();
    for(var i=0;i!=markers.length;++i) {
        markers[i].clear();
    }
    editor.clearGutter("errorGutter");
    $("#errors").animate({
        width: "0"
    }, 500, function() {
        $("#errors").remove();
    });
}

/**
 * Compile a given snippet of Whiley code.
 */
function compile() {
    var console = document.getElementById("console");
    var verify = document.getElementById("verification");
    var request = { code: editor.getValue(), verify: verify.checked };
    $.post(root_url + "/compile", request, function(response) {
        clearMessages();
        console.value = "";
        $("#spinner").hide();
        var response = $.parseJSON(response);
        if(response.result == "success") {
            clearErrors();
            addMessage("success", "Compiled successfully.");
        } else if(response.result == "errors") {
            var errors = response.errors;
            showErrors(errors);
            addMessage("error", "Compilation failed: " + errors.length + " error" + (errors.length > 1 ? "s." : "."));
        } else if(response.result == "error") {
            clearErrors();
            addMessage("error", response.error);
        }
    });
    $("#spinner").show();
}

/**
 * Compile and run a given snippet of Whiley code.
 */
function run() {
    var console = document.getElementById("console");
    var request = { code: editor.getValue() };
    $.post(root_url + "/run", request, function(response) {
        clearMessages();
        console.value = "";
        $("#spinner").hide();
        var response = $.parseJSON(response);
        if(response.result == "success") {
            clearErrors();
            addMessage("success", "Compiled successfully. Running...");
            setTimeout(function() {console.value = response.output;}, 500);
        } else if(response.result == "errors") {
            var errors = response.errors;
            showErrors(errors);
            addMessage("error", "Compilation failed: " + errors.length + " error" + (errors.length > 1 ? "s." : "."));
        } else if(response.result == "error") {
            clearErrors();
            addMessage("error", response.error);
        }
    });
    $("#spinner").show();
}

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

// Run this code when the page has loaded.
$(document).ready(function() {
    // Enable the editor with Whiley syntax.
    editor = CodeMirror.fromTextArea(document.getElementById("code"), {
        indentUnit: 4,
        lineNumbers: true,
        gutters: ["CodeMirror-linenumbers", "errorGutter"],
        matchBrackets: true,
        mode: "whiley"
    });

    // If there is an error, display the error message for 5 seconds.
    if(error != "") {
        var error_message = $("<div></div>");
        error_message.text(error);
        error_message.addClass("error");
        error_message.prependTo("#content");
        error_message.show().delay(2000).fadeOut(500, function() {
            // If the user should be redirected to the main page (due to invalid ID for example), do so.
            if(redirect == "YES") {
                window.location.replace(root_url + "/");
            }
        });
    }
});