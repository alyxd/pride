import operator

import pride
import pride.functions.utilities
import pride.components.base as base
import pride.gui
import pride.gui.shapes
import pride.gui.color
import pride.gui.sdllibrary
Instruction = pride.Instruction

import sdl2

lerp = pride.gui.lerp

def create_texture(size, access=sdl2.SDL_TEXTUREACCESS_TARGET,
                   factory="/Python/SDL_Window/Renderer/SpriteFactory",
                   renderer="/Python/SDL_Window/Renderer"):
    return objects[factory].create_texture_sprite(objects[renderer].wrapped_object,
                                                  size, access=access)

class Organizer(base.Base):
    """ Note: Using both horizontal (top/bottom) and vertical (left/right) pack modes will break *unless* a main item is present.
        If a main item is not present, then the organizer would have to decide whether to scale the height of the vertical item according to either the top/bottom arbitrarily
        Quoting the zen of python:

            > In the face of ambiguity, refuse the temptation to guess.

        If mixing horizontal and vertical pack modes is necessary, include a `main` object."""
    mutable_defaults = {"pack_queue" : list, "window_queue" : list}

    def schedule_pack(self, item):
        if isinstance(item, pride.gui.sdllibrary.SDL_Window):
            if item not in self.window_queue:
                self.window_queue.append(item)
        else:
            assert item not in self.pack_queue
            self.pack_queue.append(item)

    def unschedule_pack(self, item):
        try:
            if item.__class__.__name__ == "SDL_Window":
                self.window_queue.remove(item)
            else:
                self.pack_queue.remove(item)
        except ValueError:
            return

    def pack_items(self):
        if self.window_queue:
            window_queue = self.window_queue
            self.window_queue = []
            for sdl_window in window_queue:
                self.pack_children(sdl_window, list(sdl_window.gui_children))
                sdl_window._in_pack_queue = False
        if self.pack_queue:
            #self.alert("Packing {} top-level items".format(len(self.pack_queue)))
            pack_queue = sorted(self.pack_queue, key=operator.attrgetter('z'))
            del self.pack_queue[:]
            for item in pack_queue:
                self.pack_children(item, list(item.children))
                item._in_pack_queue = item._pack_requested = False

    def pack_children(self, parent, children):
        if not children:
            return
        area = parent.area
        z = parent.z + 1

        _lists = {"top" : [], "main" : [], "bottom" : [], "left" : [],
                  "right" : []}
        old_area = dict()
        for child in children:
            pack_mode = child.pack_mode
            if pack_mode is None or child.hidden:
                continue
            if pack_mode == "fill":
                old_area[child] = child.area
                child.z = z
                child.area = area
                continue
            else:
                try:
                    _lists[pack_mode].append(child)
                except KeyError:
                    raise NotImplementedError("Unsupported pack mode '{}' on {}".format(pack_mode, child))
                old_area[child] = child.area

        top, main, bottom, left, right = (_lists[item] for item in ("top", "main", "bottom", "left", "right"))
        assert len(main) in (0, 1), main

        if top or main or bottom:
            self.pack_verticals(area, z, top, main, bottom)
            top_height = sum(child.h for child in top)
            bottom_height = sum(child.h for child in bottom)
        else:
            top_height = bottom_height = 0

        if left or main or right:
            self.pack_horizontals(area, z, left, main, right,
                                  top_height, bottom_height)

        for child in children:
            if child.hidden or child._parent_hidden:
                continue
            _old_area = old_area[child]
            area = child.area
            if parent._in_pack_queue or area != _old_area:
                self.pack_children(child, list(child.children))
                child._pack_requested = False
                if area != _old_area:
                    child.handle_area_change(_old_area)

    def pack_horizontals(self, area, z, left, main, right, top_height, bottom_height):
        x, y, w, h = area
        left_main_right = left + main + right
        left_main_right_len = len(left_main_right)
        available_space = w
        _spacing = available_space / left_main_right_len
        small_items = [child for child in left_main_right if child.w_range[1] < _spacing]
        if small_items:
            while True: # extra space caused by small items can make spacing larger and make items that were not small become small
                spacing = _spacing + sum(_spacing - item.w_range[1] for item in small_items) / ((len(left_main_right) - len(small_items)) or 1)
                new_small_items = [child for child in left_main_right if child.w_range[1] < spacing and
                                child not in small_items]
                if new_small_items:
                    small_items += new_small_items
                else:
                    extra = w - ((spacing * len([child for child in left_main_right if child not in small_items])) +
                                sum(child.w_range[1] for child in small_items))
                    break
        else:
            spacing = _spacing
            extra = w - (spacing * left_main_right_len)
        assert extra >= 0, extra

        offset = 0
        for child in left:
            child.y = y + top_height
            child.h = h - (top_height + bottom_height)
            child.x = x + offset
            child.w = spacing
            if extra and child not in small_items:
                child.w += extra
                extra = 0
            child.z = z
            offset += child.w

        if main:
            main_item = main[0]
            main_item.x = x + offset
            main_item.w = spacing
            if extra and main_item not in small_items:
                main_item.w += extra
                extra = 0
            offset += main_item.w

        offset = 0
        for child in right:
            child.y = y + top_height
            child.h = h - (top_height + bottom_height)
            child.w = spacing
            if extra and child not in small_items:
                child.w += extra
                extra = 0
            offset += child.w
            child.x = x + w - offset
            child.z = z

    def pack_verticals(self, area, z, top, main, bottom):
        x, y, w, h = area
        top_main_bottom = top + main + bottom
        top_main_bottom_len = len(top_main_bottom)
        available_space = h

        _spacing = available_space / (top_main_bottom_len or 1)
        small_items = [child for child in top_main_bottom if child.h_range[1] < _spacing]
        if small_items:
            while True:
                spacing = _spacing + sum(_spacing - item.h_range[1] for item in small_items) / ((top_main_bottom_len - len(small_items)) or 1)
                new_small_items = [child for child in top_main_bottom if child.h_range[1] < spacing and
                                   child not in small_items]
                if new_small_items:
                    small_items += new_small_items
                else:
                    extra = h - ((spacing * len([child for child in top_main_bottom if child not in small_items])) +
                                sum(child.h_range[1] for child in small_items))
                    break
        else:
            spacing = _spacing
            extra = h - (spacing * top_main_bottom_len)
        assert extra >= 0, extra

        offset = 0
        for child in top:
            child.x = x
            child.w = w
            child.y = y + offset
            child.h = spacing
            if extra and child not in small_items:
                child.h += extra
                extra = 0
            child.z = z
            offset += child.h # h_range can constrain, so use child.h instead of spacing
        top_height = offset

        if main:
            main_item = main[0]
            main_item.y = y + offset
            main_item.h = spacing
            if extra and main_item not in small_items:
                main_item.h += extra
                extra = 0
            main_item.z = z
            offset += main_item.h

        offset = 0
        for child in bottom:
            child.x = x
            child.w = w
            child.h = spacing
            if extra and child not in small_items:
                child.h += extra
                extra = 0
            offset += child.h
            child.y = y + h - offset
            child.z = z


