function cleardata(e)
{ 
    data = document.getElementsByClassName(e);
    for( var i = 0; i < data.length; i++) { data[i].innerHTML = ""};             
}
function hidedata(e)
{ 
    data = document.getElementsByClassName(e);
    for( var i = 0; i < data.length; i++) { data[i].style.visibility = "hidden"};
}
function showdata(e)
{ 

    data = document.getElementsByClassName(e);
    for( var i = 0; i < data.length; i++) { data[i].style.visibility = "visible"};
}
function hideloading(e)
{ 

    data = document.getElementsByClassName(e);
    for( var i = 0; i < data.length; i++) {
    data[i].style.visibility = "hidden";
    data[i].style.animationPlayState = "paused";
        };
}
function showloading(e)
{ 
    data = document.getElementsByClassName(e);
    for( var i = 0; i < data.length; i++) {
    data[i].style.visibility = "visible";
    data[i].style.animationPlayState = "running";
        };
}

namespace = '/deyunio';

var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
