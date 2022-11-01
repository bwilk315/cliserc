# Cliserc
### Description
*Cliserc* stands for *Client-Server Communication* which may occur in both directions but not in the same time (collision risk). Module is designed to be handy and simple in use; these are accomplished by structure the main class has.\
Main class called *Simplex* is prepared to be either server or client, everything depends on settings that developer will choose during the initialization step.
Remember that difference between server and client matters, for better understanding: server is an upgraded version of client (it has more privileges).
### Documentation
To start using main class first import it:
```python
from cliserc.simplex import Simplex
```
All members of _Simplex_ class are listed and described below:

##### Constants
- <u>constant float **MIN_CONN_INTERVAL**</u>\
Minimum time interval in seconds between client disconnection and connection to a server assuring the proper work of both sides.

- <u>constant int **RES_NULL**</u>\
Response type indicating the lack of response type in received data.

- <u>constant int **RES_OK**</u>\
Type of response included in incoming data if sender received lastly sent data properly.

- <u>constant int **RES_EXIT**</u>\
Response included in incoming data if sender wants to close connection.

##### Constructor parameters
- <u>param string **host**</u>
	- client\
	IPv4 address of target server (local or global).
	- server\
	Address which will be binded with server.

- <u>param int **port**</u>
	- client\
	Port of cliserc-based service running on the target server.
	- server\
	Port which will be forwarded to cliserc-based service running on server machine.

- <u>param bool **is_server**</u>\
	Should current instance of class act as server?

