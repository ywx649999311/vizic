var widgets = require('jupyter-js-widgets');
var _ = require('underscore');
var L = require('leaflet/leaflet-src');
var d3 = require("d3");
var d3SC = require('d3-scale-chromatic');
require('leaflet-draw');
require('leaflet/scripts/L.DesCRS');
require('leaflet/scripts/L.SvgTile');
require('leaflet/scripts/L.Control.MousePosition');
require('leaflet-fullscreen');


L.Icon.Default.imagePath = __webpack_public_path__;

function camel_case(input) {
    // Convert from foo_bar to fooBar
    return input.toLowerCase().replace(/_(.)/g, function(match, group1) {
        return group1.toUpperCase();
    });
}

var NotebookUrlView = widgets.WidgetView.extend({

    render: function(){
        this.host = document.location.origin;
        this.base_url = document.querySelector('body').getAttribute('data-base-url');
        this.nb_url = this.host + this.base_url;
        this.el.textContent = this.nb_url;
        this.update();

    },
    update:function(){
        var that = this;
        this.model.set('nb_url', that.nb_url);
        this.touch();
    },

});

var HomeButtonView = widgets.ButtonView.extend({
    render: function(){
        HomeButtonView.__super__.render.call(this);
        var i = document.createElement('i');

        this.el.className += " home-button";
    }
});

var PopupDisView = widgets.WidgetView.extend({

    render: function(){
        this.create_obj();
        this.model_events();
    },

    model_events: function(){
        var that = this;
        this.listenTo(this.model, 'change:_object_info', function(){
            that.create_obj();
        },this);
    },
    create_obj: function(){
        var that = this;
        while (that.el.hasChildNodes()){
            that.el.removeChild(that.el.lastChild);
        }
        var table = document.createElement('TABLE');
        var jObj = this.model.get('_object_info');
        var keys = Object.keys(jObj);
        keys.forEach(function(d){
            var row = table.insertRow();
            row.insertCell().textContent = d;
            row.insertCell().textContent = jObj[d];
        });
        d3.select(table).style('font-size', '13px').style('border', '1px solid black').style('border-collapse', 'collapse');
        d3.select(table).selectAll('td').style('border','1px solid black');
        d3.select(table).selectAll('tr').on('mouseover', function(){
            d3.select(this).style('background-color', '#d5d5d5');
        });
        d3.select(table).selectAll('tr').on('mouseout', function(){
            d3.select(this).style('background-color', 'white');
        });
        this.el.append(table);
    }
});


var LeafletLayerView = widgets.WidgetView.extend({

    initialize: function (parameters) {
        LeafletLayerView.__super__.initialize.apply(this, arguments);
        this.map_view = this.options.map_view;
    },

    render: function () {
        this.create_obj();
        this.leaflet_events();
        this.model_events();
    },

    leaflet_events: function () {
    },

    model_events: function () {
    },

    get_options: function () {
        var o = this.model.get('options');
        var options = {};
        var key;
        for (var i=0; i<o.length; i++) {
            key = o[i];
            // Convert from foo_bar to fooBar that Leaflet.js uses
            options[camel_case(key)] = this.model.get(key);
        }
        return options;
    },
});

// RasterLayer
var LeafletRasterLayerView = LeafletLayerView.extend({
});