class Organized_Object(pride.gui.shapes.Bounded_Shape):

    defaults = {'x' : 0, 'y' : 0, "size" : (0, 0), "pack_mode" : '',
                "_pack_requested" : False, "_in_pack_queue" : False}

    #predefaults = {"sdl_window" : ''}

    mutable_defaults = {"_children" : list}
    verbosity = {"packed" : "packed"}

    def pack(self):
        parent = self.parent
        if not parent._in_pack_queue:
            parent._in_pack_queue = self._pack_requested = True
            self.sdl_window.organizer.schedule_pack(parent)
        #if not self._pack_scheduled2:
        #    parent = self.parent
        #    pack_scheduled = False
        #    while parent.reference != self.sdl_window:
        #        if parent._pack_scheduled:
        #            pack_scheduled = True
        #            break
        #        else:
        #            parent = parent.parent
        #    if not pack_scheduled and not parent.deleted:
        #        parent = self.parent
        #        if not parent.deleted:
        #            #print
        #            #print objects[self.sdl_window.organizer.reference] # somehow causes KeyError
        #            #print
        #            self.sdl_window.organizer.schedule_pack(parent)
        #            parent._pack_scheduled = True
        #            self._pack_scheduled2 = True


class _Window_Object(Organized_Object):
    """ to do: write documentation!

        FAQ: I get the following message when exiting, why?:
            Exception TypeError: "'NoneType' object is not callable" in <bound method Window.__del__ of <sdl2.ext.window.Window object at 0xXXXXXXX> ignore
            Except AttributeError: "'NoneType' object has no attribute 'SDL_DestroyTexture'" in ignored
        A: Your window object still exists somewhere and needs to be deleted properly. Make sure there are no scheduled instructions and/or attributes using your object"""
    defaults = {"outline_width" : 1, "center_text" : True,
                "held" : False, "allow_text_edit" : False, "wrap_text" : True,
                "_ignore_click" : False, "hidden" : False, "movable" : False,
                "text" : '', "scroll_bars_enabled" : False,
                "_scroll_bar_h" : None, "_scroll_bar_w" : None,
                "theme_type" : "pride.gui.themes.Minimal_Theme",
                "_selected" : False,
                "_cached" : False, "tip_bar_text" : '',
                "theme_profile" : "default", "clickable" : True}

    predefaults = {"_scale_to_text" : False, "_texture_invalid" : False,
                   "_texture_window_x" : 0, "_texture_window_y" : 0,
                   "_text" : '', "draw_cursor" : False,
                   "queue_scroll_operation" : False, "_backup_w_range" : tuple(),
                   "_old_z" : 0, "_parent_hidden" : False, "_hidden" : False,
                   "_always_on_top" : False, "use_custom_colors" : False,
                   "_status" : None, "_tip_set" : False,
                   "_theme_profile" : "default"}

    mutable_defaults = {"_draw_operations" : list, "_children" : list,
                        "scroll_instructions" : list, "colors" : dict}
    verbosity = {"press" : "vv", "release" : "vv"}

    hotkeys = {("\b", None) : "handle_backspace", ("\n", None) : "handle_return"}
    inherited_attributes = {"hotkeys" : dict}
    autoreferences = ("_sdl_window", )

    def _get_always_on_top(self):
        return self._always_on_top
    def _set_always_on_top(self, value):
        self._always_on_top = value
        if value:
            self.sdl_window.user_input.always_on_top.append(self)
        else:
            try:
                self.sdl_window.user_input.always_on_top.remove(self)
            except ValueError:
                pass
    always_on_top = property(_get_always_on_top, _set_always_on_top)

    def _get_texture_invalid(self):
        return self._texture_invalid
    def _set_texture_invalid(self, value):
        assert not self.deleted
        if value and not self.hidden and not self._texture_invalid:
            self.sdl_window.invalidate_object(self)
        self._redraw_needed = self._texture_invalid = value
    texture_invalid = property(_get_texture_invalid, _set_texture_invalid)

    def _on_set(self, coordinate, value):
        if not self.texture_invalid:
            self.texture_invalid = True
        super(_Window_Object, self)._on_set(coordinate, value)

    def _get_text(self):
        return self._text
    def _set_text(self, value):
        self._text = value
        if value and self.scale_to_text:
            w, h = self.sdl_window.renderer.get_text_size(self.area, value)
            w += 20
            if not self._backup_w_range:
                self._backup_w_range = self.w_range
            self.w_range = (0, w)
        elif self._backup_w_range and self._backup_w_range != self.w_range:
            self.w_range = self._backup_w_range
        self.texture_invalid = True
    text = property(_get_text, _set_text)

    def _get_scale_to_text(self):
        return self._scale_to_text
    def _set_scale_to_text(self, value):
        self._scale_to_text = value
        # If text and scale_to_text are set as kwargs, there is no priority to set scale_to_text first
        # if text is set first, then _set_text wouldn't scale w properly
        self.text = self.text # triggers _set_text descriptor;
    scale_to_text = property(_get_scale_to_text, _set_scale_to_text)


    for color_key in ("background", "text", "text_background", "shadow",
                      "shadow_thickness", "glow", "glow_thickness",
                      "vanishing_point"):
        def _getter(self, color_key=color_key):
            profile = self.theme_profile
            if profile in self.colors and color_key in self.colors[profile]:
                return self.colors[profile][color_key]
            return self.theme.theme_colors[profile][color_key]
        def _setter(self, value, color_key=color_key):
            try:
                self.colors[self.theme_profile][color_key] = value
            except KeyError:
                self.colors[self.theme_profile] = {color_key : value}
            self.texture_invalid = True
        def _deleter(self, color_key=color_key):
            del self.colors[self.theme_profile][color_key]

        if color_key not in ("shadow_thickness", "glow_thickness", "vanishing_point"):
            vars()["{}_color".format(color_key)] = property(_getter, _setter, _deleter)
        else:
            vars()[color_key] = property(_getter, _setter, _deleter)

    def _get_theme_profile(self):
        return self._theme_profile
    def _set_theme_profile(self, value):
        self._theme_profile = value
        self.texture_invalid = True
    theme_profile = property(_get_theme_profile, _set_theme_profile)

    def _get_color(self):
        return self.colors["color"]
    def _set_color(self, colors):
        self.colors["color"] = colors
        self.texture_invalid = True
    color = property(_get_color, _set_color)

    def _get_hidden(self):
        return self._hidden or self._parent_hidden
    def _set_hidden(self, value):
        self._hidden = value
    hidden = property(_get_hidden, _set_hidden)

    def _get_parent_application(self):
        result = None
        instance = self.parent
        while not result:
            if isinstance(instance, Application):
                result = instance
            else:
                try:
                    instance = instance.parent
                except AttributeError:
                    if isinstance(self, Application):
                        result = self
                    else:
                        raise AttributeError("Unable to find parent application of {}".format(self))
        return result
    parent_application = property(_get_parent_application)

    def _get_children(self):
        return self._children
    def _set_children(self, value):
        self._children = value
    children = property(_get_children, _set_children)

    def _get_sdl_window(self):
        return (self._sdl_window or getattr(self.parent, "sdl_window", self.parent_name))
    def _set_sdl_window(self, value):
        assert not isinstance(value, str)
        self._sdl_window = value
    sdl_window = property(_get_sdl_window, _set_sdl_window)

    def __init__(self, **kwargs):
        #self.colors = self.theme_type.theme_colors.copy()#DEFAULT_COLORS.copy()
        super(_Window_Object, self).__init__(**kwargs)
        self.texture_invalid = True

        self.theme = self.create(self.theme_type, wrapped_object=self)

        self._children.remove(self.theme)
        window = self.sdl_window
        window.user_input._update_coordinates(self, self.reference, self.area, self.z)
        #self.texture = window.create_texture(window.size)
        self.pack()

    def create(self, *args, **kwargs):
        kwargs.setdefault('z', self.z + 1)
        kwargs.setdefault("sdl_window", self.sdl_window)
        return super(_Window_Object, self).create(*args, **kwargs)

    def add(self, _object):
        self._children.append(_object)
        super(_Window_Object, self).add(_object)

    def remove(self, _object):
        try:
            self._children.remove(_object)
        except ValueError:
            if _object is not self.theme:
                self.alert("Failed to remove {} from _children".format(_object))
                raise
        super(_Window_Object, self).remove(_object)

    def press(self, mouse):
        self.alert("Pressing", level=self.verbosity["press"])
        self.held = True
        for instance in self.children:
            instance.held = True

    def release(self, mouse):
        self.alert("Releasing", self.verbosity["release"])
        self.held = False
        if self._ignore_click:
            self._ignore_click = False
        elif mouse.button == 1:
            self.left_click(mouse)
        elif mouse.button == 3:
            self.right_click(mouse)
        else:
            self.alert("Button {} not yet implemented".format(mouse.button), level=0)

    def left_click(self, mouse):
        pass

    def right_click(self, mouse):
        pass

    def mousewheel(self, x_amount, y_amount):
        pass

    def mousemotion(self, x, y, x_change, y_change):
        pass

    def on_hover(self):
        #self.alert("Mouse hovering")
        if self.theme_profile == "interactive":
            self.theme_profile = "hover"
            self.texture_invalid = True

        if self.tip_bar_text:
            self.sdl_window.set_tip_bar_text(self.tip_bar_text)
            self._tip_set = True

    def hover_ends(self):
        if self.theme_profile == "hover":
            self.theme_profile = "interactive"
            self.texture_invalid = True
        if self._tip_set:
            self._clear_tip_bar_text()

    def _clear_tip_bar_text(self):
        if self._tip_set:
            self.sdl_window.clear_tip_bar_text()
            self._tip_set = False

    def hide(self, parent_call=False):
        # include if already hidden early return?
        self.sdl_window.remove_window_object(self)
        self.sdl_window.dirty_layers.add(self.z)
        if parent_call:
            self._parent_hidden = True
        else:
            self.hidden = True
        self.hover_ends()
        for child in self.children:
            child.hide(True)

    def show(self, parent_call=False):
        # include if not hidden early return?
        if parent_call:
            self._parent_hidden = False
        else:
            self.hidden = False
        if not self.hidden:
            window = self.sdl_window
            window.user_input._update_coordinates(self, self.reference, self.area, self.z)
            assert not self.hidden
            assert not self.deleted
            self.texture_invalid = True
            for child in self.children:
                child.show(True)

    def draw(self, figure, *args, **kwargs):
        """ Draws the specified figure on self. figure can be any shape supported
            by the renderer, namely: "rect", "line", "point", "text", and "rect_width".
            The first argument(s) will include the destination of the shape in the
            form appropriate for the figure specified (i.e. an area for a rect, a
            pair of points for a point). For a full list of arguments for a
            particular figure, see the appropriate draw method of the renderer. """
        # draw operations are enqueued and processed in batches by the Renderer
        self._draw_operations.append((figure, args, kwargs))

    def _redraw(self):
        assert not (self.hidden or self._parent_hidden)
        if self._redraw_needed or not self._draw_operations:
            del self._draw_operations[:]
            self.draw_texture()
        self.texture_invalid = False

    def draw_texture(self):
        assert not self.hidden
        assert not self._parent_hidden
        self.theme.draw_texture()

    def pack(self):
        super(_Window_Object, self).pack()
        self.sdl_window._schedule_run()

    def delete(self):
        assert not self.deleted, self
        self.sdl_window.dirty_layers.add(self.z)
        self._clear_tip_bar_text()
        self.theme.delete()
        if self.parent.reference != self.sdl_window:
            self.pack()
        self.sdl_window.remove_window_object(self)
        super(_Window_Object, self).delete()

    def deselect(self, mouse, next_active_object):
        self._selected = False

    def select(self, mouse):
        self._selected = True

    def text_entry(self, text):
        if self.allow_text_edit:
            self.text += text

    def handle_return(self):
        pass

    def handle_backspace(self):
        if self.allow_text_edit:
            self.text = self.text[:-1]

    def __getstate__(self):
        state = super(_Window_Object, self).__getstate__()
        state["theme"] = self.theme.save()
        del state["_draw_operations"]
        del state["_children"]
        print self, "getstate"
        import pprint
        pprint.pprint(self.objects)

        return state

    def on_load(self, state):
        super(_Window_Object, self).on_load(state)
        self.theme = pride.functions.utilities.resolve_string(self.theme_type).load(self.theme)
        self.theme.wraps(self)
        self._draw_operations = []
        self._children = list(super(_Window_Object, self).children)
        print self, "on load"
        import pprint
        pprint.pprint(self.objects)
        self._children.remove(self.theme)

    def show_status(self, text):
        self.sdl_window.set_tip_bar_text(text)

    def clear_status(self):
        self.sdl_window.clear_tip_bar_text()

    def handle_area_change(self, old_area):
        assert old_area != self.area


