$(document).ready(function () {
    // create the input button and use it to replace the span/placeholder --
    // users without javascript won't notice anything.
    // This might eventually be replaced by jquery
    var node_id = 'add_remove_from_nosy';
    var user_span = document.getElementById(node_id);
    if (user_span == null) {
        return;  // we are not logged in
    }
    // create button
    var button = document.createElement('input');
    button.type = 'button';
    button.onclick = user_span.onclick;
    button.style.display = 'inline';
    // replace placeholder span with button
    var button_parent = user_span.parentNode;
    button_parent.replaceChild(button, user_span);
    button.id = node_id;
    // update +/- value
    var user = user_span.getAttribute("user")
    update_nosy_button(user);
})


function update_nosy_button(user) {
    // change the value of the button to + or -
    var button = document.getElementById('add_remove_from_nosy');
    var nosy = document.getElementById('nosy_list');
    if (nosy.value.split(",").includes(user)) {
        button.value = '-';
        button.title = 'Remove me from';
    }
    else {
        button.value = '+';
        button.title = 'Add me to';
    }
    button.title += ' the nosy list (remember to Submit Changes)';
}


function change_nosy(user) {
    // add or remove the user from the nosy list
    var button = document.getElementById('add_remove_from_nosy');
    var nosy = document.getElementById('nosy_list');
    // remove spaces at the beginning/end of the string and around the commas
    var nosy_text = nosy.value.replace(/^[\s,]*|[\s,]*$/g, '').replace(/\s*,\s*/g, ',');
    var user_list = nosy_text.length>0 ? nosy_text.split(",") : []
    if (user_list.includes(user)) {
        user_list.splice(user_list.indexOf(user), 1);  // remove user
    }
    else {
        user_list.unshift(user);  // add user at the beginning
    }
    nosy.value = user_list.join(',');
    update_nosy_button(user);
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
    function create_help_popup() {
        // create a popup that lists the available shortcuts
        var div = $([
           '<div id="shortcuts-help"><table>',
           '  <caption>Keyboard shortcuts</caption>',
           '  <tr><th></th><th>mnemonic</th><th>vim-style</th></tr>',
           '  <tr><th>first message</th><td>f</td><td>h</td></tr>',
           '  <tr><th>previous message</th><td>p</td><td>k</td></tr>',
           '  <tr><th>next message</th><td>n</td><td>j</td></tr>',
           '  <tr><th>last message</th><td>l</td><td>l</td></tr>',
           '  <tr><th>focus textarea</th><td>r</td><td>i</td></tr>',
           '  <tr><th>unfocus textarea</th><td>Esc</td><td>Esc</td></tr>',
           '  <tr><th>shortcuts help</th><td>?</td><td>?</td></tr>',
           '</table>',
           '<p>All these shortcuts can be used at any time to',
           'navigate through the messages in the issue page.</p>',
           '<span id="close-help">Close shortcuts help</span></div>'].join('\n'))
        // this should point to the devguide once a section with the shortcuts
        // is added
        var menu = $('div#menu ul.level-three:last');
        $('<li id="menu-shortcuts-help"><span>Keyb. shortcuts ' +
          '(?)</span></li>').appendTo(menu);
        menu.find('li#menu-shortcuts-help span').click(
            function() { div.toggle(); return false; })
        div.find('span').click(function() { div.hide() })
        div.hide()
        div.appendTo('body');
    }
    create_help_popup()

    var help_popup = $('#shortcuts-help');
    var textarea = $('textarea').first();
    var messages = $('table.messages tr th a:first-child');
    var last_index = messages.length - 1;
    // start from -1 so 'n' sends to the first message at the beginning
    var current = -1;
    $(document).keydown(function (event) {
        // '?' shows the help if the user is not editing the form.
        // this is here because usually '?' requires 'shift' too, and the
        // switch below is not reached when shift is pressed
        if (event.shiftKey && (event.which == 191) && !is_editing(event.target)) {
            help_popup.toggle()
            return false;
        }
        // do nothing if ctrl/alt/shift/meta are pressed
        if (event.ctrlKey || event.altKey || event.shiftKey || event.metaKey)
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
        // ESC hides the help if the user is not editing
        if (event.keyCode == 27) {
            help_popup.hide();
            return false;
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
    /* Add an autocomplete to the nosy list that searches the term in 3 lists:
         1) the list of committers (both the user and the real name);
         2) the list of triagers (both the user and the real name);
         3) the list of experts in the devguide;
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

    // this object receives the entries for committers, devs, and experts
    // and calls add_autocomplete once they are all set
    var data = {
        committers: null,
        devs: null,
        experts: null,
        add: function(data, type) {
            // type is either 'committers', 'devs', or 'experts'
            this[type] = data;
            if (this.committers && this.devs && this.experts)
                add_autocomplete(this.committers.concat(this.devs, this.experts))
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
        //   file is either 'committers', 'devs', or 'experts',
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
                if (file == 'committers') {
                    // save committers as 'Name Surname (user.name)'
                    $.each(rawdata, function(index, names) {
                        objects.push({label: names[1] + ' (' + names[0] + ')',
                                      value: names[0], category: 'Core Developers'});
                    });
                }
                else if (file == 'devs') {
                    // save triager as 'Name Surname (user.name)'
                    $.each(rawdata, function(index, names) {
                        objects.push({label: names[1] + ' (' + names[0] + ')',
                                      value: names[0], category: 'Triagers'});
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

    // request the JSONs.  This will get it from the HTML5 storage if it's there
    // or request it from the server if it's not,  The JSON will be passed to
    // the data object, that will wait to get all the files before calling the
    // add_autocomplete function.
    get_json('experts', data.add);
    get_json('committers', data.add);
    get_json('devs', data.add);
});


$(document).ready(function() {
    /* Make the "clear this message" link in the ok_message point
     * to issue page without including any extra arg */
    var link = $('p.ok-message a.form-small').first();
    if (link.length != 0)
        link.attr('href', link.attr('href').split('?')[0]);
});


$(document).ready(function() {
    /* Mark automated messages with a different background */
    $('table.messages th:nth-child(2)').each(function (i, e) {
        var e = $(e);
        if (/\(python-dev\)$/.test(e.text()))
            e.parent().next().find('td.content').css(
                'background-color', '#efeff9');
    });
});