- <u>kwarg function(_BNot_, _float_) -> _BNot_ **on_send** = lambda _resp_, _dt_: BNot({"response": Simplex.RES_OK})</u>\
Callback function taking two parameters from which first is the received data encoded in Bartek's Notation object and second is time in seconds since last receive operation. Learn more about Bartek's Notation by reading its [documentation](https://pypi.org/project/bnot/) on PyPI.

- <u>kwarg function() -> None **on_connect** = lambda: None</u>\
Function invoked when host estabilishes connection with a remote host.

- <u>kwarg function() -> None **on_refuse** = lambda: None</u>\
Custom callback function called when remote host refuses a connection from current.

- <u>kwarg function(_int_) -> None **on_exit** = lambda _code_: None</u>\
Callback invoked when connection is finished, its only parameter is set to exit status code which indicates if exit occurred due user wish or some error.

- <u>kwarg string **net_encoding** = "utf-8"</u>\
Encoding used to encode data which is then sent over network.

- <u>kwarg float **timeout** = 4.0</u>\
Maximum time in seconds for current host to wait for connection, after this time host will not continue trying to connect, if process occurs in other thread it will be closed.

- <u>kwarg int **buff_size** = 128</u>\
Amount of bytes describing communication buffer length. Length of data encoded into Bartek's Notation which is then sent over network can not exceed this amount, otherwise exceeding part of data will not be sent thus whole data will be broken.

- <u>kwarg bool **show_log** = False</u>\
If set to true, useful and readable information about everything happening in the cliserc-based network communication.

##### Class members
- <u>member tuple[2] **address**</u>\
Tuple containing two elements which are host IPv4 address and cliserc-based service port respectively, it forms a network socket ...
	- client
	... to which client will try to connect. 
	- server
	... which server will be bonded with.

- <u>member int **sent_bytes**</u>\
	Total amount of sent bytes during the current connection.

- <u>member int **recv_bytes**</u>\
	Total amount of received bytes during the current connection.

- <u>member bool **listening**</u>
	- server
	Whether server is ready and listening for connection.

- <u>member bool **connected**</u>\
	Tells if the current host is connected with a remote one.

- <u>member function(bool) -> bool **connect**</u>
	- client
	Tries to connect to the server with _address_ socket. The only parameter defines if separate thread should be created for connection process (then current will be free).

- <u>member function() -> bool **start**</u>
	- server
	Tries to bind server with IPv4 address _host_ and start cliserc-based service on port _port_. Returns whether everything went well during execution of function.

- <u>member function(bool) -> bool **wait**</u>
	- server
	Waits for incoming connection and starts client-handling loop as soon as it estabilishes the connection if there is no active one. If no connection come in _timeout_ seconds function terminates. The only parameter specifies if separate thread should be created for waiting process (current will be free). Returns if everything went well.

- <u>member function() -> None **close**</u>
	Closes the connection with remote host by ...
	- client
	... setting WOD (wish of disconnection) flag, server will then read it and call its version of this function.
	- server
	... closing all sockets and terminating client handler (if thread for it was created).

### Client example
##### Preparation
Create class instance with client behavior:
```python
client = Simplex(
	host		= '127.0.0.1',
	port		= 6000,
	is_server	= False,
	show_log	= False,
	on_send		= custom_on_send
)
```
On connection try client will try to connect to the host with address '127.0.0.1' (localhost) on port 6000, *on_send* keyword argument is set to custom function *custom_on_send* for processing received data and composing response, its value (callback function) must return Bartek's Notation object *BNot* (read more about this notation [here](https://pypi.org/project/bnot/)) which is then encoded and sent over network; callback contains two parameters: first typed *BNot* (received data as Bartek's Notation) and second typed *float* (Time between last data receive and current). As you can see you are going to manage data flow with only one function which is actually simple:
```python
from bnot import BNot  # Import notation manager.

def custom_on_send(resp: BNot, dt: float) -> BNot:
	""" Callback managing the data flow on client side """
	# Get the message value, if it is not available return default.
	msg = resp.get('msg', 'No he did not.')
	# Show message on screen.
	print(f'Server sent a message: {msg}')
	# Response to server with status OK.
	return BNot({'response': Simplex.RES_OK})
```
You can exit connection by sending _RES_EXIT_ status instead.
##### Testing
If everything is set up, try to connect:
```python
# If set to False (without another thread) current thread will
# be blocked until communication with server closes or target server
# is inaccessible.
success = client.connect(create_thread=True)
print('Current thread is now free!')
```
Now client will try to connect in another thread (current will be free), _success_ variable stores the boolean value that tells if connection was successful. You can always use _close_ member method to inform server about wish of disconnection, it works similarly to sending exit status presented in previous section.
### Server example
##### Preparation
Create class instance with server behavior:
```python
server = Simplex(
	host		= '127.0.0.1',
	port		= 6000,
	is_server 	= True,
	show_log	= False,
	on_send		= custom_on_send
)
```
Define data flow behaviour by defining a callback function:
```python
from time import sleep
from bnot import BNot  # Import notation manager.

def custom_on_send(resp: BNot, dt: float) -> BNot:
	""" Callback managing the data flow on server side """
	sleep(1)  # Limit transmission speed to 1/s.
	# Include message in response to client.
    return BNot({
		'response': Simplex.RES_OK,
		'msg': 'Greetings!'
	})
```
On _start_ method call, attempt to bind server with address 127.0.0.1 on port 6000 will occur:
```python
success = server.start()
```
Here the *success* variable stores a boolean value which indicates whether server has started properly.
##### Listening for client
Let server start listening for incoming connection using _wait_ member method:
```python
if success:
	# If set to False (without additional thread) current will be blocked
	# until server closes connection with a client or gets timed out.
	server.wait(create_thread=True)
	print('This thread is free on my demand now!')
# server.close()
```
The way with another thread included is the best for programs where something has to run in parallel with waiting process. Uncomment _close_ function call if you do not create another thread: if everything happens in another thread and current is free, program will execute next lines including method call.
### Summary
Congratulations! you have just programmed a working server software. Experiment with client example explained above this example section. Personally I invented this module to exchange android sensors' data over network (android-pc communication) in my custom notation format (reference to module called [bnot](https://pypi.org/project/bnot/)) using my another module for getting android sensors data called [sendroid](https://pypi.org/project/sendroid/). I learned a lot during this journey, now module is in beta version and ready to test, if you have any problems please create an issue on [cliserc github page](https://github.com/bwilk315/cliserc).