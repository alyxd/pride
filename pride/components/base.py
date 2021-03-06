""" Contains The root inheritance objects that provides many features of the package. """

import copy
import operator
import itertools
import sys
import heapq
import pprint
import inspect
import importlib
from six import with_metaclass

import pride
import pride.components.metaclass
import pride.functions.utilities as utilities
import pride.functions.contextmanagers
import pride.functions.module_utilities
from pride.errors import *
from pride.components import deep_update

__all__ = ["DeleteError", "AddError", "load", "Base", "Reactor", "Wrapper", "Proxy"]

def rebuild_object(saved_data):
    """ usage: load(saved_data) => restored_instance, attributes """
    #user = pride.objects["/User"]
    #attributes = user.load_data(saved_data)
    #repo_id = user.generate_tag(user.username)
    #version_control = pride.objects["/Program/Version_Control"]
    #_required_modules = []
    #module_info = attributes.pop("_required_modules")
    #class_name = saved_data["_required_modules"].pop()
    #module_object = importlib.import_module(module_info[-1])
    #for module_name in module_info:
        #source = version_control.load_module(module_name, module_id, repo_id)
        #module_object = pride.functions.module_utilities.create_module(module_name, source)
    #    _required_modules.append((module_name, module_id, module_object))
    saved_data = utilities.load_data(saved_data)
    module_name, class_name = saved_data.pop("_type_info")
    module_object = importlib.import_module(module_name)
    self_class = getattr(module_object, class_name)
    #attributes["_required_modules"] = _required_modules

    self = self_class.__new__(self_class)
    return self, saved_data

def restore_attributes(new_self, attributes):
    """ Loads and instance from a bytestream or file produced by pride.components.base.Base.save.
        Currently being reimplemented"""

    saved_objects = attributes["objects"]
    assert not attributes["objects"]
    objects = attributes["objects"] = {}
    print repr(new_self), "restoring"
    for instance_type, saved_instances in saved_objects.items():
        assert saved_instances
        objects[instance_type] = [load(instance) for instance in saved_instances]
    import pprint
    pprint.pprint(objects)

    attribute_modifier = attributes.pop("_attribute_type")
    for key, value in attributes.items():
        modifier = attribute_modifier.get(key, '')
        if modifier == "reference":
            attributes[key] = pride.objects[value]
        elif modifier == "save":
            attributes[key] = load(value)
    print repr(new_self), "Calling on load"
    new_self.on_load(attributes)
    return new_self

def load(saved_object):
    raise NotImplementedError()
    new_self, attributes = rebuild_object(saved_object)
    return restore_attributes(new_self, attributes)

