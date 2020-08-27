import pride.gui.widgets.form
from pride.functions.utilities import slide
field_info = pride.gui.widgets.form.field_info

class Tab_Button_Entry(pride.gui.widgets.form.Callable_Entry):

    defaults = {"_end_hover_set_profile" : '', "_already_constructed" : False,
                "use_lazy_loading" : True, "_just_constructed" : False}

    def left_click(self, mouse):
        parent_field = self.parent_field
        print self.use_lazy_loading, parent_field.args[0]
        if self.use_lazy_loading and not self._already_constructed:
            self.lazy_load_object()

        parent_field.value(self, *parent_field.args, **parent_field.kwargs)
        _object = self.parent_field.args[0]
        if _object.hidden:
            self._end_hover_set_profile = "interactive"
        else:
            self._end_hover_set_profile = "indicator"

    def lazy_load_object(self):
        parent_field = self.parent_field
        callable = parent_field.args[0]
        tab_ref = callable.tab_reference
        assert not self._already_constructed
        _object = callable()
        _object.tab_reference = tab_ref
        parent_field.args = (_object, ) + parent_field.args[1:]
        self._just_constructed = self._already_constructed = True

    def handle_return(self):
        parent_field = self.parent_field
        parent_field.value(self, *parent_field.args, **parent_field.kwargs)

    def hover_ends(self):
        super(Tab_Button_Entry, self).hover_ends()
        new_profile = self._end_hover_set_profile
        if new_profile:
            self.theme_profile = new_profile
            self._end_hover_set_profile = ''


class Tab_Button_Field(pride.gui.widgets.form.Callable_Field):

    defaults = {"entry_type" : Tab_Button_Entry, "editable" : True}


