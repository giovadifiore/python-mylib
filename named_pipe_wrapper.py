import os
import stat
import cPickle as pickle
import errno

MAX_SIZE = 65535


class NamedPipeWrapper:
    def __init__(self, path):
        self.pipe_path = path
        self.pipe = None

    def _open_pipe(self, mode='w', blocking=True):
	"""
	This private method is used internally to handle the open syscall for the PIPE"
	:return: the named PIPE fd on success
	"""
        # If file doesn't exist, mkfifo
        if not os.path.isfile(self.pipe_path) or not stat.S_ISFIFO(os.stat(self.pipe_path).st_mode):
            try:
                os.mkfifo(self.pipe_path)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    # named pipe exists, keep going
                    pass
                else:
                    raise

        # Configure the open mode
        flag = os.O_WRONLY
        if mode == 'r':
            flag = os.O_RDONLY

        # ORing the NONBLOCK flag
        if not blocking:
            flag |= os.O_NONBLOCK

        # Open
        self.pipe = os.open(self.pipe_path, flag)

        return self.pipe

    def _close_pipe(self):
	"""
	This method closes the PIPE, if any
	"""
        if self.pipe is not None:
            os.close(self.pipe)

    def send(self, data):
	"""
	This method attempts to write data to PIPE and automatically handles the openin/creation of it
	:return: True if success, False otherwise
	"""
        # If the pipe was not open, try to open it
        if self.pipe is None:
            self._open_pipe(blocking=False)

        # If the pipe is ready, write to it
        if self.pipe is not None:
            try:
                os.write(self.pipe, data)
                return True
            except OSError:
                pass
        else:
            return False

    def receive(self):
        """
        This method attempts to read from the open named pipe and blocks the caller until data is received
        :return: received data (loaded pickle object) from the named pipe
        """
        # This call is blocking, waiting for the next available detection status on the pipe
        tmp_data = os.read(self.pipe, MAX_SIZE)

        # If not-empty data
        if len(tmp_data) > 0:
            data = pickle.loads(tmp_data)
            return data
        else:
            # If the read returned nothing, means that the write end-point was closed
            self._close_pipe()
            # Block waiting a new open
            self._open_pipe(mode='r')
            # Call again this function
            return self.receive()
