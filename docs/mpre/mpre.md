mpre
==============

 Stores global objects including instruction and the environment 

Alert_Handler
--------------

	 Provides the backend for the base.alert method. The print_level 
        and log_level attributes act as global levels for alerts; 
        print_level and log_level may be specified as command line arguments 
        upon program startup to globally control verbosity/logging. 


Instance defaults: 

	{'_deleted': False,
	 'delete_verbosity': 'vv',
	 'dont_save': False,
	 'log_is_persistent': False,
	 'log_level': '',
	 'log_name': 'Alerts.log',
	 'parse_args': True,
	 'print_level': '',
	 'replace_reference_on_load': True}

Method resolution order: 

	(<class 'mpre.Alert_Handler'>, <class 'mpre.base.Base'>, <type 'object'>)

Environment
--------------

	 Stores global state for the process. This includes reference 
        reference information, most importantly the objects dictionary. 


Method resolution order: 

	(<class 'mpre.Environment'>, <type 'object'>)

- **update**(self, environment):

		 Updates the fields of the environment. This is currently
            unused and may be deprecated. 


- **replace**(self, component, new_component):

		 Replaces the instance component with the specified new_component.
            The new_component will be obtain the replaced components
            instance_name reference. The old component should be garbage
            collected. 


- **add**(self, instance):

		 Adds an instance to the environment. This is done automatically
            for Base objects and for objects instantiated via the create
            method. 


- **display**(self):

		 Pretty prints environment attributes 


- **delete**(self, instance):

		 Deletes an object from the environment. This is called by
            instance.delete. 


Instruction
--------------

	 usage: Instruction(component_name, method_name, 
                           *args, **kwargs).execute(priority=priority,
                                                    callback=callback,
                                                    host_info=(ip, port))
                           
        Creates and executes an instruction object. 
            - component_name is the string instance_name of the component 
            - method_name is a string of the component method to be called
            - Positional and keyword arguments for the method may be
              supplied after the method_name.
              
        host_info may supply an ip address string and port number integer
        to execute the instruction on a remote machine. This requirements
        for this to be a success are:
            
            - The machine must have an instance of metapython running
            - The machine must be accessible via the network
            - The local machine must be registered and logged in to
              the remote machine
            - The local machine may need to be registered and logged in to
              have permission to the use the specific component and method
              in question
            - The local machine ip must not be blacklisted by the remote
              machine.
            - The remote machine may require that the local machine ip
              be in a whitelist to access the method in question.
              
        Other then the security requirements, remote procedure calls require 
        zero config on the part of either host. An object will be accessible
        if it exists on the machine in question.
              
        A priority attribute can be supplied when executing an instruction.
        It defaults to 0.0 and is the time in seconds until this instruction
        will actually be performed if the instruction is being executed
        locally. If the instruction is being executed remotely, this instead
        acts as a flag. If set to a True value, the instruction will be
        placed at the front of the local queue to be sent to the host.
        
        Instructions are useful for serial and explicitly timed tasks. 
        Instructions are only enqueued when the execute method is called. 
        At that point they will be marked for execution in 
        instruction.priority seconds or sent to the machine in question. 
        
        Instructions may be saved as an attribute of a component instead
        of continuously being instantiated. This allows the reuse of
        instruction objects. The same instruction object can be executed 
        any number of times.
        
        Note that Instructions must be executed to have any effect, and
        that they do not happen inline even if the priority is 0.0. In
        order to access the result of the executed function, a callback
        function can be provided.


Method resolution order: 

	(<class 'mpre.Instruction'>, <type 'object'>)

- **execute**(self, priority, callback, host_info, transport_protocol):

		 usage: instruction.execute(priority=0.0, callback=None,
                                       host_info=tuple())
        
            Submits an instruction to the processing queue. If being executed
            locally, the instruction will be executed in priority seconds. 
            An optional callback function can be provided if the return value 
            of the instruction is needed.
            
            host_info may be specified to designate a remote machine that
            the Instruction should be executed on. If being executed remotely, 
            priority is a high_priority flag where 0 means the instruction will
            be placed at the end of the rpc queue for the remote host in 
            question. If set, the instruction will instead be placed at the 
            beginning of the queue.
            
            Remotely executed instructions have a default callback, which is 
            the appropriate RPC_Requester.alert.
            
            The transport protocol flag is currently unused. Support for
            UDP and other protocols could be implemented and dispatched
            via this flag.