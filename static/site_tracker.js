
window.onload = function(){
}

function getBaseURL() {
    var baseURL = 'http://127.0.0.1:5000';
    return baseURL;
}


$(document).ready(function(){
    loadTable();
});

/*function formatTable(data){
    items = []
    Object.keys(data).forEach(function(key,index) {
        items.push('<tr><td>'+key+'</td><td>'+data[key]+'</td></tr>');
    });
    return items.join('');
}*/

function loadTable(){
    console.log("here");
    //Creates a list of websites we are tracking
    $.getJSON("/update_values",function(data){
        console.log(data);
        
        items = []
        Object.keys(data).forEach(function(key,index) {
            items.push('<tr><td>'+key+'</td><td>'+data[key]+'</td></tr>');
        });
        $('#result_table tbody').empty();
        $('#result_table tbody').append(items.join(''));
    });
}

//Adds a tracked website when clicked
function addWebsite(){
    var url = prompt("Please enter a url to track: ");
    $.get( 'http://127.0.0.1:5000' + "/add_url/" + url, function( data ) {
        alert(data);
    });
    loadTable();
}

//Removes a tracked website when clicked
function removeWebsite(){
    var url = prompt("Please enter a url to remove: ");
    $.get( 'http://127.0.0.1:5000' + "/remove_url/" + url, function( data ) {
        alert(data);
    });
    loadTable();
}

    
