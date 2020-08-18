# layout(
#        row_info(row_no,
#                 (field_info(field_name, **field_kwargs),
#                  field_info(...), ...),
#                 **row_kwargs)
#        row_info(...),
#        ...
#       )
import keyword # for kwlist
import tokenize
import copy # for deepcopy
import operator # for attrgetter
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

TEST_LAYOUT = """\
layout(row_info(0,
                field_info("test_string"),
                field_info("test_bool"),
                h_range=(0, .1)),
      row_info(1,
               field_info("test_int"),
               field_info("test_dropdown", values=(1, '2'))
               ),
      w_range=(0, .25)
     )"""

def layout(*rows, **kwargs):
    return (dict((row[0], row) for row in rows),
            kwargs)

def row_info(row_no, *field_infos, **row_kwargs):
    return (row_no, field_infos, row_kwargs)

def field_info(field_name, **kwargs):
    return (field_name, kwargs)

def compile_layout(layout_str):
    _globals = {"layout" : layout,
                "row_info" : row_info,
                "field_info" : field_info}
    _locals = dict()
    program = "__compile_layout_output = {}".format(layout_str)
    double_check(program)
    exec program in _locals, _globals
    return _globals["__compile_layout_output"]

# if run as main, __builtins__ is a module
# otherwise, __builtins__ is a dictionary
try:
    FILTER_TOKENS = __builtins__.keys()
except AttributeError:
    FILTER_TOKENS = dir(__builtins__)
    assert FILTER_TOKENS != dir(dict)
FILTER_TOKENS += tuple(keyword.kwlist)

def double_check(program, filter=FILTER_TOKENS):
    flo = StringIO.StringIO(program)
    for _, token, _, _, _ in tokenize.generate_tokens(flo.readline):
        if token in filter:
            raise Warning("Found forbidden token '{}'".format(token))
    # cannot simply filter '.' because it is needed for floating point numbers
    # if the symbol to the right of the '.' is a numeral, then
    # it cannot be a name, as names may not start with numbers.
    if '.' in program:
        index = 0
        end = len(program)
        while index != end:
            try:
                index = program.index('.', index + 1)
            except ValueError:
                break
            if not program[index + 1].isdigit():
                raise Warning("Found an attempted attribute access")

def compile_file(_file):
    return compile_layout(_file.read())

def compile_filename(filename):
    with open(filename, 'r') as _file:
        output = compile_file(_file)
    return output

def test_field_info():
    field_name = "test name"
    kwargs = dict()
    out = field_info(field_name, **kwargs)
    assert out[0] == field_name
    assert out[1] == kwargs

def test_row_info():
    field1 = field_info("test_field1")
    field2 = field_info("test_field2")
    out = row_info(0,
                   field1,
                   field2,
                   h_range=(0, .1))
    assert out[0] == 0, out[0]
    assert out[1][0] == field1, (out[1][0], field1)
    assert out[1][1] == field2, (out[1][1], field2)
    assert out[2]["h_range"] == (0, .1), out[2]["h_range"]

def test_layout():
    row0 = row_info(0,
                    field_info("test_string"),
                    field_info("test_bool"),
                    h_range=(0, .1))
    row1 = row_info(1, field_info("test_int"),
                       field_info("test_dropdown", values=(1, '2')))

    out = layout(row0, row1, w_range=(0, .25))
    assert out[0][0] == row0, (out[0][0], row0)
    assert out[0][1] == row1, (out[0][1], row1)
    assert out[1]["w_range"] == (0, .25), out[1]["w_range"]

def test_compile_layout():
    import pprint
    row0 = row_info(0,
                    field_info("test_string"),
                    field_info("test_bool"),
                    h_range=(0, .1))
    row1 = row_info(1,
                    field_info("test_int"),
                    field_info("test_dropdown", values=(1, '2')))
    out1 = layout(row0, row1, w_range=(0, .25))

    _layout = TEST_LAYOUT
    out2 = compile_layout(_layout)
    assert out1 == out2, '\n' + pprint.pformat((out1, out2))

    import ast
    out3 = ast.literal_eval(bytes(out2))
    assert out3 == out2

