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
function formatTable(data, newurl){
    items = [];
    keys = sortData(data);
    keys.forEach(function(key,index) {
        update_value = "Old"
        if(data[key][0] == true || (newurl && key==newurl)){
            update_value = "New &#10038"
        }
        items.push('<tr><td class="url">'+convertToUrl(key) +'</td><td>'+update_value+ '</td><td>'+data[key][1] +'</td>');
        items.push('<td><button class="myButton" onclick="removeWebsite(this);">Remove Website</button></td></tr>');
    });
    //only want to empty the table on page reload, otherwise with an add we just add a new row to the table
    if(!newurl){
        $('#result_table tbody').empty();
    }
    $('#result_table tbody').append(items.join(''));
}

//Creates a table of websites we are tracking
function loadTable(newurl=null){
    $.getJSON("/update_values",function(data){
        //console.log(data)
        formatTable(data, newurl);
        document.getElementById("loader").style.display = "none";
    });
}

//Adds a tracked website when clicked
function addWebsite(){
    var url = prompt("Please enter a url to track: ");
    if (url != null){
        $.getJSON("/add_url/" + url, function( data ) {
            if (data['message']){
                alert(data['message'])
            }
            else{
                delete data["message"];
                formatTable(data, url);
                sortTable(0);
            }
        });
    }
}

//Removes a tracked website when clicked
function removeWebsite(ele){
    var $row = $(ele).closest("tr")   // Finds the closest row <tr> 
    var $url = $row.find(".url").text();
    $row.remove();
    $.get( "/remove_url/" + $url, function( data ) {
        if(data.length > 2){
            alert(data);
        }
    });
}

function sortTable(id) {
  var table, rows, switching, i, x, y, shouldSwitch;
  table = document.getElementById("result_table");
  switching = true;
  /* Make a loop that will continue until
  no switching has been done: */
  while (switching) {
    // Start by saying: no switching is done:
    switching = false;
    rows = table.rows;
    /* Loop through all table rows (except the
    first, which contains table headers): */
    for (i = 1; i < (rows.length - 1); i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
      one from current row and one from the next: */
      x = rows[i].getElementsByTagName("TD")[id];
      y = rows[i + 1].getElementsByTagName("TD")[id];
      // Check if the two rows should switch place:
      if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
        // If so, mark as a switch and break the loop:
        shouldSwitch = true;
        break;
      }
    }
    if (shouldSwitch) {
      /* If a switch has been marked, make the switch
      and mark that a switch has been done: */
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
    }
  }
}