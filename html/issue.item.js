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
    var nosy_text = nosy.value.replace(/\s+/g, '');
    if (nosy_text == "") {
        // nosy_list is empty, add the user
        nosy.value = user;
    }
    else {
        re = new RegExp("(^|,)" + user + "(,|$)");
        if (!re.test(nosy_text)) {
            // make sure the user not in nosy and then add it at the beginning
            nosy.value = user + ',' + nosy_text;
        }
    }
    // hide the button and resize the list to fill the void
    var new_width = nosy.offsetWidth + add_me_button.offsetWidth;
    add_me_button.style.display = 'none';
    nosy.style.display = 'block';
    nosy.style.width = new_width + "px";
}
