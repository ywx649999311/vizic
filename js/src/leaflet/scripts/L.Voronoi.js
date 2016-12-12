var d3 = require('d3');
L.Voronoi = L.Layer.extend({
    options: {
        color: '#88b21c',
        lineWidth: 1,
        svgZoom: 5,
    },

    initialize: function(url, options) {
        L.setOptions(this, options);
        this._url = url;
        this._json = [];
        this._vs = {};
        this._getData();
        this._gs = {};
    },

    sortJson: function(cells) {
        var canvasData = cells;
        var frameCount = 4,
            oneDimCount = Math.sqrt(frameCount);
        var sortDataDEC = canvasData.sort(this.comp_func_y),
            chunk = Math.floor(canvasData.length / frameCount),
            // frameData = {},
            sortDataRA;
        for (var i = 0, l = 0; i < oneDimCount; l += chunk * oneDimCount, i++) {
            var ra_cut = sortDataDEC.slice(l, l + chunk * oneDimCount).sort(this.comp_func_x);
            for (var j = 0, z = 0; j < oneDimCount; z += chunk, j++) {
                this._vs[this.getFrameKey(i, j)] = ra_cut.slice(z, z + chunk);
            }
        }
    },

    onAdd: function() {
        this.inertia = this._map.options.inertia;
        this.fadeAnimation = this._map.options.fadeAnimation;
        this._map.options.inertia = false;
        this._map.options.fadeAnimation = false;
        this._el = L.DomUtil.create('div', 'leaflet-zoom-hide');
        this.getPane().appendChild(this._el);
        console.log('onAdd');
    },

    add: function() {
        var that = this;
        this._voronoi = this._projectData(this._json, this._map);
        this.sortJson(this._voronoi.polygons());
        setTimeout(function() {
            that.drawSvg();
        });
    },

    onRemove: function() {
        this.getPane().removeChild(this._el);
        this._map.options.inertia = this.inertia;
        this._map.options.fadeAnimation = this.fadeAnimation;
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


    comp_func_y: function(a, b) {
        return a.data.y - b.data.y;
    },

    comp_func_x: function(a, b) {
        return a.data.x - b.data.x;
    },

    getFrameKey: function(i, j) {
        return i + ':' + j;
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

    _getData: function() {
        var that = this;
        // var init_z = this.options.init_draw_z;
        d3.json(this._url, function(error, json) {
            if (error) {
                return console.log(error);
            }
            // console.log(json.length);
            that._json = json;
            var draw = L.bind(that.add, that);
            draw();
        });

    },

    drawSvg: function() {
        var that = this,
            key,
            zoom = this._map.getZoom(),
            pixOrigin = this._map.getPixelOrigin(),
            offset = L.point(0, 0).subtract(pixOrigin);
        this.zoomOnAdd = zoom;
        svg_v = d3.select(this._el).append('svg')
            .style('width', '100000px')
            .style('height', '100000px')
            .attr('fill', 'none')
            .attr('overflow', 'visible')
            .attr('id', 'v_svg');

        for (key in this._vs) {
            L.Util.requestAnimFrame(L.bind(this.drawGroup, this, key, this._map));
        }
        L.DomUtil.setPosition(this._el, offset);
        this.getPane().appendChild(this._el);
    },

    drawGroup: function(key, map) {
        var data = this._vs[key];
        var g = svg_v.append('g');
        g.selectAll('path')
            .data(data)
            .enter()
            .append('path').attr("d", this._buildPathFromPoint)
            .attr('stroke', this.options.color)
            .attr('stroke-width', this.options.lineWidth)
            .attr('vector-effect', 'non-scaling-stroke')
            .attr("transform", "scale(" + Math.pow(2, (map.getZoom() - this.options.svgZoom)) + ")");
        // this._gs[key]=g;
        console.log(g);
    },

    _buildPathFromPoint: function(d) {
        try {
            //console.log(d);
            return "M" + d.join("L") + "Z";
        } catch (e) {

        }
    },

    _resetView: function() {
        var zoom = this._map.getZoom(),
            pixOrigin = this._map.getPixelOrigin(),
            offset = L.point(0, 0).subtract(pixOrigin),
            map = this._map;
        L.DomUtil.setPosition(this._el, offset);
        d3.select(this._el).selectAll('g').attr("transform", "scale(" + Math.pow(2, (map.getZoom() - this.zoomOnAdd)) + ")");
    },

});

L.voronoi = function(url, map) {
    return new L.Voronoi(url, map);
};
