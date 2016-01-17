Python utility classes 
===================

This repository contains a set of Python utility classes that I used in my projects. Following there is a short description of each one.

Named PIPE Wrapper (named\_pipe\_wrapper.py)
-------------

This class is implemented and tested on Linux environment and wraps the IPC communication between two Python running instances using a named PIPE.

This utility class automatically manages the creation/opening of the named PIPE into the system and allows writers and readers processes to communicate each other.

It has been tested in a scenario with one writer and multiple readers processes which agree on the named PIPE file given to the class constructor. In this implementation, the write method `send` is not blocking and returns `False` immediately if no readers are connected to the read-end of the PIPE. The `receive` method, instead, blocks the caller until data is successfully read from the PIPE. The data exchanged on the PIPE is automatically pickled/unpickled and the user can pass entire pickle-able Python objects.

Please consider security risks related to pickle object serialization. For further informations on pickling, please see this [page](https://docs.python.org/2/library/pickle.html).
#### Example of use
Reader process:

```python
# reader process that continuously reads from PIPE
pipe = NamedPipeWrapper('/tmp/my_pipe.pipe')
while (True):
	data = pipe.receive()
	print(data)  # data successfully received!
```

Writer process:
 
```python
# reader process that continuously reads from PIPE
pipe = NamedPipeWrapper('/tmp/my_pipe.pipe')
data = {'foo': 'bar'}
if pipe.send(data):
	print(data)  # data successfully sent!
else:
	pass  # no readers available
```
Thread-safe Multi-Group Message Buffer (receive\_queue.py)
-------------
This class abstracts a group-separated message buffer of fixed length implemented as a FIFO queue. It's useful in scenarios when a single compute node receives messages from multiple clients that should be consumed by a separate thread of control. The internal structure of buffers can be accessed using a `groupkey` and an `idx` key. Group keys are statically defined within class constructor, but buffers inside a single group can be dynamically allocated on demand. 

Suppose the scenario in which there is a single server node which is responsible to receive two or more kind of messages from a dynamically joining set of multiple clients (e.g. health status, telemetries, etc...). After that the receive event happens (e.g. received data from a socket) the application can enqueue the message into the desired buffer. For example, if an `health-status` message is received from a client node identified with its hostname such as `node-0`, the application can enqueue this message with one of the provided *receive* methods by calling `sync_receive('health-status', 'node-0', status)`. For instance, the `health-status` group contains as many buffers as clients nodes attempting to send their health status, and the message referred as `status` can be any type of Python object.

Data received can be then extracted using one of the provided *extract* methods, by specifying both a `groupkey` and an `idx` key. The extracted data is a tuple of fixed length containing the whole set of objects received so far. Extracted data is not deallocated and persists to subsequent calls. If the number of objects received exceeds the fixed length of the designated buffer, the least recent object enqueued for that buffer will be discarded and deallocated in accordance with the FIFO policy.

The class is thread-safe and the current version supports two kind of synchronization policies that are enabled within methods whose signature starts with `sync_` (i.e. `sync_receive`, `sync_extract`, etc...). Available synchronization policies are:

 - `exclusive` this policy completely disallow concurrent access from multiple threads, ignoring if the access is `receive` or `extract`. This is the more restrictive synchronization policy;
 - `rw` this policy implements a ReadWrite lock allowing multiple concurrent `receive` calls (i.e. multiple writers), but only one `extract` at a time (i.e. one reader). Receive and extract calls, however, are mutually exclusive so that the critical resource cannot be accessed from both a reader and a writer (or writers) at the same time.

#### Example of use
This example instantiate two groups `health` and `telemetry` of buffers with a fixed length of 10 objects, using the `exclusive` synchronization policy. 

Example of object allocation:

```python
buffers = ReceiveQueue(('health', 'telemetry'), 10, 'exclusive')
```

A receiver (i.e. writer) thread could be:

```python
# Enqueues 'xyz' to 'foo' buffer in 'health' group
buffers.sync_receive('health', 'foo', 'xyz')
# Enqueues 'xyz' and 'uvt' to 'bar' buffer in 'health' group
buffers.sync_receive('health', 'bar', 'xyz')
buffers.sync_receive('health', 'bar', 'uvt')
```
An extractor (i.e. reader) thread could be:
	
```python
# A reader can use this extract method
bar = buffers.sync_extract('health', 'bar')
print(bar)  # bar is a 2-elem tuple containing the strings 'xyz' and 'uvt'
```
Libvirt wrapper for getting domain's info (libvirt\_wrapper.py)
-------------
This extremely simple class wraps calls being done to the libvirt deamon keeping connection established during subsequent invocations. This avoids the unuseful connection creation overhead when there is the need to periodically invoke the same remote libvirt procedures.

The connection is maintained within the same contacted host which executes the libvirt daemon.

Currently, the only supported libvirt method is `info`.

#### Example of use
This example establishes a connection to a libvirt daemon on the `foo` host and to calls the info method for a specified domain identified with `instance-00000f01`. This example uses TCP to communicate with the libvirt instance which is interfacing `qemu` domains. 

```python
libvirt = LibvirtWrapper()
libvirt.connect_host('foo', 'qemu+tcp://foo/system')

# now the connection is established and internally handled with no need to renew it over invocations
data = libvirt.get_info('foo', 'instance-00000f01')
sleep(2)
data = libvirt.get_info('foo', 'instance-00000f01')
...
```
Tic-Toc Stopwatch (time\_manager.py)
-------------
This simple Python class simulate a stopwatch and is useful to compute elapsed time of execution with the given resolution. In some scenarios, it can be very useful to increase the accuracy of the busy cycle length given to a periodic task.

The `tic` method starts the stopwatch, while the `toc` stops and return the elapsed time since the last `tic` call. The `toc` method has a resolution argument that can be one of:

 - `s`: to return the elapsed time in seconds;
 - `ms`: to return the elapsed time in milliseconds;
 - `us`: to return the elapsed time in microseconds;
 - `ns`: to return the elapsed time in nanoseconds;
 - `sf`: to return elapsed time using the most accurate time available in the current system.

#### Example of use
Suppose you have a periodic time-consuming task which executes every second. To increase the time slice accuracy of the period, it's possibile to use the stopwatch as follow:
```python
tm = TimeManager()
period = 3

while(True):
	# start the stopwatch
	tm.tic()
	
	# execute the time-consuming task
	...
	...
	
	# sleep for the remaining time
	if ( period - tm.toc('sf') > 0 ):
		sleep( period - tm.toc('sf') )
	else:
		# execution is overtime !
		
```