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
            that.drawSvg();
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

    drawSvg: function(svg_id) {
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

    drawGroup: function(key, map, type) {
        var data = this._dataR[key];
        var g = svg_m.append('g');
        g.selectAll(type)
            .data(data)
            .enter()
            .append(type).attr("d", this._buildPathFromPoint)
            .attr('stroke', this.options.color)
            .attr('stroke-width', this.options.lineWidth)
            .attr('vector-effect', 'non-scaling-stroke')
            .attr("transform", "scale(" + Math.pow(2, (map.getZoom() - this.options.svgZoom)) + ")");
        // this._fms[key] = g;
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
