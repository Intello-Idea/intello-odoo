
window.onload = function (){

    editWrapLogin();
};

function editWrapLogin(){

    var wrap = document.getElementById('wrapwrap');
    if (wrap.getElementsByClassName('body_login')){

        wrap.classList.add('wrap-login-intello');
    }
};