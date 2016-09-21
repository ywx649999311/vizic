L.CanvasLayer = L.GridLayer.extend({
    createTile: function(coords){
        // create a <canvas> element for drawing
        var tile = L.DomUtil.create('canvas', 'leaflet-tile');
        // setup tile width and height according to the options
        // var size = this.getTileSize();
        tile.width = 256;
        tile.height = 256;
        // get a canvas context and draw something on it using coords.x, coords.y and coords.z
        var ctx = tile.getContext('2d');
        ctx.fillStyle = "blue";
        ctx.fillRect(10, 10, 100, 100);
        // return the tile so it can be rendered on screen
        return tile;
    }
});

L.canvasLayer = function(options){
    return new L.CanvasLayer(options);
};