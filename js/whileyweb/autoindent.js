$(document).on("ace-loaded", function autoindent() {
    editor.on("change", function(evt) {
        if (evt.data.action == "insertText" && evt.data.text == "\n") {
            var line = evt.data.range.end.row,
                prevLine = evt.data.range.start.row,
                doc = editor.getSession().getDocument(),
                prevLineText = doc.getLine(prevLine);
            if (prevLineText.charAt(prevLineText.length - 1) == ":")
                window.setTimeout(function() {editor.indent()}, 0);
        }
    })
});
