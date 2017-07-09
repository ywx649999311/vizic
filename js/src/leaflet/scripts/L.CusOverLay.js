var d3 = require("d3");
L.CusOverLay = L.Layer.extend({
    options: {
        color: '#0459e2',
        lineWidth: 1,
        svgZoom: 5,
    },

    initialize: function(url, options) {
        L.setOptions(this, options);
        this._url = url;
        this._json = [];
        this._dataR = {};
        this._getData();
    },

	add: function() {
        var that = this;
        this._json = this._projectData(this._json, this._map);
        this.sortJson(this._json);
        setTimeout(function() {
            that._drawSvg();
        });
    },

    onAdd: function() {
        this.inertia = this._map.options.inertia;
        this.fadeAnimation = this._map.options.fadeAnimation;
        this._map.options.inertia = false;
        this._map.options.fadeAnimation = false;
        this._el = L.DomUtil.create('div', 'leaflet-zoom-hide vizic-overlay');
        this.getPane().appendChild(this._el);
        console.log('onAdd');
    },

    _getData: function() {
        var that = this;
        // var init_z = this.options.init_draw_z;
        d3.json(this._url, function(error, json) {
            if (error) {
                return console.log(error);
            }
            that._json = json;
            var draw = L.bind(that.add, that);
            draw();
        });

    },

    sortJson: function(data){
        var chunk = 60,
            numGroups = Math.ceil(data.length / chunk);

        for (var i = 0, z = 0; i < numGroups; z += chunk, i++){
            this._dataR[i] = data.slice(z, z+chunk);
        }
    },

    _drawSvg: function(svg_id) {
        var that = this,
            key,
            zoom = this._map.getZoom(),
            pixOrigin = this._map.getPixelOrigin(),
            offset = L.point(0, 0).subtract(pixOrigin);
        this.zoomOnAdd = zoom;
        svg_m = d3.select(this._el).append('svg')
            .style('width', '100000px')
            .style('height', '100000px')
            .attr('fill', 'none')
            .attr('overflow', 'visible')
            .attr('id', svg_id);

        for (key in this._dataR) {
            L.Util.requestAnimFrame(L.bind(this.drawGroup, this, key, this._map));
        }
        L.DomUtil.setPosition(this._el, offset);
        this.getPane().appendChild(this._el);
    },

    getEvents: function() {
        return {
            zoomend: this._resetView,
            dragstart: this._onDrag,
            moveend: this._onMoveEnd,
        };
    },

    _onDrag: function(e) {
        this._map.scrollWheelZoom.disable();
    },

    _onMoveEnd: function(e) {
        // has to be moveend, or scroll zoom event will fire
        this._map.scrollWheelZoom.enable();
    },

    _resetView: function() {
        var zoom = this._map.getZoom(),
            pixOrigin = this._map.getPixelOrigin(),
            offset = L.point(0, 0).subtract(pixOrigin),
            map = this._map;
        L.DomUtil.setPosition(this._el, offset);
        d3.select(this._el).selectAll('g').attr("transform", "scale(" + Math.pow(2, (map.getZoom() - this.zoomOnAdd)) + ")");

    },

    onRemove: function() {
        this.getPane().removeChild(this._el);
        this._map.options.inertia = this.inertia;
        this._map.options.fadeAnimation = this.fadeAnimation;
    },
});

L.CusOverLay.Polygons = L.CusOverLay.extend({

    _drawSvg: function() {
        L.CusOverLay.prototype._drawSvg.call(this, 'svg_polys');
    },

    _buildPathFromPoint: function(d) {
        try {
            return "M" + d.join("L") + "Z";
        } catch (e) {}
    },

    drawGroup: function(key, map) {
        var data = this._dataR[key];
        var g = svg_m.append('g');
        g.selectAll('path')
            .data(data)
            .enter()
            .append('path').attr("d", this._buildPathFromPoint)
            .attr('stroke', this.options.color)
            .attr('stroke-width', this.options.lineWidth)
            .attr('vector-effect', 'non-scaling-stroke')
            .attr("transform", "scale(" + Math.pow(2, (map.getZoom() - this.options.svgZoom)) + ")");
    },
});

L.CusOverLay.Circles = L.CusOverLay.extend({

	_drawSvg: function() {
        L.CusOverLay.prototype._drawSvg.call(this, 'svg_circles');
    },

	drawGroup: function(key, map) {
        var data = this._dataR[key];
		// console.log(data);
        var g = svg_m.append('g');
        g.selectAll('circle')
            .data(data)
            .enter()
            .append('circle')
			.attr('cx', function(d){return d.x;})
			.attr('cy', function(d){return d.y;})
			.attr('r', function(d){return d.r;})
            .attr('stroke', this.options.color)
            .attr('stroke-width', this.options.lineWidth)
            .attr('vector-effect', 'non-scaling-stroke')
            .attr("transform", "scale(" + Math.pow(2, (map.getZoom() - this.options.svgZoom)) + ")");
    },

	_projectData: function(json, map) {
        var init_z = this.options.svgZoom,
			r = this.options.radius;

        json.forEach(function(d) {
            var latlng = new L.LatLng(d.DEC, d.RA);
            var point = map.project(latlng, init_z);
            d.x = point.x;
            d.y = point.y;
			d.r = d.RADIUS === undefined? r:d.RADIUS;

        });
		// console.log(json);
        return json;
    },
});

L.CusOverLay.Lines = L.CusOverLay.extend({

	_drawSvg: function() {
        L.CusOverLay.prototype._drawSvg.call(this, 'svg_lines');
    },

    drawGroup: function(key, map) {
        var data = this._dataR[key];
        var g = svg_m.append('g');
        g.selectAll('path')
            .data(data)
            .enter()
            .append('path').attr("d", this._buildPathFromPoint)
            .attr('stroke', this.options.color)
            .attr('stroke-width', this.options.lineWidth)
            .attr('vector-effect', 'non-scaling-stroke')
            .attr("transform", "scale(" + Math.pow(2, (map.getZoom() - this.options.svgZoom)) + ")");
        // this._fms[key] = g;
    },

	_buildPathFromPoint: function(d) {
        try {
            return "M" + d.x1 + ',' + d.y1 + 'L' + d.x2 + ',' + d.y2;
        } catch (e) {
            console.log(e);
        }
    },

	_projectData: function(json, map) {
        var init_z = this.options.svgZoom;
        // console.log(init_z);
        json.forEach(function(d) {
            var latlng1 = new L.LatLng(d.DEC1, d.RA1);
            var latlng2 = new L.LatLng(d.DEC2, d.RA2);

            var point1 = map.project(latlng1, init_z);
            var point2 = map.project(latlng2, init_z);

            d.x1 = point1.x;
            d.y1 = point1.y;
            d.x2 = point2.x;
            d.y2 = point2.y;

        });
        return json;
    },
});
