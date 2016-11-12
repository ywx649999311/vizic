var d3 = require("d3");
L.MST = L.Layer.extend({
	options:{
		color: 'blue',
		lineWidth: 1,
	},

	initialize: function(url, options){
		L.setOptions(this, options);
		this._url = url;
		this._json = [];
		this._msts = {};
		this._els = {};
		this._getData();
		this._el = {};
	},

	onAdd: function () {
		console.log('over');
	},

	_onAdd: function(){
		// var that = this,
		var	key,
		    zoom = this._map.getZoom(),
		    pixOrigin = this._map.getPixelOrigin(),
		    offset = L.point(0,0).subtract(pixOrigin);
		this._json = this._projectData(this._json, 1, this._map);
		this.sortJson(this._json);
		this._els[zoom] = {};
		for (key in this._msts){
			this._createlayers(zoom, key);
			L.DomUtil.setPosition(this._el[key], offset);
			this.getPane().appendChild(this._el[key]);
		}
	},
	// _creatCurrent: function(zoom, that){

	// 	var el = L.DomUtil.create('div', 'leaflet-zoom-hide mst-el'),
	// 		pixOrigin = that._map.getPixelOrigin(),
	// 	   	offset = L.point(0,0).subtract(pixOrigin);
	// 	el._zoom = zoom;
	// 	var base = d3.select(el);
	// 	el.chart = base.append("canvas")
	// 		.attr('width', Math.pow(2, zoom)*256)
	// 		.attr('height', Math.pow(2, zoom)*256);
	// 	el.context = el.chart.node().getContext('2d');
	// 	el.detachedContainer = document.createElement('custom');
	// 	el.dataContainer = d3.select(el.detachedContainer);
	// 	that.drawCustom(that._json, el);
	// 	that._el = el;
	// 	that._els[zoom] = el;
	// 	L.DomUtil.setPosition(that._el, offset);
	// 	that.getPane().appendChild(that._el);
	// 	// callback(null);
	// },

	onRemove: function (){
		var key;
		for (key in this._msts){
			this.getPane().removeChild(this._el[key]);
		}
		this._el = [];
	},

	getEvents: function (){
		return {
			zoomend: this._resetView,
			dragstart: this._onDrag,
			moveend: this._onMoveEnd,
		};
	},

	_onDrag: function(e){
		this._map.scrollWheelZoom.disable();
	},

	_onMoveEnd: function(e){
		// has to be moveend, or scroll zoom event will fire
		this._map.scrollWheelZoom.enable();

	},
	sortJson: function(json){
		var canvasData = json;
		var frameCount = 16,
			oneDimCount = Math.sqrt(frameCount);
		var sortDataRA = canvasData.sort(this.comp_func_ra),
			chunk = Math.floor(canvasData.length/frameCount),
			// frameData = {},
			sortDataDec;
		for (var i =0, l = 0; i<oneDimCount;l+=chunk*oneDimCount, i++){
			var ra_cut = sortDataRA.slice(l, l+chunk*oneDimCount).sort(this.comp_func_dec);
			for (var j=0, z=0; j<oneDimCount;z+=chunk, j++){
				this._msts[this.getFrameKey(i, j)] = ra_cut.slice(z, z+chunk);
			}
		}
	},

	comp_func_dec: function(a, b){
		return Math.abs(a.DEC1) - Math.abs(b.DEC1);
	},

	comp_func_ra: function(a, b){
		return a.RA1 - b.RA1;
	},
	_createlayers: function(zoom, key){
			var el = L.DomUtil.create('div', 'leaflet-zoom-hide mst-el');
			el._zoom = zoom;
			var base = d3.select(el);
			el.chart = base.append("canvas")
				.attr('width', Math.pow(2, zoom)*256)
				.attr('height', Math.pow(2, zoom)*256);
			el.context = el.chart.node().getContext('2d');
			el.context.clearRect(0,0,el.chart.attr('width'), el.chart.attr('height'));
			el.detachedContainer = document.createElement('custom');
			el.dataContainer = d3.select(el.detachedContainer);
			this._els[zoom][key] = el;
			this._el[key]=el;
			var that = this;
			setTimeout(function(){
				that.drawCustom(zoom, el, key);
			},0);
	},

	drawCustom: function(zoom, el, k){

		var scale = Math.pow(2,zoom-1);
		var canvasKey = this.getCanvasKey(k, zoom);
		el._key = canvasKey;

		var data = this._msts[k];
		var dataBinding = el.dataContainer.selectAll('custom.path')
			.data(data);

		dataBinding
			.attr('x1', function(d){return d.x1*scale;})
			.attr('y1', function(d){return d.y1*scale;})
			.attr('x2', function(d){return d.x2*scale;})
			.attr('y2', function(d){return d.y2*scale;});
		dataBinding.enter()
			.append('custom')
			.classed('path', true)
			.attr('x1', function(d){return d.x1*scale;})
			.attr('y1', function(d){return d.y1*scale;})
			.attr('x2', function(d){return d.x2*scale;})
			.attr('y2', function(d){return d.y2*scale;})
			.attr('remove', false);

		dataBinding.exit()
			.attr('remove', true);

		L.Util.requestAnimFrame(L.bind(this.drawCanvas, this, zoom, el));
	},

	getFrameKey: function(i, j){
		return i+':'+j;
	},

	getCanvasKey: function(k, zoom){
		return zoom+':'+k;
	},

	drawCanvas: function(zoom, el){
		var context = el.context;
		var elements = el.dataContainer.selectAll('custom.path')._groups[0];
		var that = this;
		elements.forEach(function(d){
			var node = d3.select(d);
			context.beginPath();
			context.moveTo(node.attr('x1'), node.attr('y1'));
			context.lineTo(node.attr('x2'), node.attr('y2'));
			context.lineWidth = that.options.lineWidth;
			// context.strokeStyle = that.options.color;
			// context.stroke();

			if (node.attr('remove') === 'false'){
				context.strokeStyle = that.options.color;
				context.stroke();
			}
		});
	},

	_getData: function(){
		var that = this;
		// var init_z = this.options.init_draw_z;
		d3.json(this._url, function (error, json){
			if (error) {return console.log(error);}
			// console.log(json.length);
			that._json = json;
			var add = L.bind(that._onAdd, that);
			add();
		});

	},

	_projectData: function(json, zoom, map){

		json.forEach(function (d){
		  var latlng1 = new L.LatLng(d.DEC1, d.RA1);
		  var latlng2 = new L.LatLng(d.DEC2, d.RA2);

		  var point1 = map.project(latlng1,1);
		  var point2 = map.project(latlng2,1);

		  d.x1=point1.x;
		  d.y1=point1.y;
		  d.x2=point2.x;
		  d.y2=point2.y;

		});
		return json;
	},

	_resetView: function(){
		var zoom = this._map.getZoom(),
		    pixOrigin = this._map.getPixelOrigin(),
			offset = L.point(0,0).subtract(pixOrigin),
			key;
		if (!this._els[zoom]){
			this.onRemove();
			this._els[zoom] = {};
			for (key in this._msts){
				this._createlayers(zoom, key);
				L.DomUtil.setPosition(this._el[key], offset);
				this.getPane().appendChild(this._el[key]);
			}
		}else{
			this.onRemove();
			this._el = this._els[zoom];
			for (key in this._msts){
				L.DomUtil.setPosition(this._el[key], offset);
				this.getPane().appendChild(this._el[key]);
			}

		}

	}

});

L.mst = function(url, options){
	return new  L.MST(url, options);
};
