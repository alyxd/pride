import time
import getpass

import pride
import pride.gui.gui
import pride.components.datatransfer
import pride.components.database

class Client(pride.components.datatransfer.Data_Transfer_Client):

    def receive(self, messages):
        for sender, message in messages:
            self.parent.receive_message(sender, message)


class Contact_Button(pride.gui.gui.Button):

    def left_click(self, mouse):
        self.parent_application.current_contact = self.text
        self.alert("Set contact to: {}".format(self.text), level=0)


class Popup_Menu(pride.gui.gui.Window):

    defaults = {"location" : "popup_menu", "background_color" : (15, 65, 15, 225),
                "h_range" : (0, 300), "w_range" : (0, 400)}

    def __init__(self, **kwargs):
        super(Popup_Menu, self).__init__(**kwargs)
        self.create("pride.gui.widgetlibrary.Dialog_Box", text=self.text,
                    callback=(self.reference, "handle_input"))

    def handle_input(self, text):
        self.parent_application.contacts.create(Contact_Button, text=text[:-1])
        self.delete()
        self.parent_application.pack()


class Add_Contact_Button(pride.gui.gui.Button):

    defaults = {"text" : "add contact..."}

    def left_click(self, mouse):
        self.parent_application.create(Popup_Menu, text="Enter the contacts username: ")
        self.parent_application.pack()


class Contacts(pride.gui.gui.Window):

    def __init__(self, **kwargs):
        super(Contacts, self).__init__(**kwargs)
        self.create(Add_Contact_Button)


class Message_Database(pride.components.database.Database):

    defaults = {"indexable" : False, "hash_function" : "SHA256"}

    schema = {"Messages" : ("message_number INTEGER PRIMARY KEY AUTOINCREMENT",
                                        "sender BLOB", "data_metadata BLOB")}

    def store_message(self, sender, message, timestamp):
        user = pride.objects["/User"]
        if not self.indexable:
            assert user.file_system_key, sender
            assert user.salt, sender
            hasher = pride.functions.security.hash_function(self.hash_function)
            hasher.update(user.file_system_key + user.salt + sender)
            sender = hasher.finalize()
        self.insert_into("Messages", (sender, user.encrypt(timestamp + ": " + message)),
                         columns=("sender", "data_metadata"))

    def retrieve_message(self, sender, message_id=None):
        user = pride.objects["/User"]
        if not self.indexable:
            assert user.file_system_key, sender
            assert user.salt, sender
            hasher = pride.functions.security.hash_function(self.hash_function)
            hasher.update(user.file_system_key + user.salt + sender)
            sender = hasher.finalize()

        if message_id == -1:
            message_id = self.get_last_auto_increment_value("Messages")
        if message_id is not None:
            where["message_id"] = message_id
        cryptogram = self.query("Messages", where=where, retrieve_fields=("data_metadata", ))
        if cryptogram:
            return user.decrypt(cryptogram)


class Messenger(pride.gui.gui.Application):

    defaults = {"password_prompt" : "{}: Please enter the password: ", "password" : '',
                "current_contact" : '', "display_message_timestamps" : True}

    def _get_dialog_box(self):
        return self.application_window.objects["Dialog_Box"][0].objects["Text_Box"][0]
    message_box = property(_get_dialog_box)

    def __init__(self, **kwargs):
        super(Messenger, self).__init__(**kwargs)
        self.database = self.create(Message_Database)
        self.children.remove(self.database)

        self.client = self.create(Client, username=self.username,
                                  password=self.password or
                                           getpass.getpass(self.password_prompt.format(self.reference)))
        self.children.remove(self.client)

        self.contacts = self.application_window.create(Contacts, location="left")
        self.application_window.create("pride.gui.widgetlibrary.Dialog_Box", location="right",
                                       callback=(self.reference, "send_message"))

    def set_current_contact(self, contact):
        self.current_contact = contact
        self.message_box.text = self.database.retrieve_message(contact)

    def send_message(self, message):
        assert self.current_contact
        contact = self.current_contact
        now = time.asctime()
        if self.display_message_timestamps:
            _message = "|>{}:{}: {}".format(self.username, now, message)
        else:
            _message = "|>{}: {}".format(self.username, message)
        self.message_box.text += _message
        self.client.send_to(contact, message)
        self.database.store_message(contact, message, now)

    def receive_message(self, sender, message):
        now = time.asctime()
        if self.display_message_timestamps:
            _message = "{}: {}: {}".format(sender, now, message)
        else:
            _message = "{}: {}".format(sender, message)
        self.alert(_message, level=self.verbosity.get(sender, 0))
        self.database.store_message(sender, message, now)
        self.message_box.text += _message