class Base(with_metaclass(pride.components.metaclass.Metaclass, object)):
    """ The root inheritance object. Provides many features:

    - When instantiating, arbitrary attributes may be assigned
          via keyword arguments

        - The class includes a defaults attribute, which is a dictionary
          of name:value pairs. These pairs will be assigned as attributes
          to new instances; Any attribute specified via keyword argument
          will override a default

        - A reference attribute, which provides access to the object from any context.
            - References are human readable strings indicating the name of an object.
            - References are mapped to objects in the pride.objects dictionary.
            - An example reference looks like "/Program/File_System".
            - Initial objects have no number appended to the end. The 0 is implied.
                - Explicit is better then implicit, but for some objects, it
                  makes no sense to have multiple copies, so enumerating them
                  accomplishes nothing.
            - Subsequent objects have an incrementing number appended to the end.

        - The flag parse_args=True may be passed to the call to
          instantiate a new object. If so, then the metaclass
          generated parser will be used to interpret command
          line arguments. Only command line arguments that are
          in the class defaults dictionary will be assigned to
          the new instance. Arguments by default are supplied
          explicitly with long flags in the form --attribute value.
          Arguments assigned via the command line will override
          both defaults and any keyword arg specified values.
          Consult the parser defintion for further information,
          including using short/positional args and ignoring attributes.

        - The methods create/delete, and add/remove:
            - The create method returns an instantiated object and
              calls add on it automatically. This performs book keeping
              with the environment regarding references and parent information.
            - The delete method is used to explicitly destroy a component.
              It calls remove internally to remove known locations
              where the object is stored and update any tracking
              information in the environment

        - The alert method, which makes logging and statements
          of varying verbosity simple and straight forward.
            - The verbosity class dictionary is the ideal place to store
              and dispatch alert levels, rather then hardcoding them.

        - Augmented docstrings. Information about class defaults
          and method names + argument signatures + method docstrings (if any)
          is included automatically when you print base_object.__doc__.

        - Inherited class attributes. Attributes such as the class defaults
          dictionary are automatically inherited from their ancestor class.
            - This basically enables some syntatic sugar when declaring classes,
              in that defaults don't need to be declared as a copy of the ancestor
              classes defaults explicitly.
            - Attributes that are inherited on all Base objects are:
                - defaults
                - mutable_defaults
                - predefaults
                - verbosity
                - parser_args
                - required_attributes
                - site_config_support
            - Supported attributes are extensible when defining new classes.

        - Site config support. Using the site_config module, the values of any
          accessible class attributes may be modified to customize the needs
          of where the software is deployed.
            - The attributes that are supported by default on all Base objects are:
                - defaults
                - mutable_defaults
                - predefaults
                - verbosity
            - This list is extensible when defining a new class

    Note that some features are facilitated by the metaclass. These include
    the argument parser, inherited class attributes, and documentation.

    How to use references
    ------------
    Bad:

        my_base_object.other_base_object = other_base_object

    Good:

        my_base_object.add(other_base_object)

    Also good:

        my_base_object.other_base_object = other_base_object.reference

    In the first case, the other_base_object attribute stores a literal object in
    the objects __dict__. This is a problem because the environment has no way
    of (efficiently) detecting that you have saved a reference to another
    object when the object is simply assigned as an attribute. This can cause
    memory leaks when you try to delete other_base_object or my_base_object.

    In the second case, the add method is used to store the object. The add
    method performs reference tracking information so that when my_base_object is
    deleted, other_base_object will automatically be removed, eliminating reference
    problems which can/will cause one object or both to become uncollectable
    by the garbage collector.

    By default, the add method stores objects in the my_base_object.objects
    dictionary. The add method is extensible, so for example, if your object
    has lots of one type of object added to it, you can simply append the
    object to a list in the add method, but remember to call the base class
    add as well if you do (via super). This is because add does reference
    tracking as well as storing the supplied object. You would then access the
    stored objects via enumerating the list you stored them all in and
    operating on them in a batch.

    In the third case, the object is not saved, just the objects reference.
    This is good because it will avoid the hanging reference problem that can
    cause memory leaks. This will work well when my_base_object only has the one
    other_base_object to keep track of. other_base_object is then accessed by
    looking up the reference in the pride.objects dictionary.

    base.children returns an iterator over the child objects; If you intend to
    delete all child objects, use the delete_children method."""

    # certain container type class attributes are "inherited" from base classes
    # these include defaults, required_attributes, mutable_defaults, verbosity
    # parser_args, and predefaults (all of which are explained below and above)
    # when subclassing, creating new class defaults will automatically merge the
    # newly specified defaults with the base class defaults, and similarly so for each
    # attribute inherited this way.

    # the defaults attribute sets what attributes new instances will initialize with
    # they can be overridden when initialized an object via keyword arguments
    # PITFALL: do not use mutable objects as a default. use mutable_defaults instead
    defaults = {"dont_save" : False, "parse_args" : False,
                "replace_reference_on_load" : True}

    # if certain attributes must be passed explicitly, including them in the
    # required_attributes class attribute will automatically raise an
    # ArgumentError when they are not supplied.
    required_attributes = tuple()

    # mutable objects should not be included as defaults attributes
    # for the same reason they should not be used as default arguments
    # the type associated with the attribute name will be instantiated with
    # no arguments when the object initializes
    mutable_defaults = {}

    # defaults have a pitfall that can be a problem in certain cases;
    # because dictionaries are unordered, the order in which defaults
    # are assigned cannot be guaranteed.
    # predefaults are guaranteed to be assigned before defaults.
    predefaults = {"deleted" : False}

    # verbosity is an inherited class attribute used to store the verbosity
    # level of a particular message.
    verbosity = {"delete" : "vv", "initialized" : "vv", "remove" : "vv",
                 "add" : "vv", "update" : "v", "save" : "vv"}

    auto_verbosity_ignore = ("alert", )

    # A command line argument parser is generated automatically for
    # every Base class based upon the attributes contained in the
    # class defaults dictionary. Specific attributes can be modified
    # or added by specifying them in class.parser_modifiers and
    # class.parser_args.

    # parser modifiers are attribute : options pairs, where options
    # is a dictionary. The keys may include any keyword arguments
    # that (mostly) are used by argparse.ArgumentParser.add_argument. Most
    # relevent are the "types" and "nargs" options.
    # `types` is processed by the metaclass rather than argparse.ArgumentParser
    # `types` is a tuple that specifies that the argument should be `"positional"`,
    # -s short style, or --long long style flags. e.g. ("short", "long")
    # nargs indicates the number of expected
    # arguments for the flag in question. Note that attributes default to
    # using --long style flags.
    # exit_on_help determines whether or not to quit when the --help flag
    # is specified as a command line argument
    parser_modifiers = {"exit_on_help" : True}
    parser_args = tuple() # names in parser_args enables parsing that attribute from the command line

    site_config_support = ("defaults", "verbosity", "predefaults", "mutable_defaults")

    # key : values pairs; if getattr(self, key) not in values, raises ValueError in __init__
    allowed_values = {}

    # stores names
    # the instance attribute indicated by 'name' is configured to store/dereference objects/references of the specified type
    # Solves the following problem/automates the following pattern:
    #   # (the problem)
    #   self.component = self.create(Base_object)
    #   self.delete()
    #   # self.component still holds a reference to the Base_object that was created
    #   # this can prevent it from being garbage collected
    #
    #   # (the pattern that solves the problem)
    #   self.component = self.create(Base_object).reference # store a reference instead of the object
    #   self.delete()
    #   # the created Base_object is not stored in self.component, so it can be deleted
    #
    #   # (the problem with the pattern)
    #   self.component = self.create(Base_object).reference
    #   # (at some other point in the code...)
    #   component = pride.objects[self.component]
    #   # must dereference component before it can be used - can clutter up code
    #
    #
    #   # autoreferences solve the problem while retaining the cleaner-looking code of the problematic example
    #   class Demo(pride.components.base.Base):
    #       autoreferences = {"component" : any}
    #
    #       def __init__(self, **kwargs):
    #           super(Demo, self).__init__(**kwargs)
    #           self.component = self.create("pride.components.base.Base") # is actually storing a reference
    #
    #       def do_something(self):
    #           component = self.component # no need to dereference; it's already been done
    #           component.do_thing1()
    #           component.do_thing2()
    autoreferences = tuple()

    subcomponents = dict()

    def _get_parent(self):
        return objects[self.parent_name] if self.parent_name else None
    parent = property(_get_parent)

    def _get_children(self):
        return (child for child in itertools.chain(*self.objects.values()) if child)
    children = property(_get_children)

    post_initializer = ''

    def __init__(self, **kwargs):
        super(Base, self).__init__() # facilitates complicated inheritance - otherwise does nothing
        self.references_to = []
        parent_name = self.parent_name = pride._last_creator
        # the following line fixes a bug where:
        #       base object A creates base object B
        #       base object B instantiates base object C (not via 'create')
        #       base object C would become a child of base object A
        pride._last_creator = ''
        instance_count = 0
        _name = name = parent_name + "/" + self.__class__.__name__
        while name in objects:
            instance_count += 1
            name = _name + str(instance_count)

        self.reference = name
        objects[self.reference] = self

        # the objects attribute keeps track of instances created by this self
        self.objects = {}

        for attribute, value_type in self.mutable_defaults.items():
            if attribute not in kwargs:
                setattr(self, attribute, value_type())

        subcomponents = self.subcomponents
        for attribute, value in itertools.chain(self.predefaults.items(),
                                                self.defaults.items(),
                                                kwargs.items()):
            if attribute in kwargs:
                if (attribute[-len("_kwargs"):] == "_kwargs" and
                    attribute.rsplit('_', 1)[0] in subcomponents):
                    continue
                setattr(self, attribute, kwargs.pop(attribute))
            else:
                setattr(self, attribute, value)

        if subcomponents:
            for name, component in self.subcomponents.items():
                value = copy.deepcopy(component.kwargs)
                _type = component.type
                attribute = "{}_kwargs".format(name)
                setattr(self, attribute, value)
                if attribute in kwargs:
                    new_value = kwargs.pop(attribute)
                    deep_update(value, new_value)

                attribute = "{}_type".format(name)
                if not hasattr(self, attribute):
                    setattr(self, attribute, _type)

        if self.parse_args:
            command_line_args = self.parser.get_options()
            defaults = self.defaults
            for key, value in ((key, value) for key, value in
                                command_line_args.items() if
                                value != defaults[key]):
                setattr(self, key, value)

        if self.required_attributes:
            for attribute in self.required_attributes:
                try:
                    if not getattr(self, attribute):
                        raise ArgumentError("{}: Required attribute '{}' has falsey value".format(self.reference, attribute))
                except AttributeError:
                    if hasattr(self, attribute):
                        raise
                    import pprint # note: subcomponents above pops from kwargs
                    pprint.pprint(kwargs)
                    raise ArgumentError("{}: Required attribute '{}' not assigned".format(self.reference, attribute))

        if self.allowed_values:
            for key, values in self.allowed_values.items():
                if getattr(self, key) not in values:
                    raise ValueError("Invalid {} value: '{}'; Valid values: {}".format(key, getattr(self, key), values))

        if self.parent:
            self.parent.add(self)

        try:
            self.alert("Initialized", level=self.verbosity["initialized"])
        except (AttributeError, KeyError):
            # Alert handler can not exist in some situations or not have its log yet
            pass

        if self.post_initializer:
            getattr(self, self.post_initializer)()

    def create(self, instance_type, *args, **kwargs):
        """ usage: object.create(instance_type, args, kwargs) => instance

            Given a type or string reference to a type and any arguments,
            return an instance of the specified type. The creating
            object will call .add on the created object, which
            performs reference tracking maintenance.

            Returns the created object.
            Note, instance_type could conceivably be any callable, though a
            class is usually supplied.

            If create is overloaded, ensure that ancestor create is called
            as well via super."""
        with pride.functions.contextmanagers.backup(pride, "_last_creator"):
            pride._last_creator = self.reference
            try:
                instance = instance_type(*args, **kwargs)
            except TypeError:
                if isinstance(instance_type, type) or hasattr(instance_type, "__call__"):
                    raise
                instance = utilities.resolve_string(instance_type)(*args, **kwargs)
        return instance

    def delete(self):
        """usage: object.delete()

            Explicitly delete a component. This calls remove and
            attempts to clear out known references to the object so that
            the object can be collected by the python garbage collector.

            The default alert level for object deletion is 'vv'

            If delete is overloaded, ensure that ancestor delete is called as
            well via super."""
        self.alert("Deleting", level=self.verbosity["delete"])
        if self.deleted:
            raise DeleteError("{} has already been deleted".format(self.reference))

        self.delete_children()

        if self.references_to:
            # make a copy, as remove will mutate self.references_to
            for name in self.references_to[:]:
                objects[name].remove(self)
        del objects[self.reference]
        self.deleted = True

    def delete_children(self):
        while any(self.objects.values()):
            keys = self.objects.keys()
            for key in keys:
                values = self.objects[key]
                while values:
                    for child in values:
                        child.delete()
        assert not list(self.children)
        #children = list(self.children)
        #while children:
        #    for child in children:
        #        try:
        #            child.delete()
        #        except DeleteError:
        #            if self.reference in child.references_to:
        #                raise
        #    children = list(self.children)