def test_compile_file():
    import pprint
    row0 = row_info(0,
                    field_info("test_string"),
                    field_info("test_bool"),
                    h_range=(0, .1))
    row1 = row_info(1,
                    field_info("test_int"),
                    field_info("test_dropdown", values=(1, '2')))
    out1 = layout(row0, row1, w_range=(0, .25))

    with open("_form2test.txt", 'w+') as _file:
        _file.write(TEST_LAYOUT)
        _file.seek(0)
        out2 = compile_file(_file)
    assert out1 == out2, '\n' + pprint.pformat((out1, out2))

def test_compile_filename():
    import pprint
    row0 = row_info(0,
                    field_info("test_string"),
                    field_info("test_bool"),
                    h_range=(0, .1))
    row1 = row_info(1,
                    field_info("test_int"),
                    field_info("test_dropdown", values=(1, '2')))
    out1 = layout(row0, row1, w_range=(0, .25))

    with open("_form2test.txt", 'w') as _file:
        _file.write(TEST_LAYOUT)
        _file.seek(0)
    out2 = compile_filename("_form2test.txt")
    assert out1 == out2, '\n' + pprint.pformat((out1, out2))

from pride.components import deep_update, Config
import pride.gui.gui

class Scrollable_Window(pride.gui.gui.Window):

    defaults = {"vertical_slider_position" : "right",
                "horizontal_slider_position" : "bottom"}
    predefaults = {"_x_scroll_value" : 0, "_y_scroll_value" : 0}
    autoreferences = ("main_window", "vertical_slider", "horizontal_slider")
    mutable_defaults = {"vertical_slider_entry_kwargs" : lambda: {"orientation" : "stacked"},
                        "horizontal_slider_entry_kwargs" : dict}

    def _get_y_scroll_value(self):
        return self._y_scroll_value
    def _set_y_scroll_value(self, new_value):
        old_value = self._y_scroll_value
        self._y_scroll_value = new_value
        self.handle_y_scroll(old_value, new_value)
    y_scroll_value = property(_get_y_scroll_value, _set_y_scroll_value)

    def _get_x_scroll_value(self):
        return self._x_scroll_value
    def _set_x_scroll_value(self, new_value):
        old_value = self._x_scroll_value
        self._x_scroll_value = new_value
        self.handle_x_scroll(old_value, new_value)
    x_scroll_value = property(_get_x_scroll_value, _set_x_scroll_value)

    def __init__(self, **kwargs):
        super(Scrollable_Window, self).__init__(**kwargs)
        self.create_subcomponents()

    def create_subcomponents(self):
        self.main_window = self.create(pride.gui.gui.Container,
                                       location="main")
        position = self.vertical_slider_position
        slider_type = "pride.gui.fields.Slider_Field"
        if position is not None:
            self.vertical_slider = \
            self.create(slider_type, location=position,
                        orientation="stacked", w_range=(0, .025),
                        name="y_scroll_value", minimum=0, maximum=0,
                        auto_create_id=False, target_object=self,
                        entry_kwargs=self.vertical_slider_entry_kwargs)
        position = self.horizontal_slider_position
        if position is not None:
            self.horizontal_slider = \
            self.create(slider_type, location=position,
                        orientation="side by side", h_range=(0, .025),
                        auto_create_id=False, target_object=self,
                        name="x_scroll_value", minimum=0, maximum=0,
                        entry_kwargs=self.horizontal_slider_entry_kwargs,)

    def handle_x_scroll(self, old_value, new_value):
        pass

    def handle_y_scroll(self, old_value, new_value):
        pass

# should not be an attribute of Form;
# otherwise it could be overwritten via kwargs when the Form is instantiated
# if the kwargs are controlled by an adversary (i.e. a malicious layout file)
# the field_type argument could be used to call any function

FIELD_TYPES = {"Dropdown" : "pride.gui.fields.Dropdown_Field",
               "Slider" : "pride.gui.fields.Slider_Field",
               "Toggle" : "pride.gui.fields.Toggle",
               "Spinbox" : "pride.gui.fields.Spinbox",
               "Text_Field" : "pride.gui.fields.Text_Field",
               "Text_Display" : "pride.gui.fields.Text_Display",
               "Callable" : "pride.gui.fields.Callable_Field",
               "Dropdown_Callable" : "pride.gui.fields._Dropdown_Callable"}


class Row(pride.gui.gui.Container):

    mutable_defaults = {"fields" : list}

    def delete(self):
        del self.fields[:]
        super(Row, self).delete()