var LeafletGridLayerView = LeafletRasterLayerView.extend({
    create_obj: function (){
        this.obj = L.svgTile(this.get_options());

    },
    model_events: function () {
        var that = this;
        function single_cTile(key, color, callback){
            d3.select(that.obj._cTiles[key].el).selectAll('ellipse').attr('fill', color);
            callback(null);
        }
        this.listenTo(this.model, 'change:color', function(){
            var q = d3.queue();
            var c = this.model.get('color');
            d3.selectAll('.leaflet-tile').selectAll('ellipse').attr('fill', c);
            this.obj.options.color = c;
            for (key in that.obj._cTiles){
                q.defer(single_cTile, key, c);
            }
            q.awaitAll(function(error){
                if (error) throw error;
                console.log('single color change done');
            });
        }, this);
        this.listenTo(this.model, 'change:c_min_max', function(){
            var custom_c = this.model.get('custom_c');
            var c_min_max = this.model.get('c_min_max');
            var interpolate = d3.scaleSequential(d3SC.interpolateSpectral).domain(c_min_max);
            function update_cTile(key, c_field, callback){
                d3.select(that.obj._cTiles[key].el).selectAll('ellipse').attr('fill', function(d){
                    return interpolate(d[c_field]);});
                callback(null);
            }
            var q = d3.queue();
            if (custom_c == true){
                var c_field = this.model.get('c_field');
                d3.selectAll('.leaflet-tile').selectAll('ellipse').attr('fill', function(d){
                    return interpolate(d[c_field]);});
                for (key in that.obj._cTiles){
                    q.defer(update_cTile, key, c_field);
                }
                q.awaitAll(function(error){
                    if (error) throw error;
                    console.log('update cTiles for customC');
                });
                that.obj.options.customC = true;
                that.obj.options.cMinMax = c_min_max;
                that.obj.options.cField = c_field;
            }
            else{
                d3.selectAll('.leaflet-tile').selectAll('ellipse').attr('fill', that.model.get('color'));
                var c = this.model.get('color');
                for (key in that.obj._cTiles){
                    q.defer(single_cTile, key, c);
                }
                q.awaitAll(function(error){
                    if (error) throw error;
                    console.log('back to single color');
                });
                that.obj.options.customC = false;
                that.obj.options.cMinMax = [];
                that.obj.options.cField = undefined;
            }
        }, this);

    },
    leaflet_events: function(){
        var that = this;
        this.obj.on('load', function(){
            d3.select(that.obj._level.el).selectAll('ellipse').on('click', function(d){
                that.send({
                    'event': 'popup: click',
                    'RA': d.RA,
                    'DEC': d.DEC
                });
            });
        });
    }
});

var LeafletTileLayerView = LeafletRasterLayerView.extend({

    create_obj: function () {
        this.obj = L.tileLayer(
            this.model.get('url'),
            this.get_options()
        );
    },
});

var LeafletImageOverlayView = LeafletRasterLayerView.extend({

    create_obj: function () {
        this.obj = L.imageOverlay(
            this.model.get('url'),
            this.model.get('bounds'),
            this.get_options()
        );
    },
});


// UILayer
var LeafletUILayerView = LeafletLayerView.extend({
});


var LeafletMarkerView = LeafletUILayerView.extend({

    create_obj: function () {
        this.obj = L.marker(
            this.model.get('location'),
            this.get_options()
        );
    },

    model_events: function () {
        LeafletMarkerView.__super__.model_events.apply(this, arguments);
        this.listenTo(this.model, 'change:location', function () {
            this.obj.setLatLng(this.model.get('location'));
        }, this);
        this.listenTo(this.model, 'change:z_index_offset', function () {
            this.obj.setZIndexOffset(this.model.get('z_index_offset'));
        }, this);
        this.listenTo(this.model, 'change:opacity', function () {
            this.obj.setOpacity(this.model.get('opacity'));
        }, this);
    },
});


var LeafletPopupView = LeafletUILayerView.extend({
});




// VectorLayer
var LeafletVectorLayerView = LeafletLayerView.extend({
});


var LeafletPathView = LeafletVectorLayerView.extend({

    model_events: function () {
        LeafletPathView.__super__.model_events.apply(this, arguments);
        var key;
        var o = this.model.get('options');
        for (var i=0; i<o.length; i++) {
            key = o[i];
            this.listenTo(this.model, 'change:' + key, function () {
                this.obj.setStyle(this.get_options());
            }, this);
        }
    },

});


var LeafletPolylineView = LeafletPathView.extend({
    create_obj: function () {
        this.obj = L.polyline(
            this.model.get('locations'),
            this.get_options()
        );
    },
});


var LeafletPolygonView = LeafletPolylineView.extend({
    create_obj: function () {
        this.obj = L.polygon(
            this.model.get('locations'),
            this.get_options()
        );
    },
});


var LeafletRectangleView = LeafletPolygonView.extend({
    create_obj: function () {
        this.obj = L.rectangle(
            this.model.get('bounds'),
            this.get_options()
        );
    },
});


var LeafletCircleView = LeafletPathView.extend({
    create_obj: function () {
        this.obj = L.circle(
            this.model.get('location'), this.model.get('radius'),
            this.get_options()
        );
    },
});


var LeafletCircleMarkerView = LeafletCircleView.extend({
    create_obj: function () {
        this.obj = L.circleMarker(
            this.model.get('location'), this.model.get('radius'),
            this.get_options()
        );
    },
});


