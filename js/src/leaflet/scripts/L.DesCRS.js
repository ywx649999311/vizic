L.CRS.RADEC = L.extend({}, L.CRS.Simple, {
            projection: L.Projection.LonLat,
            transformation: new L.Transformation(1, 0, 1, 0),
            // wrapLat : [-90, 90],
            // wrapLng : [0, 360],

            scale: function (zoom) {
                return Math.pow(2, zoom);
            },
            zoom: function(scale) {
                return Math.log(scale) / Math.LN2;

            },
            latLngToPoint: function(latlng, zoom) {
                var adjlatlng = L.latLng((latlng.lat-this.adjust[1])/this.adjust[3], (latlng.lng-this.adjust[0])/this.adjust[2]);
                return L.CRS.Simple.latLngToPoint(adjlatlng, zoom);
            },
            pointToLatLng: function(point, zoom) {
                var latlng = L.CRS.Simple.pointToLatLng(point, zoom);
                latlng.lng = (latlng.lng*this.adjust[2])+this.adjust[0];
                latlng.lat = (latlng.lat*this.adjust[3])+this.adjust[1];
                return latlng;
            },
            adjust: [0, 90, 0.3515625, 0.3515625]
            // adjust: {
            //     x: 322.477471, //min RA
            //     y: 0.713879+0.3736110, //Delta DEC + min_DEC
            //     scale: {
            //         x:0.00278884, //delra RA / 256
            //         y:0.0027886 //delta DEC /256
            //     }
            // }
        });
// L.CRS.S = L.extend({}, L.CRS.Simple, {
//             projection : L.Projection.LonLat,
//             transformation: new L.Transformation(1, 0, 1, 0),
//         });
