"""microfview module.

Available classes:
  - Microfview: class for delegating frames from Capture classes to
                Plugin classes
  - CameraCapture: class for interfacing cam_iface cameras
  - FMFCapture: class for interfacing FlyMovieFormat videos
  - BlockingPlugin: base class for blocking plugins
  - NonBlockingPlugin: base class for non blocking plugins

Available functions:
  - getLogger: returns the microfview logging.Logger instance

Microfview is a minimal implementation of something that is a
'fview-like' plugin framework. It comes without the whole GUI
stuff and creating a new plugin really boils down to writing
one function ('process_frame') that calculates something on
the captured frame.

Example:
  A minimal plugin example would look like this:

  >>> cam = CameraCapture()
  >>> fview = Microfview(cam)
  >>> class MySumPlugin(NonBlockingPlugin):
  >>>     def process_frame(frame_time, current_time, frame):
  >>>         print frame_time, frame.sum()
  >>> myplugin = MySumPlugin()
  >>> fview.attach_plugin(myplugin)
  >>> fview.start()

"""

import os.path as osp

pkg_dir = osp.abspath(osp.dirname(__file__))
data_dir = osp.join(pkg_dir, 'data')

__version__ = "0.1.0"

import cv2

from .main import Microfview
from .plugin import BlockingPlugin, NonBlockingPlugin, PluginFinished, PluginChain
from .capture import SeekError, get_capture_object
from .capture.transform import ImageTransform
from .util import get_logger, parse_config_file, get_argument_parser, is_color
from .plugins.display import DisplayPlugin