class Animated_Object(_Window_Object):

    defaults = {"frame_count" : 5, "_backup_theme_profile" : None,
                "theme_type" : "pride.gui.themes.Animated_Theme2",
                "animation_enabled" : True, "click_animation_enabled" : True,
                "click_radius" : 2,
                "_mouse_click_type" : "pride.gui.gui._Mouse_Click"}
    predefaults = {"animating" : False, "_old_theme" : None,
                   "_colors_backup" : None, "_start_animation_enabled" : False,
                   "_transition_state" : 0}

    def _get_theme_profile(self):
        return super(Animated_Object, self)._get_theme_profile()
    def _set_theme_profile(self, value):
        if self.animating:
            self.end_animation()
        if value != self.theme_profile:
            self._old_theme = self.theme_profile
        super(Animated_Object, self)._set_theme_profile(value)
        if (self.animation_enabled and
            self._old_theme is not None and
            self._old_theme != self.theme_profile):
            self.start_animation()
    theme_profile = property(_get_theme_profile, _set_theme_profile)

    def __init__(self, **kwargs):
        super(Animated_Object, self).__init__(**kwargs)
        self._start_animation_enabled = True

    def press(self, mouse):
        super(Animated_Object, self).press(mouse)
        if self.click_animation_enabled:
            x, y = mouse.x, mouse.y
            radius = self.click_radius
            rect = self.create(self._mouse_click_type)
            rect.area = (x - radius, y - radius, radius, radius)

    def show(self, parent_call=False):
        super(Animated_Object, self).show(parent_call)
        backup = self._backup_theme_profile or self.theme_profile
        assert backup is not None
        self.theme_profile = "blank" # forces fade-in from blank color
        self.theme_profile = backup
        self._backup_theme_profile = None

    def _invalidate_texture(self):
        self.texture_invalid = True

    def start_animation(self):
        if not self._start_animation_enabled: # dont animate when setting initial theme_profile
            return
        assert self.theme_profile != self._old_theme
        self.animating = True
        self.texture_invalid = True
        self._transition_state = 0

    def end_animation(self):
        self.animating = False
        self.colors.clear()
        self._old_theme = None
        self._transition_state = 0

    def handle_transition_animation_end(self):
        # this is used by the Animated_Theme end animation, NOT the color animation performed by this class
        pass

    def draw_texture(self):
        animating = self.animating
        state_counter = self._transition_state
        if animating:
            if state_counter == self.frame_count:
                self.end_animation()
            else:
                assert self.theme_profile != self._old_theme, (self.theme_profile, self._old_theme, state_counter, self.frame_count)
                assert state_counter < self.frame_count, (state_counter, self.frame_count)
                self.next_frame()
                self._transition_state += 1
                assert not self.deleted
                self.sdl_window.schedule_postdraw_operation(self._invalidate_texture, self)
        super(Animated_Object, self).draw_texture()

    def next_frame(self):
        end_profile = self.theme_profile
        old_profile = self._old_theme
        unit = 1.0 / self.frame_count
        scalar = self._transition_state
        set_theme = super(Animated_Object, self)._set_theme_profile
        theme = self.theme
        _theme_colors = theme.theme_colors
        _cache = theme._cache # conspires with Minimal_Theme class to keep the cache fresh when theme colors are edited
        for key in theme.theme_colors[end_profile].keys():
            if key not in ("shadow_thickness", "glow_thickness"):
                key += "_color"
            try:
                new_value = _cache[(scalar, old_profile, end_profile, key)]
            except KeyError:
                if key not in ("shadow_thickness", "glow_thickness"):
                    end_value = _theme_colors[end_profile][key[:-6]]#getattr(self, key)
                else:
                    end_value = _theme_colors[end_profile][key]
                set_theme(old_profile)
                old_value = getattr(self, key)
                set_theme(end_profile)
                if old_value != end_value:
                    new_value = lerp(old_value, end_value, scalar * unit)
                else:
                    new_value = end_value
                if key in ("shadow_thickness", "glow_thickness"):
                    new_value = int(new_value)
                _cache[(scalar, old_profile, end_profile, key)] = new_value
            assert not isinstance(new_value, float)
            setattr(self, key, new_value)

    def handle_area_change(self, old_area):
        assert self.area != old_area
        if self.animation_enabled:
            try:
                self.theme.draw_frames(old_area)
            except AttributeError:
                if hasattr(self.theme, "draw_frames"):
                    raise


