font = time = Surface = NotImplemented
import struct
import socket
from traceback import format_exc
from multiprocessing import cpu_count

SCREEN_SIZE = [800, 600]
R, G, B = 180, 180, 180
typeface = 'arial'
NO_ARGS = tuple()
NO_KWARGS = dict()
PROCESSOR_COUNT = 1#cpu_count()

# Base
Base = {"memory_size" : 8096,
"network_chunk_size" : 4096}

Process = Base.copy()
Process.update({"auto_start" : True, 
"network_buffer" : None,
"recurring" : False})

Thread = Base.copy()

Hardware_Device = Base.copy()

# machinelibrary

Timer = Base.copy()

Event_Handler = Hardware_Device.copy()
Event_Handler.update({"number_of_processors" : PROCESSOR_COUNT,
"idle_time" : .001})

Processor = Hardware_Device.copy()

Machine = Base.copy()
Machine.update({"status" : "",
"processor_count" : PROCESSOR_COUNT,
"hardware_configuration" : (("machinelibrary.Keyboard", NO_ARGS, NO_KWARGS), ),
"system_configuration" : (("systemlibrary.System", NO_ARGS, NO_KWARGS), )})

# inputlibrary
Keyboard = Hardware_Device.copy()

# systemlibrary
System = Base.copy()
System.update({"name" : "system",
"status" : "",
"hardware_configuration" : ("machinelibrary.Keyboard", ),
"startup_processes" : (("networklibrary.Network_Manager", NO_ARGS, NO_KWARGS),
                       ("eventlibrary.Task_Scheduler", NO_ARGS, NO_KWARGS))})

Task_Scheduler = Process.copy()

Application = Process.copy()
Application.update({"font" : (typeface, 16), 
"pack_mode" : "layer"})

Messenger = Application.copy()

Explorer = Application.copy()
Explorer.update({"time" : ""})

# interpreter
Shell = Process.copy()
Shell.update({"username" : "root", 
"password" : "password", 
"prompt" : ">>> ", 
"copyright" : 'Type "help", "copyright", "credits" or "license" for more information.', 
"definition" : False, 
"traceback" : format_exc, 
"backup_write" : None, 
"login_stage" : None, 
"auto_start" : False,
"auto_login" : True,
"host_name" : "localhost",
"port" : 40000,
"startup_definitions" : ''}) 

Shell_Service = Process.copy()
Shell_Service.update({"host_name" : "0.0.0.0", 
"port" : 40000, 
"prompt" : ">>> ", 
"copyright" : 'Type "help", "copyright", "credits" or "license" for more information.', 
"definition" : False, 
"traceback" : format_exc, 
"backup_write" : None}) 

# audiolibrary

Wav_File = Base.copy()
Wav_File.update({"mode" : "rb",
"filename" : "",
"repeat" : False})

PyAudio_Device = Base.copy()
PyAudio_Device.update({"format" : 8,
"frames_per_buffer" : 1024,
"data" : "",
"recording" : False})

Audio_Input = PyAudio_Device.copy()
Audio_Input.update({"input" : True})

Audio_Output = PyAudio_Device.copy()
Audio_Output.update({"output" : True, 
"mute" : False})

Audio_Configuration_Utility = Process.copy()
Audio_Configuration_Utility.update({"config_file_name" : "audiocfg",
"mode" : ("input",),
"auto_start" : False})

Audio_Manager = Process.copy()
Audio_Manager.update({"config_file_name" : "audiocfg"})

# networklibrary
Connection = Base.copy()
Connection.update({"socket_family" : socket.AF_INET, 
"socket_type" : socket.SOCK_STREAM})

Server = Connection.copy()
Server.update({"host_name" : "localhost", 
"port" : 0, 
"backlog" : 15,
"name" : "", 
"reuse_port" : 0,
"inbound_connection_type" : "networklibrary.Inbound_Connection"})
   
Outbound_Connection = Connection.copy()
Outbound_Connection.update({"as_port" : 0,
"timeout" : 10})
   
Inbound_Connection = Connection.copy()

Download = Outbound_Connection.copy()
Download.update({"filesize" : 0,
"filename" : '',
"filename_prefix" : "Download",
"download_in_progress" : False,
"network_chunk_size" : Outbound_Connection["network_chunk_size"] + len("dEL!M17&R"),
"delimiter" : "dEL!M17&R"})

