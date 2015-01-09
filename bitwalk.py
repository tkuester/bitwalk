#!/usr/bin/env python
import sys
import optparse
import curses

from bitarray import bitarray

class BitsWindow(object):
    def __init__(self, parent, win):
        self.parent = parent
        self.win = win

        self.scn_offset = 0
        self.curs_offset = 0
        self.ba = bitarray()

    def open(self, path):
        try:
            fp = open(path, 'rb')
            self.ba = bitarray()
            self.ba.fromfile(fp)
            fp.close()

            self.scn_offset = 0
            self.curs_offset = 0

            self.parent.status_msg("\"%s\" %d bits" % (path, len(self.ba)))
            self.draw()
            self.parent.refresh()
        except (IOError, OSError) as e:
            self.parent.status_msg(str(e))
            self.ba = bitarray()

    def dimensions(self):
        (y, x) = self.win.getmaxyx()
        bits_per_line = (x / 9) * 8
        if bits_per_line < 8:
            bits_per_line == 8

        return (y, x, bits_per_line)

    def curs_pos(self):
        (ydim, xdim, bits_per_line) = self.dimensions()

        y = 0
        x = 0
        scn_ofs = self.scn_offset
        while (scn_ofs + bits_per_line) <= self.curs_offset:
            scn_ofs += bits_per_line
            y += 1

        while scn_ofs < self.curs_offset:
            scn_ofs += 1
            x += 1

        # Account for spaces between groups
        x += (x / 8)

        if y >= ydim or x >= xdim:
            # TODO: how to handle this?
            return

        #self.parent.status_msg("ScnOfs: %d / CursOfs: %d / BPL: %d / Curs Pos: %d, %d" %
        #        (self.scn_offset, self.curs_offset, bits_per_line, y, x))
        self.win.move(y, x)
        return (y, x)

    def move_curs(self, x_ofs=None, y_ofs=None, abs_ofs=None, home=None):
        #TODO: Home / End
        (ydim, xdim, bits_per_line) = self.dimensions()
        bits_per_screen = ydim * bits_per_line
        
        if isinstance(y_ofs, int):
            new_ofs = self.curs_offset + y_ofs * bits_per_line

        if isinstance(x_ofs, int):
            new_ofs = self.curs_offset + x_ofs

        if isinstance(abs_ofs, int) and abs_ofs <= len(self.ba):
            new_ofs = abs_ofs

        if home is True:
            new_ofs = self.curs_offset
            new_ofs -= (new_ofs % bits_per_line)
        elif home is False:
            new_ofs = self.curs_offset
            # Add line
            new_ofs += bits_per_line
            # Go home
            new_ofs -= (new_ofs % bits_per_line)
            # Subtract one
            new_ofs -= 1

        if (0 <= new_ofs < len(self.ba)):
            self.curs_offset = new_ofs

        # todo:
        scn_ofs = self.scn_offset
        if self.curs_offset >= (self.scn_offset + bits_per_screen):
            scn_ofs += bits_per_line
        elif self.curs_offset < self.scn_offset:
            scn_ofs -= bits_per_line

        if 0 < scn_ofs < len(self.ba) and scn_ofs != self.scn_offset:
            self.scn_offset = scn_ofs
            self.draw()

        self.curs_pos()

    def draw(self):
        (ydim, xdim, bits_per_line) = self.dimensions()

        ofs = self.scn_offset
        for i in xrange(ydim):
            bits = self.ba[ofs:ofs+bits_per_line].to01()
            if len(bits) > 0:
                bits = ' '.join([bits[j:j+8] for j in xrange(0, len(bits), 8)])
                self.win.addstr(i, 0, bits)
                ofs += bits_per_line
            else:
                self.win.addstr(i, 0, '~')

            self.win.clrtoeol()

class BitWalk(object):
    def __init__(self, vals, args):
        self.vals = vals
        self.args = args

        self.running = False
        self.bits_win = None

    def do_cmd(self, cmd):
        if cmd == '':
            self.clear_status()
        elif cmd == 'q':
            self.running = False
        else:
            self.status_msg("Command not recognized: %s" % cmd)

    def clear_status(self):
        self.stdscr.move(self.max_y - 1, 0)
        self.stdscr.clrtoeol()

    def status_msg(self, message):
        # TODO: Break message over multiple lines
        if len(message) >= self.max_x:
            message = message[0:self.max_x-1]

        self.clear_status()
        self.stdscr.addstr(self.max_y - 1, 0, message)
        self.stdscr.clrtoeol()

    def status_query(self, query):
        self.status_msg(query)

        curses.echo()
        ret = self.stdscr.getstr()
        curses.noecho()

        return ret.strip()

    def refresh(self):
        self.stdscr.refresh()
        self.bits_win.win.refresh()

    def resize(self):
        (self.max_y, self.max_x) = self.stdscr.getmaxyx()
        (y, x) = (self.max_y, self.max_x)

        curses.resizeterm(y, x)

        if y == 1:
            self.bits_win.win.resize(y, x)
            self.bits_win.curs_pos()
        else:
            self.bits_win.win.resize(y - 1, x)
            self.bits_win.curs_pos()

    def init(self, stdscr):
        self.stdscr = stdscr

        # Setup Curses
        curses.noecho()
        if curses.has_colors():
            curses.start_color()

        # Build windows
        win = curses.newwin(1,1,0,0)
        self.bits_win = BitsWindow(self, win)

        self.resize()
        self.running = True

        self.bits_win.open(self.args[0])

    def run(self, stdscr):
        self.init(stdscr)

        while self.running:
            c = self.stdscr.getch()

            if c == curses.KEY_RESIZE:
                self.resize()
                self.bits_win.draw()
                self.bits_win.curs_pos()
                self.refresh()
                continue

            self.clear_status()

            if c == ord(':'):
                cmd = self.status_query(':')
                self.do_cmd(cmd)
            elif c == curses.KEY_UP:
                self.bits_win.move_curs(y_ofs=-1)
            elif c == curses.KEY_DOWN:
                self.bits_win.move_curs(y_ofs=+1)
            elif c == curses.KEY_LEFT:
                self.bits_win.move_curs(x_ofs=-1)
            elif c == curses.KEY_RIGHT:
                self.bits_win.move_curs(x_ofs=+1)
            elif c == curses.KEY_HOME:
                self.bits_win.move_curs(home=True)
            elif c == curses.KEY_END:
                self.bits_win.move_curs(home=False)

            self.refresh()


def main():
    usage = 'usage: %prog file'
    op = optparse.OptionParser(usage)
    (vals, args) = op.parse_args()

    if len(args) != 1:
        op.print_usage()
        return

    bw = BitWalk(vals, args)
    curses.wrapper(bw.run)

if __name__ == '__main__':
    main()
