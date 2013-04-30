/***********************************/
/* Dre suporting JavaScript        */
/*                                 */
/* Usage of this code is optional. */
/***********************************/


function dre_filter_setup() {
    var datefield=document.createElement("input");
    datefield.setAttribute("type", "date");
    if (datefield.type!="date"){ // Test browser for type="date" support
        $("#id_start_date").datepicker({
            dateFormat: "yy-mm-dd",
            changeMonth: true,
            changeYear: true
        });
        $("#id_end_date").datepicker({
            dateFormat: "yy-mm-dd",
            changeMonth: true,
            changeYear: true
        });
    };
    $("#id_tags").multiselect()
};


$(function() {
    dre_filter_setup();
});
