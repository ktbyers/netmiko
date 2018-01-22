"""
Google's clitable.py is inherently integrated to Linux:

This is a workaround for that (basically include modified clitable code without anything
that is Linux-specific).

_clitable.py is identical to Google's as of 2017-12-17
_texttable.py is identical to Google's as of 2017-12-17
_terminal.py is a highly stripped down version of Google's such that clitable.py works

https://github.com/google/textfsm/blob/master/clitable.py
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

import copy
import os
import re
import threading
import copyable_regex_object
import textfsm
from netmiko._textfsm import _texttable as texttable


class Error(Exception):
  """Base class for errors."""


class IndexTableError(Error):
  """General INdexTable error."""


class CliTableError(Error):
  """General CliTable error."""


class IndexTable(object):
  """Class that reads and stores comma-separated values as a TextTable.
  Stores a compiled regexp of the value for efficient matching.
  Includes functions to preprocess Columns (both compiled and uncompiled).
  Attributes:
    index: TextTable, the index file parsed into a texttable.
    compiled: TextTable, the table but with compiled regexp for each field.
  """

  def __init__(self, preread=None, precompile=None, file_path=None):
    """Create new IndexTable object.
    Args:
      preread: func, Pre-processing, applied to each field as it is read.
      precompile: func, Pre-compilation, applied to each field before compiling.
      file_path: String, Location of file to use as input.
    """
    self.index = None
    self.compiled = None
    if file_path:
      self._index_file = file_path
      self._index_handle = open(self._index_file, 'r')
      self._ParseIndex(preread, precompile)

  def __del__(self):
    """Close index handle."""
    if hasattr(self, '_index_handle'):
      self._index_handle.close()

  def __len__(self):
    """Returns number of rows in table."""
    return self.index.size

  def __copy__(self):
    """Returns a copy of an IndexTable object."""
    clone = IndexTable()
    if hasattr(self, '_index_file'):
      # pylint: disable=protected-access
      clone._index_file = self._index_file
      clone._index_handle = self._index_handle

    clone.index = self.index
    clone.compiled = self.compiled
    return clone

  def __deepcopy__(self, memodict=None):
    """Returns a deepcopy of an IndexTable object."""
    clone = IndexTable()
    if hasattr(self, '_index_file'):
      # pylint: disable=protected-access
      clone._index_file = copy.deepcopy(self._index_file)
      clone._index_handle = open(clone._index_file, 'r')

    clone.index = copy.deepcopy(self.index)
    clone.compiled = copy.deepcopy(self.compiled)
    return clone

  def _ParseIndex(self, preread, precompile):
    """Reads index file and stores entries in TextTable.
    For optimisation reasons, a second table is created with compiled entries.
    Args:
      preread: func, Pre-processing, applied to each field as it is read.
      precompile: func, Pre-compilation, applied to each field before compiling.
    Raises:
      IndexTableError: If the column headers has illegal column labels.
    """
    self.index = texttable.TextTable()
    self.index.CsvToTable(self._index_handle)

    if preread:
      for row in self.index:
        for col in row.header:
          row[col] = preread(col, row[col])

    self.compiled = copy.deepcopy(self.index)

    for row in self.compiled:
      for col in row.header:
        if precompile:
          row[col] = precompile(col, row[col])
        if row[col]:
          row[col] = copyable_regex_object.CopyableRegexObject(row[col])

  def GetRowMatch(self, attributes):
    """Returns the row number that matches the supplied attributes."""
    for row in self.compiled:
      try:
        for key in attributes:
          # Silently skip attributes not present in the index file.
          # pylint: disable=E1103
          if key in row.header and row[key] and not row[key].match(attributes[key]):
            # This line does not match, so break and try next row.
            raise StopIteration()
        return row.row
      except StopIteration:
        pass
    return 0


class CliTable(texttable.TextTable):
  """Class that reads CLI output and parses into tabular format.
  Reads an index file and uses it to map command strings to templates. It then
  uses TextFSM to parse the command output (raw) into a tabular format.
  The superkey is the set of columns that contain data that uniquely defines the
  row, the key is the row number otherwise. This is typically gathered from the
  templates 'Key' value but is extensible.
  Attributes:
    raw: String, Unparsed command string from device/command.
    index_file: String, file where template/command mappings reside.
    template_dir: String, directory where index file and templates reside.
  """

  # Parse each template index only once across all instances.
  # Without this, the regexes are parsed at every call to CliTable().
  _lock = threading.Lock()
  INDEX = {}

  # pylint: disable=C6409
  def synchronised(func):
    """Synchronisation decorator."""

    # pylint: disable=E0213
    def Wrapper(main_obj, *args, **kwargs):
      main_obj._lock.acquire()                  # pylint: disable=W0212
      try:
        return func(main_obj, *args, **kwargs)  # pylint: disable=E1102
      finally:
        main_obj._lock.release()                # pylint: disable=W0212
    return Wrapper
    # pylint: enable=C6409

  @synchronised
  def __init__(self, index_file=None, template_dir=None):
    """Create new CLiTable object.
    Args:
      index_file: String, file where template/command mappings reside.
      template_dir: String, directory where index file and templates reside.
    """
    # pylint: disable=E1002
    super(CliTable, self).__init__()
    self._keys = set()
    self.raw = None
    self.index_file = index_file
    self.template_dir = template_dir
    if index_file:
      self.ReadIndex(index_file)

  def ReadIndex(self, index_file=None):
    """Reads the IndexTable index file of commands and templates.
    Args:
      index_file: String, file where template/command mappings reside.
    Raises:
      CliTableError: A template column was not found in the table.
    """

    self.index_file = index_file or self.index_file
    fullpath = os.path.join(self.template_dir, self.index_file)
    if self.index_file and fullpath not in self.INDEX:
      self.index = IndexTable(self._PreParse, self._PreCompile, fullpath)
      self.INDEX[fullpath] = self.index
    else:
      self.index = self.INDEX[fullpath]

    # Does the IndexTable have the right columns.
    if 'Template' not in self.index.index.header:    # pylint: disable=E1103
      raise CliTableError("Index file does not have 'Template' column.")

  def _TemplateNamesToFiles(self, template_str):
    """Parses a string of templates into a list of file handles."""
    template_list = template_str.split(':')
    template_files = []
    try:
      for tmplt in template_list:
        template_files.append(
            open(os.path.join(self.template_dir, tmplt), 'r'))
    except:         # noqa
      for tmplt in template_files:
        tmplt.close()
      raise

    return template_files

  def ParseCmd(self, cmd_input, attributes=None, templates=None):
    """Creates a TextTable table of values from cmd_input string.
    Parses command output with template/s. If more than one template is found
    subsequent tables are merged if keys match (dropped otherwise).
    Args:
      cmd_input: String, Device/command response.
      attributes: Dict, attribute that further refine matching template.
      templates: String list of templates to parse with. If None, uses index
    Raises:
      CliTableError: A template was not found for the given command.
    """
    # Store raw command data within the object.
    self.raw = cmd_input

    if not templates:
      # Find template in template index.
      row_idx = self.index.GetRowMatch(attributes)
      if row_idx:
        templates = self.index.index[row_idx]['Template']
      else:
        raise CliTableError('No template found for attributes: "%s"' %
                            attributes)

    template_files = self._TemplateNamesToFiles(templates)

    try:
      # Re-initialise the table.
      self.Reset()
      self._keys = set()
      self.table = self._ParseCmdItem(self.raw, template_file=template_files[0])

      # Add additional columns from any additional tables.
      for tmplt in template_files[1:]:
        self.extend(self._ParseCmdItem(self.raw, template_file=tmplt),
                    set(self._keys))
    finally:
      for f in template_files:
        f.close()

  def _ParseCmdItem(self, cmd_input, template_file=None):
    """Creates Texttable with output of command.
    Args:
      cmd_input: String, Device response.
      template_file: File object, template to parse with.
    Returns:
      TextTable containing command output.
    Raises:
      CliTableError: A template was not found for the given command.
    """
    # Build FSM machine from the template.
    fsm = textfsm.TextFSM(template_file)
    if not self._keys:
      self._keys = set(fsm.GetValuesByAttrib('Key'))

    # Pass raw data through FSM.
    table = texttable.TextTable()
    table.header = fsm.header

    # Fill TextTable from record entries.
    for record in fsm.ParseText(cmd_input):
      table.Append(record)
    return table

  def _PreParse(self, key, value):
    """Executed against each field of each row read from index table."""
    if key == 'Command':
      return re.sub(r'(\[\[.+?\]\])', self._Completion, value)
    else:
      return value

  def _PreCompile(self, key, value):
    """Executed against each field of each row before compiling as regexp."""
    if key == 'Template':
      return
    else:
      return value

  def _Completion(self, match):
    # pylint: disable=C6114
    r"""Replaces double square brackets with variable length completion.
    Completion cannot be mixed with regexp matching or '\' characters
    i.e. '[[(\n)]] would become (\(n)?)?.'
    Args:
      match: A regex Match() object.
    Returns:
      String of the format '(a(b(c(d)?)?)?)?'.
    """
    # Strip the outer '[[' & ']]' and replace with ()? regexp pattern.
    word = str(match.group())[2:-2]
    return '(' + ('(').join(word) + ')?' * len(word)

  def LabelValueTable(self, keys=None):
    """Return LabelValue with FSM derived keys."""
    keys = keys or self.superkey
    # pylint: disable=E1002
    return super(CliTable, self).LabelValueTable(keys)

  # pylint: disable=W0622,C6409
  def sort(self, cmp=None, key=None, reverse=False):
    """Overrides sort func to use the KeyValue for the key."""
    if not key and self._keys:
      key = self.KeyValue
    super(CliTable, self).sort(cmp=cmp, key=key, reverse=reverse)
  # pylint: enable=W0622

  def AddKeys(self, key_list):
    """Mark additional columns as being part of the superkey.
    Supplements the Keys already extracted from the FSM template.
    Useful when adding new columns to existing tables.
    Note: This will impact attempts to further 'extend' the table as the
    superkey must be common between tables for successful extension.
    Args:
      key_list: list of header entries to be included in the superkey.
    Raises:
      KeyError: If any entry in list is not a valid header entry.
    """

    for keyname in key_list:
      if keyname not in self.header:
        raise KeyError("'%s'" % keyname)

    self._keys = self._keys.union(set(key_list))

  @property
  def superkey(self):
    """Returns a set of column names that together constitute the superkey."""
    sorted_list = []
    for header in self.header:
      if header in self._keys:
        sorted_list.append(header)
    return sorted_list

  def KeyValue(self, row=None):
    """Returns the super key value for the row."""
    if not row:
      if self._iterator:
        # If we are inside an iterator use current row iteration.
        row = self[self._iterator]
      else:
        row = self.row
    # If no superkey then use row number.
    if not self.superkey:
      return ['%s' % row.row]

    sorted_list = []
    for header in self.header:
      if header in self.superkey:
        sorted_list.append(row[header])
    return sorted_list
