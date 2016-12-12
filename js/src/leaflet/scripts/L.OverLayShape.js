var d3 = require("d3");
L.CusOverLay.Polygons = L.CusOverLay.extend({
	add: function() {
		var that = this;
		this._voronoi = this._projectData(this._json, this._map);
		this.sortJson(this._voronoi.polygons());
		setTimeout(function() {
			that.drawSvg();
		});
	},
	
    comp_func_y: function(a, b) {
        return a.data.y - b.data.y;
    },

    comp_func_x: function(a, b) {
        return a.data.x - b.data.x;
    },

    drawSvg: function() {
        L.CusOverLay.prototype.drawSvg.call(this, 'svg_poly');
    },

    drawGroup: function(key, map) {
        L.CusOverLay.prototype.drawGroup.call(this, key, map, 'path');
    },

    _buildPathFromPoint: function(d) {
        try {
            return "M" + d.join("L") + "Z";
        } catch (e) {}
    },

	_projectData: function(json, map) {
        var init_z = this.options.svgZoom;
        // console.log(init_z);
        json.forEach(function(d) {
            var latlng = new L.LatLng(d.DEC, d.RA);
            var point = map.project(latlng, init_z);

            d.x = point.x;
            d.y = point.y;
        });
        var sz = Math.pow(2, init_z) * 256;
        var voronoi = d3.voronoi()
            .x(function(d) {
                return d.x;
            })
            .y(function(d) {
                return d.y;
            })
            .size([sz + 1, sz + 1]);
        return voronoi(json);
    },
});

L.overLayPolygons = function(url, map) {
    return new L.CusOverLay.Polygons(url, map);
};