var LeafletLayerGroupView = LeafletLayerView.extend({
    create_obj: function () {
        this.obj = L.layerGroup();
    },
});


var LeafletFeatureGroupView = LeafletLayerGroupView.extend({
    create_obj: function () {
        this.obj = L.featureGroup();
    },
});


var LeafletMultiPolylineView = LeafletFeatureGroupView.extend({
});


var LeafletGeoJSONView = LeafletFeatureGroupView.extend({
    create_obj: function () {
        var that = this;
        var style = this.model.get('style');
        if (_.isEmpty(style)) {
            style = function (feature) {
                return feature.properties.style;
            }
        }
        this.obj = L.geoJson(this.model.get('data'), {
            style: style,
            onEachFeature: function (feature, layer) {
                var mouseevent = function (e) {
                    if (e.type == 'mouseover') {
                        layer.setStyle(that.model.get('hover_style'));
                        layer.once('mouseout', function () {
                            that.obj.resetStyle(layer);
                        });
                    }
                    that.send({
                        event: e.type,
                        properties: feature.properties,
                        id: feature.id
                    });
                };
                layer.on({
                    mouseover: mouseevent,
                    click: mouseevent
                });
            }
        });
    },
});


var LeafletMultiPolygonView = LeafletFeatureGroupView.extend({
    create_obj: function () {
        this.obj = L.multiPolygon(
            this.model.get('locations'),
            this.get_options()
        );
    },
});


var LeafletControlView = widgets.WidgetView.extend({
    initialize: function (parameters) {
        LeafletControlView.__super__.initialize.apply(this, arguments);
        this.map_view = this.options.map_view;
    },
});


var LeafletDrawControlView = LeafletControlView.extend({
    initialize: function (parameters) {
        LeafletDrawControlView.__super__.initialize.apply(this, arguments);
        this.map_view = this.options.map_view;
    },

    render: function () {
        var that = this;
        return this.create_child_view(this.model.get('layer'), {
            map_view: this.map_view
        }).then(function (layer_view) {
            that.map_view.obj.addLayer(layer_view.obj);
            // TODO: create_obj refers to the layer view instead of the layer
            // view promise. We should fix that.
            that.layer_view = layer_view;
            that.create_obj();
            return that;
        });
    },

    create_obj: function () {
        var that = this;
        var polyline = this.model.get('polyline');
        if (_.isEmpty(polyline)) { polyline = false; }
        var polygon = this.model.get('polygon');
        if (_.isEmpty(polygon)) { polygon = false; }
        var circle = this.model.get('circle');
        if (_.isEmpty(circle)) { circle = false; }
        var rectangle = this.model.get('rectangle');
        if (_.isEmpty(rectangle)) { rectangle = false; }
        var marker = this.model.get('marker');
        if (_.isEmpty(marker)) { marker = false; }
        var edit = this.model.get('edit')
        var remove = this.model.get('remove');
        this.obj = new L.Control.Draw({
            edit: {
                featureGroup: this.layer_view.obj,
                edit: edit,
                remove: remove
            },
            draw: {
                polyline: polyline,
                polygon: polygon,
                circle: circle,
                rectangle: rectangle,
                marker: marker
            }
        });
        this.map_view.obj.on('draw:created', function (e) {
            var type = e.layerType;
            var layer = e.layer;
            var geo_json = layer.toGeoJSON();
            geo_json.properties.style = layer.options;
            that.send({
                'event': 'draw:created',
                'geo_json': geo_json
            });
            that.layer_view.obj.addLayer(layer);
        });
        this.map_view.obj.on('draw:edited', function (e) {
            var layers = e.layers;
            layers.eachLayer(function (layer) {
                var geo_json = layer.toGeoJSON();
                geo_json.properties.style = layer.options;
                that.send({
                    'event': 'draw:edited',
                    'geo_json': geo_json
                });
            });
        });
        this.map_view.obj.on('draw:deleted', function (e) {
            var layers = e.layers;
            layers.eachLayer(function (layer) {
                var geo_json = layer.toGeoJSON();
                geo_json.properties.style = layer.options;
                that.send({
                    'event': 'draw:deleted',
                    'geo_json': geo_json
                });
            });
        });
    },

});


