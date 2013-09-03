ConwayTree: Life in 3d
======================

ConwayTree is my attempt to examine the forms and propeties of 3D structures formed by Conway's Life (with time as the third axis).
I used [Minecraft-clone from Michael Fogleman](https://github.com/fogleman/Minecraft) as the environment for experiments.

You can find less technical description on [the ConwayTree project's page](http://altsoph.com/projects/conwaytree/) and some related videos on [my special youtube playlist](http://www.youtube.com/playlist?list=PLDpCMqzwZGlFhCfQLzHNfDwCJQiTHibeU).

How to install
--------------

First of all, make sure you have the latest 2.x python installed.
Then clone (or just download) [this repository](https://github.com/altsoph/ConwayTree) and simple try to run the script.
There is only one non-standart library in dependencies: [pyglet](https://code.google.com/p/pyglet). 
If you miss it, try to install it using the following command:

```shell
pip install pyglet
```

**Note:** Some 64 bits Mac users may experience problems with the default pyglet package installed. The known solution for such situation is:
* Download the latest snapshot of [the  pyglet sources](https://code.google.com/p/pyglet) (right now the latest version is 1.2alpha)
* Build and install it according [the official instructions](http://www.pyglet.org/doc/programming_guide/installing_using_setup_py.html)

How to run
-----------

The simplest way to run ConwayTree is to issue `python conway_tree.py` command. 
This will bring up a ConwayTree instance with the standart R-pentomino pattern as seed. 
_Check 'Controls' section below to realize control keys and abilities; or just push 'H' after the launch_.

However, you can give the filename as a run parameter for specifying the seed pattern:
```shell
python conway_tree.py patterns/cow.cells
```

Controls
--------
* use `mouse`    to look around
* `I`            to invert the mouse Y-axis
* `ESC`          to unlock the mouse cursor


* `WASD`         to move around
* `TAB`          to turn fly mode on/off (default=on)
* `SPACE`        to jump (while not flying)
* `Q` and `E`      to strafe vertically (while flying)


* `ENTER` or `Z`   to count the next Life generation
* `X`            to start/stop Life autogeneration


* `R`            sometimes it's helpful against glitches
* `L`            to show/hide the statistics bar
* `H`            to display/hide this information

Pattern file format
-------------------
The current version of ConwayTree supports only the basic ascii-format for specifying seed patterns.
Rules of this format are:
* the space-symbol or `.` (dot) means a dead (or absent) cell
* any other symbol means an alive one
* the right alignment of a pattern isn't necessary


Deeper hacks
------------
### Video frames collecting

The frame saving mode could be activated using the special run parameter `save_frames` (it must be the last parameter in any case).
In the frame saving mode ConwayTree creates (if necessary) folder `frames` and saves there each frame it produces during the run, one by one.
This mode was made especially for making video movies of envolving Life structures.

However, the way of movie assembling from saved frames stays up to your preferences. As for me, I used the [rtJPG2Video](http://orbisvitae.com/software/rtjpg2video/) utility under Windows OS.

### Texture altering

Two default sets provided with code and one of them demonstrates the transparency trick.
Just replace `texture.png` file by `texture.png_transparent` file to take a look on it.
You can also play and change the textures file by yourself.


Known troubles
--------------
* Some troubles are known on x64 Macs with the default version of pyglet library -- check the 'How to install' section for the solution.
* Some glitches are possible during visualization huge structures with a lot of cells alive. The reason is in the original Michael Fogleman's queue processing routine -- it rejects tail of queue whenever the desired FPS is lost. If you really need to make glitch-free rendering (for movie capturing, for example) you could find the `self.model.process_queue()` call placed in the `Window.update()` method and replace it by `self.model.process_entire_queue()`. This will give you the glitch-free but very laggy version.

Credits
-------
* [John Conway](http://en.wikipedia.org/wiki/John_Horton_Conway) for the game of Life
* Michael Fogleman for the [Minecraft-clone code](https://github.com/fogleman/Minecraft)
* [zarazum@](https://twitter.com/zarazum) as a co-thinker and beta-tester
* [Conwaylife.com portal](http://www.conwaylife.com/) for a huge collection of Life patterns
