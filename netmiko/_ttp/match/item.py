def item(data, item_index):
    """Method to return item of iterable at given index"""
    item_index = int(item_index)
    # item_index not out of range
    if 0 <= item_index and item_index <= len(data) - 1:
        return data[item_index], None
    # item_index out of right range - return last item
    elif 0 <= item_index and item_index >= len(data) - 1:
        return data[-1], None
    # negative item_index not out of range
    elif 0 >= item_index and abs(item_index) <= len(data) - 1:
        return data[item_index], None
    # negative item_index out of range - return first item
    elif 0 >= item_index and abs(item_index) >= len(data):
        return data[0], None
