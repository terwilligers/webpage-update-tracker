

function getBaseURL() {
    var baseURL = 'http://127.0.0.1:5000';
    return baseURL;
}

$(document).ready(function(){
    loadTable();
});

function sortData(data){
    keys = Object.keys(data)
    sortedKeys = keys.sort();
    return sortedKeys
}

function convertToUrl(text){
    var exp = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    var text1=text.replace(exp, "<a href='$1'>$1</a>");
    var exp2 =/(^|[^\/])(www\.[\S]+(\b|$))/gim;
    var text2 = text1.replace(exp2, '$1<a target="_blank" href="http://$2">$2</a>');
    return text2;
}

//Formats the websites into a table format
function formatTable(data){
    items = [];
    keys = sortData(data);
    keys.forEach(function(key,index) {
        star = ""
        if(data[key] == true){
            star = " &#10038;"
        }
        items.push('<tr><td class="url">'+convertToUrl(key) +'</td><td>'+data[key][0]+ star+ '</td><td>'+data[key][1] +'</td>');
        items.push('<td><button class="myButton" onclick="removeWebsite(this);">Remove Website</button></td></tr>');
    });
    $('#result_table tbody').empty();
    $('#result_table tbody').append(items.join(''));
}

//Creates a table of websites we are tracking
function loadTable(){
    $.getJSON("/update_values",function(data){
        console.log(data)
        formatTable(data);
    });
}

//Adds a tracked website when clicked
function addWebsite(){
    var url = prompt("Please enter a url to track: ");
    $.get( 'http://127.0.0.1:5000' + "/add_url/" + url, function( data ) {
        if(data.length > 2){
            alert(data);
        }
    });
    loadTable();
}

//Removes a tracked website when clicked
function removeWebsite(ele){
    var $url = $(ele).closest("tr")   // Finds the closest row <tr> 
                       .find(".url")     // Gets a descendent with class="url"
                       .text();
    console.log($url);
    $.get( 'http://127.0.0.1:5000' + "/remove_url/" + $url, function( data ) {
        if(data.length > 2){
            alert(data);
        }
    });
    loadTable();
}

    
