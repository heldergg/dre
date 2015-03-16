/***********************************/
/* Dre suporting JavaScript        */
/*                                 */
/* Usage of this code is optional. */
/***********************************/

/* Test if an element is on viewport
 * from: https://github.com/moagrius/isOnScreen */

(function ($) {

    $.fn.isOnScreen = function(x, y){

        if(x == null || typeof x == 'undefined') x = 1;
        if(y == null || typeof y == 'undefined') y = 1;

        var win = $(window);

        var viewport = {
            top : win.scrollTop(),
            left : win.scrollLeft()
        };
        viewport.right = viewport.left + win.width();
        viewport.bottom = viewport.top + win.height();

        var height = this.outerHeight();
        var width = this.outerWidth();

        if(!width || !height){
            return false;
        }

        var bounds = this.offset();
        bounds.right = bounds.left + width;
        bounds.bottom = bounds.top + height;

        var visible = (!(viewport.right < bounds.left || viewport.left > bounds.right || viewport.bottom < bounds.top || viewport.top > bounds.bottom));

        if(!visible){
            return false;
        }

        var deltas = {
            top : Math.min( 1, ( bounds.bottom - viewport.top ) / height),
            bottom : Math.min(1, ( viewport.bottom - bounds.top ) / height),
            left : Math.min(1, ( bounds.right - viewport.left ) / width),
            right : Math.min(1, ( viewport.right - bounds.left ) / width)
        };

        return (deltas.left * deltas.right) >= x && (deltas.top * deltas.bottom) >= y;
    };

})(jQuery);


/* Highlight a search result list item */

function highlight( old_element, element ) {
    old_element.css("background-color","");
    element.css("background-color","#e6ce9e");
    element.scrollTop();
    var a = element.isOnScreen();
    if ( !(element.isOnScreen()) ) {
        $('html, body').animate({
            scrollTop: element.offset().top - 250
        }, 500);
    };
};


/* Keyboard navigation setup */

$(function() {
    var selected = 0

    var ENTER = 13;
    var LEFT = 37;
    var UP = 38;
    var RIGHT = 39;
    var DOWN = 40;

    $( "body" ).keydown( function( event ) {
        if ( event.target.nodeName != "INPUT" ) {
            var prev_date = $("#prev_date").attr("href");
            if ( event.keyCode == LEFT && $("#prev_date").length && event.shiftKey == true && event.ctrlKey == false ) {
                window.location.href = prev_date;
            };
            var next_date = $("#next_date").attr("href");
            if ( event.keyCode == RIGHT && $("#next_date").length && event.shiftKey == true && event.ctrlKey == false ) {
                window.location.href = next_date;
            };
            var next_page = $("#next_page").attr("href");
            if ( event.keyCode == RIGHT && $("#next_page").length && event.shiftKey == false && event.ctrlKey == false ) {
                window.location.href = next_page;
            };
            var prev_page = $("#prev_page").attr("href");
            if ( event.keyCode == LEFT && $("#prev_page").length && event.shiftKey == false && event.ctrlKey == false ) {
                window.location.href = prev_page;
            };
            var last_page = $("#last_page").attr("href");
            if ( event.keyCode == RIGHT && $("#last_page").length && event.shiftKey == false && event.ctrlKey == true ) {
                window.location.href = last_page;
            };
            var first_page = $("#first_page").attr("href");
            if ( event.keyCode == LEFT && $("#first_page").length && event.shiftKey == false && event.ctrlKey == true ) {
                window.location.href = first_page;
            };

            if ( event.keyCode == DOWN && event.shiftKey == false && event.ctrlKey == false ) {
                event.preventDefault();
                var length = $("#search_results").find("li").length ;
                if ( selected < length ) {
                    var old_element = $("#search_results"
                            ).find("ul").find("li:nth-child("+[selected]+")");
                    selected++;
                    var element = $("#search_results"
                            ).find("ul").find("li:nth-child("+[selected]+")");
                    highlight( old_element, element );
                };
            };

            if ( event.keyCode == UP && event.shiftKey == false && event.ctrlKey == false ) {
                event.preventDefault();
                if ( selected > 1 || selected == 0 ) {
                    if ( selected == 0 ) {
                        selected = 2;};
                    var old_element = $("#search_results"
                            ).find("ul").find("li:nth-child("+[selected]+")");
                    selected-- ;
                    var element = $("#search_results"
                            ).find("ul").find("li:nth-child("+[selected]+")");
                    highlight( old_element, element );
                };
            };

            if ( event.keyCode == ENTER && event.shiftKey == false && event.ctrlKey == false ) {
                var length = $("#search_results").find("li").length ;
                if (selected >= 1 && selected <= length ) {
                    var element = $("#search_results"
                            ).find("ul").find("li:nth-child("+[selected]+")");

                    window.location.href = element.find(".result_link").attr("href");
                };
            };

        };
    });
});
