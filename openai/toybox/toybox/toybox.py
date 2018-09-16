import ctypes
import numpy as np
from PIL import Image
import os
import platform
import time

platform = platform.system() 

if platform == 'Darwin':
    _lib_path_debug = 'target/debug/libopenai.dylib'
    _lib_path_release = 'target/release/libopenai.dylib'

    if os.path.exists(_lib_path_release):
        _lib_path = _lib_path_release
    elif os.path.exists(_lib_path_debug):
        _lib_path = _lib_path_debug
    else:
        raise OSError('libopenai.dylib not found on this machine')

elif platform == 'Linux':
    _lib_path = 'libopenai.so'
    
else:
    raise Exception('Unsupported platform: %s' % platform)


try:
    _lib = ctypes.CDLL(_lib_path)
except Exception:
    raise Exception('Could not load libopenai from path %s.' % _lib_path 
    + """If you are on OSX, this may be due the relative path being different 
    from `target/(target|release)/libopenai.dylib. If you are on Linux, try
    prefixing your call with `LD_LIBRARY_PATH=/path/to/library`.""")
    exit(1)

class WrapSimulator(ctypes.Structure):
    pass

class WrapState(ctypes.Structure):
    pass


# I don't know how actions will be issued, so let's have lots of options available
NOOP = 'noop'
LEFT = "left"
RIGHT = "right"
UP = "up"
DOWN = "down"
BUTTON1 = "button1"
BUTTON2 = "button2"

class Input(ctypes.Structure):
    _fields_ = [(LEFT, ctypes.c_bool), 
                (RIGHT, ctypes.c_bool),
                (UP, ctypes.c_bool),
                (DOWN, ctypes.c_bool),
                (BUTTON1, ctypes.c_bool),
                (BUTTON2, ctypes.c_bool)]

    def _set_default(self):
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.button1 = False
        self.button2 = False

    def set_input(self, input_dir, button=NOOP):
        self._set_default()

        # reset all directions
        if input_dir == NOOP:
            pass
        elif input_dir == LEFT:
            self.left = True
        elif input_dir == RIGHT:
            self.right = True
        elif input_dir == UP:
            self.up = True
        elif input_dir == DOWN:
            self.down = True
        else:
            print('input_dir:', input_dir)
            assert False

        # reset buttons
        if button == NOOP:
            pass
        elif button == BUTTON1:
            self.button1 = True
        elif button == BUTTON2:
            self.button2 = True
        else:
            assert False
            

_lib.simulator_alloc.argtypes = [ctypes.c_char_p]
_lib.simulator_alloc.restype = ctypes.POINTER(WrapSimulator)

_lib.state_alloc.argtypes = [ctypes.POINTER(WrapSimulator)]
_lib.state_alloc.restype = ctypes.POINTER(WrapState)

_lib.simulator_frame_width.argtypes = [ctypes.POINTER(WrapSimulator)]
_lib.simulator_frame_width.restype = ctypes.c_int

_lib.simulator_frame_height.argtypes = [ctypes.POINTER(WrapSimulator)]
_lib.simulator_frame_height.restype = ctypes.c_int 

_lib.state_lives.restype = ctypes.c_int
_lib.state_score.restype = ctypes.c_int
    
_lib.render_current_frame.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p]
 #(frame_ptr, size, sim.get_simulator(), self.__state)


class Simulator(object):
    def __init__(self, game_name):
        sim = _lib.simulator_alloc(game_name.encode('utf-8'))
        # sim should be a pointer
        #self.__sim = ctypes.pointer(ctypes.c_int(sim))
        self.__sim = sim 
        print('sim', self.__sim)
        self.__width = _lib.simulator_frame_width(sim)
        self.__height = _lib.simulator_frame_height(sim)
        self.deleted = False

    def __del__(self):
        if not self.deleted:
            self.deleted = True
            _lib.simulator_free(self.__sim)
            self.__sim = None

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()

    def get_frame_width(self):
        return self.__width

    def get_frame_height(self):
        return self.__height

    def get_simulator(self):
        return self.__sim

    def new_game(self):
        return State(self)


class State(object):
    def __init__(self, sim):
        self.__state = _lib.state_alloc(sim.get_simulator())
        self.deleted = False

    def __enter__(self):
        return self

    def __del__(self):
        if not self.deleted:
            self.deleted = True
            _lib.state_free(self.__state)
            self.__state = None

    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()

    def get_state(self):
        return self.__state
    
    def lives(self):
        return _lib.state_lives(self.__state)
    def score(self):
        return _lib.state_score(self.__state)
    def game_over(self):
        return self.lives() <= 0

    def render_frame(self, sim, grayscale=True):
        if grayscale:
            return self.render_frame_grayscale(sim)
        else:
            return self.render_frame_color(sim)

    def render_frame_color(self, sim):
        h = sim.get_frame_height()
        w = sim.get_frame_width()
        rgba = 4
        size = h * w  * rgba
        frame = np.zeros(size, dtype='uint8')
        frame_ptr = frame.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        _lib.render_current_frame(frame_ptr, size, False, sim.get_simulator(), self.__state)
        return np.reshape(frame, (h,w,rgba))
    
    def render_frame_grayscale(self, sim):
        h = sim.get_frame_height()
        w = sim.get_frame_width()
        size = h * w 
        frame = np.zeros(size, dtype='uint8')
        frame_ptr = frame.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        _lib.render_current_frame(frame_ptr, size, True, sim.get_simulator(), self.__state)
        return np.reshape(frame, (h,w,1))

class Toybox():

    def __init__(self, game_name, grayscale=True):
        self.rsimulator = Simulator(game_name)
        self.rstate = State(self.rsimulator)
        self.grayscale = grayscale
        # OpenAI state is a 4-frame sequence
        self.state = tuple([self.rstate.render_frame(self.rsimulator, self.grayscale)] * 4)
        self.deleted = False

    def get_state(self):
        return self.state

    def new_game(self):
        old_state = self.rstate
        del old_state
        self.rstate = self.rsimulator.new_game()

    def get_height(self):
        return self.rsimulator.get_frame_height()

    def get_width(self):
        return self.rsimulator.get_frame_width()

    def apply_action(self, action_input_obj):
        _lib.state_apply_action(self.rstate.get_state(), ctypes.byref(action_input_obj))
        new_frame = self.rstate.render_frame(self.rsimulator, self.grayscale)
        self.state = (self.state[1], self.state[2], self.state[3], new_frame)
        return new_frame

    def save_frame_image(self, path):
        img = None
        if self.grayscale:
            img = Image.fromarray(self.state[3], 'L') 
        else:
            img = Image.fromarray(self.state[3], 'RGBA')
        img.save(path)

    def get_score(self):
        return self.rstate.score()
    
    def get_lives(self):
        return self.rstate.lives()
    
    def game_over(self):
        return self.get_lives() <= 0

    def __del__(self):
        if not self.deleted:
            self.deleted = True
            del self.rstate
            self.rstate = None
            del self.rsimulator
            self.rsimulator = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()

if __name__ == "__main__":
    # benchmark our games (in grayscale)
    for game in ['amidar', 'breakout']:
        with Toybox(game) as tb:
            scores = []
            startTime = time.time()
            N = 40000
            for i in range(N):
                move_up = Input()
                move_up.up = True
                tb.apply_action(move_up)
                #tb.save_frame_image('%s%03d.png' % (game, i))
                if tb.game_over():
                    scores.append(tb.get_score())
                    tb.new_game()
            endTime = time.time()
            FPS = N / (endTime - startTime)
            print("%s-FPS: %3.4f" % (game, FPS))
            print("\t", scores)
        