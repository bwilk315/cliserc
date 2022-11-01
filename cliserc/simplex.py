
# Standard library.
from    threading  import Thread
from    time       import time
import  logging
import  socket
# Third-party modules.
from    bnot       import BNot


class Simplex:
    RES_NULL                = -1    # Appears if unknown data has been received.
    RES_OK                  = 0     # Is included in received data block if remote host received the last data successfuly
    RES_EXIT                = 1     # Received with data block if remote host (client) wants to close connection.
    MIN_CONN_INTERVAL       = 1.0   # Minimum time delay after disconnection required for a proper working of a class.      
    __lct                   = 0.0   # Last client connection time.
    __tslc                  = 0.0   # Time since the last client connection.

    def __init__(self, host: str, port: int, is_server: bool, **kwargs) -> None:
        """
            Client class represents a standard client structure. It can receive and share data with a remote host in simplex mode.
            @param host:        IPv4 address you want to connect to or bind server with.
            @param port:        Port of Simplex server service.
            @param is_server:   Is this simplex host a server? Note that features of server and client differs.
            @kwarg on_send:     Callback which will receive data, and prepare it to send.
            @kwarg on_exit:     Method called on every disconnection from remote host (after receiving 'RES_EXIT' response).
            @kwarg on_refuse:   Callback invoked when connection is refused by server (no response from server).
            @kwarg on_connect:  Called when client receives the first OK response from server.
            @kwarg show_log:    Controls visibility of action messages in the standard output.
            @kwarg timeout:     Time in seconds for receiving and sending data, if some process exceeds this value, timeout error is thrown.
            @kwarg buff_size:   Size of the send-receive buffer in bytes.
            @kwarg encoding:    Encoding type used to encode data sent to server/client. Note that receiver should decode data using the same type.
        """
        # Parameters.
        self.host               = host      # IP (version 4) address of a remote host.
        self.port               = port      # Port on which remote host works.
        self.is_server          = is_server # Boolean indicating whether server is built using the class.
        self.on_send            = kwargs.get('on_send', self.__on_send)     # Method invoked when current host receives data and is ready to send new.
        self.on_connect         = kwargs.get('on_connect', lambda: None)    # Callback called when connection with remote host estabilishes.
        self.on_refuse          = kwargs.get('on_refuse', lambda: None)     # Method called when remote host refuses connection.
        self.on_exit            = kwargs.get('on_exit', lambda: None)       # Callback invoked when connection is terminated.
        self.net_encoding       = kwargs.get('encoding', 'utf-8')           # Messages' encoding type.
        self.timeout            = kwargs.get('timeout', 4.0)                # Maximum time (timeout) in seconds for a connection process.
        self.buff_size          = kwargs.get('buff_size', 128)              # Size of the communication buffer.
        self.show_log           = kwargs.get('show_log', True)              # Should logging be enabled? These are helpful information about everything.
        # Public members.
        self.address            = (host, port)  # Address consists of host and port, it describes full pipe of communication..
        self.sent_bytes         = 0             # Total amount of sent bytes.
        self.recv_bytes         = 0             # Total amount of received bytes.
        self.listening          = False         # True Whether server is listening for connections.
        self.connected          = False         # True if server or client is connected to client or server respectively.
        # Private members.
        self.__socket           = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Socket used by the client to send and receive data.
        self.__remote           = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Socket used to communicate with connected remote host (client).
        self.__handling_thread  = None  # Handling thread reference, it is used to close it later.
        self.__raddr            = ''    # Address of a remote client connected to the server.
        self.__sr_delta_time    = 0.0   # Time between last data send and current receive operation.
        self.__send_time        = 0.0   # The time in which some data was sent by local host.
        self.__wants_exit       = False # True if the client called 'close' method, it will include exit message in the next send operation.
        self.__activated        = False # Does server sent a response message which indicates a proper activation of the conversation?
        # Initialization logic.
        if self.show_log:
            # Set the basic level of logging to info (everything will be shown).
            logging.basicConfig(
                level = logging.INFO,
                format='[%(levelname)s] %(message)s'
            )
        else:
            # Disable log messages.
            logging.disable()
        # Set the timeout of a client socket.
        self.__socket.settimeout(self.timeout)
        logging.info('Initialized the Simplex host.')

    def start(self) -> bool:
        """ Initializes server and sets it in listening state. """
        if self.is_server:
            # Try to start servicing port on specified IPv4 address.
            try:
                self.__socket.bind(self.address)
                self.__socket.listen()
                self.listening = True
            except OSError as e:
                logging.error('Error occurred when tried to bind server with specified address: %s', e)
                return False
            else:
                logging.info('Binded server with address %s on port %i.', *self.address)
                return True
        else:
            logging.error('Simplex host %s is not marked as server!', self.host)
            return False

    def wait(self, create_thread = False) -> bool:
        """ Waits for client connection and starts handling it as soon as it is active and accessible. """
        if self.listening:
            # Wait for connection in another thread if user wants that, client-handling loop will behave the same.
            if create_thread:
                Thread(target = self.__wait_for_connection, args = (True,)).start()
            else:
                self.__wait_for_connection(create_thread = False)
        else:
            logging.error('Simplex host %s:%i is not listening, so it is impossible to wait for a client connection.', *self.address)
        return False

    def connect(self, create_thread = False) -> bool:
        """ Tries to connect to the server, returns if operation was succeed. """
        self.__activated = False
        Simplex.__tslc = time() - Simplex.__lct
        # If interval between disconnection and the current try of connection is not long enough cancel method
        if Simplex.__tslc < self.MIN_CONN_INTERVAL:
            logging.warning('Time between disconnection and connection process was %fs, required at least %fs.', Simplex.__tslc, self.MIN_CONN_INTERVAL)
            return False
        # If client is marked as server, it is impossible to perform connections, cancel method
        elif self.is_server:
            logging.error('Simplex host %s is already a server.', self.host)
        # If client is somehow listening like server does, it can not perform connections, cancel method
        elif self.listening:
            logging.error('Simplex host %s is listening thus can not connect to the remote host.', self.host)
        # Finally if connection to a specified address is possible, connect to it and start server-handling process
        elif self.__socket.connect_ex(self.address) == 0:
            self.connected = True
            logging.info('Successfuly connected to %s on port %i.', *self.address)
            # Based on the option selected ('create_thread' boolean) start server-handling process
            if create_thread:
                # Start separated handling thread
                self.__handling_thread = Thread(target = self.__start_handling)
                self.__handling_thread.start()
                logging.info('Created thread for handling a server.')
            else:
                logging.info('Started server-handling process in the current thread.')
                # Handle server in the current thread
                self.__start_handling()
            return True
        logging.info('Connection failed.')
        return False

    def close(self) -> None:
        """ Sends a quit message to the remote host (as client) or closes everything now (as server). """
        if self.is_server:
            if self.__handling_thread is not None:
                self.__handling_thread.join()  # Terminate handling thread.
            self.__remote.close()
            self.__socket.close()
            self.listening = False
            self.connected = False
            logging.info('Server and client has been closed.')
        else:
            # As client show the wish of disconnection which will be processed in the next send operation
            self.__wants_exit = True
            logging.info('Alerted server about client wish of disconnection.')

    def __on_send(resp: BNot, dt: float) -> BNot:
        """ Default version of on_send callback """
        return BNot({'response': Simplex.RES_OK})

    def __force_client_close(self) -> None:
        """ Forces the remote client to disconnect from server. """
        self.connected = False
        self.__remote.close()
        logging.warning('Disconnected remote client %s without asking him.', self.__raddr[0])

    def __receive(self) -> str:
        """ Waits for incoming data from the server and returns it. """
        try:
            # Try to receive data using a proper socket
            data = (self.__remote if self.is_server else self.__socket).recv(self.buff_size).decode(self.net_encoding)
            self.__sr_delta_time = time() - self.__send_time
            self.recv_bytes += len(data)
            logging.info('Received %i bytes of data: %s', self.buff_size, data)
            return data
        except (socket.timeout, ConnectionResetError, OSError) as e:
            logging.error('Error occurred during data-receive: %s', e)
            return ''

    def __share(self, data: dict) -> int:
        """
            Serializes 'data' dictionary into Bartek's Notation and sends it to remote host.
            @param data:    Dictionary of variable names as keys and their values as keys' values.
        """
        # Check if provided data has a dictionary type
        if not isinstance(data, dict):
            logging.error('Data provided (%s) is not a dictionary!', data)
            return None
        # Serialize dictionary using Bartek's Notation object
        actual_msg = BNot(data = data)
        am_code = actual_msg.encode()
        # Check if message length does not exceed the buffer size.
        if len(am_code) > self.buff_size:
            logging.error('Message current host wants to send is too big (%i bytes) for specified maximum buffer size of %i bytes.', len(am_code), self.buff_size)
            return 0
        try:
            # Try to send serialized data through proper socket
            actual_socket = self.__remote if self.is_server else self.__socket
            # Send actual data.
            am_bytes = actual_socket.send(am_code.encode(self.net_encoding))
            self.__send_time = time()
            self.sent_bytes += am_bytes
            logging.info('Sent %i bytes of data: %s', am_bytes, am_code)
            return am_bytes
        except socket.error as e:
            logging.error('Error occurred during data-sent: %s', e)
            self.on_exit()
            self.__socket.close()
            return 0

    def __wait_for_connection(self, create_thread: bool) -> bool:
        # Try to accept incoming connection from client. If timeout error is thrown finish method
        try:
            logging.info('Waiting for connection ...')
            client_socket, client_addr  = self.__socket.accept()  # Wait for connection
            # If server is already connected, refuse other client connection requests
            if self.connected:
                client_socket.close()
                logging.warning('Refused connection from %s. Actually there is already a connected host %s', client_addr[0], self.__raddr[0])
                return False
            else:
                self.__remote   = client_socket
                self.__raddr    = client_addr
        except socket.timeout as e:
            logging.error('Time for client connection is up: %s', e)
        except OSError as e:
            logging.error('Error occurred in the client. Server has thrown an error: %s', e)
            self.__force_client_close()
            self.close()
        else:
            # If connection was accepted successfuly, prepare handling method for client
            self.connected = True
            # Send first empty message with status OK to begin conversation loop
            sent_bytes = self.__share({'response': Simplex.RES_OK})
            if sent_bytes == 0:
                logging.error('Initialization of conversation failed.')
                return False
            logging.info('Initialized a conversation loop.')
            # Based on the option selected (create_thread boolean), start client-handling process
            if create_thread:
                # Start client-handling thread
                self.__handling_thread = Thread(target = self.__start_handling)
                self.__handling_thread.start()
                logging.info('Created a separated thread for handling a client.')
            else:
                logging.info('Started handling a client in the current thread.')
                # Begin client-handling process in the current thread
                self.__start_handling()
            return True

    def __start_handling(self) -> None:
        """ Manages communication with remote host, calls callback functions to let user introduce custom behaviour. """
        while self.connected:
            try:
                bnot = BNot.decode(self.__receive())  # Receive incoming message and convert it into Bartek's Notation
                resp = bnot.get('response', Simplex.RES_NULL)  # Get response type.
                # If server accepted client disconnection the client will receive a message to break the loop
                if resp == Simplex.RES_EXIT:
                    self.connected = False
                    Simplex.__lct = time()
                    self.on_exit()
                    if self.is_server:
                        # If server received disconnection request, response the same to let client know that he can
                        self.__share({'response': Simplex.RES_EXIT})
                    else:
                        self.__socket.close()           # If client received exit message (confirmation from server), close his socket
                        if self.__handling_thread is not None:
                             # Terminate handling thread for sure (break already does that).
                            self.__handling_thread.join()
                    break
                # If server responsed that he got the last message, call callback method and tell him that client got the information
                elif resp == Simplex.RES_OK:
                    # Activation switch, works only on the first OK message sent by server
                    if not self.__activated:
                        self.on_connect()
                        self.__activated = True
                    # Provide received data and get new to send
                    bnot = self.on_send(bnot, self.__sr_delta_time)
                    # If client wants to exit, include EXIT message (later sent to server) and reset the wish of disconnection boolean
                    if self.__wants_exit:
                        bnot.var('response', Simplex.RES_EXIT)
                        self.__wants_exit = False
                    else:
                        bnot.var('response', Simplex.RES_OK)
                    # If the current host wants to increase communication buffer, inform remote host about it.
                    sent_bytes = self.__share(bnot.data)
                    # If there are no bytes sent there was an error; initiate client wish of disconnection
                    if sent_bytes == 0:
                        if self.is_server:
                            self.__force_client_close()
                        else:
                            self.close()
                        break
                # If response has not been matched, it is broken thus communication is probably broken. Finish the handling loop
                else:
                    if not self.__activated:
                        self.on_refuse()  # If no OK message was received, client is not activated and thus connection was refused
                    self.on_exit()
                    self.__socket.close()
                    break
                    # Try-except block is for console purposes
            except KeyboardInterrupt:
                self.close()
        