#        for child in list(self.children):
#            try:
#                child.delete()
#            except DeleteError:
#                if self.reference in child.references_to:
#                    raise

    def add(self, instance):
        """ usage: object.add(instance)

            Adds an object to caller.objects[instance.__class__.__name__] and
            notes the reference location.

            The default alert level for add is 'vv'

            Raises AddError if the supplied instance has already been added to
            this object.

            If overloading the add method, ensure super is called to invoke the
            ancestor version that performs bookkeeping.

            Make sure to overload remove if you modify add (if necessary)"""
        self.alert("Adding: {}".format(instance), level=self.verbosity["add"])
        self_objects = self.objects
        instance_class = type(instance).__name__
        try:
            siblings = self_objects[instance_class]
        except KeyError:
            self_objects[instance_class] = siblings = [instance]
        else:
            if instance in siblings:
                raise AddError
            siblings.append(instance)

        instance.references_to.append(self.reference)

    def remove(self, instance):
        """ Usage: object.remove(instance)

            Removes an instance from self.objects. Modifies object.objects
            and instance.references_to.

            The default alert level for object removal is 'vv'"""
        self.alert("Removing {}".format(instance), level=self.verbosity["remove"])
        self.objects[type(instance).__name__].remove(instance)
        instance.references_to.remove(self.reference)

    def alert(self, message, level=0, display_name=''):
        """usage: base.alert(message, level=0, display_name='')

        Display/log a message according to the level given. The alert may
        be printed for immediate attention and/or logged, depending on
        the current Alert_Handler print_level and log_level.

        - message is a string that will be logged and/or displayed
        - level is an integer indicating the severity of the alert.
        - display_name is a string that should be in place of the component name
        alert severity is relative to Alert_Handler log_level and print_level;
        a lower verbosity indicates a less verbose notification, while 0
        indicates a message that should not be suppressed. log_level and
        print_level may passed in as command line arguments to globally control verbosity.

        An objects verbosity can be modified via the site_config module. """
        alert_handler = objects["/Alert_Handler"]
        message = "{}: {}".format(display_name or self.reference, message)
        if level in alert_handler._print_level or level is 0 or "debug" in alert_handler._print_level:
            sys.stdout.write(message + "\n")
            sys.stdout.flush()
        if level in alert_handler._log_level or level is 0 or "debug" in alert_handler._log_level:
            alert_handler.append_to_log(message, level)

    def __getstate__(self):
        return self.__dict__.copy()

    def __setstate__(self, state):
        self.on_load(state)

    def __str__(self):
        assert self.reference is not None
        return self.reference

    def save(self, _file=None):
        """ usage: base_object.save(_file=None)

            Saves the state of the calling objects __dict__. If _file is not
            specified, a serialized stream is returned. If _file is specified,
            the stream is written to the supplied file like object and then
            returned.

            This method and load are being reimplemented"""
        raise NotImplementedError()
        self.alert("Saving", level=self.verbosity["save"])
        attributes = self.__getstate__()
        self_objects = attributes.pop("objects", {})
        saved_objects = attributes["objects"] = {}
        found_objects = []
        for component_type, values in self_objects.items():
            saved_objects[component_type] = new_values = []
            for value in sorted(values, key=operator.attrgetter("reference")):
                if hasattr(value, "save"):
                    found_objects.append(value)
                    if not getattr(value, "dont_save", False):
                        new_values.append(value.save())

        attribute_type = attributes["_attribute_type"] = {}
        for key, value in attributes.items():
            if value in found_objects:
                attributes[key] = value.reference
                attribute_type[key] = "reference"
            elif hasattr(value, "save") and not getattr(value, "dont_save"):
                attributes[key] = value.save()
                attribute_type[key] = "saved"

        #required_modules = pride.functions.module_utilities.get_all_modules_for_class(type(self))
        #version_control = objects["/Program/Version_Control"]
        #user = objects["/User"]
        #hash_function = user.generate_tag
        #repo_id = hash_function(user.username)
        #_required_modules = []
        #for module_name, source, module_object in required_modules:
            #module_id = hash_function(source)
            #version_control.save_module(module_name, source, module_id, repo_id)
            #_required_modules.append(module_name)

        #attributes["_required_modules"] = _required_modules + [self.__class__.__name__]
        attributes["_type_info"] = (self.__module__, self.__class__.__name__)
        #try:
        #    saved_data = pride.objects["/User"].save_data(attributes)
        #except TypeError:
        #    self.alert("Unable to save attributes '{}'".format(pprint.pformat(attributes)), level=0)
        #    raise
        saved_data = utilities.save_data(attributes)
        if _file:
            _file.write(saved_data)
        return saved_data

    load = staticmethod(load)

    def on_load(self, attributes):
        """ usage: base.on_load(attributes)

            Implements the behavior of an object after it has been loaded.
            This method may be extended by subclasses to customize
            functionality for instances created by the load method. Often
            times this will implement similar functionality as the objects
            __init__ method does (i.e. opening a file or database).

            NOTE: Currently being reimplemented"""
        raise NotImplementedError()
        [setattr(self, key, value) for key, value in attributes.items()]

        if self.replace_reference_on_load:
            #print "Replacing instance", self
            pride.objects[self.reference] = self
            #print "Done"
        self.alert("Loaded", level='v')

    def update(self, update_children=False, _already_updated=None):
        """usage: base_instance.update() => updated_base

           Reloads the module that defines base and returns an updated
           instance. The old component is replaced by the updated component
           in the environment. Further references to the object via
           reference will be directed to the new, updated object.
           Attributes of the original object will be assigned to the
           updated object.

           Note that modules are preserved when update is called. Any
           modules used in the updated class will not necessarily be the
           same as the modules in use in the current global scope.

           The default alert level for update is 'v'

           Potential pitfalls:

                - Classes that instantiate base objects as a class attribute
                  will produce an additional object each time the class is
                  updated. Solution: instantiate base objects in __init__ """
        raise NotImplementedError()
        self.alert("Beginning Update ({})...".format(id(self)), level=self.verbosity["update"])
        _already_updated = _already_updated or [self.reference]
        class_base = utilities.updated_class(type(self))
        class_base._required_modules.append(self.__class__.__name__)
        new_self = class_base.__new__(class_base)
        for attribute, value in ((key, value) for key, value in
                                 self.__dict__.items() if key not in
                                 self.__class__.__dict__):
            setattr(new_self, attribute, value)
        if not hasattr(new_self, "reference"):
            new_self.reference = self.reference
        if not hasattr(new_self, "references_to"):
            new_self.references_to = self.references_to[:]

        assert "reference" not in self.__class__.__dict__, self.__class__.__dict__
        assert hasattr(self, "reference"), pprint.pformat(self.__dict__)
      #  assert "reference" in self.__dict__, pprint.pformat(self.__dict__.keys())
        assert hasattr(new_self, "reference"), pprint.pformat(new_self.__dict__)
        references = self.references_to[:]
        for reference in references:#self.references_to[:]:
            _object = pride.objects[reference]
            _object.remove(self)
        for reference in references:
            _object = pride.objects[reference]
            _object.add(new_self)

        pride.objects[self.reference] = new_self
        if update_children:
            for child in self.children:
                if child.reference not in _already_updated:
                    _already_updated.append(child.reference)
                    child.update(True, _already_updated)
        self.alert("... Finished updating", level=0)
        return new_self