class Visible_Row(pride.gui.gui.Container):

    defaults = {"_current_row" : None, "_current_row_old_name" : None,
                "current_row_number" : None}

    def load_row(self, row):
        assert self._current_row is None
        self._current_row = row
        self._current_row_old_name = row.parent_name
        self.current_row_number = row.row_number
        row.parent_name = self.reference
        self.add(row)

        row_kwargs = self.parent.parent.layout[0][row.row_number][-1]
        for key, value in row_kwargs.items():
            setattr(self, key, value)
        self.pack()

    def unload_row(self, new_row_indices):
        old_row = self._current_row
        if old_row is not None:
            old_row.parent_name = self._current_row_old_name
            self.remove(old_row)
            self._current_row = None
            self._current_row_old_name = None
            self._current_row_number = None
            if old_row.row_number not in new_row_indices:
                old_row.hide()

    def delete(self):
        self.unload_row(tuple())
        super(Visible_Row, self).delete()

API = {"Base" : (("delete", ), tuple()),
       "Shape" : (tuple(), ("h_range", "w_range")),
       "Organized_Object" : (tuple(), ("location", )),
       "Window_Object" : (tuple(), ("center_text", "hoverable", "wrap_text",
                                    "theme_name", "theme_profile", "text")),
       "Form" : (tuple(), ("max_rows", "horizontal_slider_position",
                           "vertical_slider_position")),
       "Field" : (tuple(), tuple("name", "orientation", "editable",
                                 "location"))}

def flatten_interface(interfaces):
    methods = []
    attributes = []
    for api_name in interfaces:
        interface_methods, interface_attributes = API[api_name]
        methods.extend(interface_methods)
        attributes.extend(interface_attributes)
    return (methods, attributes)


