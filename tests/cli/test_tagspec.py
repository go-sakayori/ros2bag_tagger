import pytest
from ros2bag_tagger.cli.tagspec import _validate_ego_vehicle_movement

# Test cases for _validate_ego_vehicle_movement

# Valid Cases
def test_valid_empty_ego_movement():
    data = {"ego_vehicle_movement": {}}
    errors = _validate_ego_vehicle_movement(data)
    assert not errors

def test_valid_missing_ego_movement_key():
    data = {} # ego_vehicle_movement key is missing
    errors = _validate_ego_vehicle_movement(data)
    assert not errors

def test_valid_simple_lane_keep_normal():
    data = {"ego_vehicle_movement": {"lane_keep": {"normal": [[[1, 2], [3, 4]]]}}}
    errors = _validate_ego_vehicle_movement(data)
    assert not errors

def test_valid_parked_and_pull_out():
    data = {
        "ego_vehicle_movement": {
            "parked": [[10, 20]],
            "pull_out": {"from_left_side": [[1, 2]]}
        }
    }
    errors = _validate_ego_vehicle_movement(data)
    assert not errors

def test_valid_floats_and_negative_numbers():
    data = {
        "ego_vehicle_movement": {
            "lane_change": {"left": [[-1.5, 0.5], [1.0, 2.5]]}
        }
    }
    errors = _validate_ego_vehicle_movement(data)
    assert not errors

def test_valid_various_movements():
    data = {
        "ego_vehicle_movement": {
            "lane_keep": {"normal": [[1,2]]},
            "turn": {"left_turn": [[10, 11], [12, 13]]},
            "lane_change": {"right": [[20, 20]]}, # items can be equal
            "obstacle_avoidance": {"steer_left": [[5,6]]},
            "stopped": {"at_traffic_light": [[100, 101]]},
            "parked": [[200, 201]],
            "pull_out": {"from_right_side": [[300,301]]},
            "pull_over": {"to_left_side": [[400,401]]}
        }
    }
    errors = _validate_ego_vehicle_movement(data)
    assert not errors

def test_valid_empty_sub_lists():
    data = {
        "ego_vehicle_movement": {
            "lane_keep": {"normal": []}, # Empty list of arrays
            "parked": [] # Empty list of arrays
        }
    }
    errors = _validate_ego_vehicle_movement(data)
    assert not errors

def test_valid_sub_keys_present_but_empty_objects():
    data = {
        "ego_vehicle_movement": {
            "lane_keep": {}, # Empty object for lane_keep
            "turn": {"left_turn": []} # Empty list of arrays
        }
    }
    errors = _validate_ego_vehicle_movement(data)
    assert not errors

# Invalid Cases
def test_invalid_array_too_short():
    data = {"ego_vehicle_movement": {"parked": [[[1]]]}}
    errors = _validate_ego_vehicle_movement(data)
    assert len(errors) == 1
    assert "must have exactly two items" in errors[0]
    assert "ego_vehicle_movement.parked[0]" in errors[0]

def test_invalid_array_too_long():
    data = {"ego_vehicle_movement": {"lane_keep": {"normal": [[[1, 2, 3]]]}}}
    errors = _validate_ego_vehicle_movement(data)
    assert len(errors) == 1
    assert "must have exactly two items" in errors[0]
    assert "ego_vehicle_movement.lane_keep.normal[0]" in errors[0]

def test_invalid_array_not_ascending():
    data = {"ego_vehicle_movement": {"turn": {"right_turn": [[[2, 1]]]}}}
    errors = _validate_ego_vehicle_movement(data)
    assert len(errors) == 1
    assert "must be in ascending order" in errors[0]
    assert "ego_vehicle_movement.turn.right_turn[0]" in errors[0]

def test_invalid_array_non_numeric_item1():
    data = {"ego_vehicle_movement": {"stopped": {"at_crosswalk": [[["a", 2]]]}}}
    errors = _validate_ego_vehicle_movement(data)
    assert len(errors) == 1
    assert "must be numbers" in errors[0]
    assert "ego_vehicle_movement.stopped.at_crosswalk[0]" in errors[0]

def test_invalid_array_non_numeric_item2():
    data = {"ego_vehicle_movement": {"pull_over": {"to_right_side": [[[1, "b"]]]}}}
    errors = _validate_ego_vehicle_movement(data)
    assert len(errors) == 1
    assert "must be numbers" in errors[0]
    assert "ego_vehicle_movement.pull_over.to_right_side[0]" in errors[0]

def test_mixed_valid_and_invalid_arrays():
    data = {
        "ego_vehicle_movement": {
            "lane_keep": {"normal": [[[1, 2], [5, 4]]]}, # second is invalid
            "parked": [[10, 11], [120, 100], [1,2,3]] # second and third are invalid
        }
    }
    errors = _validate_ego_vehicle_movement(data)
    assert len(errors) == 3
    paths = sorted([err.split("'")[1] for err in errors]) # Extract paths and sort for consistent order

    # Expected paths based on new logic
    # ego_vehicle_movement.lane_keep.normal[0][1] (for [5,4]) - error: ascending order
    # ego_vehicle_movement.parked[1] (for [120,100]) - error: ascending order
    # ego_vehicle_movement.parked[2] (for [1,2,3]) - error: length
    expected_paths = sorted([
        "ego_vehicle_movement.lane_keep.normal[0][1]",
        "ego_vehicle_movement.parked[1]",
        "ego_vehicle_movement.parked[2]"
    ])
    assert paths == expected_paths

    # Check error messages based on their paths
    error_map = {err.split("'")[1]: err for err in errors}
    assert "must be in ascending order" in error_map["ego_vehicle_movement.lane_keep.normal[0][1]"]
    assert "must be in ascending order" in error_map["ego_vehicle_movement.parked[1]"]
    assert "must have exactly two items" in error_map["ego_vehicle_movement.parked[2]"]


