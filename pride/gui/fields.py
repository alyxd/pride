import collections

import pride.gui.gui
import pride.functions.utilities

import sdl2

# key codes used for hotkeys
UP_ARROW = 1073741906
DOWN_ARROW = 1073741905
RIGHT_ARROW = 1073741903
LEFT_ARROW = 1073741904
DELETE_KEY = "\x7f"

ENTRY_TYPE = {"Field" : "pride.gui.fields.Entry",
              "Callable_Field" : "pride.gui.fields.Callable_Entry",
              "Text_Field" : "pride.gui.fields.Text_Entry",
              "Dropdown_Field" : "pride.gui.fields.Dropdown_Entry",
              "Spinbox" : "pride.gui.fields.Spinbox_Entry",
              "Toggle" : "pride.gui.fields.Toggle_Entry",
              "Slider_Field" : "pride.gui.fields.Slider_Entry",
              "_Endcap" : "pride.gui.fields._Endcap_Entry"}



class Entry(pride.gui.gui.Button):

    defaults = {"location" : "right", "confidential" : False,
                "show_status_when_selected" : True}
    predefaults = {"parent_field" : None, "text_initialized" : False}
    autoreferences = ("parent_field", )

    def _get_text(self):
        return str(self.parent_field.value)
    def _set_text(self, value):
        if self.text_initialized:
            if self.allow_text_edit:
                if isinstance(self, Spinbox_Entry):
                    self.parent_field.value = int(value)
                else:
                    self.parent_field.value = value
            else:
                parent_field = self.parent_field
                try:
                    value = str(getattr(parent_field.target_object, parent_field.name))
                except AttributeError:
                    if not hasattr(parent_field, "target_object"):
                        raise
                    value = str(parent_field.target_object[parent_field.name])
                super(Entry, self)._set_text(value)
        else:
            super(Entry, self)._set_text(value)
            self.text_initialized = True
    text = property(_get_text, _set_text)

    def select(self):
        super(Entry, self).select()
        field = self.parent_field
        if field.parent_form is not None:
            field.parent_form.handle_entry_selected(self, _needs_select=False)
        if self.show_status_when_selected:
            name = getattr(field, "button_text", '') or field.display_name or field.name
            self.show_status("Selected: {}".format(name))


class Field(pride.gui.gui.Container):

    defaults = {"name" : '', "orientation" : "stacked",
                "_value_initialized" : False,
                "editable" : True, "location" : "left", "has_label" : True,
                "display_name" : ''}
    mutable_defaults = {"entry_kwargs" : dict, "id_kwargs" : dict}
    predefaults = {"target_object" : None}
    autoreferences = ("identifier", "parent_form")
    allowed_values = {"orientation" : ("stacked", "side by side")}

    def _get_value(self):
        try:
            return getattr(self.target_object, self.name)
        except (TypeError, AttributeError) as exception:
            try:
                return self.target_object[self.name]
            except TypeError:
                raise exception
    def _set_value(self, value):
        if self.editable:
            old_value = self.value
            if self.handle_value_changed(old_value, value):
                try:
                    setattr(self.target_object, self.name, value)
                except (TypeError, AttributeError) as exception:
                    assert hasattr(self, "target_object")
                    try: # duck typing might fail for mapping-like objects that don't restrict attribute assignment the way a dict does
                        self.target_object[self.name] = value
                    except TypeError:
                        if hasattr(self, "target_object") and hasattr(self, "name"):
                            raise exception

                self.entry.texture_invalid = True # updates text later
                parent_form = self.parent_form
                if parent_form is not None:
                    parent_form.handle_value_changed(self, old_value, value)
    value = property(_get_value, _set_value)

    def __init__(self, **kwargs):
        super(Field, self).__init__(**kwargs)
        self.create_subcomponents()

    def create_subcomponents(self):
        id_kwargs = self.id_kwargs
        orientation = self.orientation
        if orientation == "stacked":
            location = "top"
            id_kwargs.setdefault("scale_to_text", False)
            id_kwargs.setdefault("h_range", (0, .05))
        else:
            assert orientation == "side by side"
            location = "left"
        assert self.identifier is None
        self.create_id(location, **id_kwargs)
        self.create_entry(location)

    def create_id(self, location, **id_kwargs):
        id_kwargs.setdefault("tip_bar_text", self.tip_bar_text)
        self.identifier = self.create(pride.gui.gui.Container, location=location,
                                      text=self.display_name or self.name,
                                      **id_kwargs)
        if not self.has_label:
            self.identifier.hide()

    def create_entry(self, location):
        kwargs = self.entry_kwargs
        kwargs.setdefault("location", location)
        entry_type = ENTRY_TYPE[self.__class__.__name__]
        self.entry = self.create(entry_type, parent_field=self, **kwargs)

    def handle_value_changed(self, old_value, new_value):
        if old_value == new_value:
            return False
        self.alert("Value changing from {} to {}".format(old_value, new_value),
                    level=self.verbosity["handle_value_changed"])
        return True

    def delete(self):
        del self.entry_kwargs
        del self.target_object
        super(Field, self).delete()


