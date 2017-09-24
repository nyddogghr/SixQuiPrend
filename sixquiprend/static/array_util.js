Array.prototype.pluck = function(key) {
  return this.map(function(object) { return object[key]; });
};
