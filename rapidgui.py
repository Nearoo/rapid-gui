import threading, json, queue, sys, typing


class App:
    def __init__(self, data):
        self.data = data
        self.gui_thread = threading.Thread(target=self._run_gui)
        self.call_proxies = {gui_obj["meta"]["identifier"]: GuiCallProxy(self.gui_thread) for gui_obj in
                             data["components"]}

        self.run()

    def __call__(self, target_comp):
        if target_comp in self.call_proxies:
            return self.call_proxies[target_comp]
        else:
            raise ValueError(f"There is no GUI component with identifier {target_comp}")

    def run(self):
        self.gui_thread.start()

    def _run_gui(self):
        import gui_components as gui  # Module has to be imported here so its imported in other thread

        gui_component_mapping = {
            "button": gui.Button,
            "progressbar": gui.ProgressBar,
        }

        app = gui.GuiApp(**self.data["app-properties"])

        for comp in self.data["components"]:
            meta = comp["meta"]
            props = comp['properties']
            _type, identifier = meta["type"], meta["identifier"]
            call_proxy = self.call_proxies[identifier]
            if _type not in gui_component_mapping:
                raise ValueError(f"Unknown GUI component type {_type}")
            
            NewComp = gui_component_mapping[_type]
            app.add_component(identifier, NewComp(call_proxy.get_q(), **meta, **props))

        app.run()


def load(filepath):
    with open(filepath) as f:
        data = json.load(f)

    return App(data)


class _DummyQueue(queue.Queue):
    def __init__(self, size=...):
        pass

    """ Acts like a queue but immediately discards all elements"""
    def put(self, item: typing.Any, block: bool = ..., timeout: typing.Optional[float] = ...) -> None:
        pass

    def get(self, block: bool = ..., timeout: typing.Optional[float] = ...) -> typing.Any:
        return


class GuiCallProxy:
    """
    A class that acts as a buffer between the main thread and a gui thread.

    It stores arbitrary calls for later execution by the gui thread and registers
    event callback functions. Callbacks are put onto the same queue as a call to the method
    "add_event_listener", with the callback function as the first parameter.

    Before putting anything onto the queue, it checks if the GUI thread is still alive. If it is dead, the main
    thread exits silently.

    Callback example:
    gcp = GuiCallProxy()
    gcp.foobar(7, h=3)

    puts ("foobar", [7], {h=3}) onto the queue.

    Signalregistration example:
    gcp = GuiCallProxy()

    @gcp
    def pressed():
        pass

    Puts ("add_event_listener", [pressed], {}) onto the queue.
    Notice that pressed is a reference to the actual function, not just its name.


    """

    def __init__(self, gui_thread: threading.Thread, q: queue.Queue = None):
        self.gui_thread = gui_thread
        self.q = q if q else queue.Queue(200)

    def get_q(self):
        """ Return the queue on which the calls are put """
        return self.q

    def enqueue_call(self, name: str, args, kwargs, ret_q: queue.Queue = _DummyQueue()):
        self._exit_if_gui_dead()
        call = (name, args, kwargs, ret_q)
        try:
            self.q.put(call, timeout=1)
        except queue.Full:
            self._exit_if_gui_dead()
            raise

    def _exit_if_gui_dead(self):
        """ Method used to silently exit gui thread is dead. Usually called before raising an exception."""
        if not self.gui_thread.is_alive():
            sys.exit()

    def __getattr__(self, name):
        """ Returns a function which, if called, puts its call onto the queue """

        def save_call(*args, **kwargs):
            ret_q = queue.Queue(1) if name.startswith("get_") else _DummyQueue()
            self.enqueue_call(name, args, kwargs, ret_q)

            while True:
                try:
                    return ret_q.get(timeout=0.1)
                except queue.Empty:
                    self._exit_if_gui_dead()

        return save_call

    def __call__(self, f):
        self.enqueue_call("add_event_listener", [f], {})