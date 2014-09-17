import curses

from bwbuffer import BitWalkBuffer

class BitWalkGui(object):
    def __init__(self, bitwalk, stdscr):
        self.bitwalk = bitwalk
        self.stdscr = stdscr
        self.main_win = curses.newwin(80, 25, 0, 0)

        curses.noecho()
        if curses.has_colors():
            curses.start_color()

        self.buffers = [BitWalkBuffer(self)]
        self.active_buffer = 0

        self.resize()

    def new_buffer(self, path=None):
        buf = BitWalkBuffer(self)
        self.buffers.append(buf)

        if path is not None:
            buf.open(path)

        self.get_active_buffer().render()

    def status_msg(self, message):
        self.clear_status()
        self.stdscr.addstr(self.max_y - 1, 0, message)
        self.stdscr.noutrefresh()
        #self.get_active_buffer().move_curs()
        curses.doupdate()

    def status_query(self, query):
        self.status_msg(query)

        curses.echo()
        ret = self.stdscr.getstr()
        curses.noecho()

        self.get_active_buffer().move_curs()

        return ret

    def clear_status(self):
        self.stdscr.move(self.max_y - 1, 0)
        self.stdscr.clrtoeol()
        self.stdscr.noutrefresh()
        curses.doupdate()

    def resize(self):
        (self.max_y, self.max_x) = self.stdscr.getmaxyx()
        curses.resizeterm(self.max_y, self.max_x)

        #self.stdscr.resize(self.max_y, self.max_x)
        self.stdscr.clear()
        self.stdscr.noutrefresh()

        self.main_win.resize(self.max_y - 1, self.max_x)
        self.buffers[self.active_buffer].render()

        # TODO: Reposition cursor
        self.get_active_buffer().move_curs()

        curses.doupdate()

    def left(self):
        self.get_active_buffer().move_curs(x_del=-1)

    def right(self):
        self.get_active_buffer().move_curs(x_del=1)

    def up(self):
        self.get_active_buffer().move_curs(y_del=-1)

    def down(self):
        self.get_active_buffer().move_curs(y_del=1)

    def get_active_buffer(self):
        return self.buffers[self.active_buffer]
