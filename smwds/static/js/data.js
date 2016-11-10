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
function update_sitestatus(j){
    ///console.log(j);
    data = JSON.parse(j);
    //console.log(data);
    document.getElementById('node').innerHTML = data.managed_nodes;
    document.getElementById('sc').innerHTML =  data.system_capacity;
    document.getElementById('su').innerHTML =  data.system_utilization + '%';
    document.getElementById('user').innerHTML =  data.user_count;
    document.getElementById('mm').innerHTML =  data.registered_master;
    document.getElementById('task').innerHTML =  data.total_task;
    document.getElementById('sl').innerHTML =  data.service_level + '%';
    document.getElementById('up').innerHTML = data.uptime + 'd';
    var sparklineCharts = function(){
        $("#sparkline1").sparkline(data.m, {
            type: 'line',
            width: '100%',
            height: '50',
            lineColor: '#1ab394',
            fillColor: "transparent"
        });

        $("#sparkline2").sparkline(data.n, {
            type: 'line',
            width: '100%',
            height: '50',
            lineColor: '#1ab394',
            fillColor: "transparent"
        });

    };


    sparklineCharts();
    hideloading('site-loading');
}


namespace = '/deyunio';

var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
