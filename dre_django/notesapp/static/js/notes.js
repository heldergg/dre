/***********************************/
/* Notes suporting JavaScript      */
/*                                 */
/* Usage of this code is optional. */
/***********************************/

var note_form_visible = null;

function note_form_setup() {
    $(".add_note").addClass("hidden");

    note_form_visible = null;
    $(".note_control").click( function() {
        if (note_form_visible) {
            $(note_form_visible).parent().parent().find('.add_note').hide();
            $(note_form_visible).parent().parent().find('.user_notes').show();
            $(note_form_visible).find("img").attr("src", STATIC_URL + "img/edit-note.png");
            };
        if ( this != note_form_visible ) {
            note_form_visible = this;
            $(this).find("img").attr("src", STATIC_URL + "img/remove-note.png");
            $(this).parent().parent().find('.add_note').show();
            $(this).parent().parent().find('.user_notes').hide();
            }
        else {
            note_form_visible = null;
            };
        });
    }; // End form_setup

function note_ajax_add_setup() {
    /* Ajaxy note add */
    $(".add_note form").submit(function () {
        var form_values = $(this).serializeArray();
        var post_url = $(this).attr("action")
        var result_note = $(this).parent().parent().find('.user_notes')
        var image = $(this).parent().parent().find('.note_control').find('img')
        var note_form = $(this)

        $(image).attr("src", STATIC_URL + "img/progress.gif");

        $.post( post_url, form_values, function (data) {
            $(image).attr("src", STATIC_URL + "img/remove-note.png");
            if (data.success ) {
                result_note.empty().append(data.html)
                result_note.show();
            // TODO: Change the form html when adding a new note (must use
            // the modify url...
                result_note.parent().find('.add_note').hide();
                $(image).attr("src", STATIC_URL + "img/edit-note.png");
                note_form_visible = null;
                };
            $("#notification").html(data.message);
            $("#notification").fadeIn(200).delay(500).fadeOut(2000);
            }, "json" );

        return false;
        });
    }; // ajax_add_setup

$(function() {
    note_form_setup();
    note_ajax_add_setup();
});
