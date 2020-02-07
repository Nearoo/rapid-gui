import pyglet, queue, typing, threading
from dataclasses import dataclass

Point = typing.Tuple[int, int]
Color = typing.Tuple[int, int, int, int]


@dataclass
class GuiApp:
    """ This class represents a gui app. It holds a window and can register elements that draw on it. """
    width: int = 500
    height: int = 500
    background_color: Color = (255, 255, 255, 255)

    def __post_init__(self):
        self.window = pyglet.window.Window(self.width, self.height)
        self.components = {}
        self.set_background_color(*self.background_color)

    def set_background_color(self, r, g, b, a=255):
        pyglet.gl.glClearColor(*map(lambda x: x / 255, [r, g, b, a]))

    def add_component(self, identifier, comp):
        self.components[identifier] = comp
        self.window.push_handlers(comp)

    def on_draw(self):
        self.window.clear()

    def run(self):
        self.window.push_handlers(self)  # Push own event handlers on very top of event stack
        pyglet.app.run()


@dataclass
class GuiComponent(pyglet.event.EventDispatcher):
    """ This abstract class provides the basics to build a gui component.

    It executes callbacks from the queue and registers even callbacks. Also offers a couple of useful methods.
    """
    q: queue.Queue = queue.Queue()
    type: str = ""
    identifier: str = ""
    name: str = None
    update_interval: float = 0.1

    def __post_init__(self):
        self.name = self.name if self.name else type(self).__name__
        self.register_event_type("on_process_queued_calls")
        pyglet.clock.schedule_interval_soft(
            lambda dt: self.dispatch_event("on_process_queued_calls"),
            .015  # ~ 60 fps
        )

    def on_process_queued_calls(self):
        """Process calls by attempting to call methods with same name as call or raising AttributeError.
        The default constructor schedules this method to be called every :update_intveral:-seconds."""
        for i in range(self.q.qsize()):
            try:
                callback = self.q.get(block=False)
            except queue.Empty:
                break

            fname, args, kwargs, ret_q = callback
            f = getattr(self, fname, None)
            if callable(f):
                ret_q.put(f(*args, **kwargs))
            else:
                raise AttributeError(f"Method {fname} doesn't exist for object of type {self.name}")

    def add_event_listener(self, f):
        """ Pushes f onto own event callback stack """
        thr = [threading.Thread(target=f, daemon=True)]

        def async_f():
            if not thr[0].is_alive():
                thr[0] = threading.Thread(target=f, daemon=True)
                thr[0].start()

        async_f.__name__ = f.__name__
        self.push_handlers(async_f)


class Illustrator:
    """ An Illustrator functions similar to pyglet.gl.Batch but supports many useful drawing calls.

    Usage:
    * Instantiate
    * Add graphics calls
    * call draw() to execute drawing calls

    Contrary to batches, elements will be drawn in the same order of the calls.
    """

    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self.draw_number = 0

    def add_path(self, points: typing.Tuple[Point, ...], color: Color = (0, 0, 0, 255)):
        """ Draws line along the path given by points with color color. """
        vector_list = []
        for i in range(len(points) - 1):
            vector_list.extend(points[i])
            vector_list.extend(points[i + 1])

        num_points = len(vector_list) // 2
        color_list = color * num_points

        self.draw_number += 1
        self.batch.add(num_points, pyglet.gl.GL_LINES, self.get_new_group(), ('v2f', vector_list), ('c4B', color_list))

    def get_new_group(self):
        """ Returns a new group with ordering one larger to the previous call"""
        self.draw_number += 1
        return pyglet.graphics.OrderedGroup(self.draw_number)

    def draw(self):
        self.batch.draw()

    def add_quad(self, edge_points: typing.Tuple[Point, Point, Point, Point], color: Color):
        a, b, c, d = edge_points
        self.batch.add(4, pyglet.gl.GL_QUADS, self.get_new_group(), ('v2f', (*a, *b, *c, *d)), ('c4B', color * 4))


