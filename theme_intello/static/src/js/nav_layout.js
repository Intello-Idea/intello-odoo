window.onload = function() {
    //initPage();
};

/*window.onscroll = function () {
    navFunction();
};*/

function navFunction() {
    if (document.body.scrollTop > 70 || document.documentElement.scrollTop > 70) {
        document.getElementById('sticky-nav').classList.remove("sticky-top");
        document.getElementById('sticky-nav').classList.add("fixed-top");
    } else {
        document.getElementById('sticky-nav').classList.remove("fixed-top");
        document.getElementById('sticky-nav').classList.add("sticky-top");
    }
};

function initPage(){
    var header_top = document.getElementById('top');
    if (header_top){
        header_top.remove();
    }
}