class Tabbed_Window(pride.gui.widgets.form.Scrollable_Window):

    defaults = {"include_new_tab_button" : True, "tab_targets" : tuple(),
                "new_window_type" : "pride.gui.gui.Container",
                "include_tab_delete_button" : True, "tab_bar_label" : '',
                "new_window_tab_text" : "New Window", "include_label" : False,
                "tab_bar_title_text" : '', "tabs_per_row" : 16,
                "top_bar_type" : "pride.gui.gui.Container",
                "new_tab_button_type" : "pride.gui.widgets.form.Form"}
    autoreferences = ("tab_bar", "top_bar")

    subcomponent_kwargs = {"top_bar" : {"location" : "top",
                                        "h_range" : (0, .05)},
                           "tab_bar" : {"location" : "left",
                                        "entry_kwargs" : {"orientation" :
                                                                      "stacked",
                                                     "include_minmax_buttons" :
                                                                         False},
                                        "form_name" : '', "max_rows" : 1},
                           "new_tab_button" : {"location" : "left",
                                               "button_text" : '+',
                                               "entry_kwargs" :
                                                      {"scale_to_text" : False},
                                               "w_range" : (0, .05)},
                           "new_tab_button2" : {"location" : "left",
                                                "w_range" : (0, .05)},
                           "tab" : {"button_text" : "New Window",
                                    "theme_profile" : "placeholder",
                                    "field_type" :
                                    "pride.gui.widgets.tabs.Tab_Button_Field",
                                    "entry_kwargs" : {"scale_to_text" : True,
                                                  "use_lazy_loading" : True}},
                          "tab_bar_row" : dict(),
                          "tab_delete_button" :
                              {"button_text" : 'x',
                               "theme_profile" : "placeholder",
                               "entry_kwargs" :
                                               {"theme_profile" : "placeholder",
                                                "scale_to_text" : True}}}

    def __init__(self, **kwargs):
        super(Tabbed_Window, self).__init__(**kwargs)
        self.create_subcomponents()

    def create_subcomponents(self):
        self.create_topbar()

        if self.include_new_tab_button:
            self.create_new_tab_button()

        fields = self.create_tab_fields()
        offset = 0
        if self.include_label:
            offset += 1
            self.create_label_fields(fields)
        self.create_tab_bar(fields, offset)

    def create_topbar(self):
        kwargs = self.top_bar_kwargs
        self.top_bar = self.create(self.top_bar_type, **kwargs)

    def create_new_tab_button(self):
        #print self.new_tab_button_kwargs
        fields = [[("new_tab", self.new_tab_button_kwargs)]]
        kwargs = self.new_tab_button2_kwargs
        self.top_bar.create(self.new_tab_button_type, fields=fields,
                            target_object=self, **kwargs)

    def create_tab_fields(self):
        fields = []
        _kwargs = self.tab_kwargs

        for row in slide(self.tab_targets, self.tabs_per_row):
            _row = []
            for _object in row:
                tab_kwargs = _kwargs.copy()
                tab_kwargs.setdefault("w_range", (0, 1.0 / self.tabs_per_row))
                tab_kwargs["args"] = (_object, )
                tab_kwargs.update(getattr(_object, "tab_kwargs", dict()))
                _row.append(field_info("select_tab", **tab_kwargs))
            fields.append(_row)
        return fields

    def create_label_fields(self, fields):
        entry = ("tab_bar_label", {"hoverable" : False,
                                   "field_type" : "pride.gui.gui.Window",
                                   "location" : "left",
                                   "text" : self.tab_bar_label,
                                   "scale_to_text" : True
                                   })
        fields = [[entry]]
        self.top_bar.create("pride.gui.widgets.form.Form", fields=fields,
                            location="left")

    def create_tab_bar(self, fields, offset):
        kwargs = self.tab_bar_kwargs.copy()
        kwargs["fields"] = fields
        kwargs["target_object"] = self
        kwargs["row_kwargs"] = dict((x, self.tab_bar_row_kwargs.copy()) for
                                    x in range(len(fields)))
        window = self.top_bar
        self.tab_bar = window.create(pride.gui.widgets.form.Form, **kwargs)

        tabs = self.tab_bar.fields_list
        for tab_no, target in enumerate(self.tab_targets):
            target.tab_reference = tabs[tab_no].reference

        if self.tab_targets:
            first_tab = tabs[offset]
            try:
                self._set_color(first_tab.entry, self.tab_targets[0])
            except AttributeError:
                first_tab.entry.lazy_load_object()
                self._set_color(first_tab.entry, first_tab.args[0])
                first_tab.entry._just_constructed = False

        if not tabs:
            self.tab_bar.hide()

    def new_tab(self):
        tab_bar = self.tab_bar
        if tab_bar.hidden:
            tab_bar.show()
        _object = self.main_window.create(self.new_window_type,
                                          parent_form=tab_bar)
        kwargs = self.tab_kwargs.copy()
        kwargs.setdefault("args", (_object, ))
        try:
            kwargs["entry_kwargs"]["use_lazy_loading"] = False
        except KeyError:
            kwargs["entry_kwargs"] = {"use_lazy_loading" : False}
        fields = [("select_tab", kwargs)]

        offset = -1
        if self.include_tab_delete_button:
            offset -= 1
            del_kwargs = self.tab_delete_button_kwargs.copy()
            del_kwargs["args"] = (_object, )
            fields.append(("delete_tab", del_kwargs))

        # find the first row that is not full
        tabs_per_row = self.tabs_per_row
        for row in sorted(tab_bar.rows.values()):
            if len(row.children) < tabs_per_row:
                break
        else: # there are no non-full rows
            row_no = len(tab_bar.rows)
            try:
                _row_kwargs = tab_bar.row_kwargs[row_no]
            except KeyError:
                _row_kwargs = self.tab_bar_row_kwargs.copy()
                tab_bar.row_kwargs[row_no] = _row_kwargs

            row = tab_bar.create_row(len(tab_bar.rows))
            #tab_bar.sort_rows()
            #tab_bar.synchronize_scroll_bars()

        fields_count = len(tab_bar.fields_list)
        for offset, field_info in enumerate(fields):
            field_no = fields_count + offset
            field = tab_bar.create_field(field_no, field_info, row)
            if field.name == "select_tab":
                self._set_color(field.entry, field.args[0])
        tab_bar.fields.append(fields)
        _object.tab_reference = tab_bar.fields_list[offset].reference

        #tab_bar.sort_rows()
        tab_bar.set_row_visibility(max(0, len(tab_bar.fields) - tab_bar.max_rows))
        tab_bar.synchronize_scroll_bars()

    def select_tab(self, tab, _object):
        #if not hasattr(_object, "hidden"):
        #    if tab.use_lazy_loading and not tab._already_constructed:
        #        tab.lazy_load_object()
        #        _object = tab.parent_field.args[0]

        if not tab._just_constructed:
            if _object.hidden:
                _object.show()
            else:
                _object.hide()
            _object.pack()
        else:
            tab._just_constructed = False
        self._set_color(tab, _object)
        #self.sdl_window.schedule_postdraw_operation(lambda: self._set_color(tab, _object), self)

    def _set_color(self, tab, _object):
        if _object.hidden:
            tab.theme_profile = "interactive"
        else:
            tab.theme_profile = "indicator"

    def delete_tab(self, _object):
        _object.delete()
        fields = [field for field in self.tab_bar.fields_list.values() if
                  getattr(field, "args", False) and field.args[0] == _object]
        for field in fields: # will be delete button and tab button
            field.delete()   # delete would modify fields_list during iteration and cause bugs
        row = field.parent
        if not row.children:
            del self.tab_bar.rows[row.row_number]
            row.delete()
            #self.tab_bar.sort_rows()

        if not self.tab_bar.fields_list:
            self.tab_bar.hide()

    def delete(self):
        super(Tabbed_Window, self).delete()
        del self.tab_targets


def test_Tabbed_Window():
    import pride.gui
    import pride.gui.main
    window = pride.objects[pride.gui.enable(x=52, y=52)]
    window.create(pride.gui.main.Gui, startup_programs=(Tabbed_Window, ),
                  user=pride.objects["/User"])

if __name__ == "__main__":
    test_Tabbed_Window()