class Wrapper(Base):
    """ A wrapper to allow 'regular' python objects to function as a Base.
        The attributes on this wrapper will overload the attributes
        of the wrapped object. Any attributes not present on the wrapper object
        will be gotten from the underlying wrapped object. This class
        acts primarily as a wrapper and secondly as the wrapped object.
        This allows easy preemption/overloading/extension of methods by
        defining them.

        The class supports a "wrapped_object_name" attribute. When creating
        a new class of wrappers,  wrapped object can be made available as
        an attribute using the name given. If this attribute is not assigned,
        then the wrapped object can be accessed via the wrapped_object attribute"""

    defaults = {"wrapped_object" : None}

    wrapped_object_name = ''

    auto_verbosity_ignore = ("wraps", )

    def __init__(self, **kwargs):
        super(Wrapper, self).__init__(**kwargs)
        if self.wrapped_object is not None:
            self.wraps(self.wrapped_object)

    def __getattr__(self, attribute):
        try:
            return getattr(self.wrapped_object, attribute)
        except AttributeError:
            raise AttributeError("'{}' object has no attribute '{}'".format(type(self.wrapped_object).__name__, attribute))

    def wraps(self, _object):
        """ Sets the specified object as the object wrapped by this object. """
        assert _object is not self
        assert _object is not None
        self.wrapped_object = _object
        if self.wrapped_object_name:
            setattr(self, self.wrapped_object_name, _object)