class _Mouse_Click(Animated_Object):

    defaults = {"clickable" : False, "pack_mode" : "fill"}

    def handle_transition_animation_end(self):
        #self.delete()
        self.sdl_window.schedule_postdraw_operation(self.delete, self)


Window_Object = Animated_Object # can upgrade everything in-place by changing this


class Window(Window_Object):

    defaults = {"pack_mode" : "main"}


class Container(Window_Object):

    defaults = {"pack_mode" : "top"}


class Button(Window_Object):

    defaults = {"pack_mode" : "top", "theme_profile" : "interactive"}


class Application(Window):
    """ Applications have an application_window attribute.
        This extra window allows the background to be customized (e.g. rotating stars)"""
    defaults = {"application_window_type" : "pride.gui.gui.Window"}
    autoreferences = ("application_window", )

    def __init__(self, **kwargs):
        super(Application, self).__init__(**kwargs)
        self.application_window = self.create(self.application_window_type)

    def __getstate__(self):
        state = super(Application, self).__getstate__()
        del state["application_window"]
        return state

    def on_load(self, state):
        super(Application, self).on_load(state)
        self.application_window = self.objects["Window"][0] # brittle, needs to be done properly


class Placeholder(Container):

    defaults = {"pack_mode" : "left", "theme_profile" : "placeholder"}


