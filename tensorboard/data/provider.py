# Copyright 2019 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Experimental framework for generic TensorBoard data providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc
import collections

import six


@six.add_metaclass(abc.ABCMeta)
class DataProvider(object):
  """Interface for reading TensorBoard scalar, tensor, and blob data.

  These APIs are under development and subject to change. For instance,
  providers may be asked to implement more filtering mechanisms, such as
  downsampling strategies or domain restriction by step or wall time.

  Unless otherwise noted, any methods on this class may raise errors
  defined in `tensorboard.errors`, like `tensorboard.errors.NotFound`.
  """

  def data_location(self, experiment_id):
    """Render a human-readable description of the data source.

    For instance, this might return a path to a directory on disk.

    The default implementation always returns the empty string.

    Args:
      experiment_id: ID of enclosing experiment.

    Returns:
      A string, which may be empty.
    """
    return ""

  @abc.abstractmethod
  def list_runs(self, experiment_id):
    """List all runs within an experiment.

    Args:
      experiment_id: ID of enclosing experiment.

    Returns:
      A collection of `Run` values.

    Raises:
      tensorboard.errors.PublicError: See `DataProvider` class docstring.
    """
    pass

  @abc.abstractmethod
  def list_scalars(self, experiment_id, plugin_name, run_tag_filter=None):
    """List metadata about scalar time series.

    Args:
      experiment_id: ID of enclosing experiment.
      plugin_name: String name of the TensorBoard plugin that created
        the data to be queried. Required.
      run_tag_filter: Optional `RunTagFilter` value. If omitted, all
        runs and tags will be included.

    The result will only contain keys for run-tag combinations that
    actually exist, which may not include all entries in the
    `run_tag_filter`.

    Returns:
      A nested map `d` such that `d[run][tag]` is a `ScalarTimeSeries`
      value.

    Raises:
      tensorboard.errors.PublicError: See `DataProvider` class docstring.
    """
    pass

  @abc.abstractmethod
  def read_scalars(
      self, experiment_id, plugin_name, downsample=None, run_tag_filter=None
  ):
    """Read values from scalar time series.

    Args:
      experiment_id: ID of enclosing experiment.
      plugin_name: String name of the TensorBoard plugin that created
        the data to be queried. Required.
      downsample: Integer number of steps to which to downsample the
        results (e.g., `1000`). Required.
      run_tag_filter: Optional `RunTagFilter` value. If provided, a time
        series will only be included in the result if its run and tag
        both pass this filter. If `None`, all time series will be
        included.

    The result will only contain keys for run-tag combinations that
    actually exist, which may not include all entries in the
    `run_tag_filter`.

    Returns:
      A nested map `d` such that `d[run][tag]` is a list of
      `ScalarDatum` values sorted by step.

    Raises:
      tensorboard.errors.PublicError: See `DataProvider` class docstring.
    """
    pass

  def list_tensors(self):
    """Not yet specified."""
    pass

  def read_tensors(self):
    """Not yet specified."""
    pass

  def list_blob_sequences(
      self, experiment_id, plugin_name, run_tag_filter=None
  ):
    """List metadata about blob sequence time series.

    Args:
      experiment_id: ID of enclosing experiment.
      plugin_name: String name of the TensorBoard plugin that created the data
        to be queried. Required.
      run_tag_filter: Optional `RunTagFilter` value. If omitted, all runs and
        tags will be included. The result will only contain keys for run-tag
        combinations that actually exist, which may not include all entries in
        the `run_tag_filter`.

    Returns:
      A nested map `d` such that `d[run][tag]` is a `BlobSequenceTimeSeries`
      value.

    Raises:
      tensorboard.errors.PublicError: See `DataProvider` class docstring.
    """
    pass

  def read_blob_sequences(
      self, experiment_id, plugin_name, downsample=None, run_tag_filter=None
  ):
    """Read values from blob sequence time series.

    Args:
      experiment_id: ID of enclosing experiment.
      plugin_name: String name of the TensorBoard plugin that created the data
        to be queried. Required.
      downsample: Integer number of steps to which to downsample the results
        (e.g., `1000`). Required.
      run_tag_filter: Optional `RunTagFilter` value. If provided, a time series
        will only be included in the result if its run and tag both pass this
        filter. If `None`, all time series will be included. The result will
        only contain keys for run-tag combinations that actually exist, which
        may not include all entries in the `run_tag_filter`.

    Returns:
      A nested map `d` such that `d[run][tag]` is a list of
      `BlobSequenceDatum` values sorted by step.

    Raises:
      tensorboard.errors.PublicError: See `DataProvider` class docstring.
    """
    pass

  def read_blob(self, blob_key):
    """Read data for a single blob.

    Args:
      blob_key: A key identifying the desired blob, as provided by
        `read_blob_sequences(...)`.

    Returns:
      Raw binary data as `bytes`.

    Raises:
      tensorboard.errors.PublicError: See `DataProvider` class docstring.
    """
    pass