class Form(Scrollable_Window):

    defaults = {"target_object" : None, "max_rows" : 4,
                "horizontal_slider_position" : None}
    subcomponent_kwargs = {"row" : Config(location="top",
                                          h_range=(0, 1.0))}
    mutable_defaults = {"rows" : dict, "visible_rows" : list,
                        "interfaces" :
                          lambda: {"Form" : ("Base",
                                             "Shape",
                                             "Organized_Object",
                                             "Window_Object"),
                                   "Row" : (
    hotkeys = {("\t", None) : "handle_tab"}
    autoreferences = ("selected_entry", )

    def create_subcomponents(self):
        if self.target_object is None:
            self.target_object = self

        self.filter_layout()

        super(Form, self).create_subcomponents()

        _row_info = self.layout[0]
        max_rows = self.max_rows
        amount = min(max_rows, len(_row_info))
        # make a fixed number of visible rows
        # set the rows to represent the data of a given range of row_infos
        window = self.main_window
        self.visible_rows = [window.create(Visible_Row) for
                             count in range(amount)]
        for row_no in range(amount):
            self.create_row(_row_info[row_no])
        self.load_rows()

        if self.selected_entry is None:
            self.selected_entry = self.rows[0].fields[0].entry

        self.synchronize_scroll_bars()

    def filter_layout(self):
        (interface_methods,
        interface_attributes) = flatten_interface(self.interfaces)

        # if a key is in the form.__dict__,
        #    then it must be listed in the interface to be accessible
        # otherwise, it is assumed to be uncontrolled data defined by the layout
        form_kwargs = self.layout[-1]
        api_controlled_values = self.__dict__.keys()
        uncontrolled = []
        for key, value in form_kwargs.iteritems():
            if key in api_controlled_values:
                if key not in interface_attributes:
                    message  = "Layout attempted to set non-interface attribute"
                    message += " '{}' to {}".format(key, value)
                    raise ValueError(message)
            else:
                uncontrolled.append(key)

        (row_iface_methods,
         row_iface_attrs) = flatten_interface(self.row_interface)
        (field_iface_methods,
         field_iface_attrs) = flatten_interface(self.field_interface)

        target_object = self.target_object
        for row_no, fields, row_kwargs in self.layout[0].values():
            for key, value in row_kwargs.iteritems():
                if key not in interface_attributes:
                    message  = "Row {}: ".format(row_no)
                    message += "Layout attempted to set non-interface attribute"
                    message += " '{}' to {}".format(key, value)
                    raise ValueError(message)
            for f_name, field_kwargs in fields:
                if f_name not in interface_attributes:
                    if f_name not in uncontrolled:
                        message  = "Row {}, Field {}: ".format(row_no, f_name)
                        message += "Layout attempted to create field for non-"
                        message += "interface attribute '{}'".format(f_name)
                        raise ValueError(message)

                if not hasattr(target_object, f_name):
                    if f_name not in uncontrolled:
                        message = "Target has no attribute '{}'".format(f_name)
                        raise ValueError(message)

                for key, value in field_kwargs.iteritems():
                    if key not in interface_attributes:
                        message  = "Row {}, Field {}: ".format(row_no, f_name)
                        message += "Layout attempted to set non-interface "
                        message += "attribute '{}' to {}".format(key, value)
                        raise ValueError(message)

                if hasattr(target_object, f_name):
                    is_callable = hasattr(getattr(target_object, f_name),
                                        "__call__")
                    if is_callable and f_name not in interface_methods:
                        message  = "Row {}, Field {}: ".format(row_no, f_name)
                        message += "Layout attempted to use non-interface "
                        message += "method '{}'".format(f_name)
                        raise ValueError(message)

    def unload_rows(self, new_row_indices):
        for row in self.visible_rows:
            row.unload_row(new_row_indices)

    def load_rows(self):
        start = self.y_scroll_value
        rows = self.rows
        visible_rows = self.visible_rows
        row_infos = self.layout[0]
        max_rows = self.max_rows
        amount = min(max_rows, len(row_infos))

        # must unload rows before calling load_row
        self.unload_rows(range(start, start + amount))
        for offset in range(amount):
            row_no = start + offset
            try:
                row = rows[row_no]
            except KeyError:
                self.create_row(self.layout[0][row_no])
                row = rows[row_no]
            visible_row = visible_rows[offset]
            row.show()
            visible_row.load_row(row)
            visible_row.show()

        excess = max_rows - amount
        if excess:
            for offset in range(excess):
                row_no = start + amount + offset
                visible_rows[row_no].hide()

    def create_row(self, _row_info):
        kwargs = copy.deepcopy(self.row_kwargs)
        row_no, row_kwargs = _row_info[0], _row_info[-1]
        deep_update(kwargs, _row_info[-1])
        kwargs.setdefault("row_number", _row_info[0])

        window = self.main_window
        row = window.create("pride.gui.form2.Row", **kwargs)
        self.rows[row_no] = row
        _field_infos = _row_info[1:-1][0]
        for _field_info in _field_infos:
            self.create_field(_field_info, row)
        row.hide()
        window.remove(row)

    def create_field(self, _field_info, row):
        field_name, field_kwargs = _field_info
        target_object = field_kwargs.get("target_object", self.target_object)
        field_type = self.determine_field_type(target_object,
                                               field_name,
                                               field_kwargs)
        field_kwargs.setdefault("target_object", self.target_object)
        field = row.create(field_type, name=field_name, parent_form=self,
                           **field_kwargs)
        row.fields.append(field)

    def determine_field_type(self, target_object, name, entries):
        field_type = entries.get("field_type", None)
        if field_type is None:
            try:
                value = getattr(target_object, name)
            except AttributeError as exception:
                try:
                    value = target_object[name]
                except TypeError:
                    raise exception
            #if hasattr(value, "field_type"):
            #    field_type = value.field_type
            if "values" in entries: # check for dropdowns before checking value
                field_type = "Dropdown"
            elif "minimum" in entries and "maximum" in entries: # check here before checking for int/float
                field_type = "Slider"
            elif isinstance(value, bool): # must compare for bool before comparing for int; bool is a subclass of int
                field_type = "Toggle"
            elif isinstance(value, int) or isinstance(value, float):
                field_type = "Spinbox"
            elif isinstance(value, str):
                field_type = "Text_Field"
            elif hasattr(value, "__call__"):
                field_type = "Callable"
            #elif isinstance(value, tuple) or isinstance(value, list):
            #    field_type = "pride.gui.widgets.formext.Tabbed_Form"
        if field_type is None:
            message = "Unable to determine field_type for {}"
            raise ValueError(message.format((target_object, name, value, entries)))
        if field_type not in FIELD_TYPES:
            message = "Requested field_type '{}' is unavailable"
            raise ValueError(message.format(field_type))
        return FIELD_TYPES[field_type]

    def handle_value_changed(self, field, old, new):
        pass

    def synchronize_scroll_bars(self):
        slider = self.vertical_slider
        if slider is not None:
            slider.maximum = max(0, len(self.layout[0]) - self.max_rows)
            slider.update_position_from_value()
            slider.entry.texture_invalid = True
            self.pack()

    def handle_y_scroll(self, old, new):
        super(Form, self).handle_y_scroll(old, new)
        # y_scroll points to the current top row
        assert self.y_scroll_value == new, (self.y_scroll_value, new)
        self.load_rows()
        ## check if the selected entry is still visible, unselect it if not
        #row_no = self.selected_entry.parent_field.parent.row_number
        #amount = min(self.max_rows, len(self.layout[0]))
        #if row_no < new and row_no >= new + amount:
        #    self.selected_entry.deselect()
        #    new_entry = self.visible_rows[0]._current_row.fields[0].entry
        #    self.handle_entry_selected(new_entry, scroll=False)

    def handle_tab(self):
        # go to the next field in the row
        # if there are no more fields, go to the next row
        # if there are no more rows, go to the initial row
        entry = self.selected_entry
        field = entry.parent_field
        row = field.parent
        fields = row.fields
        field_index = fields.index(field)
        next_field_index = field_index + 1
        try:
            self.handle_entry_selected(fields[next_field_index].entry,
                                       scroll=True)
        except IndexError:
            rows = self.rows
            row_info = self.layout[0]
            row_count = len(row_info)
            row_index = row.row_number
            next_row_index = (row_index + 1) % row_count
            if next_row_index in row_info:
                if next_row_index not in rows:
                    self.create_row(row_info[row_index + 1])
                next_row = rows[next_row_index]
            else:
                next_row = rows[0]
            if not next_row.fields:
                has_fields = lambda row: row[1]
                has_any_fields = [row for row in
                                  row_info.values() if has_fields(row)]
                if not has_any_fields:
                    return
                for next_row_index in range(next_row_index, row_count):
                    if has_fields(row_info[next_row_index]):
                        break
                else:
                    for next_row_index in range(next_row_index + 1):
                        if has_fields(row_info[next_row_index]):
                            break
                if next_row_index not in rows:
                    self.create_row(row_info[next_row_index])
                next_row = rows[next_row_index]

            self.handle_entry_selected(next_row.fields[0].entry, scroll=True)

    def handle_entry_selected(self, entry, _needs_select=True,
                              scroll=False):
        if self.selected_entry is not None:
            old_entry = self.selected_entry
            old_entry.deselect(entry)
        self.selected_entry = entry
        if _needs_select:
            self.sdl_window.user_input.select_active_item(entry)

        if scroll:
            row_no = entry.parent_field.parent.row_number
            max_index = len(self.layout[0]) - self.max_rows
            row_no = min(row_no, max_index)
            y_value = self.y_scroll_value
            if row_no < y_value:
                self.y_scroll_value = row_no
                self.handle_y_scroll(y_value, row_no)
            elif row_no > y_value + self.max_rows:
                self.y_scroll_value = row_no
                self.handle_y_scroll(y_value, self.y_scroll_value)
            elif row_no == max_index:
                self.y_scroll_value = row_no
                self.handle_y_scroll(y_value, row_no)
            self.synchronize_scroll_bars()

    def set_row_theme(self, index, profile_name):
        self.rows[index].theme_profile = profile_name

    def delete(self):
        self.rows.clear()
        del self.target_object
        del self.visible_rows
        super(Form, self).delete()

def test_Form():
    import pride.gui.main
    _layout = layout(row_info(0,
                              field_info("test_bool"),
                              field_info("test_text"),
                              field_info("test_int"),
                              h_range=(0, .2)),
                     row_info(1,
                              field_info("test_slider", minimum=0, maximum=100),
                              field_info("test_dropdown",
                                         orientation="stacked",
                                         values=(0, 1, 2, 3, 5, 8, 13, 21,
                                                 34, 55, 89, 144)),
                              field_info("test_callable",
                                         button_text="Test Callable"),
                              h_range=(0, .3)),
                     row_info(2), row_info(3), row_info(4),
                     row_info(5, field_info("test_bool")),
                     test_bool=True, test_text="Text", test_int=0,
                     test_slider=50, test_dropdown=0)


    class Test_Form(Form):

        defaults = {"layout" : _layout}

        def test_callable(self):
            self.alert("test_callable")


    pride.gui.main.run_programs([Test_Form])


if __name__ == "__main__":
    test_field_info()
    test_row_info()
    test_layout()
    test_compile_layout()
    test_compile_file()
    test_compile_filename()
    test_Form()
