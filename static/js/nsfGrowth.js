
$(document).ready(function(){
  $("A[href='#select_all']").click( function() {
          $("#" + $(this).attr('rel') + " INPUT[type='checkbox']").attr('checked', true);
          return false;
      });
});
