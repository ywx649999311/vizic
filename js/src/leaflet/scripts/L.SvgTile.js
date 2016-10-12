var d3 = require("d3");
L.SvgTile = L.GridLayer.extend({

            options: {
                maxZoom: 12,
                errorTileUrl: '',
                zoomOffset: 0,
                maxNativeZoom: null, // Number
                //tms: false,
                //zoomReverse: false,
                detectRetina: false,
                crossOrigin: true,
                collection: '',
                xRange: 1,
                yRange: 1,
            },

            initialize: function (options){
                options = L.setOptions(this, options);
                //this._xhrs = [];
                this._cTiles={};
                this._data={};

            },

            createTile: function (coords, done){

                var tile = L.DomUtil.create('div','leaflet-tile');
                var that = this;
                tile.alt = '';

                var tile_url = this.getTileUrl(coords);
                key = this._tileCoordsToKey(coords);
                d3.json(tile_url, function (error, json){

                    if (error) {

                        return console.log(error);
                    }
                    // console.log(json);
                    json.forEach(function (d){
                        var latlng = new L.LatLng(d.DEC, d.RA);
                        var map_point = that._map.project(latlng, coords.z).round();

                        d.cx=map_point.x-coords.x*256;
                        d.cy=map_point.y-coords.y*256;
                        d.rotate=['rotate(', d.THETA_IMAGE+90, d.cx, d.cy, ')'].join(' ');

                    });
                    that._drawShapes(json, tile, coords);
                    that._data[key]=json;
                    done(null, tile);
                });
                return tile;
            },

            getTileUrl: function (coords) {

                return L.Util.template('/tiles/{coll}/{z}/{x}/{y}.json', L.extend({
                    //r: this.options.detectRetina && L.Browser.retina && this.options.maxZoom > 0 ? '@2x' : '',
                    //s: this._getSubdomain(coords),
                    x: coords.x,
                    y: coords.y,
                    z: this._getZoomForUrl(),
                    coll: this.options.collection,
                }, this.options));
            },

            _pruneTiles: function () {
                var key, tile;

                var zoom = this._map.getZoom();
                if (zoom > this.options.maxZoom ||
                    zoom < this.options.minZoom) { return this._removeAllTiles(); }

                for (key in this._tiles) {
                    tile = this._tiles[key];
                    tile.retain = tile.current;
                }

                for (key in this._tiles) {
                    tile = this._tiles[key];
                    if (tile.current && !tile.active) {
                        var coords = tile.coords;
                        if (!this._retainParent(coords.x, coords.y, coords.z, coords.z - 5)) {
                            this._retainChildren(coords.x, coords.y, coords.z, coords.z + 2);
                        }
                    }
                }

                for (key in this._tiles) {
                    if (!this._tiles[key].retain) {
                        this._cTiles[key]=this._tiles[key];
                        this._removeTile(key);
                    }
                }
            },

            _resetView: function (e) {
                var animating = e && (e.pinch || e.flyTo);
                this._setView(this._map.getCenter(), this._map.getZoom(), animating, animating);
                //set a timeout to wait for the animation to finish
                setTimeout(this._removeOldLevel(this._map.getZoom()), 300);

            },

            _isValidTile: function (coords){
                var limit = Math.pow(2, coords.z);

                if (coords.x < 0 || coords.y < 0 || coords.x >= limit || coords.y >= limit){
                    return false;
                }

                if (!this.options.bounds) { return true; }


                // don't load tile if it doesn't intersect the bounds in options
                var tileBounds = this._tileCoordsToBounds(coords);
                return L.latLngBounds(this.options.bounds).overlaps(tileBounds);
            },

            _addTile: function (coords, container) {
                var tilePos = this._getTilePos(coords),
                    key = this._tileCoordsToKey(coords);

                if (this._cTiles[key]){
                    this._addCTile(tilePos, key, container, coords);
                    // callback(null);
                    return ;
                }

                var tile = this.createTile(this._wrapCoords(coords), L.bind(this._tileReady, this, coords));

                this._initTile(tile);

                // if createTile is defined with a second argument ("done" callback),
                // we know that tile is async and will be ready later; otherwise
                if (this.createTile.length < 2) {
                    // mark tile as ready, but delay one frame for opacity animation to happen
                    L.Util.requestAnimFrame(L.bind(this._tileReady, this, coords, null, tile));
                }

                L.DomUtil.setPosition(tile, tilePos);

                // save tile in cache
                this._tiles[key] = {
                    el: tile,
                    coords: coords,
                    current: true
                };

                container.appendChild(tile);
                this.fire('tileloadstart', {
                    tile: tile,
                    coords: coords
                });

                // callback(null);
            },

            _addCTile: function(tilePos, key, container, coords){
                this._tiles[key]=this._cTiles[key];
                this._removeCTile(key);
                var tile = this._tiles[key].el;

                L.DomUtil.setPosition(tile, tilePos);

                this._tiles[key].current=true;
                container.appendChild(tile);

                this.fire('tileloadstart',{
                    tile: tile,
                    coords: coords

                });

                //L.Util.requestAnimFrame(L.bind(this._tileReady,this, coords, null, tile));
                this._tileReady(coords, null, tile);


            },

            _removeCTile: function (key) {
                var tile = this._cTiles[key];
                if (!tile) { return; }

                L.DomUtil.remove(tile.el);

                delete this._cTiles[key];
            },

            _updateLevels: function () {

                var zoom = this._tileZoom,
                    maxZoom = this.options.maxZoom;

                for (var z in this._levels) {
                    if (this._levels[z].el.children.length || z === zoom) {
                        this._levels[z].el.style.zIndex = maxZoom - Math.abs(zoom - z);
                    } else {
                        L.DomUtil.remove(this._levels[z].el);
                        delete this._levels[z];
                    }
                }

                var level = this._levels[zoom],
                    map = this._map;



                if (!level) {
                    level = this._levels[zoom] = {};

                    level.el = L.DomUtil.create('div', 'leaflet-tile-container leaflet-zoom-animated', this._container);
                    level.el.style.zIndex = maxZoom;

                    //different size of div for different zooms, and set it to balck
                    width_height = Math.pow(2,zoom)*256+'px';
                    level.el.style.width = width_height;
                    level.el.style.height = width_height;
                    level.el.style.background = 'black';

                    //avoid extra shift to make the level well aligned with the tile divs
                    level.origin = L.point(0,0);
                    level.zoom = zoom;
                    this._setZoomTransform(level, this._map.getCenter(), this._map.getZoom());
                    // force the browser to consider the newly added element for transition
                    //L.Util.falseFn(level.el.offsetWidth);
                }

                this._level = level;

                return level;
            },

            // _setZoomTransform: function (level, center, zoom) {
            //     var viewHalf = this._map.getSize()._divideBy(2);
            //     var projectedCenter = this._map.project(center, zoom);
            //     var newOrigin = projectedCenter._subtract(viewHalf)._add(this._map._getMapPanePos()).round();
        	// 	var scale = this._map.getZoomScale(zoom, level.zoom),
        	// 	    translate = level.origin.multiplyBy(scale)
        	// 	        .subtract(newOrigin).round();
            //
        	// 	if (L.Browser.any3d) {
        	// 		L.DomUtil.setTransform(level.el, translate, scale);
        	// 	} else {
        	// 		L.DomUtil.setPosition(level.el, translate);
        	// 	}
        	// },


            _drawShapes: function(data, tile, coords){

                var zoom = coords.z;
                var multi_X = (256*Math.pow(2,zoom))/this.options.xRange,
                    multi_Y = (256*Math.pow(2,zoom))/this.options.yRange;

                var svg_pane=d3.select(tile).append('svg')
                    .attr('viewBox', '0 0 256 256')
                    .style('overflow', 'visible');
                    //.attr('height', 256)
                    //.attr('width', 256);

                var svg_g = svg_pane.append('g').attr('class', 'leaflet-zoom-hide');

                var ellipses = svg_g.selectAll('ellipse')
                                .data(data)
                                .enter()
                                .append('ellipse')
                                .attr('cx', function (d){ return d.cx;})
                                .attr('cy', function (d){ return d.cy;})
                                .attr('rx', function (d) {return d.a*multi_X;})
                                .attr('ry', function (d){ return d.b*multi_Y;})
                                .attr('transform', function (d){return d.rotate;})
                                .attr('fill', 'red');

                // d3.select(tile).selectAll('ellipse').on('click', L.DomEvent.stop)
                                                    // .on('click', function(e){layerClass._displayObject(e);});

                return ellipses;

            },

            _displayObject: function(e){
                var object_url = 'object/'+e.RA+'/'+e.DEC+'.json';
                var html='';

               d3.json(object_url, function(error,json){

                    if (error) {return console.log(error);}

                    json = json[0];

                    for (var key in json){
                        if (key!=='_id'){
                            html+=key+':'+json[key]+'<br>';
                        }

                    }

                    document.getElementById('object_display').innerHTML=html;

               });
            },

            _removeOldLevel: function(zoom){

                for (var i in this._levels){
                    if (i != zoom){
                        this._removeOldTiles(i);
                        L.DomUtil.remove(this._levels[i].el);
                        delete this._levels[i];
                    }
                }
            },

            _removeOldTiles: function (zoom){
                //console.log(typeof(zoom));
                var coords;

                for (var key in this._tiles){
                    coords = this._keyToTileCoords(key);
                    if (coords.z==zoom){
                        this._cTiles[key]=this._tiles[key];
                        delete this._tiles[key];
                    }
                }

            },

            _getKey: function (coords) {

                z = this._getZoomForUrl();
                x = coords.x;
                y = coords.y;
                return x + ':' + y + ':' + z;
            },

            _getZoomForUrl: function () {

                var options = this.options,
                    zoom = this._tileZoom;

                // if (options.zoomReverse) {
                //     zoom = options.maxZoom - zoom;
                // }

                zoom += options.zoomOffset;

                return options.maxNativeZoom !== null ? Math.min(zoom, options.maxNativeZoom) : zoom;
            }
        });

L.svgTile = function (options){
    return new L.SvgTile(options);
};
