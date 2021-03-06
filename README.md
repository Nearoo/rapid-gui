### Rapid Gui Developement in Python
Most gui solutions for python are written with feature-completeness, efficiency and end-user-experience in mind. This results in those packages being complicated and requiring a lot time to setup and learn before any usable guis can be created. 

RapidGui has a different approach: It is oriented completely towards the experience of _developing_ the gui. It's intended for developers who don't really care about class hierarchies, event loops or state propagation, but instead just want to get some graphical interactivity with their app as fast and easily as possible. RapidGui can provide interactivity with as little as three lines of code.

The project is still a work in progress. To get a more complete picture of the idea, read more [here](https://www.notion.so/Python-Package-Rapid-Gui-Creation-024082aaa7484ecdbd47ae6694215f77). Below you can read about what has already been implemented. It's still more of an idea than a usable solution. Contributions are welcome!

### Running the example:
1. Install Python 3.7
2. Install dependencies: `pip3 install decorator pyglet`
3. Run `python3 goal.py`

### The example

```python
import time, random
import rapidgui

# Load gui file: window opens
app = rapidgui.load("example.json")


def do_heavy_work():
    time.sleep(random.choice(range(3)))


def my_super_duper_long_function():
    for i in range(20):
        
        # Update widget referenced in gui file: Set % for progress bar
        app("myprogressbar").set_pct(i/20*100) 
        do_heavy_work()

    app("myprogressbar").set_pct(100)
    print("Done doing heavy work.")


# Bind an event to a button widget
@app("mybutton")
def on_pressed(): # even is: user pressed button
    app("mybutton").set_enabled(False) # Disable the button
    my_super_duper_long_function() # Start work
```
![example vis](https://s3.us-west-2.amazonaws.com/secure.notion-static.com/e84b21ee-1a8e-4e21-9490-4af6db0d9c1c/delete.gif?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAT73L2G45O3KS52Y5%2F20200506%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20200506T161031Z&X-Amz-Expires=86400&X-Amz-Signature=d769353c127056368dd7dfb71777cf342c5a86eeb61297fa09dfe791a91b8d80&X-Amz-SignedHeaders=host&response-content-disposition=filename%20%3D%22delete.gif%22)

### Implemented GUI components:
To start a gui thread and open a window, simply put 
```python
import rapidgui
app = rapidgui.load("example.json")
```
at the top of a python file. The window will open even before the script has started to bind itself to its widgets; this is done later asynchronously. To see a thorough example, look into `goal.py` or read the example  [here](https://www.notion.so/Python-Package-Rapid-Gui-Creation-024082aaa7484ecdbd47ae6694215f77).

There are currently two gui component types. View "implementation" below to see how to add them to `example.json`.

#### Button
Parameters:
```json
    {
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 50,
                "label_text": "Hello",
                "background_color": [164, 219, 211, 255],
                "line_color": null,
                "enabled": true
     }
```

Signals:
* `on_pressed()` called when the button is pressed

Methods:
* `set_enabled(enabled: bool)` activates or deactivates the label, rendering it grey
* `set_label(label: str)` 
* `get_labeel() -> str` 

#### ProgressBar
Parameters
```json5
            {
                "x": 500,
                "y": 100,
                "width": 400,
                "height": 50,
                "background_color": [230, 230, 230, 255],
                "pct": 0, // initial percentage
                "bar_color": [164, 219, 211, 255],
                "border_width": 5
            }
```

Signals:  
_None_  
Methods:
* `set_pct(pct: int)` set percentage that bar shows, between 0 and 100
* `get_pct()->int` get percentage, between 0 and 100


### File Format
The `example.json` describes how the gui looks like before it is attached to your app. This is the file that can be created using an editor in the future. For now, it is written by hand. All parameters are optional and have default values. Unknown parameters will raise an exception.

At the top level, the format is as follows:
```json5
{
    "app-properties": {
        "width": 1000,
        "height": 500,
        "background_color": [255, 255, 255]
    },


    "components" : [
      // GUI components
    ]
}
```

`components` lists all gui components, which are placed by absolute position onto the window. The coordinate is laid out with `(0, 0)` at the bottom left, and increasing axes in both directions.

Every gui component has the following format:

```json5
        {
            "meta": {
                "type": <type of gui component, e.g. button>
                "identifier": <unique id of the button, e.g. "StartParsingButton"
            },
            "properties": {
                <configure component in accordance to type, e.g. text_color>
            }
        }
```

