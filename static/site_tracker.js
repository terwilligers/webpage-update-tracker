
window.onload = function(){
}

function getBaseURL() {
    var baseURL = 'http://127.0.0.1:5000';
    return baseURL;
}

$(document).ready(function(){
    //Creates a list of websites we are tracking
    $.getJSON("/update_values",function(data){
        console.log(data);
        
        items = []
        Object.keys(data).forEach(function(key,index) {
            items.push('<tr><td>'+key+'</td><td>'+data[key]+'</td></tr>');
        });
        $('#result_table tbody').append(items.join(''))
    });
});
    
