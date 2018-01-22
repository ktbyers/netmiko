"""
Google's clitable.py is inherently integrated to Linux:

This is a workaround for that (basically include modified clitable code without anything
that is Linux-specific).

_clitable.py is identical to Google's as of 2017-12-17
_texttable.py is identical to Google's as of 2017-12-17
_terminal.py is a highly stripped down version of Google's such that clitable.py works

https://github.com/google/textfsm/blob/master/clitable.py

A module to represent and manipulate tabular text data.

A table of rows, indexed on row number. Each row is a ordered dictionary of row
elements that maintains knowledge of the parent table and column headings.

Tables can be created from CSV input and in-turn supports a number of display
formats such as CSV and variable sized and justified rows.
"""

# Some of this code is from Google with the following license:
#
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import copy
from functools import cmp_to_key
import textwrap
# pylint: disable=redefined-builtin
from six.moves import range
from netmiko._textfsm import _terminal as terminal


class Error(Exception):
  """Base class for errors."""


class TableError(Error):
  """Error in TextTable."""


class Row(dict):
  """Represents a table row. We implement this as an ordered dictionary.

  The order is the chronological order of data insertion. Methods are supplied
  to make it behave like a regular dict() and list().

  Attributes:
    row: int, the row number in the container table. 0 is the header row.
    table: A TextTable(), the associated container table.
  """

  def __init__(self, *args, **kwargs):
    super(Row, self).__init__(*args, **kwargs)
    self._keys = list()
    self._values = list()
    self.row = None
    self.table = None
    self._color = None
    self._index = {}

  def _BuildIndex(self):
    """Recreate the key index."""
    self._index = {}
    for i, k in enumerate(self._keys):
      self._index[k] = i

  def __getitem__(self, column):
    """Support for [] notation.

    Args:
      column: Tuple of column names, or a (str) column name, or positional
        column number, 0-indexed.

    Returns:
      A list or string with column value(s).

    Raises:
      IndexError: The given column(s) were not found.
    """
    if isinstance(column, (list, tuple)):
      ret = []
      for col in column:
        ret.append(self[col])
      return ret

    try:
      return self._values[self._index[column]]
    except (KeyError, TypeError, ValueError):
      pass

    # Perhaps we have a range like '1', ':-1' or '1:'.
    try:
      return self._values[column]
    except (IndexError, TypeError):
      pass

    raise IndexError('No such column "%s" in row.' % column)

  def __contains__(self, value):
    return value in self._values

  def __setitem__(self, column, value):
    for i in range(len(self)):
      if self._keys[i] == column:
        self._values[i] = value
        return
    # No column found, add a new one.
    self._keys.append(column)
    self._values.append(value)
    self._BuildIndex()

  def __iter__(self):
    return iter(self._values)

  def __len__(self):
    return len(self._keys)

  def __str__(self):
    ret = ''
    for v in self._values:
      ret += '%12s  ' % v
    ret += '\n'
    return ret

  def __repr__(self):
    return '%s(%r)' % (self.__class__.__name__, str(self))

  def get(self, column, default_value=None):
    """Get an item from the Row by column name.

    Args:
      column: Tuple of column names, or a (str) column name, or positional
        column number, 0-indexed.
      default_value: The value to use if the key is not found.

    Returns:
      A list or string with column value(s) or default_value if not found.
    """
    if isinstance(column, (list, tuple)):
      ret = []
      for col in column:
        ret.append(self.get(col, default_value))
      return ret
    # Perhaps we have a range like '1', ':-1' or '1:'.
    try:
      return self._values[column]
    except (IndexError, TypeError):
      pass
    try:
      return self[column]
    except IndexError:
      return default_value

  def index(self, column):  # pylint: disable=C6409
    """Fetches the column number (0 indexed).

    Args:
      column: A string, column to fetch the index of.

    Returns:
      An int, the row index number.

    Raises:
      ValueError: The specified column was not found.
    """
    for i, key in enumerate(self._keys):
      if key == column:
        return i
    raise ValueError('Column "%s" not found.' % column)

  def iterkeys(self):
    return iter(self._keys)

  def items(self):
    # TODO(harro): self.get(k) should work here but didn't ?
    return [(k, self.__getitem__(k)) for k in self._keys]

  def _GetValues(self):
    """Return the row's values."""
    return self._values

  def _GetHeader(self):
    """Return the row's header."""
    return self._keys

  def _SetHeader(self, values):
    """Set the row's header from a list."""
    if self._values and len(values) != len(self._values):
      raise ValueError('Header values not equal to existing data width.')
    if not self._values:
      for _ in range(len(values)):
        self._values.append(None)
    self._keys = list(values)
    self._BuildIndex()

  def _SetColour(self, value_list):
    """Sets row's colour attributes to a list of values in terminal.SGR."""
    if value_list is None:
      self._color = None
      return
    colors = []
    for color in value_list:
      if color in terminal.SGR:
        colors.append(color)
      elif color in terminal.FG_COLOR_WORDS:
        colors += terminal.FG_COLOR_WORDS[color]
      elif color in terminal.BG_COLOR_WORDS:
        colors += terminal.BG_COLOR_WORDS[color]
      else:
        raise ValueError('Invalid colour specification.')
    self._color = list(set(colors))

  def _GetColour(self):
    if self._color is None:
      return None
    return list(self._color)

  def _SetValues(self, values):
    """Set values from supplied dictionary or list.

    Args:
      values: A Row, dict indexed by column name, or list.

    Raises:
      TypeError: Argument is not a list or dict, or list is not equal row
      length or dictionary keys don't match.
    """

    def _ToStr(value):
      """Convert individul list entries to string."""
      if isinstance(value, (list, tuple)):
        result = []
        for val in value:
          result.append(str(val))
        return result
      else:
        return str(value)

    # Row with identical header can be copied directly.
    if isinstance(values, Row):
      if self._keys != values.header:
        raise TypeError('Attempt to append row with mismatched header.')
      self._values = copy.deepcopy(values.values)

    elif isinstance(values, dict):
      for key in self._keys:
        if key not in values:
          raise TypeError('Dictionary key mismatch with row.')
      for key in self._keys:
        self[key] = _ToStr(values[key])

    elif isinstance(values, list) or isinstance(values, tuple):
      if len(values) != len(self._values):
        raise TypeError('Supplied list length != row length')
      for (index, value) in enumerate(values):
        self._values[index] = _ToStr(value)

    else:
      raise TypeError('Supplied argument must be Row, dict or list, not %s',
                      type(values))

  def Insert(self, key, value, row_index):
    """Inserts new values at a specified offset.

    Args:
      key: string for header value.
      value: string for a data value.
      row_index: Offset into row for data.

    Raises:
      IndexError: If the offset is out of bands.
    """
    if row_index < 0:
      row_index += len(self)

    if not 0 <= row_index < len(self):
      raise IndexError('Index "%s" is out of bounds.' % row_index)

    new_row = Row()
    for idx in self.header:
      if self.index(idx) == row_index:
        new_row[key] = value
      new_row[idx] = self[idx]
    self._keys = new_row.header
    self._values = new_row.values
    del new_row
    self._BuildIndex()

  color = property(_GetColour, _SetColour, doc='Colour spec of this row')
  header = property(_GetHeader, _SetHeader, doc="List of row's headers.")
  values = property(_GetValues, _SetValues, doc="List of row's values.")


