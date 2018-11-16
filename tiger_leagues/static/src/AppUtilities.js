
/**
 * @description Send a HTTP request with the specified arguments.
 * 
 * @param {string} method The method to use, e.g. `POST`
 * @param {string} url The URL that the request will be sent to
 * @param {JSON} payload The data that will be sent along with the request
 * @returns {Promise} If successful, the parameter will be the entire response.
 */
function sendHTTPRequest(method, url, payload, contentType="application/json") {
    return new Promise(function(resolve, reject) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState == 4) {
                resolve(this.response);
            }
        };
        xhttp.open(method, url, true);
        xhttp.setRequestHeader("Content-Type", contentType);
        xhttp.send(JSON.stringify(payload));
    });
    
}