@dataclass
class Rectangle(GuiComponent):
    x: int = 0
    y: int = 0
    width: int = 10
    height: int = 10
    background_color: Color = None # None == transparent
    line_color: Color = None

    def __post_init__(self):
        super().__post_init__()
        self.register_event_type("on_clicked")
        self.register_event_type("on_hover_begin")
        self.register_event_type("on_hover_end")

        self._mouse_hovering = False

    def collides_with(self, x, y):
        return (self.x <= x <= (self.x + self.width)) and (self.y <= y <= (self.y + self.height))

    def draw(self):
        illus = Illustrator()

        x, y, w, h = self.x, self.y, self.width, self.height
        verts = (x, y), (x + w, y), (x + w, y + h), (x, y + h)

        if self.background_color:
            illus.add_quad(verts, self.background_color)
        if self.line_color:
            illus.add_path(verts + (verts[0],), self.line_color)
        illus.draw()

    def on_draw(self):
        self.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        if self.collides_with(x, y):
            self._mouse_hovering = True

            if not self.collides_with(x + dx, y + dy):
                self.dispatch_event("on_hover_end")
        else:
            self._mouse_hovering = False
            if self.collides_with(x + dx, y + dy):
                self.dispatch_event("on_hover_begin")

    def on_mouse_press(self, x, y, button, modifiers):
        if self.collides_with(x, y):
            self.dispatch_event("on_clicked", x, y, button, modifiers)

    def get_center(self):
        return self.x + self.width/2, self.y + self.height/2

    def get_width(self):
        return self.width

    def set_width(self, val):
        self.width = val

    def get_height(self):
        return self.height

    def set_height(self, val):
        self.height = val

    def set_center(self, x, y):
        self.x, self.y = x-self.width/2, y-self.height/2

    def set_background_color(self, color: Color):
        self.background_color = color

    def mouse_is_hovering(self):
        return self._mouse_hovering


@dataclass
class Button(Rectangle):
    label_text: str = ""
    font_size: int = 20
    font_color: Color = (255, 255, 255, 255)
    anchor_x: str = "center"
    anchor_y: str = "center"
    font_name: str = "Arial"
    enabled: bool = True

    def __post_init__(self):
        super().__post_init__()

        lx, ly = self.get_center()
        self.label = pyglet.text.Label(text=self.label_text,
                                       font_name=self.font_name,
                                       font_size=self.font_size,
                                       color=self.font_color,
                                       x=lx, y=ly,
                                       anchor_x=self.anchor_x,
                                       anchor_y=self.anchor_y)

        self.register_event_type("on_pressed")

        r, g, b, a = self.background_color

        self._no_hover_bg_color = self.background_color
        dc = 5
        self._hover_bg_color = min(255, r+dc), min(255, g+dc), min(255, b+dc), a
        dc = 20
        self._click_bg_color = min(255, r+dc), min(255, g+dc), min(255, b+dc), a

    def on_draw(self):
        if not self.enabled:
            self.set_background_color((230, 230, 230, 255))
        super().on_draw()
        self.label.draw()
        self.background_color = self._hover_bg_color if self.mouse_is_hovering() else self._no_hover_bg_color

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def on_clicked(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT and self.enabled:
            self.dispatch_event("on_pressed")

    def on_pressed(self):
        self.set_background_color(self._click_bg_color)

    def set_label(self, text):
        self.label.text = text
        self.label_text = text

    def get_label(self):
        return self.label_text

@dataclass
class ProgressBar(Rectangle):
    bar_color: Color = (64, 219, 211, 255)
    pct: int = 20
    border_width: int = 5

    def __post_init__(self):
        super().__post_init__()
        self.inner_rect_max_width = self.width - self.border_width*2
        self.inner_rect = Rectangle(x=self.x            + self.border_width,
                                    y=self.y            + self.border_width,
                                    width=int(self.inner_rect_max_width*self.pct/100),
                                    height=self.height  - self.border_width*2,
                                    background_color=self.bar_color)

    def on_draw(self):
        super().on_draw()
        w_old = self.inner_rect.get_width()
        w_target = self.inner_rect_max_width*(self.pct/100)
        w_new = (w_old + w_target) / 2
        self.inner_rect.set_width(w_new)
        self.inner_rect.draw()

    def set_pct(self, pct: int):
        self.pct = max(0, min(100, pct))

    def get_pct(self) -> int:
        return int(self.pct)