var LeafletMapView = widgets.DOMWidgetView.extend({
    initialize: function (options) {
        LeafletMapView.__super__.initialize.apply(this, arguments);
    },

    remove_layer_view: function (child_view) {
        this.obj.removeLayer(child_view.obj);
        child_view.remove();
    },

    add_layer_model: function (child_model) {
        var that = this;
        return this.create_child_view(child_model, {
            map_view: this
        }).then(function (child_view) {
            that.obj.addLayer(child_view.obj);
            return child_view;
        });
    },

    remove_control_view: function (child_view) {
        this.obj.removeControl(child_view.obj);
        child_view.remove();
    },

    add_control_model: function (child_model) {
        var that = this;
        return this.create_child_view(child_model, {
            map_view: this
        }).then(function (child_view) {
            that.obj.addControl(child_view.obj);
            return child_view;
        });
    },

    render: function () {
        this.el.style['width'] = this.model.get('width');
        this.el.style['height'] = this.model.get('height');
        this.layer_views = new widgets.ViewList(this.add_layer_model, this.remove_layer_view, this);
        this.control_views = new widgets.ViewList(this.add_control_model, this.remove_control_view, this);
        this.displayed.then(_.bind(this.render_leaflet, this));
    },

    render_leaflet: function () {
        this.create_obj();
        this.layer_views.update(this.model.get('layers'));
        this.control_views.update(this.model.get('controls'));
        this.leaflet_events();
        this.model_events();
        this.update_bounds();
        // console.log(this.obj.options.crs.adjust);
        // TODO: hack to get all the tiles to show.
        var that = this;

        this.update_crs()
        // window.setTimeout(function () {
        //     // that.update_crs();
        //     that.obj.invalidateSize();
        //     // that.update_crs();
        // }, 1000);
        return that;
    },

    create_obj: function () {
        this.obj = L.map(this.el, this.get_options());
    },

    get_options: function () {
        var o = this.model.get('options');
        var options = {};
        var key;
        for (var i=0; i<o.length; i++) {
            key = o[i];
            // Convert from foo_bar to fooBar that Leaflet.js uses
            options[camel_case(key)] = this.model.get(key);
        }
        options.crs = L.extend({},L.CRS.RADEC);
        return options;
    },

    leaflet_events: function () {
        var that = this;
        this.obj.on('moveend', function (e) {
            var c = e.target.getCenter();
            that.model.set('center', [c.lat, c.lng]);
            that.touch();
            that.update_bounds();
        });
        this.obj.on('zoomend', function (e) {
            var z = e.target.getZoom();
            that.model.set('zoom', z);
            that.touch();
            that.update_bounds();
        });
        this.obj.on('fullscreenchange', function(e){
            if (!that.obj.isFullscreen()){
                that.obj.invalidateSize();
            }
            // if (document.webkitIsFullScreen) {
            //     window.setTimeout(function(){
            //         that.obj.invalidateSize();
            //     }, 150);
            // }
        });
    },

    update_bounds: function () {
        var that = this;
        var b = this.obj.getBounds();
        this.model.set('_north', b.getNorth());
        this.model.set('_south', b.getSouth());
        this.model.set('_east', b.getEast());
        this.model.set('_west', b.getWest());
        this.touch();
    },

    model_events: function () {
        var that = this;
        this.listenTo(this.model, 'msg:custom', this.handle_msg, this);
        this.listenTo(this.model, 'change:layers', function () {
            this.layer_views.update(this.model.get('layers'));
        }, this);
        this.listenTo(this.model, 'change:controls', function () {
            this.control_views.update(this.model.get('controls'));
        }, this);
        this.listenTo(this.model, 'change:zoom', function () {
            this.obj.setZoom(this.model.get('zoom'));
            this.update_bounds();
        }, this);
        this.listenTo(this.model, 'change:center', function () {
            this.obj.panTo(this.model.get('center'));
            this.update_bounds();
        }, this);
        this.listenTo(this.model, 'change:pan_loc', function(){
            var loc = this.model.get('pan_loc');
            if (loc.length != 0){
                console.log(loc.length);
                this.obj.setView([loc[0], loc[1]], loc[2]);
                this.update_bounds();
            }
        },this)
        this.listenTo(this.model, 'change:_des_crs', function() {
            _.bind(this.update_crs(), this);
            this.update_bounds();
        }, this);
    },

    update_crs: function(){
        var that = this;
        that.obj.options.crs.adjust = that.model.get('_des_crs');
        // // Force the new crs options to be propagated to the end
        that.obj._pixelOrigin = that.obj._getNewPixelOrigin(that.model.get('center'), that.model.get('zoom'));
    },

    handle_msg: function (content) {
        switch(content.method) {
            case 'foo':
                break;
        }
    },
});

