import curses

from bitarray import bitarray

class BitWalkBuffer(object):
    def __init__(self, gui):
        self.gui = gui
        self.bit_group = 8
        self.ba = bitarray()
        self.path = None
        self.modlock = False
        self.modified = False

        self.curs_offset = 0
        self.offset = 0

    def open(self, path):
        try:
            fp = open(path, 'rb')
            self.path = path
            self.ba.fromfile(fp)
            self.offset = 0
            self.curs_offset = 0
            fp.close()
        except (OSError, IOError) as e:
            self.gui.status_msg('Unable to open "%s": %s' % (path, e.strerror))
            return

        # If we read more than a megabyte, put on the mod lock to protect
        # against accidentally taking forever to do something
        self.modlock = (len(self.ba) > 8000000)
        self.modified = False

        self.gui.resize()
        self.gui.status_msg('"%s"%s' % (path, ' [readonly]' if self.modlock else ''))

    def move_curs(self, x_del=None, y_del=None, abs_offset=None):
        bpr = self.get_bits_per_row()
        if y_del is not None:
            self.curs_offset += y_del * bpr

        if x_del is not None:
            self.curs_offset += x_del

        if abs_offset is not None:
            self.curs_offset = abs_offset

        (max_y, max_x) = self.gui.main_win.getmaxyx()
        start = self.offset
        stop = start + (bpr * max_y)

        # Check to make sure we're still on the screen!!!
        if self.curs_offset < 0:
            self.curs_offset = 0
        elif self.curs_offset == len(self.ba):
            pass

        if self.curs_offset > stop:
            self.offset += bpr
            if self.offset > len(self.ba):
                self.offset = self.ba
            self.render()
        elif self.curs_offset < start:
            self.offset -= bpr
            if self.offset < 0:
                self.offset = 0
            self.render()

        pos = self.curs_offset - self.offset
        y = pos / bpr
        pos = pos % bpr
        x = (pos % self.bit_group)
        x += (pos / self.bit_group) * (self.bit_group + 1)

        if y >= max_y:
            y = max_y - 1

        try:
            self.gui.stdscr.move(y, x)
        except curses.error:
            self.gui.status_msg('Moving to %d, %d (bpr: %d)' % (y, x, bpr))


    def get_bits_per_row(self):
        (y, x) = self.gui.main_win.getmaxyx()
        return ((x - 1) / (self.bit_group + 1)) * self.bit_group

    def render(self):
        self.gui.main_win.erase()
        (y, x) = self.gui.main_win.getmaxyx()

        bits_per_row = ((x - 1) / (self.bit_group + 1)) * self.bit_group
        eof = False

        for row in xrange(y):
            self.gui.main_win.move(row, 0)

            if eof and row > 0:
                self.gui.main_win.addch('~')
                continue

            start = row * bits_per_row + self.offset
            stop = start + bits_per_row

            line = self.ba[start:stop].to01()
            if len(line) != bits_per_row:
                eof = True

            for i in xrange(0, len(line), self.bit_group):
                self.gui.main_win.addstr(line[i:i+self.bit_group])
                self.gui.main_win.addch(' ')

        self.move_curs()
        self.gui.main_win.noutrefresh()
