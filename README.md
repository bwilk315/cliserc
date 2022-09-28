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
All methods *Simplex* class is equipped with are listed below:

- List will be available soon

### Client example
###### Preparation
Create class instance with client behavior:
```python
client = Simplex('127.0.0.1', 6000, is_server: False, on_send=custom_on_send)
```
On connection try client will try to connect to the host with address '127.0.0.1' (localhost) on port 6000, *on_send* keyword argument is set to custom function *custom_on_send* for processing received data and composing response, its value (which is actually lambda) must return Bartek's Notation object *BNot* which is then encoded and sent over network, and contain two parameters typed *BNot* (received data as Bartek's Notation) and *float* (Time between last data receive and current) respectively. As you can see you are going to manage data flow with only one function which is actually simple:
```python
def custom_on_send(resp: BNot, dt: float) -> BNot:
	# Get value of 'x' from dictionary-like object 'resp'
	x = float(resp.get('x', 0))
	# Print the received data
	print(f'Received value of x: {x}!')
	# Response with status OK
	return BNot({'response': Simplex.RES_OK})
```
It may look complicated but it is not:
- **resp**
Data received from the server packed into Bartek's Notation object
- **dt**
Time since last receive operation (call of this function)\
###### Testing
If everything is set up, try to connect:
```python
success = client.connect(create_thread=True)
```
Now client will try to connect in another thread (current will be free), *success* variable stores the boolean value that tells if connection was successful.
###### Summary
We have just programmed a client application which will print the value of 'x' every *dt* seconds if server included it in its response (otherwise default value will be used, here equal 0). Our custom function always responses with status *OK*, which indicates a proper communication.
### Server example
###### Preparation
Create class instance with server behavior:
```python
server = Simplex('127.0.0.1', 6000, is_server: True)
```
On *start* method call, attempt to bind server with address '127.0.0.1' on port 6000 will occur:
```python
success = server.start()
```
Here the *success* variable stores a boolean value which indicates whether server has started without any errors.
###### Listening for client
Let server start listening for incoming connection using *wait* method which will stop thread on which it is running on, until some client connects:
```python
# Start listening only if server has been initialized successfully
if success:
	# Use try statement if you are going to stop program with keyboard.
	# It will let the program to safely close server using method
	try:
		# Start infinite loop which will listen for a client, if client is already
		# connected, it will just continue. Remember that only one client per
		# server is allowed.
		while True:
			server.wait(create_thread=False)
	except KeyboardInterrupt:
		pass
server.close()
```
###### Summary
Congratulations! you have just programmed a working server software, experiment with example client software project described above the current.