class Texture_Atlas(pride.components.base.Base):

    defaults = {'x' : 0, 'y' : 0, 'w' : 4096, 'h' : 4096, 'z' : -1,
                "size" : (4096, 4096), "subsections" : tuple(),
                "placeholder_type" : Placeholder, "pack_mode" : "main",
                "sdl_window" : None}

    predefaults = {"_pack_scheduled" : False}#{"sdl_window" : ''}
    required_attributes = ("sdl_window", )

    def _get_area(self):
        return self.x, self.y, self.w, self.h
    area = property(_get_area)

    def _get_position(self):
        return self.x, self.y
    position = property(_get_position)

    def __init__(self, *args, **kwargs):
        super(Texture_Atlas, self).__init__(*args, **kwargs)
        # top-left: screen;      top-right: vertical placeholders
        #         bottom-top: square placeholders
        #         bottom-bottom: horizontal placeholders
        placeholder_type = self.placeholder_type
        sdl_window = self.sdl_window

        screen_w, screen_h = self.screen_size = pride.objects[sdl_window].size

        top = self.create(placeholder_type, pack_mode="top",
                          sdl_window=sdl_window, h_range=(screen_h, screen_h))
        bottom = self.create(placeholder_type, pack_mode="top", sdl_window=sdl_window)

        #top_left = top.create(placeholder_type, w_range=(screen_w, screen_w),
        #                      pack_mode="left", sdl_window=sdl_window)
        #top_right = top.create(placeholder_type, pack_mode="left", sdl_window=sdl_window)

        #bottom_top = bottom.create(placeholder_type, pack_mode="top", sdl_window=sdl_window)
        #bottom_bottom = bottom.create(placeholder_type, pack_mode="top", sdl_window=sdl_window)
        #self.subsections = (top_left, top_right, bottom_top, bottom_bottom)

    def add_to_atlas(self, window_object):
        subsection, pack_mode = self.determine_subsection(window_object)
        placeholder = subsection.create(self.placeholder_type, pack_mode=pack_mode,
                                        sdl_window=self.sdl_window,
                                        w_range=(window_object.w, window_object.w),
                                        h_range=(window_object.h, window_object.h))
        window_object._texture_atlas_reference = placeholder.reference
        #placeholder.pack()
        return placeholder.position

    def remove_from_atlas(self, window_object):
        pride.objects[window_object._texture_atlas_reference].delete()
        del window_object._texture_atlas_reference

    def determine_subsection(self, window_object):
        # determine approximate "square-ness" of (w, h)
        #   - if w / h > 2:
        #       item is horizontal
        #   - if h / w > 2:
        #       item is vertical
        #   - else item fits well enough in a square
        # also returns which way to pack the item into the according subsection
        w, h = window_object.size
        if h and w / h > 2:
            return self.subsections[3], "top" # horizontal -> bottom: bottom
        elif w and h / w > 2:
            return self.subsections[1], "left" # vertical -> top: right
        else:
            return self.subsections[2], "left" # square -> bottom: top
