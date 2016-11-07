var d3 = require("d3");
L.MST = L.Layer.extend({
	options:{
		init_draw_z: 5,
	},
	initialize: function(url, options){
		L.setOptions(this, options);
		this._url = url;
		// this._map = map;
		this._json = [];
		this._mst = [];
		// this._lastZoom = this._map.getZoom();
		this._getData();
	},
	onAdd: function () {
		this._el = L.DomUtil.create('div', 'leaflet-zoom-hide');
		this.getPane().appendChild(this._el);
	},

	onRemove: function (){
		this.getPane().removeChild(this._el);
	},

	getEvents: function (){
		return {
			zoomend: this._resetView
		};
	},
	_getData: function(){
		var that = this;
		var init_z = this.options.init_draw_z;
		d3.json(this._url, function (error, json){
			if (error) {return console.log(error);}
			console.log(json.length);
			// that._json = json;
			json.forEach(function (d){
	          var latlng1 = new L.LatLng(d.DEC1, d.RA1);
	          var latlng2 = new L.LatLng(d.DEC2, d.RA2);

	          var point1 = that._map.project(latlng1,init_z);
	          var point2 = that._map.project(latlng2,init_z);

	          d.x1=point1.x;
	          d.y1=point1.y;
	          d.x2=point2.x;
	          d.y2=point2.y;

			});
			that._draw(json);
			that._mst = json;
		});

	},

	_draw: function(data){

		// if (!this._mst) {
		// 	console.log('mst');
		// 	return null;
		// }
		// var data = this._mst;
		var pixOrigin = this._map.getPixelOrigin(),
			offset = L.point(0,0).subtract(pixOrigin);

		svg_m = d3.select(this._el).append('svg')
									.style('width', '100000px')
									.style('height', '100000px')
									.attr('fill', 'none')
									.attr('overflow', 'visible')
									.attr('id', 'mst_svg');

		g_m = svg_m.append('g');
    	g_m.selectAll('path')
	    .data(data)
	    .enter()
	    .append('path').attr("d", this._buildPathFromPoint)
	    .attr('stroke','#00ff00')
	    .attr('stroke-width',1)
	    .attr('vector-effect','non-scaling-stroke');
	    this._resetView();
	},

	_buildPathFromPoint: function(d){
		try{
		    //console.log(d);
		    return "M" + d.x1+','+d.y1+'L'+d.x2+','+d.y2 ;
		  }catch(e){

		  }
	},

	_resetView: function(){
		var zoom = this._map.getZoom(),
		    pixOrigin = this._map.getPixelOrigin(),
			offset = L.point(0,0).subtract(pixOrigin),
			map = this._map;
		L.DomUtil.setPosition(this._el, offset);
		g_m.attr("transform", "scale("+Math.pow(2,(map.getZoom()-this.options.init_draw_z))+")");
		// if (d3.event){
		// 	g_m.attr('transform', d3.event.transform);
		//
		// }
	}

});

L.mst = function(url, options){
	return new  L.MST(url, options);
};
