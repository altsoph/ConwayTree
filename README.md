ConwayTree: Life in 3D
======================

ConwayTree is an attempt to explore 3D structures formed by generations of Conway's Life cellular automaton (with time as the third axis). I used [the Minecraft clone by Michael Fogleman](https://github.com/fogleman/Minecraft) as 3D engine.

You can find the general description on [the ConwayTree project's page](http://altsoph.com/projects/conwaytree/) and some related videos on [my ConwayTree youtube playlist](http://www.youtube.com/playlist?list=PLDpCMqzwZGlFhCfQLzHNfDwCJQiTHibeU).

Installation
------------

First of all, make sure you have the latest 2.x python installed. Then clone (or download) [this repository](https://github.com/altsoph/ConwayTree) and try to run the script. The script requires [pyglet](https://code.google.com/p/pyglet) multimedia library. If it is missing on your computer, try to install it with the following command:


```shell
pip install pyglet
```

**Note:** Some Mac users may need to build *pyglet* from source code due to problems with the stable version of *pyglet* on latest 64-bit Intel Macs. The known solution for this situation is:
* Download the latest snapshot of [the  pyglet sources](https://code.google.com/p/pyglet) (right now the latest version is 1.2alpha)
* Build and install it according [the official instructions](http://www.pyglet.org/doc/programming_guide/installing_using_setup_py.html):

```shell
sudo python setup.py install
```

*Please note you'll need superuser privileges.*

Use
---

The simplest way to try ConwayTree is to type `python conway_tree.py` command in your favorite console. This will bring up a ConwayTree instance with famous [R-pentomino](http://www.conwaylife.com/wiki/R-pentomino) pattern as a seed (generation zero pattern laying on the ground level of visible 3D environment). 

Hit `H` key to get help on controls.

You can give the filename of prefab pattern as a parameter for the script to start with some different seed pattern: `python conway_tree.py patterns/cow.cells`

Controls
--------
* use `mouse` to look around
* `I` to invert the mouse Y-axis
* `ESC` to unlock the mouse cursor
* `W``A``S``D` to move around
* `TAB` to turn fly mode on/off (default=on)
* `SPACE` to jump (while not flying)
* `Q` and `E` to strafe vertically (while flying)
* `ENTER` or `Z` to compute the next Life generation
* `X` to run/pause automatic computing of Life generations
* `R` sometimes is helpful against visual glitches
* `L` to show/hide the statistics bar
* `H` to show/hide the information about control keys

Pattern file format
-------------------
The current version of ConwayTree supports simplest ASCII plain text:

* ` ` (space) or `.` (period) character means a dead (or absent) cell 
* any other symbol means an alive one
* the right alignment of a pattern is not necessary

E.g. R-pentomino pattern can be specified like this: 
```
.XX
XX
.X
```

Some hacks
----------
### Video recording
The frame saving mode could be activated using the special run parameter `save_frames` (it must be the last parameter in any case). In the frame saving mode ConwayTree creates (if necessary) folder `frames` and saves each frame it produces during the run, one by one. This mode was made especially for making video movies of evolving Life structures.
Each frame file uses the JPG format and has a name like "frame_XXXXXXXX.jpg", where XXXXXXXX is the number of the given frame.

However, assembling the movie from separate frames is up to you. As for me, I used the [rtJPG2Video](http://orbisvitae.com/software/rtjpg2video/) utility under Windows OS. On Mac and Linux you can try [ffmpeg](http://ffmpeg.org/) or MEncoder (part of [MPlayer project](http://www.mplayerhq.hu/design7/dload.html)). 

### Texture alteration
By default, the blocks forming the Conway Life tree are covered with one of the two prepackaged textures. 
`texture.png` is the solid one, while `texture.png_transparent` demonstrates the transparency trick. Just replace the `texture.png` with the `texture.png_transparent` file to take a look on it. You can also play and change the file with textures by yourself.

Known troubles
--------------
* Some troubles are known on Mac with the default version of the pyglet library -- check the 'Installation' section for the solution.
* Some glitches are possible while visualizing huge structures with many living cells. The reason for that is the way the original Michael Fogleman's queue processing routine works: it rejects tail of queue whenever the desired FPS is lost. If you really need glitch-free rendering (for movie capturing, for example), you could replace the `self.model.process_queue()` in the `Window.update()` method with `self.model.process_entire_queue()`. It should remove the glitches, at a cost of significant slow-down.

Credits
-------
* [John Conway](http://en.wikipedia.org/wiki/John_Horton_Conway) for the game of Life 
* Michael Fogleman for [the Minecraft clone code](https://github.com/fogleman/Minecraft) 
* [zarazum@](https://twitter.com/zarazum) as a co-thinker and beta-tester 
* [the Conwaylife.com portal](http://www.conwaylife.com/) for a huge collection of Life patterns