var def_loc = [0.0, 0.0];

var LeafletLayerModel = widgets.WidgetModel.extend({
    defaults: _.extend({}, widgets.WidgetModel.prototype.defaults, {
        _view_name : 'LeafletLayerView',
        _model_name : 'LeafletLayerModel',
        _view_module : 'jupyter-astro-leaflet',
        _model_module : 'jupyter-astro-leaflet',
        // bottom : false,
        options : []
    }),


});


var LeafletUILayerModel = LeafletLayerModel.extend({
    defaults: _.extend({}, LeafletLayerModel.prototype.defaults, {
        _view_name : 'LeafletUILayerView',
        _model_name : 'LeafletUILayerModel'
    })
});


var LeafletMarkerModel = LeafletUILayerModel.extend({
    defaults: _.extend({}, LeafletUILayerModel.prototype.defaults, {
        _view_name :'LeafletMarkerView',
        _model_name : 'LeafletMarkerModel',
        location : def_loc,
        z_index_offset: 0,
        opacity: 1.0,
        clickable: true,
        draggable: false,
        keyboard: true,
        title: '',
        alt: '',
        rise_on_hover: false,
        rise_offset: 250
    })
});


var LeafletPopupModel = LeafletUILayerModel.extend({
    defaults: _.extend({}, LeafletUILayerModel.prototype.defaults, {
         _view_name : 'LeafletPopupView',
         _model_name : 'LeafletPopupModel'
    })
});


var LeafletRasterLayerModel = LeafletLayerModel.extend({
    defaults: _.extend({}, LeafletLayerModel.prototype.defaults, {
        _view_name : 'LeafletRasterLayerView',
        _model_name : 'LeafletRasterLayerModel'
    })
});


var LeafletTileLayerModel = LeafletRasterLayerModel.extend({
    defaults: _.extend({}, LeafletRasterLayerModel.prototype.defaults, {
        _view_name : 'LeafletTileLayerView',
        _model_name : 'LeafletTileLayerModel',

        // bottom : true,
        url : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        min_zoom : 0,
        max_zoom : 18,
        tile_size : 256,
        attribution : 'Map data (c) <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
        opacity : 1.0,
        detect_retina : false
    })
});

var LeafletGridLayerModel = LeafletRasterLayerModel.extend({
    defaults: _.extend({}, LeafletRasterLayerModel.prototype.defaults, {
        _view_name : 'LeafletGridLayerView',
        _model_name : 'LeafletGridLayerModel',

        _des_crs : [],
        bottom : false,
        min_zoom : 0,
        max_zoom : 8,
        collection: '',
        x_range: 1.0,
        y_range: 1.0,
        center: [],
        color: 'red',
        c_min_max: [],
        custom_c: false,
        c_field: '',
        // tile_size : 256,
        // opacity : 1.0,
        detect_retina : false
    }),
    initialize(attributes,options){
        widgets.WidgetModel.prototype.initialize(this, attributes, options);
        // console.log(this.attributes);
    }

});


var LeafletImageOverlayModel = LeafletRasterLayerModel.extend({
    defaults: _.extend({}, LeafletRasterLayerModel.prototype.defaults, {
        _view_name : 'LeafletImageOverlayView',
        _model_name : 'LeafletImageOverlayModel',

        url : '',
        bounds : [def_loc, def_loc],
        opacity : 1.0,
        attribution : ''
    })
});


var LeafletVectorLayerModel = LeafletLayerModel.extend({
    defaults: _.extend({}, LeafletLayerModel.prototype.defaults, {
        _view_name : 'LeafletVectorLayerView',
        _model_name : 'LeafletVectorLayerModel'
    })
});


var LeafletPathModel = LeafletVectorLayerModel.extend({
    defaults: _.extend({}, LeafletVectorLayerModel.prototype.defaults, {
        _view_name : 'LeafletPathView',
        _model_name : 'LeafletPathModel',

        stroke : true,
        color : '#0033FF',
        weight : 5,
        opacity : 0.5,
        fill : true,
        fill_color : '#0033FF',
        fill_opacity : 0.2,
        dash_array : '',
        line_cap : '',
        line_join :  '',
        clickable : true,
        pointer_events : '',
        class_name : ''
    })
});