class Callable_Entry(Entry):

    hotkeys = {('\n', None) : "handle_return"}

    def _get_text(self):
        return self.parent_field.button_text
    def _set_text(self, value):
        field = self.parent_field
        try:
            value = field.button_text
        except AttributeError:
            if not hasattr(self, "parent_field"):
                raise
        self.text_initialized = False
        super(Callable_Entry, self)._set_text(value)
        if field is not None:
            #backup = getattr(field, "_backup_w_range", None)
            #if backup is None:
            #    field._backup_w_range = self.w_range
            field.w_range = self.w_range
            field.pack()

    text = property(_get_text, _set_text)

    def handle_return(self):
        print("Callable_Entry handle_return")
        parent_field = self.parent_field
        parent_field.value(*parent_field.args, **parent_field.kwargs)

    def left_click(self, mouse):
        parent_field = self.parent_field
        parent_field.value(*parent_field.args, **parent_field.kwargs)


class Callable_Field(Field):

    defaults = {"orientation" : "side by side",
                "has_label" : False, "button_text" : '', "args" : tuple()}
    mutable_defaults = {"entry_kwargs" : lambda: {"scale_to_text" : True},
                        "kwargs" : dict}

    def create_entry(self, location):
        super(Callable_Field, self).create_entry(location)
        self.entry.text = self.entry.text # .text may not get set, if so then scale_to_text wont happen

    def delete(self):
        del self.kwargs
        super(Callable_Field, self).delete()


class Text_Entry(Entry):

    defaults = {"h" : 16, "allow_text_edit" : False, "cursor_blink_rate" : 13,
                "cursor_symbol" : '_', "_cursor_offset" : 0}
    hotkeys = {(LEFT_ARROW, None) : "handle_left_arrow",
               (RIGHT_ARROW, None) : "handle_right_arrow",
               ("\b", None) : "handle_backspace", (DELETE_KEY, None) : "handle_delete_key"}

    def handle_left_arrow(self):
        self._cursor_offset = min(self._cursor_offset + 1, len(self.text))
        self.keep_cursor_visible() # keeps cursor visible while moving cursor

    def handle_right_arrow(self):
        self._cursor_offset = max(0, self._cursor_offset - 1)
        self.keep_cursor_visible()

    def handle_backspace(self):
        if self.allow_text_edit:
            offset = self._cursor_offset
            if offset:
                self.text = self.text[:-offset - 1] + self.text[-offset:]
            else:
                self.text = self.text[:-1]
            self.keep_cursor_visible()

    def handle_delete_key(self):
        if self.allow_text_edit:
            offset = self._cursor_offset
            if offset:
                if offset == 1:
                    self.text = self.text[:-offset]
                else:
                    self.text = self.text[:-offset] + self.text[-(offset - 1):]
                self._cursor_offset = max(0, offset - 1)
            self.keep_cursor_visible()

    def text_entry(self, text):
        if self.allow_text_edit:
            offset = self._cursor_offset
            if offset:
                text = self.text[:-offset] + text + self.text[-offset:]
            else:
                text = self.text + text
            self.text = text
            self.keep_cursor_visible()

    def keep_cursor_visible(self):
        self.disable_cursor(False)
        self.enable_cursor()

    def select(self):
        super(Text_Entry, self).select()
        if self.parent_field.editable:
            self.alert("Turning text input on", level='vv')
            self.allow_text_edit = True
            sdl2.SDL_StartTextInput()
            if not self.draw_cursor:
                self.enable_cursor()

    def wait_and_disable(self):
        if self._counter == self.cursor_blink_rate:
            self.disable_cursor()
        else:
            self._counter += 1
            self.sdl_window.schedule_postdraw_operation(self.wait_and_disable, self)

    def wait_and_enable(self):
        if self._counter == self.cursor_blink_rate:
            if not self.draw_cursor:
                self.enable_cursor()
        else:
            self._counter += 1
            self.sdl_window.schedule_postdraw_operation(self.wait_and_enable, self)

    def enable_cursor(self):
        assert self.draw_cursor == False
        assert not self.deleted
        self.sdl_window.schedule_postdraw_operation(self.wait_and_disable, self)
        self.texture_invalid = self.draw_cursor = True
        self._counter = 0

    def disable_cursor(self, reenable=True):
        assert not self.deleted
        self.draw_cursor = False
        self.texture_invalid = True
        if reenable:
            self.sdl_window.schedule_postdraw_operation(self.wait_and_enable, self)
            self._counter = 0
        else:
            self.purge_blink_instructions()

    def purge_blink_instructions(self):
        try:
            self.sdl_window.unschedule_postdraw_operation(self.wait_and_enable, self)
        except (KeyError, ValueError):
            pass
        try:
            self.sdl_window.unschedule_postdraw_operation(self.wait_and_disable, self)
        except (KeyError, ValueError):
            pass

    def deselect(self, next_active_object):
        super(Text_Entry, self).deselect(next_active_object)
        self.alert("Disabling text input", level='vv')
        self.allow_text_edit = False
        sdl2.SDL_StopTextInput()
        self.disable_cursor(False)


