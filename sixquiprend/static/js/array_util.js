/**
 * Find first object in an array with a key matching value
 * @return item or null
 */
function find_by_key(array, key, value)
{
  if (array instanceof Array) {
    for (var i = 0; i < array.length; ++i) {
      if (array[i][key] == value) {
        return array[i];
      }
    }
  }
  return null;
}

/**
 * Filter elements with a key matching given values
 * @param key: key to look up
 * @param key_value: value or list of values
 * @return array
 */
function filter_by_key(items, key, key_value)
{
  if (!items)
    return [];

  return items.filter(function(item) {
    if (key_value instanceof Array) {
      for (var i = 0; i < key_value.length; ++i) {
        if (item[key] == key_value[i])
          return true;
      }
      return false;
    }
    return item[key] == key_value;
  });
}

/**
 * Get unique values
 * @return array
 */
function array_unique(array)
{
  return array.filter(function(value, index, self) {
    return self.indexOf(value) === index;
  });
}

/**
 * Regroup objects with a shared property in a dict
 * @param shared_property: the shared attribute name, or a function returning the shared property between items
 * @return dict
 */
function array_group_by(array, shared_property)
{
  var dict = {};
  if (!array)
    return dict;

  for (var i = 0; i < array.length; ++i) {
    var item = array[i];

    // Get the shared value for current item
    var value = typeof(shared_property) === "function" ?
      shared_property(item) :
      item[shared_property];

    // Insert item in dict
    if (value !== undefined) {
      if (dict.hasOwnProperty(value))
        dict[value].push(item);
      else
        dict[value] = [item];
    }
  }
  return dict;
}

/**
 * Remove objects with a key matching a given value
 * @param array: array to edit
 */
function remove_by_key(array, key, key_value)
{
  for (var i = 0; i < array.length; ++i) {
    if (array[i][key] == key_value) {
      array.splice(i--, 1);
      continue;
    }
  }
}

/**
 * Remove values from array
 * @return array
 */
function remove_value(array, value)
{
  return array.filter(function(item) {
    if (value == item)
      return false;
    return true;
  });
}

/**
 * Remove values from array
 * @return array
 */
function remove_values(array, values)
{
  return array.filter(function(item) {
    for (var i = 0; i < values.length; ++i) {
      if (values[i] == item)
        return false;
    }
    return true;
  });
}

/**
 * Sum values from array
 * @return integer
 */
function sum_values(array, value)
{
  return array.reduce(function(sum, value) {
    return sum + value;
  }, 0);
}

// The following methods extend the native array class - be warned!
//   - Array.pluck(attr) -> array
//   - Array.min -> value
//   - Array.max -> value

/**
 * Extract given attribute from objects
 * @return array
 */
Array.prototype.pluck = function(attribute)
{
  return this.map(function(item) {
    return item[attribute];
  });
}

/**
 * Get minimal value in array
 * @return value
 */
Array.prototype.min = function() {
  var len = this.length;
  var min;
  while (len--) {
    if (this[len] < min || min === undefined) {
      min = this[len];
    }
  }
  return min;
}

/**
 * Get maximal value in array
 * @return value
 */
Array.prototype.max = function() {
  var len = this.length;
  var max;
  while (len--) {
    if (this[len] > max || max === undefined) {
      max = this[len];
    }
  }
  return max;
}

/**
 * Filter out all occurrences of a given value in array
 * @return array
 */
Array.prototype.whithout_value = function(value) {
  return this.filter(function(item) {
    return value != item;
  });
};

/**
 * Remove null and undefined values from an array
 */
Array.prototype.compact = function() {
  return this.filter(function(x) {
    return x !== null && x !== undefined;
  });
};
