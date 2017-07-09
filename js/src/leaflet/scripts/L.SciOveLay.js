var d3 = require("d3");
Voronoi = L.CusOverLay.Polygons.extend({

    _drawSvg: function() {
        L.CusOverLay.prototype._drawSvg.call(this, 'svg_v');
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
        return voronoi(json).polygons();
    },
});

Delaunay = Voronoi.extend({

	_drawSvg: function() {
        L.CusOverLay.prototype._drawSvg.call(this, 'svg_d');
    },

	_buildPathFromPoint: function(d) {
		var line_gen = d3.line()
					.x(function(d){return d.x;})
					.y(function(d){return d.y;});
        try {
            return line_gen(d) + "Z";
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
        return voronoi(json).triangles();
    },
});

Healpix = L.CusOverLay.Polygons.extend({

    _drawSvg: function() {
        L.CusOverLay.prototype._drawSvg.call(this, 'svg_h');
    },

	_projectData: function(json, map) {
        var init_z = this.options.svgZoom;
		var new_j = [];
		// console.log(json);
        json.forEach(function(d) {
			var arr = [];
			for (var i=0; i<4; i++){
				var latlng = new L.LatLng(d.dec[i], d.ra[i]);
	            var point = map.project(latlng, init_z);
				arr.push([point.x, point.y]);
			}
			new_j.push(arr);
        });

        return new_j;
    },
});

MST = L.CusOverLay.Lines.extend({
	_drawSvg: function() {
        L.CusOverLay.prototype._drawSvg.call(this, 'svg_mst');
    },

	key_func: function(d){
		return d.line_index;
	},

    drawGroup: function(key, map) {
        var data = this._dataR[key];
        var g = svg_m.append('g');
        g.selectAll('path')
            .data(data, this.key_func)
            .enter()
            .append('path').attr("d", this._buildPathFromPoint)
            .attr('stroke', this.options.color)
            .attr('stroke-width', this.options.lineWidth)
            .attr('vector-effect', 'non-scaling-stroke')
            .attr("transform", "scale(" + Math.pow(2, (map.getZoom() - this.options.svgZoom)) + ")");
    },
});

CirclesOverLay = function(url, options) {
    return new L.CusOverLay.Circles(url, options);
};