class Run(object):
  """Metadata about a run.

  Attributes:
    run_id: A unique opaque string identifier for this run.
    run_name: A user-facing name for this run (as a `str`).
    start_time: The wall time of the earliest recorded event in this
      run, as `float` seconds since epoch, or `None` if this run has no
      recorded events.
  """

  __slots__ = ("_run_id", "_run_name", "_start_time")

  def __init__(self, run_id, run_name, start_time):
    self._run_id = run_id
    self._run_name = run_name
    self._start_time = start_time

  @property
  def run_id(self):
    return self._run_id

  @property
  def run_name(self):
    return self._run_name

  @property
  def start_time(self):
    return self._start_time

  def __eq__(self, other):
    if not isinstance(other, Run):
      return False
    if self._run_id != other._run_id:
      return False
    if self._run_name != other._run_name:
      return False
    if self._start_time != other._start_time:
      return False
    return True

  def __hash__(self):
    return hash((self._run_id, self._run_name, self._start_time))

  def __repr__(self):
    return "Run(%s)" % ", ".join((
        "run_id=%r" % (self._run_id,),
        "run_name=%r" % (self._run_name,),
        "start_time=%r" % (self._start_time,),
    ))


class _TimeSeries(object):
  """Metadata about time series data for a particular run and tag.

  Superclass of `ScalarTimeSeries` and `BlobSequenceTimeSeries`.
  """

  __slots__ = (
      "_max_step",
      "_max_wall_time",
      "_plugin_content",
      "_description",
      "_display_name",
  )

  def __init__(
      self, max_step, max_wall_time, plugin_content, description, display_name
  ):
    self._max_step = max_step
    self._max_wall_time = max_wall_time
    self._plugin_content = plugin_content
    self._description = description
    self._display_name = display_name

  @property
  def max_step(self):
    return self._max_step

  @property
  def max_wall_time(self):
    return self._max_wall_time

  @property
  def plugin_content(self):
    return self._plugin_content

  @property
  def description(self):
    return self._description

  @property
  def display_name(self):
    return self._display_name


class ScalarTimeSeries(_TimeSeries):
  """Metadata about a scalar time series for a particular run and tag.

  Attributes:
    max_step: The largest step value of any datum in this scalar time series; a
      nonnegative integer.
    max_wall_time: The largest wall time of any datum in this time series, as
      `float` seconds since epoch.
    plugin_content: A bytestring of arbitrary plugin-specific metadata for this
      time series, as provided to `tf.summary.write` in the
      `plugin_data.content` field of the `metadata` argument.
    description: An optional long-form Markdown description, as a `str` that is
      empty if no description was specified.
    display_name: An optional long-form Markdown description, as a `str` that is
      empty if no description was specified. Deprecated; may be removed soon.
  """

  def __eq__(self, other):
    if not isinstance(other, ScalarTimeSeries):
      return False
    if self._max_step != other._max_step:
      return False
    if self._max_wall_time != other._max_wall_time:
      return False
    if self._plugin_content != other._plugin_content:
      return False
    if self._description != other._description:
      return False
    if self._display_name != other._display_name:
      return False
    return True

  def __hash__(self):
    return hash((
        self._max_step,
        self._max_wall_time,
        self._plugin_content,
        self._description,
        self._display_name,
    ))

  def __repr__(self):
    return "ScalarTimeSeries(%s)" % ", ".join((
        "max_step=%r" % (self._max_step,),
        "max_wall_time=%r" % (self._max_wall_time,),
        "plugin_content=%r" % (self._plugin_content,),
        "description=%r" % (self._description,),
        "display_name=%r" % (self._display_name,),
    ))