class Text_Field(Field): pass # entry_type defined in ENTRY_TYPE



class Increment_Button(pride.gui.gui.Button):

    defaults = {"increment" : 1, "text" : '+'}
    autoreferences = ("target_entry", )

    def left_click(self, mouse):
        super(Increment_Button, self).left_click(mouse)
        self.target_entry.increment_value(self.increment)


class Decrement_Button(pride.gui.gui.Button):

    defaults = {"increment" : 1, "text" : '-'}
    autoreferences = ("target_entry", )

    def left_click(self, mouse):
        super(Decrement_Button, self).left_click(mouse)
        self.target_entry.decrement_value(self.increment)


class Spinbox_Entry(Text_Entry):

    def _get_text(self):
        return super(Spinbox_Entry, self)._get_text()
    def _set_text(self, value):
        if value and value[-1] == '-':
            value = value[:-1]
            sign = -1
        else:
            sign = 1
        try:
            int(value)
        except TypeError: # value can be None
            pass
        except ValueError: # have to remove any non-decimal-numeric characters
            value = ''.join(item for item in value if item in "0123456789")
            if not value:
                value = '0'

        value = value.lstrip('0')
        if not value: # remove leading zeros
            value = '0'
        if sign:
            value = str(sign * int(value))
        assert value

        field = self.parent_field
        if field is not None:
            _min, _max = field.minimum, field.maximum
            assert value is not None
            value = int(value)
            if _min is not None:
                value = max(_min, value)
            if _max is not None:
                value = min(_max, value)
            value = str(value)
        super(Spinbox_Entry, self)._set_text(value)
    text = property(_get_text, _set_text)

    def increment_value(self, amount):
        parent_field = self.parent_field
        _min, _max = parent_field.minimum, parent_field.maximum
        value = int(parent_field.value or '0') + amount
        if _max is not None:
            value = min(_max, value)
        if _min is not None:
            value = max(_min, value)
        parent_field.value = value

    def decrement_value(self, amount):
        self.increment_value(-amount)


class Status_Light(pride.gui.gui.Container):

    defaults = {"location" : "top",
                "theme_profile" : "placeholder", "clickable" : False}

    def enable_indicator(self):
        self.theme_profile = "indicator"

    def disable_indicator(self):
        self.theme_profile = "placeholder"


class Toggle_Entry(Entry):

    mutable_defaults = {"indicator_kwargs" : dict}
    autoreferences = ("status_light", )
    hotkeys = {('\n', None) : "handle_return"}

    def __init__(self, **kwargs):
        super(Toggle_Entry, self).__init__(**kwargs)
        self.create_subcomponents()

    def handle_return(self):
        self._toggle()

    def create_subcomponents(self):
        self.status_light = self.create(Status_Light, **self.indicator_kwargs)
        if self.parent_field.value:
            self.status_light.enable_indicator()
        else:
            self.status_light.disable_indicator()

    def left_click(self, mouse):
        super(Toggle_Entry, self).left_click(mouse)
        self._toggle()

    def _toggle(self):
        parent_field = self.parent_field
        parent_field.value = not parent_field.value
        if parent_field.value:
            self.status_light.enable_indicator()
        else:
            self.status_light.disable_indicator()


