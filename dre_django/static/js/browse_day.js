$(document).ready(function() {
    $("#calendar").datepicker({
        defaultDate: default_date,
        onSelect: function(dateText, inst) {
            window.location.replace("/dre/data/" + inst.currentYear + "/" + (inst.currentMonth+1) + "/" + inst.currentDay + "/" );
            },
        
        });
    });