class ScalarDatum(object):
  """A single datum in a scalar time series for a run and tag.

  Attributes:
    step: The global step at which this datum occurred; an integer. This
      is a unique key among data of this time series.
    wall_time: The real-world time at which this datum occurred, as
      `float` seconds since epoch.
    value: The scalar value for this datum; a `float`.
  """

  __slots__ = ("_step", "_wall_time", "_value")

  def __init__(self, step, wall_time, value):
    self._step = step
    self._wall_time = wall_time
    self._value = value

  @property
  def step(self):
    return self._step

  @property
  def wall_time(self):
    return self._wall_time

  @property
  def value(self):
    return self._value

  def __eq__(self, other):
    if not isinstance(other, ScalarDatum):
      return False
    if self._step != other._step:
      return False
    if self._wall_time != other._wall_time:
      return False
    if self._value != other._value:
      return False
    return True

  def __hash__(self):
    return hash((self._step, self._wall_time, self._value))

  def __repr__(self):
    return "ScalarDatum(%s)" % ", ".join((
        "step=%r" % (self._step,),
        "wall_time=%r" % (self._wall_time,),
        "value=%r" % (self._value,),
    ))


class BlobSequenceTimeSeries(_TimeSeries):
  """Metadata about a blob sequence time series for a particular run and tag.

  Attributes:
    max_step: The largest step value of any datum in this scalar time series; a
      nonnegative integer.
    max_wall_time: The largest wall time of any datum in this time series, as
      `float` seconds since epoch.
    latest_max_index: The largest index in the sequence at max_step (0-based,
      inclusive).
    plugin_content: A bytestring of arbitrary plugin-specific metadata for this
      time series, as provided to `tf.summary.write` in the
      `plugin_data.content` field of the `metadata` argument.
    description: An optional long-form Markdown description, as a `str` that is
      empty if no description was specified.
    display_name: An optional long-form Markdown description, as a `str` that is
      empty if no description was specified. Deprecated; may be removed soon.
  """

  __slots__ = ("_latest_max_index",)

  def __init__(
      self,
      max_step,
      max_wall_time,
      latest_max_index,
      plugin_content,
      description,
      display_name,
  ):
    super(BlobSequenceTimeSeries, self).__init__(
        max_step, max_wall_time, plugin_content, description, display_name
    )
    self._latest_max_index = latest_max_index

  @property
  def latest_max_index(self):
    return self._latest_max_index

  def __eq__(self, other):
    if not isinstance(other, BlobSequenceTimeSeries):
      return False
    if self._max_step != other._max_step:
      return False
    if self._max_wall_time != other._max_wall_time:
      return False
    if self._latest_max_index != other._latest_max_index:
      return False
    if self._plugin_content != other._plugin_content:
      return False
    if self._description != other._description:
      return False
    if self._display_name != other._display_name:
      return False
    return True

  def __hash__(self):
    return hash((
        self._max_step,
        self._max_wall_time,
        self._latest_max_index,
        self._plugin_content,
        self._description,
        self._display_name,
    ))

  def __repr__(self):
    return "BlobSequenceTimeSeries(%s)" % ", ".join((
        "max_step=%r" % (self._max_step,),
        "max_wall_time=%r" % (self._max_wall_time,),
        "latest_max_index=%r" % (self._latest_max_index,),
        "plugin_content=%r" % (self._plugin_content,),
        "description=%r" % (self._description,),
        "display_name=%r" % (self._display_name,),
    ))


