window.onload = function () {
    // create the input button and use it to replace the span/placeholder --
    // users without javascript won't notice anything.
    // This might eventually be replaced by jquery
    var node_id = 'add_me_to_nosy';
    var add_me_span = document.getElementById(node_id);
    if (add_me_span == null) {
        // we are already in the nosy or we are not logged in
        return;
    }
    var add_me_button = document.createElement('input');
    var add_me_parent = add_me_span.parentNode;
    add_me_button.type = 'button';
    add_me_button.value = '+';
    add_me_button.title = 'Add me to the nosy list (remember to Submit Changes)';
    add_me_button.onclick = add_me_span.onclick;
    add_me_button.style.display = 'inline';
    add_me_parent.replaceChild(add_me_button, add_me_span);
    add_me_button.id = node_id;
}


function add_to_nosy(user) {
    var add_me_button = document.getElementById('add_me_to_nosy');
    var nosy = document.getElementsByName('nosy')[0];
    // remove spaces at the beginning/end of the string and around the commas
    var nosy_text = nosy.value.replace(/^[\s,]*|[\s,]*$/g, '').replace(/\s*,\s*/g, ',');
    if (nosy_text == "") {
        // nosy_list is empty, add the user
        nosy.value = user;
    }
    else {
        re = new RegExp("(^|,)" + user + "(,|$)");
        if (!re.test(nosy_text)) {
            // make sure the user is not in nosy and then add it at the beginning
            nosy.value = user + ',' + nosy_text;
        }
    }
    // hide the button and resize the list to fill the void
    var new_width = nosy.offsetWidth + add_me_button.offsetWidth;
    add_me_button.style.display = 'none';
    nosy.style.display = 'inline';
    nosy.style.width = new_width + "px";
}


$(document).ready(function() {
    /* Keyboard shortcuts */
    function is_editing(node) {
        // return true if the focus is on a form element
        var element = node.nodeName;
        return ((element == 'TEXTAREA') || (element == 'SELECT') ||
                (element == 'INPUT' && node.type != 'file'));
    }
    function scroll_to(node) {
        // scroll the page to the given node
        window.scrollTo(0, node.offset().top)
    }
    function add_help() {
        // add some help to the sidebar
        $(['<li><strong>Keyboard shortcuts</strong>',
           '<ul id="help" class="level-three">',
           '  <li><a>f/h: first msg</a></li>',
           '  <li><a>p/k: previous msg</a></li>',
           '  <li><a>n/j: next msg</a></li>',
           '  <li><a>l: last msg</a></li>',
           '  <li><a>r/i: focus textarea</a></li>',
           '  <li><a>ESC: unfocus textarea</a></li>',
           '</ul></div>'].join('\n')).appendTo('div#menu ul.level-two');
        // the empty <a> are just an hack to get the style right,
        // this help will anyway be moved to the devguide soon
    }
    add_help()
    var textarea = $('textarea').first();
    var messages = $('table.messages tr th a:first-child');
    var last_index = messages.length - 1;
    // start from -1 so 'n' sends to the first message at the beginning
    var current = -1;
    $(document).keydown(function (event) {
        // do nothing if ctrl/alt/shift are pressed
        if (event.ctrlKey || event.altKey || event.shiftKey)
            return true;

        // disable the shortcuts while editing form elements (except ESC)
        if (is_editing(event.target)) {
            // ESC - unfocus the form
            if (event.keyCode == 27) {
                $(event.target).blur();
                return false;
            }
            return true;
        }

        // support two groups of shortcuts for first/prev/next/last/reply:
        //    mnemonics: f/p/n/l/r
        //    vim-style: h/k/j/l/i
        switch (event.which) {
            // f/h - first
            case 70:
            case 72:
                scroll_to(messages.first());
                current = 0;
                return false;
            // p/k - previous
            case 80:
            case 75:
                if (current <= 0)
                    return false;
                scroll_to(messages.eq(--current));
                return false;
            // n/j - next
            case 78:
            case 74:
                if (current >= last_index)
                    return false;
                scroll_to(messages.eq(++current));
                return false;
            // l - last
            case 76:
                scroll_to(messages.last());
                current = last_index;
                return false;
            // r/i - reply
            case 82:
            case 73:
                // do nothing if the textarea is not available
                if (textarea.length == 0)
                    return false;
                scroll_to(textarea);
                textarea.focus();
                return false;
            default:
                return true;
        }
    });
})