def test_invalid_array_direct_under_movement_not_list_of_list():
    # This structure isn't quite what the schema expects for 'parked' (expects list of lists)
    # but testing how robust the traversal is. The current _traverse_and_validate
    # only calls _check_array_properties if all(isinstance(inner_list, list) for inner_list in current_item)
    # This means [1,2] won't be validated by _check_array_properties, which is correct.
    # If schema demands 'parked' must be List[List[number]], schema validation should catch this.
    # Our function is checking the *contents* of the inner lists.
    data = {"ego_vehicle_movement": {"parked": [1, 2]}}
    errors = _validate_ego_vehicle_movement(data)
    assert not errors # No errors from _check_array_properties as it won't be called on [1,2]

def test_invalid_array_nested_under_category_not_list_of_list():
    data = {"ego_vehicle_movement": {"lane_keep": {"normal": [1, 2]}}}
    errors = _validate_ego_vehicle_movement(data)
    assert not errors # Similar to above, no errors from our specific validation.

def test_invalid_deeply_nested_error():
    data = {
        "ego_vehicle_movement": {
            "level1": {
                "level2": {
                    "level3_list": [
                        [1, 2],
                        [3, 4, 5], # Invalid length
                        [6, 7],
                        [9, 8]  # Invalid order
                    ]
                }
            }
        }
    }
    errors = _validate_ego_vehicle_movement(data)
    assert len(errors) == 2
    assert "ego_vehicle_movement.level1.level2.level3_list[1]" in errors[0]
    assert "must have exactly two items" in errors[0]
    assert "ego_vehicle_movement.level1.level2.level3_list[3]" in errors[1]
    assert "must be in ascending order" in errors[1]

def test_array_with_non_list_item_mixed_in_list_of_lists():
    # The current _traverse_and_validate has a condition:
    # if all(isinstance(inner_list, list) for inner_list in current_item):
    # This means if a list is like [[1,2], "not_a_list", [3,4]], it won't attempt to validate.
    # This seems like a reasonable approach as schema validation should catch type mismatches.
    # Our function's job is to validate the *contents* of what are supposed to be the time-range arrays.
    data = {
        "ego_vehicle_movement": {
            "lane_keep": {"normal": [[[1,2], "not_a_list_item", [3,4]]]}
        }
    }
    errors = _validate_ego_vehicle_movement(data)
    # It will try to validate the outer list: "lane_keep.normal[0]" which is [[1,2], "not_a_list_item", [3,4]]
    # The `all(isinstance(el, list) for el in current_item)` check in `_traverse_and_validate`
    # will cause the 'else' branch of that if to be taken, meaning this list is not processed for these specific validations.
        # assert not errors # This assertion is now incorrect due to improved logic handling this case.

    # Test case: ego_vehicle_movement.lane_keep.normal = [ TRA_1 ]
    # TRA_1 = [[1,2], "not_a_list_item", [3,4]]
    # Expected: error for "not_a_list_item" at path normal[0][1]
    current_data = {
        "ego_vehicle_movement": {
            "lane_keep": {"normal": [[[1,2], "not_a_list_item", [3,4]]]}
    }
    }
    current_errors = _validate_ego_vehicle_movement(current_data)
    assert len(current_errors) == 1
    assert "Item at path 'ego_vehicle_movement.lane_keep.normal[0][1]' was expected to be a TimeRange (a list) but found type str." in current_errors[0]


    # Test for a TimeRangeArray that contains a mix of valid TimeRanges and items that are not lists.
    data_mixed_inner = {
         "ego_vehicle_movement": {
            "lane_keep": {"normal": [[1,2], "this_is_not_a_list_but_an_element_of_the_outer_list"]}
        }
    }
    # Here, "lane_keep.normal" is a TimeRangeArray: [[1,2], "string"]
    # - [1,2] is a valid TimeRange.
    # - "string" is not a list, so it's not a valid TimeRange.
    errors_mixed_inner = _validate_ego_vehicle_movement(data_mixed_inner)
    assert len(errors_mixed_inner) == 1
    assert "Item at path 'ego_vehicle_movement.lane_keep.normal[1]' was expected to be a TimeRange (a list) but found type str." in errors_mixed_inner[0]


    data_mixed_inner_invalid = {
         "ego_vehicle_movement": {
            "lane_keep": {"normal": [[1,2,3], ["this_is_not_a_list_but_an_element_of_the_outer_list"]]}
        }
    }
    errors_mixed_inner_invalid = _validate_ego_vehicle_movement(data_mixed_inner_invalid)
    # Error 1: for [1,2,3] -> length error at normal[0]
    # Error 2: for "this_is_not_a_list..." -> not a list error at normal[1]
    assert len(errors_mixed_inner_invalid) == 2

    error_map_invalid = {err.split("'")[1]: err for err in errors_mixed_inner_invalid}
    assert "ego_vehicle_movement.lane_keep.normal[0]" in error_map_invalid
    assert "must have exactly two items" in error_map_invalid["ego_vehicle_movement.lane_keep.normal[0]"]

    assert "ego_vehicle_movement.lane_keep.normal[1]" in error_map_invalid
    # This item is ["this_is_not_a_list_but_an_element_of_the_outer_list"]
    # _check_array_properties will be called on it.
    # It will fail the "must be numbers" check because the item is a string.
    # It will also fail the "length must be 2" check as its length is 1.
    # Depending on the order of checks in _check_array_properties, one of these will be reported.
    # _check_array_properties: 1. length, 2. type, 3. order
    # So, it should be a length error.
    assert "must have exactly two items" in error_map_invalid["ego_vehicle_movement.lane_keep.normal[1]"]
