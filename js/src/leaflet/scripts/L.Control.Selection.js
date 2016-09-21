L.Control.Selection = L.Control.extend({
	options: {
		position: 'topleft',
		rectText: '<i class="material-icons">stop</i>',
		rectTitle: 'Make Retangualr Selection',
		// circleText: '<i class="material-icons" style="display:block; font-size:18px" >brightness_1</i>',
		// circleTitle: 'Make Circular Selection',

		rectOptions: {
			stroke: true,
			color: '#f06eaa',
			weight: 2,
			opacity: 0.5,
			fill: true,
			fillColor: null, //same as color by default
			fillOpacity: 0.2,
			clickable: false
		}

		// circleOptions: {
		// 	stroke: true,
		// 	color: '#f06eaa',
		// 	weight: 2,
		// 	opacity: 0.5,
		// 	fill: true,
		// 	fillColor: null, //same as color by default
		// 	fillOpacity: 0.2,
		// 	clickable: false
		// }
	},

	onAdd: function (map) {
		this._map = map;
		var selectionName = 'leaflet-control-select',
		    container = L.DomUtil.create('div', selectionName + ' leaflet-bar'),
		    options = this.options;

		this._rectButton  = this._createButton(options.rectText, options.rectTitle,
		        selectionName + '-rect',  container, this._rect);
		// this._circleButton = this._createButton(options.circleText, options.circleTitle,
		//         selectionName + '-circle', container, this._circle);

		// this._updateDisabled();
		// map.on('zoomend zoomlevelschange', this._updateDisabled, this);

		return container;
	},

	// onRemove: function (map) {
	// 	map.off('zoomend zoomlevelschange', this._updateDisabled, this);
	// },

	disable: function () {
		this._disabled = true;
		//this._updateDisabled();
		return this;
	},

	enable: function () {
		this._disabled = false;
		//this._updateDisabled();
		return this;
	},

	_rect: function(){
		if (!this._disabled && !this._rectClicked) {

			this._rectClicked = true;

			this._map.dragging.disable();

			this._map.on('mousedown', L.DomEvent.stop)
					.on('click', L.DomEvent.stopPropagation)
					.on('mousedown', this._onMousedown, this);
							
		}
		else{

			this._rectClicked = false;
			this._map.dragging.enable();

			this._shape.remove();
			delete this._shape;

			this._map.off('mousedown', L.DomEvent.stop)
					.off('click')
					.off('mousedown', this._onMousedown, this)
					.off('mousemove', this._onMousemove, this)
					.off('mouseup', this._onMouseUp, this);
						
		}
	},

	// _circle: function(){
	// 	if (!this._disabled && !this._circleClicked) {

	// 		this._circleClicked = true;

	// 		this._map.dragging.disable();

	// 		this._map.on('mousedown', L.DomEvent.stop)
	// 				.on('click', L.DomEvent.stopPropagation)
	// 				.on('mousedown', this._onMousedown, this);
							
	// 	}
	// 	else{

	// 		this._circleClicked = false;
	// 		this._map.dragging.enable();

	// 		if (this._shape){
				
	// 			this._shape.remove();
	// 			delete this._shape;

	// 		}
			

	// 		this._map.off('mousedown', L.DomEvent.stop)
	// 				.off('click')
	// 				.off('mousedown', this._onMousedown, this)
	// 				.off('mousemove', this._onMousemove, this)
	// 				.off('mouseup', this._onMouseUp, this);
						
	// 	}
	// },

	_onMousedown: function(e){

		this._isDown = true;
		this._startLatlng = e.latlng;


		this._map.on('mousemove', this._onMousemove, this);	

		L.DomEvent
			.on(document, 'mouseup', this._onMouseUp, this)
			.preventDefault(e.originalEvent);


	},

	_onMousemove: function(e){

		var new_latlng = e.latlng;
		this._lastLatlng = new_latlng;

		if (this._isDown){

			if (this._rectClicked){

				this._drawRect(new_latlng);
			}
			// else if (this._circleClicked){
				
			// 	this._drawCircle(new_latlng);
			// }
		}

		this._isDrawing = true;

	},

	_onMouseUp: function(e){
		
		this._map.off('mousemove', this._onMousemove, this);
		this._drawing = false;

		var rectSelection=this;
		var bounds = new L.LatLngBounds(rectSelection._startLatlng,rectSelection._lastLatlng);

		this._url = this._boundsToUrl(bounds);

		if (this._isDrawing){
			d3.json(this._url, function(error, json){
				if (error) {return console.log(error);}
				//console.log(json);
				var output="RA, DEC<br>";
				for (var i in json){
					output+=json[i].RA+','+json[i].DEC+'<br>';
				}
				document.getElementById("catalog").innerHTML=output;
			});
			this._isDrawing = false;
		}
		

	},
	
	_boundsToUrl: function(latlngBounds){
		var b_swLat = latlngBounds.getSouthWest().lat,
			b_swLng = latlngBounds.getSouthWest().lng,
			b_neLat = latlngBounds.getNorthEast().lat,
			b_neLng = latlngBounds.getNorthEast().lng;

		return L.Util.template('rectSelection/{swLng}/{swLat}/{neLng}/{neLat}.json',
								{
									swLng:b_swLng,
									swLat:b_swLat,
									neLng:b_neLng,
									neLat:b_neLat
								});

	},


	_drawRect: function (latlng) {
		var startPoint = this._startLatlng;
		if (!this._shape) {
			
			this._shape = new L.Rectangle(new L.LatLngBounds(startPoint, latlng), this.options.rectOptions);
			this._map.addLayer(this._shape);
		} else {
			this._shape.setBounds(new L.LatLngBounds(startPoint, latlng));
		}

	},

	// _drawCircle: function (latlng) {
	// 	var center = this._startLatlng;

	// 	if (!this._shape) {			
	// 		this._shape = new L.Circle(center, center.distanceTo(latlng), this.options.circleOptions);
	// 		this._map.addLayer(this._shape);
	// 	} else {
	// 		this._shape.setRadius(center.distanceTo(latlng));
	// 	}
	// },

	_createButton: function (html, title, className, container, fn) {
		var link = L.DomUtil.create('a', className, container);
		link.innerHTML = html;
		link.href = '#';
		link.title = title;

		L.DomEvent
		    .on(link, 'mousedown dblclick', L.DomEvent.stopPropagation)
		    .on(link, 'click', L.DomEvent.stop)
		    .on(link, 'click', fn, this)
		    .on(link, 'click', this._refocusOnMap, this);

		return link;
	}

	// _updateDisabled: function () {
	// 	var map = this._map,
	// 	    className = 'leaflet-disabled';

	// 	L.DomUtil.removeClass(this._zoomInButton, className);
	// 	L.DomUtil.removeClass(this._zoomOutButton, className);

	// 	if (this._disabled || map._zoom === map.getMinZoom()) {
	// 		L.DomUtil.addClass(this._zoomOutButton, className);
	// 	}
	// 	if (this._disabled || map._zoom === map.getMaxZoom()) {
	// 		L.DomUtil.addClass(this._zoomInButton, className);
	// 	}
	// }


});


L.Map.mergeOptions({
	selectControl: true
});

L.Map.addInitHook(function () {
	if (this.options.selectControl) {
		this.selectControl = new L.Control.Selection();
		this.addControl(this.selectControl);
	}
});

L.control.selection = function (options) {
	return new L.Control.Selection(options);
};



















