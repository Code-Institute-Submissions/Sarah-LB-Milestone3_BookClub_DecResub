$(document).ready(function(){
    $('.sidenav').sidenav({edge: "right"});
    $("#rateYo").rateYo({
      rating: 1.5,
      halfStar: true
    });
    $('select').formSelect();
  });