from pyglet.gl import *
from pyglet.window import key
from ctypes import c_float
import math
import random
import time
from collections import defaultdict
import sys, os

SECTOR_SIZE = 16

def cube_vertices(x, y, z, n):
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n, # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n, # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n, # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n, # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n, # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n, # back
    ]

def tex_coord(x, y, n=4):
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

def tex_coords(top, bottom, side):
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result

GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))
STONE1 = tex_coords((0, 2), (0, 2), (0, 2))
STONE2 = tex_coords((1, 2), (1, 2), (1, 2))
STONE3 = tex_coords((2, 1), (2, 1), (2, 1))

FACES = [
    ( 0, 1, 0),
    ( 0,-1, 0),
    (-1, 0, 0),
    ( 1, 0, 0),
    ( 0, 0, 1),
    ( 0, 0,-1),
]

class TextureGroup(pyglet.graphics.Group):
    def __init__(self, path):
        super(TextureGroup, self).__init__()
        if os.path.isfile(path):
            self.texture = pyglet.image.load(path).get_texture()
        else:
            self.texture = pyglet.image.CheckerImagePattern( color1=(100,100,100,155), color2=(200,200,200,155) ).create_image(256,256).get_texture()
    def set_state(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)
    def unset_state(self):
        glDisable(self.texture.target)

def normalize(position):
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return (x, y, z)

def sectorize(position):
    x, y, z = normalize(position)
    x, y, z = x / SECTOR_SIZE, y / SECTOR_SIZE, z / SECTOR_SIZE
    return (x, 0, z)

class Model(object):
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self.group = TextureGroup('texture.png')
        self.world = {}
        self.shown = {}
        self._shown = {}
        self.sectors = {}
        self.queue = []
        self.floor_size = 50
        self.gen_n = int(0)
        self.setcl = lambda x, i, j: (x.__setitem__((i, j), x[(i, j)] + 16))
        self.inccl = lambda x, i, j: (x.__setitem__((i, j), x[(i, j)] + 1))
        self.first_generated = 1
        self.last_generation = defaultdict(int)
        self.initialize()

    def initialize(self):
        # get the source of pattern
        if len(sys.argv)>1 and os.path.isfile(sys.argv[1]):
            infile = open(sys.argv[1])
        else:
            infile = (" XX", "XX", " X") # init default R-pentamino

        # beget 0-day cells
        maxi = 0
        maxj = 0
        for i,l in enumerate(infile):
            if l[0] == "!": # skip comments
                continue
            maxi = max(i,maxi)
            for j,c in enumerate(l):
                maxj = max(j,maxj)
                if c not in " .\r\t\n":
                    self.setcl(self.last_generation,j,i)

        # draw floor
        for x in xrange(-self.floor_size, self.floor_size + 1, 1):
            for z in xrange(-self.floor_size, self.floor_size + 1, 1):
                self.init_block((x+int(maxj/2.), -2, z+int(maxi/2.)), SAND)

        # run some life
        while self.gen_n < self.first_generated:
            self.nextgen()
        self.show_blocks()

    def nextgen(self):
        self.gen_n += 1
        new_generation = defaultdict(int)

        for z in self.last_generation:
            if self.last_generation[z]&16:
                for (dx, dy) in [(dx, dy) for dx in [-1,0,1] for dy in [-1,0,1] if (dy!=0 or dx!=0)]:
                    self.inccl(new_generation,z[0]+dx,z[1]+dy)

        for z in new_generation:
            v = new_generation[z]
            if v&15 == 3:
                self.setcl(new_generation,z[0],z[1])
            elif (v&15 == 2) and (self.last_generation[z]&16):
                self.setcl(new_generation,z[0],z[1])

        for z in self.last_generation:
            if self.last_generation[z]&16:
                if new_generation[z]&16:
                    self.add_block((z[0], self.gen_n - 2, z[1]), STONE1)
                else:
                    if new_generation[z]&15<3:
                        self.add_block((z[0], self.gen_n - 2, z[1]), STONE2)
                    else:
                        self.add_block((z[0], self.gen_n - 2, z[1]), STONE3)

        self.last_generation = new_generation

    def hit_test(self, position, vector, max_distance=8):
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in xrange(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None
    def exposed(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False
    def init_block(self, position, texture):
        self.add_block(position, texture, False)
    def add_block(self, position, texture, sync=True):
        if position in self.world:
            self.remove_block(position, sync)
        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        if sync:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)
    def remove_block(self, position, sync=True):
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)
        if sync:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)
    def check_neighbors(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self.shown:
                    self.show_block(key)
            else:
                if key in self.shown:
                    self.hide_block(key)
    def show_blocks(self):
        for position in self.world:
            if position not in self.shown and self.exposed(position):
                self.show_block(position)
    def show_block(self, position, immediate=True):
        texture = self.world[position]
        self.shown[position] = texture
        if immediate:
            self._show_block(position, texture)
        else:
            self.enqueue(self._show_block, position, texture)
    def _show_block(self, position, texture):
        x, y, z = position
        # only show exposed faces
        index = 0
        count = 24
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture)
        for dx, dy, dz in []:#FACES:
            if (x + dx, y + dy, z + dz) in self.world:
                count -= 4
                i = index * 12
                j = index * 8
                del vertex_data[i:i + 12]
                del texture_data[j:j + 8]
            else:
                index += 1
        # create vertex list
        self._shown[position] = self.batch.add(count, GL_QUADS, self.group, 
            ('v3f/static', vertex_data),
            ('t2f/static', texture_data))
    def hide_block(self, position, immediate=True):
        self.shown.pop(position)
        if immediate:
            self._hide_block(position)
        else:
            self.enqueue(self._hide_block, position)
    def _hide_block(self, position):
        try:
            self._shown.pop(position).delete()
        except:
            pass
    def show_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)
    def hide_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False)
    def change_sectors(self, before, after):
        before_set = set()
        after_set = set()
        pad = 4
        for dx in xrange(-pad, pad + 1):
            for dy in [0]: # xrange(-pad, pad + 1):
                for dz in xrange(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)
    def enqueue(self, func, *args):
        self.queue.append((func, args))
    def dequeue(self):
        func, args = self.queue.pop(0)
        func(*args)
    def process_queue(self):
        start = time.clock()
        while self.queue and time.clock() - start < 1 / 60.0:
            self.dequeue()
    def process_entire_queue(self):
        while self.queue:
            self.dequeue()

