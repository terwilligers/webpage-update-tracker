# webpage-update-tracker
This webapp displays a webpage where the user can track websites for content changes. It lets the users create a list of websites that they want to track, and see when websites have most recently been updated. The app has been deployed and can be accessed at: https://webpage-update-tracker.herokuapp.com/index

The Flask web application uses a posgresql database to store user data, and tracked website information. The backend is in Python, and the frontend encorporates Javascript, HTML, and CSS. Currently the method for calculating whether a site has been updated involves removing scripts from the page source, and hashing it. This works in most cases, but some dynamic pages will often give false positives for updates.

In the future, next steps will be improving the method of comparing webpages, and potentially allowing users to select which parts of a webpage they want to track.
