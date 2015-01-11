/***********************************/
/* Dre suporting JavaScript        */
/*                                 */
/* Usage of this code is optional. */
/***********************************/


function dre_filter_setup() {
    var datefield=document.createElement("input");
    datefield.setAttribute("type", "date");
    if (datefield.type!="date"){ // Test browser for type="date" support
        $("#id_date").datepicker({
            dateFormat: "yy-mm-dd",
            changeMonth: true,
            changeYear: true
        });
        $("#id_date").datepicker("setDate", date );
    };
    $("select#id_series").change(function() {
        $("#form_filter").submit();
    });
    $("#id_doc_type").change(function() {
        $("#form_filter").submit();
    });
    $("#id_date").change(function() {
        $("#form_filter").submit();
    });

    $("#id_doc_type").multiselect();
    $(".ui-multiselect").css('width', '15em');
};


$(function() {
    dre_filter_setup();
});
