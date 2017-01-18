function open_confirm(m,n,k){
   
    document.getElementById('confirm-content').innerHTML = '<strong><p>Task: ' + m +'</p></strong>' + '<strong><p>TGT:' + n +'</p></strong>' + k;
    document.getElementById('confirm-execute').onclick = function() { 
            emit_salt_job(m,n,k); 
        };
}

function emit_salt_job(m,n,k){
    msg =  JSON.stringify({"tgt": n, "func": "salt_ping","task":m,"info":k});
    console.log(msg);
    socket.emit('func_init',msg);

}

function syntaxHighlight(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'key';
            } else {
                cls = 'string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'boolean';
        } else if (/null/.test(match)) {
            cls = 'null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}


function emit_salt_jid(j){
    showloading('return-loading');
    cleardata('return-jid');
    document.getElementById('return-content').innerHTML = "";
    msg =  JSON.stringify({"jid": j, "func": "salt_jid"});
   // console.log(j + ' : ' +msg);
    socket.emit('func_init',msg);
}

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

var socket = io.connect('https://' + document.domain + ':' + location.port + namespace,{secure: true});