from pride.gui.form2 import Form, layout, row_info, field_info

class Dropdown_Form(Form):

    defaults = {"menu_open" : True}
    interfaces = {"Form" : ("Base",
                            "Shape",
                            "Organized_Object",
                            "Window_Object"),
                  "Row" : ("Base",
                           "Shape",
                           "Organized_Object",
                           "Window_Object"),
                  "Field" : ("Field", "Dropdown")}

    hotkeys = {(UP_ARROW, None) : "handle_up_arrow",
               (DOWN_ARROW, None) : "handle_down_arrow"}

    def select_entry(self, value, index):
        if self.menu_open:
            self.close_menu(value, index)
        else:
            self.open_menu()

    def open_menu(self):
        self.vertical_slider.show()
        self.pack()
        self.load_rows()
        self.menu_open = True

    def close_menu(self, value, index):
        dropdown_entry = self.parent
        dropdown_entry.value = value
        dropdown_entry.current_value_index = index

        if index not in (row.current_row_number for row in self.visible_rows):
            self.y_scroll_value = index

        for row in self.visible_rows:
            if row.current_row_number != index:
                row.hide()
                row.pack()

        self.menu_open = False
        self.vertical_slider.hide()
        self.pack()

    def handle_up_arrow(self):
        if not self.menu_open:
            self.open_menu()
        before = self.y_scroll_value
        modulus = (len(self.layout[0]) - self.max_rows)  + 1
        self.y_scroll_value = (self.y_scroll_value - 1) % modulus
        self.synchronize_scroll_bars()

    def handle_down_arrow(self):
        if not self.menu_open:
            self.open_menu()

        before = self.y_scroll_value
        modulus = (len(self.layout[0]) - self.max_rows) + 1
        self.y_scroll_value = (self.y_scroll_value + 1) % modulus
        self.synchronize_scroll_bars()


class Dropdown_Entry(Callable_Entry):

    autoreferences = ("dropdown_form", )

    def __init__(self, **kwargs):
        super(Dropdown_Entry, self).__init__(**kwargs)
        self.scale_to_text = False
        self.create_subcomponents()

    def create_subcomponents(self):
        rows = (row_info(i,
                         field_info("select_entry",
                                    button_text=str(value),
                                    args=(value, i), target_object=self,
                                    entry_kwargs={"scale_to_text" : False})) for
                i, value in enumerate(self.parent_field.values))

        _layout = layout(*rows)
        self.dropdown_form = self.create(Dropdown_Form, layout=_layout)
        self.select_entry(self.parent_field.values[0], 0)


class Dropdown_Field(Callable_Field):

    defaults = {"has_label" : True,
                "orientation" : "side by side"}


class Spinbox(Field):

    defaults = {"include_incdec_buttons" : False,
                "minimum" : None, "maximum" : None}
                # can only use either minimum or maximum but not both by default
                # must specify Spinbox type explicitly if min and max are used.
    mutable_defaults = {"entry_kwargs" : lambda: {"location" : "left"}}
    allowed_values = {"include_incdec_buttons" : (False, )} # not actually part of the interface

    def create_entry(self, location):
        container = self.create(pride.gui.gui.Container, location=location)
        entry_type = ENTRY_TYPE[self.__class__.__name__]
        entry = self.entry = container.create(entry_type, parent_field=self,
                                              tip_bar_text=self.tip_bar_text,
                                               **self.entry_kwargs)
        if self.editable:
            subcontainer = container.create(pride.gui.gui.Container, location="left",
                                            w_range=(0, .05))
            kwargs = {"target_entry" : entry, "location" : "top"}
            self.inc_button = subcontainer.create(Increment_Button, **kwargs)
            assert kwargs == {"target_entry" : entry, "location" : "top"}
            self.dec_button = subcontainer.create(Decrement_Button, **kwargs)
            self.include_incdec_buttons = True # this is used by Form tab selection feature

    def handle_value_changed(self, old_value, new_value):
        return super(Spinbox, self).handle_value_changed(int(old_value), int(new_value))


class Toggle(Field): pass # entry_type defined in ENTRY_TYPE