class Proxy(Base):
    """ usage: Proxy(wrapped_object=my_object) => proxied_object

       Produces an instance that will act as the object it wraps and as an
       Base object simultaneously. The object will act primarily as
       the wrapped object and secondly as a Proxy object. This means that
       Proxy attributes are get/set on the underlying wrapped object first,
       and if that object does not have the attribute or it cannot be
       assigned, the action is performed on the proxy instead. This
       prioritization is the opposite of the Wrapper class.

       This class also supports a wrapped_object_name attribute. See
       Base.Wrapper for more information."""

    wrapped_object_name = ''
    auto_verbosity_ignore = ("wraps", )

    def __init__(self, **kwargs):
        wraps = super(Proxy, self).__getattribute__("wraps")
        try:
            wrapped_object = kwargs.pop("wrapped_object")
        except KeyError:
            pass
        else:
            wraps(wrapped_object)
        super(Proxy, self).__init__(**kwargs)

    def wraps(self, _object):
        """ usage: wrapper.wraps(object)

            Makes the supplied object the object that is wrapped
            by the Proxy. """
        set_attr = super(Proxy, self).__setattr__
        set_attr("wrapped_object", _object)
        if self.wrapped_object_name:
            set_attr(self.wrapped_object_name, _object)

    def __getattribute__(self, attribute):
        try:
            wrapped_object = super(Proxy, self).__getattribute__("wrapped_object")
            value = super(type(wrapped_object), wrapped_object).__getattribute__(attribute)
        except AttributeError:
            value = super(Proxy, self).__getattribute__(attribute)
        return value

    def __setattr__(self, attribute, value):
        super_object = super(Proxy, self)
        try:
            wrapped_object = super_object.__getattribute__("wrapped_object")
            super(type(wrapped_object), wrapped_object).__setattr__(attribute, value)
        except AttributeError:
            super_object.__setattr__(attribute, value)