$(document).ready(function() {
    /* Add an autocomplete to the nosy list that searches the term in two lists:
         1) the list of developers (both the user and the real name);
         2) the list of experts in the devguide;
       See also the "categories" and "multiple values" examples at
       http://jqueryui.com/demos/autocomplete/. */

    if ($("input[name=nosy]").length == 0) {
        // if we can't find the nosy <input>, the user can't edit the nosy
        // so there's no need to load the autocomplete
        return;
    }

    // create a custom widget to group the entries in categories
    $.widget("custom.catcomplete", $.ui.autocomplete, {
        _renderMenu: function(ul, items) {
            var self = this, current_category = "";
            // loop through the items, adding a <li> when a new category is
            // found, and then render the item in the <ul>
            $.each(items, function(index, item) {
                if (item.category != current_category) {
                    ul.append("<li class='ui-autocomplete-category'>" + item.category + "</li>");
                    current_category = item.category;
                }
                self._renderItem(ul, item);
            });
        }
    });

    function split(val) {
        return val.split(/\s*,\s*/);
    }
    function extract_last(term) {
        return split(term).pop();
    }
    function unix_time() {
        return Math.floor(new Date().getTime() / 1000);
    }
    function is_expired(time_str) {
        // check if the cached file is older than 1 day
        return ((unix_time() - parseInt(time_str)) > 24*60*60);
    }

    // this will be called once we have retrieved the data
    function add_autocomplete(data) {
        $("input[name=nosy]")
            // don't navigate away from the field on tab when selecting an item
            .bind("keydown", function(event) {
                if (event.keyCode === $.ui.keyCode.TAB &&
                        $(this).data("autocomplete").menu.active) {
                    event.preventDefault();
                }
            })
            .catcomplete({
                minLength: 2, // this doesn't seem to work
                delay: 0,
                source: function(request, response) {
                    // delegate back to autocomplete, but extract the last term
                    response($.ui.autocomplete.filter(
                        data, extract_last(request.term)));
                },
                focus: function() {
                    // prevent value inserted on focus
                    return false;
                },
                select: function(event, ui) {
                    var usernames = split(this.value);
                    // remove the current input
                    usernames.pop();
                    // add the selected item
                    $.each(split(ui.item.value), function(i, username) {
                        // check if any of the usernames are already there
                        if ($.inArray(username, usernames) == -1)
                            usernames.push(username);
                    });
                    // add placeholder to get the comma at the end
                    usernames.push("");
                    this.value = usernames.join(",") ;
                    return false;
                }
            });
    }


    // check if we have HTML5 storage available
    try {
        var supports_html5_storage = !!localStorage.getItem;
    } catch(e) {
        var supports_html5_storage = false;
    }

    // this object receives the entries for the devs and experts and
    // when it has both it calls add_autocomplete
    var data = {
        devs: null,
        experts: null,
        add: function(data, type) {
            // type is either 'devs' or 'experts'
            this[type] = data;
            if (this.devs && this.experts)
                add_autocomplete(this.devs.concat(this.experts))
        }
    };

    /* Note: instead of using a nested structure like:
       {"Platform": {"plat1": "name1,name2", "plat2": "name3,name4", ...},
        "Module": {"mod1": "name1,name2", "mod2": "name3,name4", ...},
        ...}
       (i.e. the same format sent by the server), we have to change it and
       repeat the category for each entry, because the autocomplete wants a
       flat structure like:
       [{label: "plat1: name1,name2", value: "name1,name2", category: "Platform"},
        {label: "plat2: name3,name4", value: "name3,name4", category: "Platform"},
        {label: "mod1: name1,name2", value: "name1,name2", category: "Module"},
        {label: "mod2: name3,name4", value: "name3,name4", category: "Module"},
        ...].
       Passing a nested structure to ui.autocomplete.filter() and attempt
       further parsing in _renderMenu doesn't seem to work.
    */
    function get_json(file, callback) {
        // Get the JSON from either the HTML5 storage or the server.
        //   file is either 'devs' or 'experts',
        //   the callback is called once the json is retrieved
        var json;
        if (supports_html5_storage &&
                ((json = localStorage[file]) != null) &&
                !is_expired(localStorage[file+'time'])) {
            // if we have HTML5 storage and already cached the JSON, use it
            callback(JSON.parse(json), file);
        }
        else {
            // if we don't have HTML5 storage or the cache is empty, request
            // the JSON to the server
            $.getJSON('user?@template='+file, function(rawdata) {
                var objects = []; // array of objs with label, value, category
                if (file == 'devs') {
                    // save devs as 'Name Surname (user.name)'
                    $.each(rawdata, function(index, names) {
                        objects.push({label: names[1] + ' (' + names[0] + ')',
                                      value: names[0], category: 'Developer'});
                    });
                }
                else {
                    // save experts as e.g. 'modname: user1,user2'
                    $.each(rawdata, function(category, entries) {
                        $.each(entries, function(entry, names) {
                            objects.push({label: entry + ': ' + names,
                                          value: names, category: category});
                        });
                    });
                }
                // cache the objects if we have HTML5 storage
                if (supports_html5_storage) {
                    localStorage[file] = JSON.stringify(objects);
                    localStorage[file+'time'] = unix_time();
                }
                callback(objects, file);
            });
        }
    }

    // request the JSON.  This will get it from the HTML5 storage if it's there
    // or request it to the server if it's not,  The JSON will be passed to the
    // data object, that will wait to get both the files before calling the
    // add_autocomplete function.
    get_json('experts', data.add);
    get_json('devs', data.add);
});