class Continuum(pride.gui.gui.Button):

    autoreferences = ("notch", "bar", "parent_field", "parent_entry")

    def __init__(self, **kwargs):
        super(Continuum, self).__init__(**kwargs)
        if self.orientation == "side by side":
            bar_location = "left"
            notch_kwargs = {"location" : "right", "w_range" : (0, .025)}
            self._adjustment_target = "w_range"
        else:
            bar_location = "top"
            notch_kwargs = {"location" : "bottom", "h_range" : (0, .025)}
            self._adjustment_target = "h_range"
        self.bar = bar = self.create(pride.gui.gui.Container, location=bar_location,
                                     clickable=False)
        self.notch = bar.create(pride.gui.gui.Container, clickable=False,
                                theme_profile="interactive", **notch_kwargs)

    def update_position_from_value(self):
        if self._adjustment_target == "w_range":
            size = 'w'
        else:
            assert self._adjustment_target == "h_range"
            size = 'h'

        parent_field = self.parent_field
        entry = parent_field.entry
        left = entry.left; right = entry.right
        value = parent_field.value

        if left is None:
            left_size = 0
        else:
            left_size = getattr(left, size)
        if right is None:
            right_size = 0
        else:
            right_size = getattr(right,size)
        maximum = parent_field.maximum; minimum = parent_field.minimum
        width = (getattr(entry, size) - left_size) - right_size
        if value == maximum:
            new_size = width
        elif value == minimum:
            new_size = 0
        else:
            bucket_width = width / (float(maximum - minimum) + 1)
            new_size = int(bucket_width * parent_field.value)
        setattr(self.bar, "{}_range".format(size), (new_size, new_size))
        self.bar.pack()

    def left_click(self, mouse):
        super(Continuum, self).left_click(mouse)
        if not self.parent_field.editable:
            return
        # partition available space into n buckets
        # make notch w equal to bucket_width in size
        # find which bucket was clicked and assign that value
        # set width of bar to bucket_width * bucket_number
        #   aligns right edge of notch to right edge of selected bucket
        if self._adjustment_target == "w_range":
            coord = 'x'
            size = 'w'
        else:
            assert self._adjustment_target == "h_range"
            coord = 'y'
            size = 'h'

        # unpack data
        # evaluate contextual meaning of data (build more data from relations between present data)
        # compute value based on data
        # ensure value fits the expected constraints
        # respond to computed value
        parent_field = self.parent_field; entry = parent_field.entry;
        left = entry.left; right = entry.right
        if left is None:
            left_size = 0
        else:
            left_size = getattr(left, size)
        if right is None:
            right_size = 0
        else:
            right_size = getattr(right, size)
        width = (getattr(entry, size) - left_size) - right_size
        maximum = parent_field.maximum; minimum = parent_field.minimum
        buckets = (maximum - minimum) + 1 # + 1 because minimum is a selectable choice (e.g. max = 1, min = 0)
        bucket_width = width / float(buckets)
        offset = getattr(mouse, coord) - getattr(entry, coord) - left_size
        value = max(min(int(offset / bucket_width), maximum), minimum)
        assert minimum <= value <= maximum
        before = parent_field.value
        parent_field.value = value

        if value == maximum:
            new_size = width
        elif value == minimum:
            new_size = 0
        else:
            new_size = int(bucket_width * value)
        bar = self.bar
        setattr(bar, "{}_range".format(size), (new_size, new_size))
        bar.pack()

    def mousemotion(self, x, y, x_change, y_change, mouse):
        if self.held:
            self.left_click(self._mousetuple(x, y))

    def _mousetuple(self, x, y, f=collections.namedtuple("mouse", ('x', 'y'))):
        return f(x, y)


class _Endcap_Entry(Text_Entry):

    defaults = {"show_status_when_selected" : False}

    def left_click(self, mouse):
        super(_Endcap_Entry, self).left_click(mouse)
        parent_field = self.parent_field
        slider_field = parent_field.target_object
        assert parent_field.name in ("minimum", "maximum")
        value = getattr(slider_field, parent_field.name)
        slider_field.value = value
        slider_field.update_position_from_value()


class _Endcap(Text_Entry):

    defaults = {"editable" : False, "has_label" : False}