class BlobReference(object):
  """A reference to a blob.

  Attributes:
    blob_key: A string containing a key uniquely identifying a blob, which
      may be dereferenced via `provider.read_blob(blob_key)`.

      These keys must be constructed such that they can be included directly in
      a URL, with no further encoding. Concretely, this means that they consist
      exclusively of "unreserved characters" per RFC 3986, namely
      [a-zA-Z0-9._~-]. These keys are case-sensitive; it may be wise for
      implementations to normalize case to reduce confusion. The empty string
      is not a valid key.

      Blob keys must not contain information that should be kept secret.
      Privacy-sensitive applications should use random keys (e.g. UUIDs), or
      encrypt keys containing secret fields.
    url: (optional) A string containing a URL from which the blob data may be
      fetched directly, bypassing the data provider. URLs may be a vector
      for data leaks (e.g. via browser history, web proxies, etc.), so these
      URLs should not expose secret information.
  """

  __slots__ = ("_url", "_blob_key")

  def __init__(self, blob_key, url=None):
    self._blob_key = blob_key
    self._url = url

  @property
  def blob_key(self):
    """Provide a key uniquely identifying a blob.

    Callers should consider these keys to be opaque-- i.e., to have no intrinsic
    meaning. Some data providers may use random IDs; but others may encode
    information into the key, in which case callers must make no attempt to
    decode it.
    """
    return self._blob_key

  @property
  def url(self):
    """Provide the direct-access URL for this blob, if available.

    Note that this method is *not* expected to construct a URL to the
    data-loading endpoint provided by TensorBoard. If this method returns
    None, then the caller should proceed to use `blob_key()` to build the URL,
    as needed.
    """
    return self._url

  def __eq__(self, other):
    if not isinstance(other, BlobReference):
      return False
    if self._blob_key != other._blob_key:
      return False
    if self._url != other._url:
      return False
    return True

  def __hash__(self):
    return hash((self._blob_key, self._url))

  def __repr__(self):
    return "BlobReference(%s)" % ", ".join(
        ("blob_key=%r" % (self._blob_key,), "url=%r" % (self._url,))
    )


class BlobSequenceDatum(object):
  """A single datum in a blob sequence time series for a run and tag.

  Attributes:
    step: The global step at which this datum occurred; an integer. This is a
      unique key among data of this time series.
    wall_time: The real-world time at which this datum occurred, as `float`
      seconds since epoch.
    values: A tuple of `BlobReference` objects, providing access to elements of
      this sequence.
  """

  __slots__ = ("_step", "_wall_time", "_values")

  def __init__(self, step, wall_time, values):
    self._step = step
    self._wall_time = wall_time
    self._values = values

  @property
  def step(self):
    return self._step

  @property
  def wall_time(self):
    return self._wall_time

  @property
  def values(self):
    return self._values

  def __eq__(self, other):
    if not isinstance(other, BlobSequenceDatum):
      return False
    if self._step != other._step:
      return False
    if self._wall_time != other._wall_time:
      return False
    if self._values != other._values:
      return False
    return True

  def __hash__(self):
    return hash((self._step, self._wall_time, self._values))

  def __repr__(self):
    return "BlobSequenceDatum(%s)" % ", ".join((
        "step=%r" % (self._step,),
        "wall_time=%r" % (self._wall_time,),
        "values=%r" % (self._values,),
    ))


class RunTagFilter(object):
  """Filters data by run and tag names."""

  def __init__(self, runs=None, tags=None):
    """Construct a `RunTagFilter`.

    A time series passes this filter if both its run *and* its tag are
    included in the corresponding whitelists.

    Order and multiplicity are ignored; `runs` and `tags` are treated as
    sets.

    Args:
      runs: Collection of run names, as strings, or `None` to admit all
        runs.
      tags: Collection of tag names, as strings, or `None` to admit all
        tags.
    """
    self._runs = None if runs is None else frozenset(runs)
    self._tags = None if tags is None else frozenset(tags)

  @property
  def runs(self):
    return self._runs

  @property
  def tags(self):
    return self._tags

  def __repr__(self):
    return "RunTagFilter(%s)" % ", ".join((
        "runs=%r" % (self._runs,),
        "tags=%r" % (self._tags,),
    ))