class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.exclusive = False
        self.flying = True
        self.strafe = [0, 0]
        self.zstrafe = 0
        self.position = (0, 0, 5)
        self.frame = 0
        self.rotation = (0, 0)
        self.sector = None
        self.reticle = None
        self.dy = 0
        self.maskirq = False
        self.label_visible = False
        self.mouse_y_dir = 1
        self.run_autogen = False
        self.show_help = False
        self.save_frames = False
        self.label = pyglet.text.Label('', font_name='Courier', font_size=12, 
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top', 
            color=(0, 0, 0, 255), multiline=True, width = self.width - 20, bold = True)
        pyglet.clock.schedule_interval(self.update, 1.0 / 60)
        pyglet.clock.schedule_interval(self.autogen, 1.0)
        self.model = False
    def set_exclusive_mouse(self, exclusive):
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive
    def get_sight_vector(self):
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)
    def get_motion_vector(self):
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            if self.flying:
                m = math.cos(math.radians(y))
                dy = math.sin(math.radians(y))
                if self.strafe[1]:
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    dy *= -1
                dx = math.cos(math.radians(x + strafe)) * m
                dz = math.sin(math.radians(x + strafe)) * m
            else:
                dy = 0.0
                dx = math.cos(math.radians(x + strafe))
                dz = math.sin(math.radians(x + strafe))
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        if self.zstrafe:
            dy += self.zstrafe
        return (dx, dy, dz)
    def update(self, dt):
        if not self.model:
            self.model = Model()
        if self.maskirq:
            return
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        m = 8
        dt = min(dt, 0.2)
        for _ in xrange(m):
            self._update(dt / m)

        if self.save_frames:
            pyglet.image.get_buffer_manager().get_color_buffer().save("frames/frame_%08d.jpg" % (self.frame, ))
            
        self.frame += 1
    def _update(self, dt):
        # walking
        speed = 15 if self.flying else 5
        d = dt * speed
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        # gravity
        if not self.flying:
            self.dy -= dt * 0.044 # g force, should be = jump_speed * 0.5 / max_jump_height
            self.dy = max(self.dy, -0.5) # terminal velocity
            dy += self.dy
        # collisions
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), 2)
        self.position = (x, y, z)
    def autogen(self,dt):
        if self.run_autogen:
            self.maskirq = True
            self.model.nextgen()
            self.maskirq = False

    def collide(self, position, height):
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in FACES: # check all surrounding blocks
            for i in xrange(3): # check each dimension independently
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in xrange(height): # check each height
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    op = tuple(op)
                    if op not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0, -1, 0) or face == (0, 1, 0):
                        self.dy = 0
                    break
        return tuple(p)
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        return
        x, y, z = self.position
        dx, dy, dz = self.get_sight_vector()
        d = scroll_y * 10
        self.position = (x + dx * d, y + dy * d, z + dz * d)
    def on_mouse_press(self, x, y, button, modifiers):
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if button == pyglet.window.mouse.LEFT:
                if block:
                    texture = self.model.world[block]
                    if texture != STONE:
                        self.model.remove_block(block)
            else:
                if previous:
                    self.model.add_block(previous, BRICK)
        else:
            self.set_exclusive_mouse(True)
    def on_mouse_motion(self, x, y, dx, dy):
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + self.mouse_y_dir * dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)
    def on_key_press(self, symbol, modifiers):
        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.Q:
            self.zstrafe += 0.2
        elif symbol == key.E:
            self.zstrafe -= 0.2
        elif symbol == key.ENTER or symbol == key.Z:
            if not self.maskirq:
                self.maskirq = True
                self.model.nextgen()
                self.maskirq = False
        elif symbol == key.SPACE:
            if self.dy == 0:
                self.dy = 0.015 # jump speed
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB:
            self.flying = not self.flying
    def on_key_release(self, symbol, modifiers):
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1
        elif symbol == key.Q:
            self.zstrafe -= 0.2
        elif symbol == key.E:
            self.zstrafe += 0.2
        elif symbol == key.I:
            self.mouse_y_dir = -self.mouse_y_dir
        elif symbol == key.X:
            self.run_autogen = not self.run_autogen
        elif symbol == key.R:
            self.model.show_blocks()
        elif symbol == key.L:
            if self.label_visible:
                if not self.show_help:
                    self.label_visible = False
                else:
                    self.show_help = False
            else:
                self.label_visible = True
                self.show_help = False
            # self.label_visible = not self.label_visible
        elif symbol == key.H:
            if self.label_visible:
                if not self.show_help:
                    self.show_help = True
                else:
                    self.label_visible = False
            else:
                self.label_visible = True
                self.show_help = True

    def on_resize(self, width, height):
        # label
        self.label.y = height - 10
        # reticle
        if self.reticle:
            self.reticle.delete()
        x, y = self.width / 2, self.height / 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
            ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
        )
    def set_2d(self):
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    def set_3d(self):
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)
    def on_draw(self): #,first = false):
        self.clear()
        if self.model:
            self.set_3d()
            glColor3d(1, 1, 1)
            self.model.batch.draw()
            self.draw_focused_block()
            self.set_2d()
            if self.label_visible:
                self.draw_label()
            self.draw_reticle()
        else:
            self.clear()
            self.set_2d()
            self.label.text = 'precalculating... please wait...'
            self.label.draw()
    def draw_focused_block(self):
        vector = self.get_sight_vector()
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            x, y, z = block
            vertex_data = cube_vertices(x, y, z, 0.51)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    def draw_label(self):
        if self.show_help:
            self.label.text = "ConwayTree v1.2  (c) altsoph, 2013\n  https://github.com/altsoph/ConwayTree\n\nBased on the Michael Fogleman's code:\n  https://github.com/fogleman/Minecraft.git" \
            "\n\n\n\nControls:" \
            "\n" \
            "\n\t<mouse>      to look around" \
            "\n\tI            to invert the mouse Y-axis" \
            "\n\tESC          to unlock the mouse cursor" \
            "\n" \
            "\n\tWASD         to move around" \
            "\n\tTAB          to turn fly mode on/off (default=on)" \
            "\n\tSPACE        to jump (while not flying)" \
            "\n\tQ and E      to strafe vertically (while flying)" \
            "\n" \
            "\n\tENTER or Z   to count the next Life generation" \
            "\n\tX            to start/stop Life autogeneration" \
            "\n" \
            "\n\tR            sometimes it's helpful against glitches" \
            "\n\tL            to show/hide the statistics bar" \
            "\n\tH            to display/hide this information" \
            ""
        else:
            x, y, z = self.position
            self.label.text = 'fps: %02d, xyz: (%.2f, %.2f, %.2f), blocks: %d, generation: %d' % (
                pyglet.clock.get_fps(), x, y, z, 
                len(self.model.world)-4*self.model.floor_size*(self.model.floor_size+1)-1, self.model.gen_n)
        self.label.draw()
    def draw_reticle(self):
        glColor3d(0, 0, 0)
        self.reticle.draw(GL_LINES)

def setup_fog():
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (c_float * 4)(0.53, 0.81, 0.98, 1))
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_DENSITY, 0.35)
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)

def setup():
    glClearColor(0.53, 0.81, 0.98, 1)
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
def main():
    save_frames = False
    if len(sys.argv)>1:
        if sys.argv[-1] == 'save_frames':
            save_frames = True
            if not os.path.exists("frames"):
                os.makedirs("frames")
            sys.argv = sys.argv[:-1]
    window = Window(width=800, height=600, caption='Pyglet', resizable=True)
    window.save_frames = save_frames
    window.set_exclusive_mouse(True)
    setup()
    pyglet.app.run()

if __name__ == '__main__':
    main()
