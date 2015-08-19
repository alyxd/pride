import traceback
import json

import mpre
import mpre.base
import mpre.network
import mpre.networkssl
import mpre.authentication
import mpre.persistence
objects = mpre.objects

def packetize_send(send):
    def _send(self, data):
        return send(self, str(len(data)) + ' ' + data)   
    return _send
    
def packetize_recv(recv):
    def _recv(self, buffer_size=0):
        data = recv(self, buffer_size)
        packets = []
        while data:
            try:
                packet_size, data = data.split(' ', 1)
            except ValueError:
                self._old_data = data
                break
            packet_size = int(packet_size)
            packets.append(data[:packet_size])
            data = data[packet_size:]   
        return packets    
    return _recv
    
class Session(object):
    
    def _get_context(self):
        return self.id, self.host_info
    context = property(_get_context)
    
    def __init__(self, session_id, host_info):
        self.id = session_id
        self.host_info = host_info
        if host_info not in hosts:
            hosts[host_info] = self.create(Host, host_info=host_info)
            
    def execute(self, instruction, callback):
        request = ' '.join((self.id, instruction.component_name,
                            instruction.method, 
                            json.dumps((instruction.args, instruction.kwargs))))
        hosts[self.host_info].requester.make_request(request, callback)
        
        
class Host(mpre.authentication.Authenticated_Client):
            
    defaults = mpre.authentication.Authenticated_Client.defaults.copy()
    
    def _get_host_info(self):
        return (self.ip, self.port)
    def _set_host_info(self, value):
        self.ip, self.port = value
    host_info = property(_get_host_info, _set_host_info)
    
    def __init__(self, **kwargs):
        super(Host, self).__init__(**kwargs)
        host_info = self.host_info
        hosts[host_info] = self
        self.requester = self.create("mpre.rpc.Rpc_Requester", 
                                     host_info=host_info,).instance_name
        
    def delete(self):
        del mpre.hosts[self.host_info]
        super(Host, self).delete()
        
        
class Session_Manager(mpre.base.Base):
    
    defaults = mpre.base.Base.defaults.copy()
    defaults.update({"session_id" : '0',
                     "host_info" : tuple()})
    
    def _get_current(self):
        return self.session_id, self.host_info
    def _set_current(self, value):
        self.session_id, self.host_info = value
    current_session = property(_get_current, _set_current)
        
            
class Packet_Client(mpre.networkssl.SSL_Client):
            
    defaults = mpre.networkssl.SSL_Client.defaults.copy()
    defaults.update({"_old_data" : bytes()})
    
    @packetize_send
    def send(self, data):
        return super(Packet_Client, self).send(data)
    
    @packetize_recv
    def recv(self, buffer_size=0):
        return super(Packet_Client, self).recv(buffer_size)      
        
        
class Packet_Socket(mpre.networkssl.SSL_Socket):
            
    defaults = mpre.networkssl.SSL_Socket.defaults.copy()
    defaults.update({"_old_data" : bytes()})
    
    @packetize_send
    def send(self, data):
        return super(Packet_Socket, self).send(data)
    
    @packetize_recv
    def recv(self, buffer_size=0):        
        return super(Packet_Socket, self).recv(buffer_size)
                       
            
class Packet_Server(mpre.networkssl.SSL_Server):
    
    defaults = mpre.networkssl.SSL_Server.defaults.copy()
    defaults.update({"Tcp_Socket_type" : Packet_Socket})
        
            
        
class Rpc_Client(Packet_Client):
            
    defaults = Packet_Client.defaults.copy()
        
    def on_ssl_authentication(self):
        for request, callback in self._requests:
            self.send(request)
            self.callbacks.append(callback)       
        
    def make_request(self, request, callback):
        if not self.ssl_authenticated:
            self._requests.append((request, callback))
        else:    
            self.send(request)
            self.callbacks.append(callback)
        
    def recv(self, packet_count=0):
        for response in super(Rpc_Client, self).recv():
            self.callbacks.pop(0)(self.deserealize(response))
            
        
class Rpc_Socket(Packet_Socket):
            
    defaults = Packet_Socket.defaults.copy()
    
    def on_connect(self):
        self._peername = self.getpeername()
        super(Rpc_Socket, self).on_connect()
        
    def recv(self, packet_count=0):
        peername = self._peername
        environment_access = mpre.objects["Environment_Access"]
        session_manager = mpre.objects["Session_Manager"]
        
        for packet in super(Rpc_Socket, self).recv():
            (channel_session_id, application_session_id, 
             component_name, method, 
             serialized_arguments) = packet.split(' ', 4)
             
            permission = False
            if channel_session_id == '0': 
                if (method in ("register", "login") and 
                    component_name == "Environment_Access"):
                    
                    permission = True
            else:
                session_manager.current_sesion = (channel_session_id, _peername)
                if (permission or 
                    environment_access.validate()):
                    
                    session_manager.current_session = (application_session_id,
                                                       _peername)
                    try:
                        args, _kwargs = self.deserealize(serialized_arguments)
                        instance = mpre.objects[component_name]
                        result = getattr(instance, method)(*args, **kwargs)
                    except BaseException as error:
                        self.alert("Error processing request: \n{}",
                                   [error], level=0)
                        result = error
                    response = self.serealize(result)
                    self.send(response)
                    
    def deserealize(self, serialized_arguments):
        return json.loads(serialized_arguments)
        
    def serealize(self, result):
        return json.dumps(result)

        
class Environment_Access(mpre.authentication.Authenticated_Service):
    
    defaults = mpre.authentication.Authenticated_Service.defaults.copy()
    defaults.update({"allow_registration" : True})
    
    def __init__(self, **kwargs):
        super(Environment_Access, self).__init__(**kwargs)
        self.create("mpre.rpc.Rpc_Server")
        self.create("mpre.rpc.Session_Manager")
    @mpre.authentication.whitelisted
    @mpre.authentication.authenticated
    def validate(self):
        # presuming the host info passed the checks done by the above decorators,
        # the host will have permission to use the environment. 
        return True
        
    @mpre.authentication.whitelisted
    def login(self, username, credentials):
        auth_token, host_info = $Session_Manager.current_session
        if (username == "localhost" and 
            host_info[0] not in ("localhost", "127.0.0.1")):
            
            self.alert("Detected login attempt by username 'localhost'" + 
                       "from non local endpoint {}", (host_info, ))
            raise UnauthorizedError()
        return super(Environment_Access, self).login(username, credentials)
        
        
class Environment_Access_Client(mpre.authentication.Authenticated_Client):
    
    defaults = mpre.authentication.Authenticated_Client.defaults.copy()
    defaults.update({"target_service" : "Environment_Access",
                     "username" : "",
                     "password" : ""})             

        
class RPC_Server(mpre.networkssl.SSL_Server):
    
    defaults = mpre.networkssl.SSL_Server.defaults.copy()
    defaults.update({"port" : 40022,
                     "interface" : "localhost",
                     "Tcp_Socket_type" : "mpre.rpc.RPC_Request"})
    