var LeafletPolylineModel = LeafletPathModel.extend({
    defaults: _.extend({}, LeafletPathModel.prototype.defaults, {
        _view_name : 'LeafletPolylineView',
        _model_name : 'LeafletPolylineModel',

        locations : [],
        smooth_factor : 1.0,
        no_clip : false
    })
});


var LeafletPolygonModel = LeafletPolylineModel.extend({
    defaults: _.extend({}, LeafletPolylineModel.prototype.defaults, {
        _view_name : 'LeafletPolygonView',
        _model_name : 'LeafletPolygonModel'
    })
});


var LeafletRectangleModel = LeafletPolygonModel.extend({
    defaults: _.extend({}, LeafletPolygonModel.prototype.defaults, {
        _view_name : 'LeafletRectangleView',
        _model_name : 'LeafletRectangleModel',
        bounds : []
    })
});


var LeafletCircleModel = LeafletPathModel.extend({
    defaults: _.extend({}, LeafletPathModel.prototype.defaults, {
        _view_name : 'LeafletCircleView',
        _model_name : 'LeafletCircleModel',
        location : def_loc,
        radius : 10000
    })
});


var LeafletCircleMarkerModel = LeafletCircleModel.extend({
    defaults: _.extend({}, LeafletCircleModel.prototype.defaults, {
        _view_name : 'LeafletCircleMarkerView',
        _model_name : 'LeafletCircleMarkerModel',
        radius : 10
    })
});


var LeafletLayerGroupModel = LeafletLayerModel.extend({
    defaults: _.extend({}, LeafletLayerModel.prototype.defaults, {
        _view_name : 'LeafletLayerGroupView',
        _model_name : 'LeafletLayerGroupModel',
        layers : []
    })
}, {
    serializers: _.extend({
        layers: { deserialize: widgets.unpack_models }
    }, widgets.DOMWidgetModel.serializers)
});


var LeafletFeatureGroupModel = LeafletLayerModel.extend({
    defaults: _.extend({}, LeafletLayerModel.prototype.defaults, {
        _view_name : 'LeafletFeatureGroupView',
        _model_name : 'LeafletFeatureGroupModel'
    })
});


var LeafletGeoJSONModel = LeafletFeatureGroupModel.extend({
    defaults: _.extend({}, LeafletFeatureGroupModel.prototype.defaults, {
        _view_name : 'LeafletGeoJSONView',
        _model_name : 'LeafletGeoJSONModel',
        data : {},
        style : {},
        hover_style : {},
    })
});


var LeafletMultiPolylineModel = LeafletFeatureGroupModel.extend({
    defaults: _.extend({}, LeafletFeatureGroupModel.prototype.defaults, {
        _view_name : 'LeafletMultiPolylineView',
        _model_name : 'LeafletMultiPolylineModel'
    })
});


var LeafletMultiPolygonModel = LeafletFeatureGroupModel.extend({
    defaults: _.extend({}, LeafletFeatureGroupModel.prototype.defaults, {
        _view_name : 'LeafletMultiPolygonView',
        _model_name : 'LeafletMultiPolygonModel',
        locations: []
    })
});


var LeafletControlModel = widgets.WidgetModel.extend({
    defaults: _.extend({}, widgets.WidgetModel.prototype.defaults, {
        _view_name : 'LeafletControlView',
        _model_name : 'LeafletControlModel',
        _view_module : 'jupyter-astro-leaflet',
        _model_module : 'jupyter-astro-leaflet',
        options : []
    })
});


var LeafletDrawControlModel = LeafletControlModel.extend({
    defaults: _.extend({}, LeafletControlModel.prototype.defaults, {
        _view_name : 'LeafletDrawControlView',
        _model_name : 'LeafletDrawControlModel',

        layer : undefined,
        polyline : { shapeOptions : {} },
        polygon : { shapeOptions : {} },
        circle : {},
        rectangle : {},
        marker : {},
        edit : true,
        remove : true
    })
}, {
    serializers: _.extend({
        layer : { deserialize: widgets.unpack_models }
    }, LeafletControlModel.serializers)
});