Upload = Inbound_Connection.copy()
Upload.update({"use_mmap" : False,
"resource" : None,
"delimiter" : "dEL!M17&R"})

UDP_Socket = Base.copy()
UDP_Socket.update({"host_name" : "0.0.0.0",
"port" : 0,
"timeout" : 10})

# only addresses in the range of 224.0.0.0 to 230.255.255.255 are valid for IP multicast
Multicast_Beacon = Base.copy()
Multicast_Beacon.update({"packet_ttl" : struct.pack("b", 127),
"multicast_group" : "224.0.0.0", 
"multicast_port" : 1929})

Multicast_Receiver = Base.copy()
Multicast_Receiver.update({"listener_address" : "0.0.0.0",
"multicast_group" : "224.0.0.0",
"port" : 0})

Basic_Authentication_Client = Thread.copy()

Basic_Authentication = Thread.copy()
Network_Manager = Process.copy()

Service_Listing = Process.copy()

Scanner = Process.copy()
Scanner.update({"subnet" : "127.0.0.1",
"ports" : (22, ),
"range" : (0, 0, 0, 254),
"timeout" : 10,
"priority" : "high"})

# File transfer utility
File_Transfer_Utility = Base.copy()
File_Transfer_Utility.update({"port" : 40004})


# Guilibrary
Display = Process.copy()
Display.update({"x" : 0, 
'y' : 0, 
"size" : SCREEN_SIZE, 
"layer" : 0, 
"max_layer" : 0, 
"drawing" : False})

# Widgets
# these are the required attributes for a fully draw-able object
Gui_Object = Base.copy()
Gui_Object.update({'x' : 0, 
        'y' : 0, 
        'size' : SCREEN_SIZE, 
        "layer" : 1, 
        "color" : (R, G, B), 
        "outline" : 5, 
        "popup" : False, 
        "pack_mode" : None, 
        "typeface" : (typeface, 16), 
        "pack_modifier" : None, 
        "color_scalar" : .6})

Window = Gui_Object.copy()
Window.update({"title_bar" : False, 
"pack_mode" : "layer"})

Container = Window.copy()
Container.update({"alpha" : 1, 
        "pack_mode" : "vertical"})

Button = Container.copy()
Button.update({"shape" : "rect"})

Popup_Window = Window.copy()
Popup_Window.update({"popup" : True, 
        "pack_modifier" : lambda parent, child: setattr(child, "position", (SCREEN_SIZE[0]/2, SCREEN_SIZE[1]/2))})

File_Menu = Popup_Window.copy()
File_Menu.update({"pack_mode" : "vertical", 
        "pack_modifier" : lambda parent, child: setattr(child, "y", child.y+parent.size[1])})

Right_Click_Menu = Popup_Window.copy()
Right_Click_Menu.update({"pack_mode": "layer", 
"size" : (SCREEN_SIZE[0]/2, SCREEN_SIZE[1]/2)})

Homescreen = Window.copy()
Homescreen.update({"background_filename" : "C:\\test.jpg"})

Property_Editor = Window.copy()
Property_Editor.update({"pack_modifier" : lambda parent, child:\
setattr(child, "position", (SCREEN_SIZE[0]/2, SCREEN_SIZE[1]/2))})

Menu_Bar = Container.copy()
Menu_Bar.update({"pack_mode" : "menu_bar"})

Title_Bar = Menu_Bar.copy()
Title_Bar.update({"pack_modifier" : lambda parent, child:\
setattr(child, "y", child.y+child.size[1])})

Task_Bar = Menu_Bar.copy()
Task_Bar.update({"pack_modifier" : lambda parent, child:\
setattr(child, "y", (parent.y+parent.size[1])-child.size[1])\
}) # ^ aligns the bottom left corners of the parent and child object

Date_Time = Button.copy()
Date_Time.update({"pack_mode" : "horizontal"})

Help_Bar = Button.copy()
Help_Bar.update({"pack_mode" : "horizontal"})

Property_Button = Button.copy()
Property_Button.update({"property" : None, 
"display" : False})

File_Button = Button.copy()
File_Button.update({"display" : False})

Text_Line = Button.copy()
Text_Line.update({"edit_mode" : False})

Text_Character = Button.copy()
Text_Character.update({"text" : "", 
        "pack_mode" : "text", 
        "outline" : 0})