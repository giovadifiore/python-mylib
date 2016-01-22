import os
import stat
import cPickle as pickle
import errno

MAX_SIZE = 65535


class NamedPipeWrapper:
    def __init__(self, path):
        self.pipe_path = path
        self.pipe = None

    def open_pipe(self, mode='w', blocking=True):
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
        try:
            self.pipe = os.open(self.pipe_path, flag)
        except OSError as e:
            if e.errno == errno.ENXIO:
                self.pipe = None

        return self.pipe

    def close_pipe(self):
        if self.pipe is not None:
            os.close(self.pipe)

    def write_pipe(self, data):
        # If the pipe was not open, try to open it
        if self.pipe is None:
            self.open_pipe(blocking=False)

        # If the pipe is ready, write to it
        if self.pipe is not None:
            try:
                # pickle data and write to PIPE
                data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
                os.write(self.pipe, data)
                return True
            except OSError:
                pass
        else:
            return False

    def read_pipe(self):
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
            self.close_pipe()
            # Block waiting a new open
            self.open_pipe(mode='r')
            # Call again this function
            return self.read_pipe()
