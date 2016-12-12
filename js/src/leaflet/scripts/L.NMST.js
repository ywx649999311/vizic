var d3 = require("d3");
L.MST = L.Layer.extend({
    options: {
        color: '#0459e2',
        lineWidth: 1,
        svgZoom: 5,
    },

    initialize: function(url, options) {
        L.setOptions(this, options);
        this._url = url;
        this._json = [];
        this._msts = {};
        this._getData();
        this._gs = {};
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
        this._json = this._projectData(this._json, this._map);
        this.sortJson(this._json);
        setTimeout(function() {
            that.drawSvg();
        });
    },

    drawSvg: function() {
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
            .attr('id', 'mst_svg');

        for (key in this._msts) {
            L.Util.requestAnimFrame(L.bind(this.drawGroup, this, key, this._map));
        }
        L.DomUtil.setPosition(this._el, offset);
        this.getPane().appendChild(this._el);
    },

    drawGroup: function(key, map) {
        var data = this._msts[key];
        var g = svg_m.append('g');
        g.selectAll('path')
            .data(data)
            .enter()
            .append('path').attr("d", this._buildPathFromPoint)
            .attr('stroke', this.options.color)
            .attr('stroke-width', this.options.lineWidth)
            .attr('vector-effect', 'non-scaling-stroke')
            .attr("transform", "scale(" + Math.pow(2, (map.getZoom() - this.options.svgZoom)) + ")");
        // this._gs[key]=g;
    },

    _buildPathFromPoint: function(d) {
        try {
            //console.log(d);
            return "M" + d.x1 + ',' + d.y1 + 'L' + d.x2 + ',' + d.y2;
        } catch (e) {
            console.log(e);
        }
    },

    _resetView: function() {
        var zoom = this._map.getZoom(),
            pixOrigin = this._map.getPixelOrigin(),
            offset = L.point(0, 0).subtract(pixOrigin),
            map = this._map;
        L.DomUtil.setPosition(this._el, offset);
        d3.select('#mst_svg').selectAll('g').attr("transform", "scale(" + Math.pow(2, (map.getZoom() - this.zoomOnAdd)) + ")");

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

    sortJson: function(json) {
        var canvasData = json;
        var frameCount = 4,
            oneDimCount = Math.sqrt(frameCount);
        var sortDataRA = canvasData.sort(this.comp_func_ra),
            chunk = Math.floor(canvasData.length / frameCount),
            // frameData = {},
            sortDataDec;
        for (var i = 0, l = 0; i < oneDimCount; l += chunk * oneDimCount, i++) {
            var ra_cut = sortDataRA.slice(l, l + chunk * oneDimCount).sort(this.comp_func_dec);
            for (var j = 0, z = 0; j < oneDimCount; z += chunk, j++) {
                this._msts[this.getFrameKey(i, j)] = ra_cut.slice(z, z + chunk);
            }
        }
    },

    comp_func_dec: function(a, b) {
        return Math.abs(a.DEC1) - Math.abs(b.DEC1);
    },

    comp_func_ra: function(a, b) {
        return a.RA1 - b.RA1;
    },

    getFrameKey: function(i, j) {
        return i + ':' + j;
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

    _projectData: function(json, map) {
        var init_z = this.options.svgZoom;
        console.log(init_z);
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

L.mst = function(url, options) {
    return new L.MST(url, options);
};
