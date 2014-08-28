function getOutputOptionDefaults() {
    var ooDefaults = new Object();

    ooDefaults["inp_woc_graf"] = true;
    ooDefaults["inp_woc_graf_grp_msgs_by_date"] = true;
    ooDefaults["inp_woc_graf_day_msgs_by_name"] = true;
    ooDefaults["inp_woc_graf_all_msgs_by_name"] = false;

    ooDefaults["inp_woc_wcloud"] = true;
    ooDefaults["inp_woc_wcloud_all_names"] = false;
    ooDefaults["inp_woc_wcloud_day_names"] = true;
    ooDefaults["inp_woc_wcloud_all_msgs"] = false;
    ooDefaults["inp_woc_wcloud_day_msgs"] = true;

    ooDefaults["inp_woc_csv"] = false;

    return ooDefaults;
}
function getOutputOptions() {
    var ooo = new Object();
    ooo["inp_woc_csv"] = [];
    ooo["inp_woc_graf"] = [
        "inp_woc_graf_grp_msgs_by_date",
        "inp_woc_graf_day_msgs_by_date",
        "inp_woc_graf_all_msgs_by_date"
    ];
    ooo["inp_woc_wcloud"] = [
        "inp_woc_wcloud_all_names",
        "inp_woc_wcloud_day_names",
        "inp_woc_wcloud_all_msgs",
        "inp_woc_wcloud_day_msgs"
    ];
    return ooo;
}

function getGraphOptionInputNames() {
    var a = [
        "inp_woc_graf_grp_msgs_by_date",
        "inp_woc_graf_day_msgs_by_name",
        "inp_woc_graf_all_msgs_by_name"
    ];
    return a;
}
function getWordCloudOptionInputNames() {
    var a = [
        "inp_woc_wcloud_all_names",
        "inp_woc_wcloud_day_names",
        "inp_woc_wcloud_all_msgs",
        "inp_woc_wcloud_day_msgs"
    ];
    return a;
}
function updateOutputSubOptions(enable, elementIds) {
    var callable = enable ? element_enabler : element_disabler;
    
    elementIds.forEach(callable);
}
function getChatTextModeInputElementNames() {
    var a = [
        "inp_dtfmt_ddmmyyyy",
        "inp_dtfmt_mmddyyyy",
        "inp_tmfmt_hh12mmssaa",
        "inp_tmfmt_hh24mmss",
        "inp_tmfmt_hh24mm",
        "inp_dtstr",
        "wa_output_options_button",
    ];
    var woo = getOutputOptionDefaults();
    for(var ooid in woo) {
        a.push(ooid);
    }
    return a;
}
function getChatTextModeDivIds() {
    var a = [
        "wa_chat_text_options",
        "wa_output_options_button"
    ];
    return a;
}
function getWaOutputOptionsContainerId() {
    return "wa_output_options";
}
function getWaOutputOptionsContainerElement() {
    return document.getElementById(getWaOutputOptionsContainerId());
}
function element_disabler(elementId, index, arr) {
    disableIt(document.getElementById(elementId));
}
function element_enabler(elementId, index, arr) {
    enableIt(document.getElementById(elementId));
}

function disableIt(x) {
    x.disabled = true;
}
function enableIt(x) {
    x.disabled = false;
}

function hideIt(x) {
    x.style.visibility = 'hidden';
    x.style.display = 'none';
}
function showIt(x) {
    x.style.visibility = 'visible';
    x.style.display = 'block';
}

function set_plain_text_mode() {

    getChatTextModeInputElementNames().forEach(element_disabler);
    
    getChatTextModeDivIds().forEach(
        function(ele, ind, arr) {
            hideIt(document.getElementById(ele));
        }
    );
    hideOutputOptions();
}
function set_chat_text_mode() {

    getChatTextModeInputElementNames().forEach(element_enabler);

    getChatTextModeDivIds().forEach(
        function(ele, ind, arr) {
            showIt(document.getElementById(ele));
        }
    );
    restoreOutputOptionDefaults();
}
function restoreOutputOptionDefaults() {
    var ooDefaults = getOutputOptionDefaults();
    for(var ooid in ooDefaults) {
        document.getElementById(ooid).checked =
            ooDefaults[ooid];
    }
    var ooo = getOutputOptions();
    for(var ooid in ooo) {
        updateOutputSubOptions(document.getElementById(ooid).checked, ooo[ooid]);
    }
}
function toggleOutputOptions() {
    var woo = getWaOutputOptionsContainerElement();
    var vis = woo.style.visibility;
    if(vis == 'hidden') {
        showOutputOptions();
    } else {
        hideOutputOptions();
    }
}
function showOutputOptions() {
    var oobutton = document.getElementById("wa_output_options_button");
    oobutton.innerHTML = "Restore defaults and hide output options";
    var woo = getWaOutputOptionsContainerElement();
    showIt(woo);
}
function hideOutputOptions() {
    var oobutton = document.getElementById("wa_output_options_button");
    oobutton.innerHTML = "Show output options";
    var woo = getWaOutputOptionsContainerElement();
    hideIt(woo);
    restoreOutputOptionDefaults();
}
function remove_error_msg_area(error_number) {
    var err_id = "error_msg_area_" + error_number;
    hideIt(document.getElementById(err_id));
}
function setInnerHTML(elementID, txt) {
    var ele = document.getElementById(elementID)
    ele.innerHTML = txt;
}
