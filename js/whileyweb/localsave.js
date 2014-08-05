function getFileData() {
    if ("files" in localStorage)
        return JSON.parse(localStorage["files"])
    return [
                {
                    text: 'Project 1',
                    state: {
                        opened: true
                    },
                    children: [
                        {
                            text: 'Hello World',
                            type: 'file',
                            data: "import whiley.lang.System\n\nmethod main(System.Console console):\n    console.out.println(\"Hello World\")",
                            state: {
                                selected: true
                            }
                        }
                    ]
                }
            ]
}

function saveFile() {
    var $files = $('#file-browser');
    
    localStorage["files"] = JSON.stringify($files.jstree(true).get_json('#', {'flat':true}));
}
