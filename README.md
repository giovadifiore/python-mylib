Python utility classes 
===================

This repository contains a set of Python utility classes that I used in my projects. Following there is a short description of each one.

Named PIPE Wrapper (named\_pipe\_wrapper.py)
-------------

This class is implemented and tested on Linux environment and wraps the IPC communication between two Python running instances using a named PIPE.
This utility class automatically manages the creation/opening of the named PIPE into the system and allows writers and readers processes to communicate each other.
It has been tested in a scenario with one writer and multiple readers processes which agree on the named PIPE file given to the class constructor. In this implementation, the write method `send` is not blocking and returns `False` immediately if no readers are connected to the read-end of the PIPE. The `receive` method, instead, blocks the caller until data is successfully read from the PIPE. The data exchanged on the PIPE is automatically pickled/unpickled and the user can pass entire pickle-able Python objects.
Please consider security risks related to pickle object serialization. For further informations on pickling, please see this [page](https://docs.python.org/2/library/pickle.html).
#### Sample of use 
Reader process:

    # reader process that continuously reads from PIPE
    pipe = NamedPipeWrapper('/tmp/my_pipe.pipe')
    while (True):
	    data = pipe.receive()
	    print(data)  # data successfully received!

Writer process:
 
    # reader process that continuously reads from PIPE
    pipe = NamedPipeWrapper('/tmp/my_pipe.pipe')
    data = {'foo': 'bar'}
	if pipe.send(data):
		print(data)  # data successfully sent!
	else:
		pass  # no readers available