class Slider_Entry(Entry):

    defaults = {"orientation" : "side by side", "include_incdec_buttons" : True,
                "include_minmax_buttons" : True, "hide_text" : False}
    autoreferences = ("left", "continuum", "right", "max_button", "min_button",
                      "inc_button", "dec_button")
    hotkeys = {(UP_ARROW, None) : "handle_up_arrow",
               (DOWN_ARROW, None) : "handle_down_arrow",
               (LEFT_ARROW, None) : "handle_left_arrow",
               (RIGHT_ARROW, None) : "handle_right_arrow"}

    def _get_text(self):
        if self.hide_text:
            #super(Slider_Entry, self)._get_text()
            return ''
        else:
            return super(Slider_Entry, self)._get_text()
    def _set_text(self, value):
        super(Slider_Entry, self)._set_text(value)
    text = property(_get_text, _set_text)

    def __init__(self, **kwargs):
        super(Slider_Entry, self).__init__(**kwargs)
        self.create_subcomponents()

    def handle_left_arrow(self):
        if self.orientation == "side by side":
            self.decrement_value()

    def handle_right_arrow(self):
        if self.orientation == "side by side":
            self.increment_value()

    def handle_up_arrow(self):
        if self.orientation == "stacked":
            self.decrement_value()

    def handle_down_arrow(self):
        if self.orientation == "stacked":
            self.increment_value()

    def create_subcomponents(self):
        parent_field = self.parent_field
        assert parent_field.minimum is not None and parent_field.maximum is not None

        orientation = self.orientation
        kwargs = dict()
        if orientation == "stacked":
            location = "top"
            kwargs["h_range"] = (0, .05)
            kwargs["entry_kwargs"] = {"scale_to_text" : False}
        else:
            location = "left"
            kwargs["w_range"] = (0, .08)
        if self.parent_field.editable:
            kwargs["show_status_when_selected"] = False

            include_minmax = self.include_minmax_buttons
            include_incdec = self.include_incdec_buttons
            if include_minmax and include_incdec:
                left = self.create(pride.gui.gui.Container, location=location, **kwargs)
                self.left = left
            else:
                left = None

            if include_minmax:
                if left is not None:
                    self.min_button = left.create(_Endcap, location=location, name="minimum",
                                                target_object=parent_field, **kwargs)
                else:
                    self.min_button = self.left = self.create(_Endcap, location=location, name="minimum",
                                                            target_object=parent_field, **kwargs)
            if include_incdec:
                if left is not None:
                    self.dec_button = left.create(Callable_Field,
                                                name="decrement_value",
                                                location=location,
                                                parent_field=parent_field,
                                                target_object=self,
                                                button_text='-', **kwargs)
                else:
                    self.dec_button = self.left =\
                    self.create(Callable_Field, name="decrement_value",
                                location=location, parent_field=parent_field,
                                target_object=self, button_text='-', **kwargs)

        self.continuum = self.create(Continuum, location=location,
                                     orientation=orientation, parent_entry=self,
                                     parent_field=parent_field)
        if self.parent_field.editable:
            if include_minmax and include_incdec:
                right = self.create(pride.gui.gui.Container, location=location,
                                    **kwargs)
                self.right = right
            else:
                right = None

            if include_incdec:
                if right is not None:
                    self.inc_button = self.right.create(Callable_Field,
                                                        name="increment_value",
                                                        location=location,
                                                        parent_field=parent_field,
                                                        target_object=self,
                                                        button_text='+', **kwargs)
                else:
                    self.inc_button = self.right =\
                    self.create(Callable_Field, name="increment_value",
                                location=location, parent_field=parent_field,
                                target_object=self, button_text='+', **kwargs)

            if include_minmax:
                if right is not None:
                    self.max_button = right.create(_Endcap,
                                                target_object=parent_field,
                                                location=location,
                                                name="maximum", **kwargs)
                else:
                    self.max_button = self.right =\
                    self.create(_Endcap, target_object=parent_field,
                                location=location, name="maximum", **kwargs)

    def increment_value(self):
        parent_field = self.parent_field
        parent_field.value = min(parent_field.value + 1, parent_field.maximum)
        parent_field.update_position_from_value()

    def decrement_value(self):
        parent_field = self.parent_field
        parent_field.value = max(parent_field.value - 1, parent_field.minimum)
        parent_field.update_position_from_value()


class Slider_Field(Field):

    predefaults = {"_minimum" : 0, "_maximum" : 0}

    def _get_minimum(self):
        return self._minimum
    def _set_minimum(self, value):
        self._minimum = value
        if self.minimum == self.maximum:
            self.hide()
        else:
            self.show()
    minimum = property(_get_minimum, _set_minimum)

    def _get_maximum(self):
        return self._maximum
    def _set_maximum(self, value):
        self._maximum = value
        if self.minimum == self.maximum:
            self.hide()
        else:
            self.show()
    maximum = property(_get_maximum, _set_maximum)

    def handle_transition_animation_end(self):
        super(Slider_Field, self).handle_transition_animation_end()
        self.update_position_from_value()

    def update_position_from_value(self):
        self.entry.continuum.update_position_from_value()