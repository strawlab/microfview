"""microfview.plugin module

Provides to classes from which you can derive your own Plugins.

BlockingPlugin:
  Derive from BlockingPlugin and override method process_frame to get
  a Plugin which blocks the Microfview mainloop when running
  process_frame.

NonBlockingPlugin:
  Derive from NonBlockingPlugin and override method process_frame to
  get a Plugin which does not block the Microfview mainloop when running
  process_frame. But it skips a frame if process_frame did not return
  before the next incoming frame.

"""
import threading
import time

import logging
logger = logging.getLogger('microfview')

class PluginFinished(Exception):
    pass

class _Plugin(object):

    def __init__(self, every=1):
        """BlockingPlugin.

        Args:
          every (int): process_frame gets called every Nth frame.

        """
        self.logger = logger
        self.every = int(every)
        self.finished = False

    def start(self):
        """compatibility function."""
        pass

    def stop(self):
        """compatibility function."""
        pass

    def process_frame(self, frame_time, current_time, frame):
        """override this function."""
        pass

class BlockingPlugin(_Plugin):

    def push_frame(self, *callargs):
        """compatibility function."""
        self.process_frame(*callargs)
        return True

class NonBlockingPlugin(_Plugin, threading.Thread):

    def __init__(self, every=1, max_start_delay_sec=0.001):
        """NonBlockingPlugin.

        Starts a worker thread that listens for incoming frames.

        Args:
          every (int): process_frame gets called every Nth frame.
          max_start_delay_sec (float): spins the workerthread on this
            timescale. Defaults to 0.001 sec.

        """
        _Plugin.__init__(self, every)
        threading.Thread.__init__(self)
        self.daemon = True
        self._frame_available = False
        self._lock = threading.Lock()
        self._idle_wait = float(max_start_delay_sec)
        self.callargs = (None, None, None)

    def stop(self):
        """stop the worker thread."""
        with self._lock:
            self._run = False

    def push_frame(self, *callargs):
        """push a frame to the worker queue.

        Returns True if the queue is empty. False if the worker thread is still
        processing a frame.

        """
        with self._lock:
            frame_available = self._frame_available
        if frame_available:
            return False
        else:
            self.callargs = callargs
            with self._lock:
                self._frame_available = True
            return True

    def run(self):
        """worker mainloop."""
        logger.info("starting worker")
        self._run = True
        while not self.finished:
            with self._lock:
                frame_available = self._frame_available
                if not self._run:
                    logger.info("exiting worker")
                    break
            if not frame_available:
                time.sleep(self._idle_wait)
                continue
            try:
                self.process_frame(*self.callargs)
            except PluginFinished:
                self.finished = True
            except:
                logger.exception("error in process_frame")
            with self._lock:
                self._frame_available = False

