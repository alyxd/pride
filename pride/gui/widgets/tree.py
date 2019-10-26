# - make a tree viewer abstraction
# - a file directory explorer is a special case of a tree viewer
# - Use Forms if convenient to make the tree viewer
#
#
# |    parent nodes    |       child nodes       |
#
#
# each parent node is a callable field that sets the content of the child node viewer
# given a list of N nodes, determine how many rows and columns there should be
# - There should be approximately sqrt(N) rows and columns. The last row may not be filled completely.
# - Must put limit to size of sqrt(N) - if N is very large, having more than a certain number of columns would be impossible to display
#     - 64x64 pixels is probably smallest practical size to use for a field
#         - number of fields that can fit in space w: w/64
#         - number of Forms required to display N items: N / min(w/64, sqrt(N))
#         - number of fields in remaining Form: N % min(w/64, sqrt(N))
#     - Put remaining Forms into new page further down
#     - use slider to control which page is selected
# create/show the parent nodes form
# setting the content of the child node viewer should create/show a Form of Callable Fields
# clicking/hovering on child node should show information (e.g. file metadata) in tip bar
# - further behavior can be customised per application
import os
import time

import pride.gui.gui
import pride.gui.widgets.form
from pride.functions.utilities import slide


class Node_Viewer(pride.gui.widgets.form.Form):

    pass


class Tree_Viewer(pride.gui.gui.Application):

    defaults = {"current_node" : '', "max_count" : 8, "node_label" : "current node"}
    autoreferences = ("top", "bottom", "viewer")
    mutable_defaults = {"history" : list}

    def __init__(self, **kwargs):
        super(Tree_Viewer, self).__init__(**kwargs)
        self.create_subcomponents()
        self.view_node()

    def create_subcomponents(self):
        window = self.application_window
        fields=[
                [("handle_back", {"button_text" : '<',
                                  "scale_to_text" : True}),
                 ("handle_up", {"button_text" : "up", "scale_to_text" : True}),
                 ("current_node", {"display_name" : self.node_label}),
                 ("view_node", {"button_text" : "view",
                                "scale_to_text" : True})
                ]
               ]
        self.top = window.create(pride.gui.widgets.form.Form, pack_mode="top",
                                 target_object=self, h_range=(0, .1),
                                 fields=fields)
        self.bottom = window.create("pride.gui.gui.Container", pack_mode="top")

    def view_node(self, identifier=None): # "view" button does not identifier and uses self.current_node
        if identifier is None:
            identifier = self.current_node
        if self.history and identifier == self.history[-1]:
            return
        children = self.lookup(identifier)
        fields = self.children_to_fields(children)
        if self.viewer is not None:
            self.viewer.delete()
        self.viewer = self.bottom.create(Node_Viewer, target_object=self,
                                         fields=fields, row_h_range=(0, .15))
        if self.history: # need to check for contents before testing [-1] in case history is empty
            if self.history[-1] != identifier:
                self.history.append(identifier)
        else:
            self.history.append(identifier)
        self.current_node = identifier
        self.top.update_text("current_node")

    def handle_back(self):
        if self.history:
            assert self.history[-1] == self.current_node, (self.history, self.current_node)
        try:
            prior = self.history[-2]
        except IndexError:
            return
        else:
            del self.history[-2:]
            self.view_node(prior)

    def handle_up(self):
        raise NotImplementedError()

    def children_to_fields(self, children):
        return [[self.new_entry(child) for child in chunk] for
                 chunk in slide(children, self.max_count)]

    @staticmethod
    def new_entry(child):
        return ("view_node", {"button_text" : getattr(child, "text", str(child)),
                              "args" : (child, ), "scale_to_text" : False})

    def lookup(self, identifier):
        raise NotImplementedError()


class Directory_Viewer(Tree_Viewer):

    defaults = {"current_node" : '~/', "selected_file" : '',
                "node_label" : "Directory Explorer"}

    @staticmethod
    def epoch_to_english(_time):
        return time.asctime(time.localtime(_time))

    @staticmethod
    def new_entry(child):
        alt = os.path.split(str(child))[-1]
        if os.path.isfile(child):
            name = "select_file"
        else:
            name = "view_node"
        return (name, {"button_text" : getattr(child, "text", alt),
                       "args" : (child, )})

    def convert_size_unit(self, size):
        units = ["bytes", "KB", "MB", "GB", "TB"]
        index = 0
        while size > 1024:
            index += 1
            size /= 1024.0
        # size < 1024 won't trigger loop and size would be an int
        # int has no `is_integer` method that select_file expects size to have
        return float(size), units[index]

    def select_file(self, identifier):
        self.selected_file = identifier
        extension = os.path.splitext(identifier)[-1]
        size, unit = self.convert_size_unit(os.path.getsize(identifier))
        if not size.is_integer():
            size = "{:.2f}".format(size)
        else:
            size = int(size)
        file_information = os.stat(identifier)
        created  = self.epoch_to_english(file_information.st_ctime)
        modified = self.epoch_to_english(file_information.st_mtime)
        str1 = "Selected file: {}  |  Type: {}  |  Size: {} {}\n".format(identifier, extension, size, unit)
        str2 = str1 + "Created: {}  |  Modified: {}".format(created, modified)
        self.show_status(str2)

    def lookup(self, identifier):
        if identifier == '~': # normalize because os.path.split('~') = ('', '~'); os.path.split("~/") = ('~', '/')
            identifier = "~/"
        identifier = identifier.strip()
        identifier = os.path.expanduser(identifier) # will change ~/ into home directory, or not do anything at all
        if not os.path.exists(identifier) and identifier[0]:
            raise ValueError("{} does not exist".format(identifier))
        if os.path.isdir(identifier):
            children = os.listdir(identifier)
            return sorted([os.path.join(identifier, child) for
                           child in children if max(set(bytearray(child))) < 128])
        else:
            return [identifier]

    def handle_up(self):
        node = os.path.split(self.current_node)[0]
        if node == '~':
            node = "~/"
        if self.current_node != node:
            self.current_node = node
            self.view_node()


def unit_test():
    import pride.gui
    window = pride.objects[pride.gui.enable()]
    window.create("pride.gui.main.Gui", startup_programs=(Directory_Viewer, ),
                  user=pride.objects["/User"])

if __name__ == "__main__":
    unit_test()
