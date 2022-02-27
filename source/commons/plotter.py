import datetime
import functools
import multiprocessing as mp
import threading
import time
import warnings

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider

from .utils import text_wrap

warnings.filterwarnings("ignore")
# supported for chinese character
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.constrained_layout.use'] = True


class ProcessPlotter:
    """
    A backend class that uses a pipe to receive backend data, for the tsp algorithm.
    This is useful for getting periodic events through the backend's native event loop.
    Implemented only for backends with GUIs.

    Figure is divided into two Axes, the left one is used to generate the report of the problem
    and the log of the algorithm running, and the right one is used to show the path of the tour.
    In addition, the speed of the animation can be efficiently adjusted by the Speed Slider.
    """

    def __init__(self, win_name, win_size, interval=50, style='seaborn-notebook'):
        # gui properties
        self.win_name = win_name
        self.win_size = win_size
        self.interval = interval
        self.style = style
        # info board
        self.infos = dict()
        self.logging = []
        self.board_width = 50
        self.text_ref = None
        # problem and solution
        self.coords = None
        self.solution = None
        self.distance = None
        # tour drawing task
        self.draw_task = None
        self.draw_interval = .1
        self.draw_flag = False

    def terminate(self):
        self.pipe.close()
        plt.close(self.win_name)
        print('[Plotter Process]: Closed.')

    def update_interval(self, interval):
        self.draw_interval = interval

    def update_log(self, info):
        if len(self.logging) > 10:
            self.logging.pop(0)
        self.logging.append('{} {}'.format(
            datetime.datetime.now().strftime('[%H:%M:%S]'), info))
        self._update_info_axes()

    def update_infos(self, infos):
        self.infos = infos
        self._update_info_axes()

    def plot_cities(self, cities):
        self.coords = np.asarray(cities)
        self._update_tour_axes()

    def plot_tours(self, *args):
        if len(args) != 2 or len(args[0]) != len(args[1]):
            raise ValueError(
                'the size between solution and distance array should be equal: '
                '{}, {}'.format(len(args[0]), len(args[1])))
        if not self.draw_flag:
            self.draw_flag = True
            self.solution, self.distance = args
            self.draw_task = threading.Thread(target=self._draw_tour_path, args=(self,), daemon=True)
            self.draw_task.start()
        else:
            # warning
            self.update_log('*** Warning: there is another tour-plotter task going on')
            pass

    def _update_tour_axes(self):
        self.ax1.cla()
        if self.coords is not None:
            self.ax1.scatter(self.coords[:, 0], self.coords[:, 1])

    def _init_info_axes(self):
        self.ax0.cla()
        self.ax0.set_xticks([])
        self.ax0.set_yticks([])
        self.ax0.set_xlim(0, 1)
        self.ax0.set_ylim(0, 1)
        self.ax0.fill([0, 0, 1, 1], [0, 1, 1, 0], 'C0', alpha=0.3)
        self.text_ref = self.ax0.text(0.05, 0.95, '', transform=self.ax0.transAxes, fontsize=13,
                                      verticalalignment='top')

    def _update_info_axes(self):
        infos = '[PROBLEM INFO]' + '\n' + self._wrap_infos()
        logs = '[LOGGING INFO]' + '\n' + self._wrap_logs()
        text = infos + '\n' + logs
        self.text_ref.set_text(text)

    @staticmethod
    def _draw_tour_path(self):
        self._update_tour_axes()
        _line, _text = None, None
        for idx in range(len(self.solution)):
            path_mat = np.asarray(self.solution[idx])
            x, y = path_mat[:, 0], path_mat[:, 1]
            if _line is None:
                _line, = self.ax1.plot(x, y, color='C1', alpha=.6, label='tour')
                props = dict(boxstyle='round', facecolor='C2', alpha=0.2)
                _text = self.ax1.text(0.02, 0.98, '', transform=self.ax1.transAxes, fontsize=12,
                                      verticalalignment='top', bbox=props)
            else:
                _line.set_xdata(x)
                _line.set_ydata(y)
                _text.set_text('distance = {:<10.3g}'.format(self.distance[idx]))
            time.sleep(self.draw_interval)
        self.draw_flag = False
        if len(self.distance) > 1:
            self.update_log('Best Distance = {:<10.3g}'.format(self.distance[-1]))
        self.drawing_signal.release()

    def _wrap_logs(self):
        return '\n'.join(map(functools.partial(text_wrap, width=self.board_width), self.logging))

    def _wrap_infos(self):
        # create strings for plotting
        key2str = {}
        for key, val in self.infos.items():
            if isinstance(val, float):
                val_str = '%-8.3g' % (val,)
            else:
                val_str = str(val)
            key2str[self._truncate(key)] = self._truncate(val_str)

        if len(key2str) == 0:
            # print('*** warning: tried to write empty infos dict on the board')
            return ''
        else:
            # find max widths
            key_width = max(map(len, key2str.keys()))
            val_width = max(map(len, key2str.values()))

        # write out the data
        dashes = '-' * (key_width + val_width + 7)
        lines = [dashes]
        for key, val in key2str.items():
            lines.append('| %s%s | %s%s |' % (
                key,
                ' ' * (key_width - len(key)),
                val,
                ' ' * (val_width - len(val)),
            ))
        lines.append(dashes)
        return '\n'.join(lines)

    def _truncate(self, s):
        width = self.board_width // 2
        return s[:width] + '...' if len(s) > width else s

    def _pipe_receiver(self):
        if self.pipe.poll():
            opt, args = self.pipe.recv()
            if not isinstance(opt, str) or not hasattr(self, opt):
                return False
            attr = getattr(self, opt)
            if not callable(attr):
                return False
            try:
                attr(*args)
            except Exception as exc:
                self.update_log('*** Error[opt={}]: {!r}'.format(opt, exc))
        try:
            self.fig.canvas.draw()
        except Exception as exc:
            print('[Plotter Process]: Failed to draw canvas. {!r}'.format(exc))
        return True

    def _update_interval(self, val):
        self.draw_interval = val / 100

    def __call__(self, pipe, signal):
        print('[Plotter Process]: Initialing...')
        self.pipe = pipe
        self.drawing_signal = signal
        # config plt
        plt.style.use(self.style)
        self.fig = plt.figure(self.win_name, figsize=self.win_size)
        gs = self.fig.add_gridspec(20, 2)
        self.ax0 = self.fig.add_subplot(gs[:-1, 0])
        self.ax1 = self.fig.add_subplot(gs[:-1, 1])
        self._init_info_axes()
        # a speed slider
        self.ax2 = self.fig.add_subplot(gs[-1, 1])
        # axSpeed = self.fig.add_axes([0.05, 0.01, 0.4, 0.03], facecolor='lightsteelblue', alpha=0.3)
        sSpeed = Slider(self.ax2, 'Speed', 5, 50, valinit=10, valstep=5)
        sSpeed.on_changed(self._update_interval)
        # create a new backend-specific subclass of Timer
        # To accept some from fronted
        timer = self.fig.canvas.new_timer(interval=self.interval)
        timer.add_callback(self._pipe_receiver)
        timer.start()
        plt.show(block=True)
        timer.stop()
        self.terminate()


class Plotter:
    """
    A class for handling task sending from frontend.
    Used for back-end process management and pipeline data transfer.
    """

    def __init__(self, win_name, win_size=(12, 6)):
        self.master_pipe, self.plotter_pipe = mp.Pipe()
        # a signal that indicates whether tours drawing is taking place
        self.drawing_signal = mp.Semaphore(0)
        self.plot_process = mp.Process(target=ProcessPlotter(win_name, win_size, ),
                                       args=(self.plotter_pipe, self.drawing_signal), daemon=True)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self):
        self.plot_process.start()

    def close(self):
        self.plot_process.join()
        self.plot_process.close()

    def task_done(self, opt, *args, finished=False, block=False):
        """ send data via pipe """
        send = self.master_pipe.send
        if finished:
            send(('terminate',))
            self.master_pipe.close()
        else:
            send((opt, args))
        if block:
            # wait for a released semaphore
            self.drawing_signal.acquire(block=True)
