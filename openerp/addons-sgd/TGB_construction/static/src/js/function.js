function showPosition(position) {
    var latlon = position.coords.latitude + "," + position.coords.longitude;
    var img_url = "http://maps.googleapis.com/maps/api/staticmap?center="
        + latlon + "&zoom=14&size=400x300&sensor=false";
    document.getElementById("mapholder").innerHTML = "<img src='" + img_url + "'>";
}
function showErrorStr(str) {
    var x = document.getElementById("demo");
    x.innerHTML = str;
}

function showError(error) {
    var x = document.getElementById("demo");
    switch (error.code) {
        case error.PERMISSION_DENIED:
            x.innerHTML = "User denied the request for Geolocation."
            break;
        case error.POSITION_UNAVAILABLE:
            x.innerHTML = "Location information is unavailable."
            break;
        case error.TIMEOUT:
            x.innerHTML = "The request to get user location timed out."
            break;
        case error.UNKNOWN_ERROR:
            x.innerHTML = "An unknown error occurred."
            break;
    }
}


openerp.TGB_construction = function (openerp) {
    openerp.web.form.widgets.add('test', 'openerp.web.form.test');

    openerp.web.form.test = openerp.web.form.FieldChar.extend(
        {
            template: 'test_button',

            init: function () {
                this._super.apply(this, arguments);
                this._start = null;
                console.log('INIT');

            },

            start: function () {
                console.log('START');
                $('button#bstart').click(this.getLocation);  //link button to function
            },

            getLocation: function () {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(showPosition, showError);
                } else {
                    showErrorStr("Geolocation is not supported by this browser.");
                }
            },

        }
    )

}

