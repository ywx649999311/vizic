L.CRS.RADEC = L.extend({}, L.CRS, {
            projection: L.Projection.LonLat,
            transformation: new L.Transformation(1, 0, 1, 0),
            wrapLat : [-90, 90],
            wrapLng : [0, 360],

            scale: function (zoom) {
                return Math.pow(2, zoom);
            },
            zoom: function(scale) {
                return Math.log(scale) / Math.LN2;

            },
            // latLngToPoint: function(latlng, zoom) {
            //     var adjlatlng = L.latLng((latlng.lat-this.adjust.y)/this.adjust.scale.y, (latlng.lng-this.adjust.x)/this.adjust.scale.x);
            //     return L.CRS.Simple.latLngToPoint(adjlatlng, zoom);
            // },
            // pointToLatLng: function(point, zoom) {
            //     var latlng = L.CRS.Simple.pointToLatLng(point, zoom);
            //     latlng.lng = (latlng.lng*this.adjust.scale.x)+this.adjust.x;
            //     latlng.lat = (latlng.lat*this.adjust.scale.y)+this.adjust.y;
            //     return latlng;
            // },
            // adjust: {
            //     x: 155.00166, //min RA
            //     y: 44.999326, //Delta DEC + min_DEC
            //     scale: {
            //         x:0.078105742, //delra RA / 256
            //         y:0.078120164 //delta DEC /256
            //     }
            // }
        });