class Adapter(Base):
    """ Modifies the interface of the wrapped object. Effectively supplies
        the keys in the adaptations dictionary as attributes. The value
        associated with that key in the dictionary is the corresponding
        attribute on the wrapped object that has the appropriate value. """
    adaptations = {}

    wrapped_object_name = ''
    auto_verbosity_ignore = ("wraps", )

    def __init__(self, **kwargs):
        if "wrapped_object" in kwargs:
            self.wraps(kwargs.pop("wrapped_object"))
        else:
            self.wrapped_object = None
        super(Adapter, self).__init__(**kwargs)

    def wraps(self, _object):
        self.wrapped_object = _object
        if self.wrapped_object_name:
            setattr(self, self.wrapped_object_name, _object)

    def __getattribute__(self, attribute):
        get_attribute = super(Adapter, self).__getattribute__
        _attribute = get_attribute("adaptations").get(attribute, None)
        if _attribute is not None:
            result = getattr(get_attribute("wrapped_object"), _attribute)
        else:
            result = get_attribute(attribute)
        return result

    def __setattr__(self, attribute, value):
        get_attribute = super(Adapter, self).__getattribute__
        _attribute = get_attribute("adaptations").get(attribute, None)
        if _attribute is not None:
            setattr(self.wrapped_object, _attribute, value)
        else:
            super(Adapter, self).__setattr__(attribute, value)


class Static_Wrapper(Base):
    """ Wrapper that statically wraps attributes upon initialization. This
        differs from the default Wrapper in that changes made to the data of
        the wrapped object on a Wrapper will be reflected in the wrapper object
        itself.

        With a Static_Wrapper, changes made to the wrapped objects attributes
        will not be reflected in the Static_Wrapper object, unless the object
        is explicitly wrapped again using the wraps method.

        Attribute access on a static wrapper is faster then the regular wrapper. """
    wrapped_attributes = tuple()
    wrapped_object_name = ''
    auto_verbosity_ignore = ("wraps", )
    defaults = {"wrapped_object" : None}

    def __init__(self, **kwargs):
        super(Static_Wrapper, self).__init__(**kwargs)
        if self.wrapped_object:
            self.wraps(self.wrapped_object)

    def wraps(self, _object):
        if self.wrapped_attributes:
            for attribute in self.wrapped_attributes:
                setattr(self, attribute, getattr(_object, attribute))
        else:
            for attribute in dir(_object):
                if "__" != attribute[:2] and "__" != attribute[:-2]:
                    setattr(self, attribute, getattr(_object, attribute))

        self.wrapped_object = _object
        if self.wrapped_object_name:
            setattr(self, self.wrapped_object_name, _object)