var LeafletMapModel = widgets.DOMWidgetModel.extend({
    defaults: _.extend({}, widgets.DOMWidgetModel.prototype.defaults, {
        _view_name : "LeafletMapView",
        _model_name : "LeafletMapModel",
        _model_module : "jupyter-astro-leaflet",
        _view_module : "jupyter-astro-leaflet",

        center : def_loc,
        width : "512px",
        height : "512px",
        // grid_added = false,
        zoom : 1,
        max_zoom : 12,
        min_zoom : 0,
        // max_bounds: [[-90, 0], [90, 360]],

        dragging : true,
        touch_zoom : true,
        scroll_wheel_zoom : true,
        wheel_debounce_time:60,
        wheel_px_per_zoom_level: 60,
        double_click_zoom : true,
        box_zoom : true,
        tap : true,
        tap_tolerance : 15,
        world_copy_jump : false,
        close_popup_on_click : true,
        bounce_at_zoom_limits : true,
        keyboard : true,
        keyboardPanDelta : 80,
        inertia : true,
        inertia_deceleration : 3000,
        inertia_max_speed : 1500,
        zoom_control : true,
        attribution_control : true,
        // fade_animation : bool(?),
        // zoom_animation : bool(?),
        zoom_animation_threshold : 4,
        // marker_zoom_animation : bool(?),
        position_control : true,
        fullscreen_control : true,
        _south : def_loc[0],
        _north : def_loc[0],
        _east : def_loc[1],
        _west : def_loc[1],
        options : [],
        layers : [],
        controls : [],
        _des_crs : [],
        _pan_loc : []
    })
}, {
    serializers: _.extend({
        layers : { deserialize: widgets.unpack_models },
        controls : { deserialize: widgets.unpack_models }
    }, widgets.DOMWidgetModel.serializers)
});

module.exports = {
    // views
    LeafletLayerView : LeafletLayerView,
    LeafletUILayerView : LeafletUILayerView,
    LeafletMarkerView : LeafletMarkerView,
    LeafletPopupView : LeafletPopupView,
    LeafletRasterLayerView : LeafletRasterLayerView,
    LeafletGridLayerView : LeafletGridLayerView,
    LeafletTileLayerView : LeafletTileLayerView,
    LeafletImageOverlayView : LeafletImageOverlayView,
    LeafletVectorLayerView : LeafletVectorLayerView,
    LeafletPathView : LeafletPathView,
    LeafletPolylineView : LeafletPolylineView,
    LeafletPolygonView : LeafletPolygonView,
    LeafletRectangleView : LeafletRectangleView,
    LeafletCircleView : LeafletCircleView,
    LeafletCircleMarkerView : LeafletCircleMarkerView,
    LeafletLayerGroupView : LeafletLayerGroupView,
    LeafletFeatureGroupView : LeafletFeatureGroupView,
    LeafletMultiPolylineView : LeafletMultiPolylineView,
    LeafletGeoJSONView : LeafletGeoJSONView,
    LeafletMultiPolygonView : LeafletMultiPolygonView,
    LeafletControlView : LeafletControlView,
    LeafletDrawControlView : LeafletDrawControlView,
    LeafletMapView : LeafletMapView,
    NotebookUrlView:NotebookUrlView,
    PopupDisView : PopupDisView,
    HomeButtonView: HomeButtonView,
    // models
    LeafletLayerModel : LeafletLayerModel,
    LeafletUILayerModel : LeafletUILayerModel,
    LeafletGridLayerModel : LeafletGridLayerModel,
    LeafletMarkerModel : LeafletMarkerModel,
    LeafletPopupModel : LeafletPopupModel,
    LeafletRasterLayerModel : LeafletRasterLayerModel,
    LeafletTileLayerModel : LeafletTileLayerModel,
    LeafletImageOverlayModel : LeafletImageOverlayModel,
    LeafletVectorLayerModel : LeafletVectorLayerModel,
    LeafletPathModel : LeafletPathModel,
    LeafletPolylineModel : LeafletPolylineModel,
    LeafletPolygonModel : LeafletPolygonModel,
    LeafletRectangleModel : LeafletRectangleModel,
    LeafletCircleModel : LeafletCircleModel,
    LeafletCircleMarkerModel : LeafletCircleMarkerModel,
    LeafletLayerGroupModel : LeafletLayerGroupModel,
    LeafletFeatureGroupModel : LeafletFeatureGroupModel,
    LeafletGeoJSONModel : LeafletGeoJSONModel,
    LeafletMultiPolylineModel : LeafletMultiPolylineModel,
    LeafletMultiPolygonModel : LeafletMultiPolygonModel,
    LeafletControlModel : LeafletControlModel,
    LeafletDrawControlModel : LeafletDrawControlModel,
    LeafletMapModel : LeafletMapModel
};
