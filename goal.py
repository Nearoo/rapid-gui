import time, random
import rapidgui

app = rapidgui.load("example.json")


def do_heavy_work():
    time.sleep(random.choice(range(3)))


def my_super_duper_long_function():
    pct = 0
    app("myprogressbar").set_pct(pct)
    for i in range(20):
        pct = i * 1 / 20
        app("myprogressbar").set_pct(pct*100)
        do_heavy_work()

    app("myprogressbar").set_pct(100)
    print("Done doing heavy work.")


@app("mybutton")
def on_pressed():
    app("mybutton").set_enabled(False)
    my_super_duper_long_function()