class TextTable(object):
  """Class that provides data methods on a tabular format.

  Data is stored as a list of Row() objects. The first row is always present as
  the header row.

  Attributes:
    row_class: class, A class to use for the Row object.
    separator: str, field separator when printing table.
  """

  def __init__(self, row_class=Row):
    """Initialises a new table.

    Args:
      row_class: A class to use as the row object. This should be a
        subclass of this module's Row() class.
    """
    self.row_class = row_class
    self.separator = ', '
    self.Reset()

  def Reset(self):
    self._row_index = 1
    self._table = [[]]
    self._iterator = 0      # While loop row index

  def __repr__(self):
    return '%s(%r)' % (self.__class__.__name__, str(self))

  def __str__(self):
    """Displays table with pretty formatting."""
    return self.table

  def __incr__(self, incr=1):
    self._SetRowIndex(self._row_index + incr)

  def __contains__(self, name):
    """Whether the given column header name exists."""
    return name in self.header

  def __getitem__(self, row):
    """Fetches the given row number."""
    return self._table[row]

  def __iter__(self):
    """Iterator that excludes the header row."""
    return self.next()

  def next(self):
    # Maintain a counter so a row can know what index it is.
    # Save the old value to support nested interations.
    old_iter = self._iterator
    try:
      for r in self._table[1:]:
        self._iterator = r.row
        yield r
    finally:
      # Recover the original index after loop termination or exit with break.
      self._iterator = old_iter

  def __add__(self, other):
    """Merges two with identical columns."""

    new_table = copy.copy(self)
    for row in other:
      new_table.Append(row)

    return new_table

  def __copy__(self):
    """Copy table instance."""

    new_table = self.__class__()
    # pylint: disable=protected-access
    new_table._table = [self.header]
    for row in self[1:]:
      new_table.Append(row)
    return new_table

  def Filter(self, function=None):
    """Construct Textable from the rows of which the function returns true.


    Args:
      function: A function applied to each row which returns a bool. If
                function is None, all rows with empty column values are
                removed.
    Returns:
      A new TextTable()

    Raises:
      TableError: When an invalid row entry is Append()'d
    """
    flat = lambda x: x if isinstance(x, str) else ''.join([flat(y) for y in x])   # noqa
    if function is None:
      function = lambda row: bool(flat(row.values))     # noqa

    new_table = self.__class__()
    # pylint: disable=protected-access
    new_table._table = [self.header]
    for row in self:
      if function(row) is True:
        new_table.Append(row)
    return new_table

  def Map(self, function):
    """Applies the function to every row in the table.

    Args:
      function: A function applied to each row.

    Returns:
      A new TextTable()

    Raises:
      TableError: When transform is not invalid row entry. The transform
                  must be compatible with Append().
    """
    new_table = self.__class__()
    # pylint: disable=protected-access
    new_table._table = [self.header]
    for row in self:
      filtered_row = function(row)
      if filtered_row:
        new_table.Append(filtered_row)
    return new_table

  # pylint: disable=C6409
  # pylint: disable=W0622
  def sort(self, cmp=None, key=None, reverse=False):
    """Sorts rows in the texttable.

    Args:
      cmp: func, non default sort algorithm to use.
      key: func, applied to each element before sorting.
      reverse: bool, reverse order of sort.
    """

    def _DefaultKey(value):
      """Default key func is to create a list of all fields."""
      result = []
      for key in self.header:
        # Try sorting as numerical value if possible.
        try:
          result.append(float(value[key]))
        except ValueError:
          result.append(value[key])
      return result

    key = key or _DefaultKey
    # Exclude header by copying table.
    new_table = self._table[1:]

    if cmp is not None:
      key = cmp_to_key(cmp)

    new_table.sort(key=key, reverse=reverse)

    # Regenerate the table with original header
    self._table = [self.header]
    self._table.extend(new_table)
    # Re-write the 'row' attribute of each row
    for index, row in enumerate(self._table):
      row.row = index
  # pylint: enable=W0622

  def extend(self, table, keys=None):
    """Extends all rows in the texttable.

    The rows are extended with the new columns from the table.

    Args:
      table: A texttable, the table to extend this table by.
      keys: A set, the set of columns to use as the key. If None, the
        row index is used.

    Raises:
      IndexError: If key is not a valid column name.
    """
    if keys:
      for k in keys:
        if k not in self._Header():
          raise IndexError("Unknown key: '%s'", k)

    extend_with = []
    for column in table.header:
      if column not in self.header:
        extend_with.append(column)

    if not extend_with:
      return

    for column in extend_with:
      self.AddColumn(column)

    if not keys:
      for row1, row2 in zip(self, table):
        for column in extend_with:
          row1[column] = row2[column]
      return

    for row1 in self:
      for row2 in table:
        for k in keys:
          if row1[k] != row2[k]:
            break
        else:
          for column in extend_with:
            row1[column] = row2[column]
          break

  # pylint: enable=C6409
  def Remove(self, row):
    """Removes a row from the table.

    Args:
      row: int, the row number to delete. Must be >= 1, as the header
        cannot be removed.

    Raises:
      TableError: Attempt to remove nonexistent or header row.
    """
    if row == 0 or row > self.size:
      raise TableError('Attempt to remove header row')
    new_table = []
    # pylint: disable=E1103
    for t_row in self._table:
      if t_row.row != row:
        new_table.append(t_row)
        if t_row.row > row:
          t_row.row -= 1
    self._table = new_table

  def _Header(self):
    """Returns the header row."""
    return self._table[0]

  def _GetRow(self, columns=None):
    """Returns the current row as a tuple."""

    row = self._table[self._row_index]
    if columns:
      result = []
      for col in columns:
        if col not in self.header:
          raise TableError('Column header %s not known in table.' % col)
        result.append(row[self.header.index(col)])
      row = result
    return row

  def _SetRow(self, new_values, row=0):
    """Sets the current row to new list.

    Args:
      new_values: List|dict of new values to insert into row.
      row: int, Row to insert values into.

    Raises:
      TableError: If number of new values is not equal to row size.
    """

    if not row:
      row = self._row_index

    if row > self.size:
      raise TableError('Entry %s beyond table size %s.' % (row, self.size))

    self._table[row].values = new_values

  def _SetHeader(self, new_values):
    """Sets header of table to the given tuple.

    Args:
      new_values: Tuple of new header values.
    """
    row = self.row_class()
    row.row = 0
    for v in new_values:
      row[v] = v
    self._table[0] = row

  def _SetRowIndex(self, row):
    if not row or row > self.size:
      raise TableError('Entry %s beyond table size %s.' % (row, self.size))
    self._row_index = row

  def _GetRowIndex(self):
    return self._row_index

  def _GetSize(self):
    """Returns number of rows in table."""

    if not self._table:
      return 0
    return len(self._table) - 1

  def _GetTable(self):
    """Returns table, with column headers and separators.

    Returns:
      The whole table including headers as a string. Each row is
      joined by a newline and each entry by self.separator.
    """
    result = []
    # Avoid the global lookup cost on each iteration.
    lstr = str
    for row in self._table:
      result.append(
          '%s\n' %
          self.separator.join(lstr(v) for v in row))

    return ''.join(result)

  def _SetTable(self, table):
    """Sets table, with column headers and separators."""
    if not isinstance(table, TextTable):
      raise TypeError('Not an instance of TextTable.')
    self.Reset()
    self._table = copy.deepcopy(table._table)   # pylint: disable=W0212
    # Point parent table of each row back ourselves.
    for row in self:
      row.table = self

  def _SmallestColSize(self, text):
    """Finds the largest indivisible word of a string.

    ...and thus the smallest possible column width that can contain that
    word unsplit over rows.

    Args:
      text: A string of text potentially consisting of words.

    Returns:
      Integer size of the largest single word in the text.
    """
    if not text:
      return 0
    stripped = terminal.StripAnsiText(text)
    return max(len(word) for word in stripped.split())

  def _TextJustify(self, text, col_size):
    """Formats text within column with white space padding.

    A single space is prefixed, and a number of spaces are added as a
    suffix such that the length of the resultant string equals the col_size.

    If the length of the text exceeds the column width available then it
    is split into words and returned as a list of string, each string
    contains one or more words padded to the column size.

    Args:
      text: String of text to format.
      col_size: integer size of column to pad out the text to.

    Returns:
      List of strings col_size in length.

    Raises:
      TableError: If col_size is too small to fit the words in the text.
    """
    result = []
    if '\n' in text:
      for paragraph in text.split('\n'):
        result.extend(self._TextJustify(paragraph, col_size))
      return result

    wrapper = textwrap.TextWrapper(width=col_size-2, break_long_words=False,
                                   expand_tabs=False)
    try:
      text_list = wrapper.wrap(text)
    except ValueError:
      raise TableError('Field too small (minimum width: 3)')

    if not text_list:
      return [' '*col_size]

    for current_line in text_list:
      stripped_len = len(terminal.StripAnsiText(current_line))
      ansi_color_adds = len(current_line) - stripped_len
      # +2 for white space on either side.
      if stripped_len + 2 > col_size:
        raise TableError('String contains words that do not fit in column.')

      result.append(' %-*s' % (col_size - 1 + ansi_color_adds, current_line))

    return result

  def FormattedTable(self, width=80, force_display=False, ml_delimiter=True,
                     color=True, display_header=True, columns=None):
    """Returns whole table, with whitespace padding and row delimiters.

    Args:
      width: An int, the max width we want the table to fit in.
      force_display: A bool, if set to True will display table when the table
          can't be made to fit to the width.
      ml_delimiter: A bool, if set to False will not display the multi-line
          delimiter.
      color: A bool. If true, display any colours in row.colour.
      display_header: A bool. If true, display header.
      columns: A list of str, show only columns with these names.

    Returns:
      A string.  The tabled output.

    Raises:
      TableError: Width too narrow to display table.
    """

    def _FilteredCols():
      """Returns list of column names to display."""
      if not columns:
        return self._Header().values
      return [col for col in self._Header().values if col in columns]

    # Largest is the biggest data entry in a column.
    largest = {}
    # Smallest is the same as above but with linewrap i.e. largest unbroken
    # word in the data stream.
    smallest = {}
    # largest == smallest for a column with a single word of data.
    # Initialise largest and smallest for all columns.
    for key in _FilteredCols():
      largest[key] = 0
      smallest[key] = 0

    # Find the largest and smallest values.
    # Include Title line in equation.
    # pylint: disable=E1103
    for row in self._table:
      for key, value in row.items():
        if key not in _FilteredCols():
          continue
        # Convert lists into a string.
        if isinstance(value, list):
          value = ', '.join(value)
        value = terminal.StripAnsiText(value)
        largest[key] = max(len(value), largest[key])
        smallest[key] = max(self._SmallestColSize(value), smallest[key])
    # pylint: enable=E1103

    min_total_width = 0
    multi_word = []
    # Bump up the size of each column to include minimum pad.
    # Find all columns that can be wrapped (multi-line).
    # And the minimum width needed to display all columns (even if wrapped).
    for key in _FilteredCols():
      # Each column is bracketed by a space on both sides.
      # So increase size required accordingly.
      largest[key] += 2
      smallest[key] += 2
      min_total_width += smallest[key]
      # If column contains data that 'could' be split over multiple lines.
      if largest[key] != smallest[key]:
        multi_word.append(key)

    # Check if we have enough space to display the table.
    if min_total_width > width and not force_display:
      raise TableError('Width too narrow to display table.')

    # We have some columns that may need wrapping over several lines.
    if multi_word:
      # Find how much space is left over for the wrapped columns to use.
      # Also find how much space we would need if they were not wrapped.
      # These are 'spare_width' and 'desired_width' respectively.
      desired_width = 0
      spare_width = width - min_total_width
      for key in multi_word:
        spare_width += smallest[key]
        desired_width += largest[key]

      # Scale up the space we give each wrapped column.
      # Proportional to its size relative to 'desired_width' for all columns.
      # Rinse and repeat if we changed the wrap list in this iteration.
      # Once done we will have a list of columns that definitely need wrapping.
      done = False
      while not done:
        done = True
        for key in multi_word:
          # If we scale past the desired width for this particular column,
          # then give it its desired width and remove it from the wrapped list.
          if (largest[key] <= round((largest[key] / float(desired_width)) * spare_width)):
            smallest[key] = largest[key]
            multi_word.remove(key)
            spare_width -= smallest[key]
            desired_width -= largest[key]
            done = False
          # If we scale below the minimum width for this particular column,
          # then leave it at its minimum and remove it from the wrapped list.
          elif (smallest[key] >=
                round((largest[key] / float(desired_width)) * spare_width)):
            multi_word.remove(key)
            spare_width -= smallest[key]
            desired_width -= largest[key]
            done = False

      # Repeat the scaling algorithm with the final wrap list.
      # This time we assign the extra column space by increasing 'smallest'.
      for key in multi_word:
        smallest[key] = int(round((largest[key] / float(desired_width))
                                  * spare_width))

    total_width = 0
    row_count = 0
    result_dict = {}
    # Format the header lines and add to result_dict.
    # Find what the total width will be and use this for the ruled lines.
    # Find how many rows are needed for the most wrapped line (row_count).
    for key in _FilteredCols():
      result_dict[key] = self._TextJustify(key, smallest[key])
      if len(result_dict[key]) > row_count:
        row_count = len(result_dict[key])
      total_width += smallest[key]

    # Store header in header_list, working down the wrapped rows.
    header_list = []
    for row_idx in range(row_count):
      for key in _FilteredCols():
        try:
          header_list.append(result_dict[key][row_idx])
        except IndexError:
          # If no value than use whitespace of equal size.
          header_list.append(' '*smallest[key])
      header_list.append('\n')

    # Format and store the body lines
    result_dict = {}
    body_list = []
    # We separate multi line rows with a single line delimiter.
    prev_muli_line = False
    # Unless it is the first line in which there is already the header line.
    first_line = True
    for row in self:
      row_count = 0
      for key, value in row.items():
        if key not in _FilteredCols():
          continue
        # Convert field contents to a string.
        if isinstance(value, list):
          value = ', '.join(value)
        # Store results in result_dict and take note of wrapped line count.
        result_dict[key] = self._TextJustify(value, smallest[key])
        if len(result_dict[key]) > row_count:
          row_count = len(result_dict[key])

      if row_count > 1:
        prev_muli_line = True
      # If current or prior line was multi-line then include delimiter.
      if not first_line and prev_muli_line and ml_delimiter:
        body_list.append('-'*total_width + '\n')
        if row_count == 1:
          # Our current line was not wrapped, so clear flag.
          prev_muli_line = False

      row_list = []
      for row_idx in range(row_count):
        for key in _FilteredCols():
          try:
            row_list.append(result_dict[key][row_idx])
          except IndexError:
            # If no value than use whitespace of equal size.
            row_list.append(' '*smallest[key])
        row_list.append('\n')

      if color and row.color is not None:
        # Don't care about colors
        body_list.append(''.join(row_list))
        # body_list.append(
        #    terminal.AnsiText(''.join(row_list)[:-1],
        #                      command_list=row.color))
        # body_list.append('\n')
      else:
        body_list.append(''.join(row_list))

      first_line = False

    header = ''.join(header_list) + '='*total_width
    if color and self._Header().color is not None:
      pass
      # header = terminal.AnsiText(header, command_list=self._Header().color)
    # Add double line delimiter between header and main body.
    if display_header:
      return '%s\n%s' % (header, ''.join(body_list))
    return '%s' % ''.join(body_list)

  def LabelValueTable(self, label_list=None):
    """Returns whole table as rows of name/value pairs.

    One (or more) column entries are used for the row prefix label.
    The remaining columns are each displayed as a row entry with the
    prefix labels appended.

    Use the first column as the label if label_list is None.

    Args:
      label_list: A list of prefix labels to use.

    Returns:
      Label/Value formatted table.

    Raises:
      TableError: If specified label is not a column header of the table.
    """
    label_list = label_list or self._Header()[0]
    # Ensure all labels are valid.
    for label in label_list:
      if label not in self._Header():
        raise TableError('Invalid label prefix: %s.' % label)

    sorted_list = []
    for header in self._Header():
      if header in label_list:
        sorted_list.append(header)

    label_str = '# LABEL %s\n' % '.'.join(sorted_list)

    body = []
    for row in self:
      # Some of the row values are pulled into the label, stored in label_prefix.
      label_prefix = []
      value_list = []
      for key, value in row.items():
        if key in sorted_list:
          # Set prefix.
          label_prefix.append(value)
        else:
          value_list.append('%s %s' % (key, value))

      body.append(''.join(
          ['%s.%s\n' % ('.'.join(label_prefix), v) for v in value_list]))

    return '%s%s' % (label_str, ''.join(body))

  table = property(_GetTable, _SetTable, doc='Whole table')
  row = property(_GetRow, _SetRow, doc='Current row')
  header = property(_Header, _SetHeader, doc='List of header entries.')
  row_index = property(_GetRowIndex, _SetRowIndex, doc='Current row.')
  size = property(_GetSize, doc='Number of rows in table.')

  def RowWith(self, column, value):
    """Retrieves the first non header row with the column of the given value.

    Args:
      column: str, the name of the column to check.
      value: str, The value of the column to check.

    Returns:
      A Row() of the first row found, None otherwise.

    Raises:
      IndexError: The specified column does not exist.
    """
    for row in self._table[1:]:
      if row[column] == value:
        return row
    return None

  def AddColumn(self, column, default='', col_index=-1):
    """Appends a new column to the table.

    Args:
      column: A string, name of the column to add.
      default: Default value for entries. Defaults to ''.
      col_index: Integer index for where to insert new column.

    Raises:
      TableError: Column name already exists.

    """
    if column in self.table:
      raise TableError('Column %r already in table.' % column)
    if col_index == -1:
      self._table[0][column] = column
      for i in range(1, len(self._table)):
        self._table[i][column] = default
    else:
      self._table[0].Insert(column, column, col_index)
      for i in range(1, len(self._table)):
        self._table[i].Insert(column, default, col_index)

  def Append(self, new_values):
    """Adds a new row (list) to the table.

    Args:
      new_values: Tuple, dict, or Row() of new values to append as a row.

    Raises:
      TableError: Supplied tuple not equal to table width.
    """
    newrow = self.NewRow()
    newrow.values = new_values
    self._table.append(newrow)

  def NewRow(self, value=''):
    """Fetches a new, empty row, with headers populated.

    Args:
      value: Initial value to set each row entry to.

    Returns:
      A Row() object.
    """
    newrow = self.row_class()
    newrow.row = self.size + 1
    newrow.table = self
    headers = self._Header()
    for header in headers:
      newrow[header] = value
    return newrow

  def CsvToTable(self, buf, header=True, separator=','):
    """Parses buffer into tabular format.

    Strips off comments (preceded by '#').
    Optionally parses and indexes by first line (header).

    Args:
      buf: String file buffer containing CSV data.
      header: Is the first line of buffer a header.
      separator: String that CSV is separated by.

    Returns:
      int, the size of the table created.

    Raises:
      TableError: A parsing error occurred.
    """
    self.Reset()

    header_row = self.row_class()
    if header:
      line = buf.readline()
      header_str = ''
      while not header_str:
        # Remove comments.
        header_str = line.split('#')[0].strip()
        if not header_str:
          line = buf.readline()

      header_list = header_str.split(separator)
      header_length = len(header_list)

      for entry in header_list:
        entry = entry.strip()
        if entry in header_row:
          raise TableError('Duplicate header entry %r.' % entry)

        header_row[entry] = entry
      header_row.row = 0
      self._table[0] = header_row

    # xreadlines would be better but not supported by StringIO for testing.
    for line in buf:
      # Support commented lines, provide '#' is first character of line.
      if line.startswith('#'):
        continue

      lst = line.split(separator)
      lst = [l.strip() for l in lst]
      if header and len(lst) != header_length:
        # Silently drop illegal line entries
        continue
      if not header:
        header_row = self.row_class()
        header_length = len(lst)
        header_row.values = dict(zip(range(header_length),
                                     range(header_length)))
        self._table[0] = header_row
        header = True
        continue

      new_row = self.NewRow()
      new_row.values = lst
      header_row.row = self.size + 1
      self._table.append(new_row)

    return self.size

  def index(self, name=None):  # pylint: disable=C6409
    """Returns index number of supplied column name.

    Args:
      name: string of column name.

    Raises:
      TableError: If name not found.

    Returns:
      Index of the specified header entry.
    """
    try:
      return self.header.index(name)
    except ValueError:
      raise TableError('Unknown index name %s.' % name)
