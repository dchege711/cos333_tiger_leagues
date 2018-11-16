
/**
 * @description Send a HTTP request with the specified arguments.
 * 
 * @param {string} method The method to use, e.g. `POST`
 * @param {string} url The URL that the request will be sent to
 * @param {JSON} payload The data that will be sent along with the request
 */
function sendHTTPRequest(method, url, payload) {
    return new Promise(function(resolve, reject) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState == 4 && this.status == 200) {
                try {
                    let json_response_data = JSON.parse(this.responseText);
                    resolve(json_response_data);
                } catch (err) { 
                    reject(err);
                }
            }
        };
        xhttp.open(method, url, true);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify(payload));
    });
    
}