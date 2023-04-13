
# WINDrone
Autonomus embedded toy drone getting into a building from a window.
### Ilustration:
 on [laptop](https://drive.google.com/drive/u/0/folders/1Ui3aVITxfdUsNWyqbkA_s0EW2ZDXliQU)
 on [Raspberry Pi zero 2](1Ui3aVITxfdUsNWyqbkA_s0EW2ZDXliQU)

## Running:
1.  Download the model file `detector.tflite` [here](https://drive.google.com/file/d/16kEloEK5v90bYICJlbFAkU8QdNBY_eAW/view?usp=sharing). Place it in the project directory.
2. `pip install` all packages that are used.
3. Make sure that the Tello is connected by WiFi. 
4. From the project directory run `python main.py <parameters>`.

If you are running on Raspberry, you may want to make the WiFi connection automatic on boot, disable password, and call the `python` in `.bashrc`.

### Parameters:
`-e, --edges`: Float in [0,0.5], how much from the picture is considered as edge. 
`-o, --outdoor`: 1 if the drone should fly outside the window and start navigating to get inside, 0 if the drone should escape the room. 
`-f, --fly`:If 0 will not takeoff.
`--headless`: if 1 will not display windows. Must be used on Raspberry.
`--lrenabled`: Specific criterion in the navigation logic, consider removing or improving.

## Files
The system is spitted between 3 files:
### `drone.py`: 
Implements the `Drone` object, including a thread and a property `frame` which enable reading the last frame in secure way.

The methods `fly_to_start`, `fly_to_finish` are called before the navigation is started and after the drone entered the window to start the task and land safely. You may want to modify the commands with respect to your physical room.

### `detector.py`:
Implements the `Model`. The `detect` method should be used to get the target box to navigate.
The model can be replaced with any model with input and output format as Yolov5 or Yolov8, exported to Tensorflow Lite. 

The current model is Yolov8n trained on the windows subset of [Open Images V7](https://storage.googleapis.com/openimages/web/index.html) dataset.

Straight forward modifications that can be done is changing number of threads and image size in this file, to speed up inference. make sure to export a matching size model.

### `main.py`:

The navigation itself is implemented here, as well as the video management sections.

The navigation logic check few conditions about the place of the window in the frame using short lambda functions, and by saving the conditions information for the last two frames, a decision about the movement is made. The method is completely heuristic and I encourage everyone to test this logic and try to improve it! 
