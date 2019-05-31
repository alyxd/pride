import pride.functions.utilities
import pride.components.base

class Documentation_Creator(pride.components.base.Base):

    defaults = {"object_name" : ''}
    parser_args = ("object_name", )

    def __init__(self, **kwargs):
        super(Documentation_Creator, self).__init__(**kwargs)
        self.create("pride.components.package.Documentation", resolve_string(self.object_name))

if __name__ == "__main__":
    documentation_creator = Documentation_Creator(parse_args=True)
    # and done!
