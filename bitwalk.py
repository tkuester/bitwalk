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
            self.scn_offset = 0
            self.curs_offset = 0
            fp.close()

            self.parent.status_msg("\"%s\" %d bits" % (path, len(self.ba)))
            self.draw()
            self.parent.refresh()
        except (IOError, OSError) as e:
            self.parent.status_msg(str(e))
            self.ba = bitarray()

    def curs_to_pos(self):
        pass

    def draw(self):
        (y, x) = self.win.getmaxyx()
        bits_per_line = (x / 9) * 8
        if bits_per_line < 8:
            bits_per_line == 8

        self.parent.status_msg("New dims: %d, %d / %d per row" % (y, x,
            bits_per_line))

        ofs = self.scn_offset
        for i in xrange(y):
            bits = self.ba[ofs:ofs+bits_per_line].to01()
            if len(bits) > 0:
                bits = ' '.join([bits[j:j+8] for j in xrange(0, len(bits), 8)])
                self.win.addstr(i, 0, bits)
                ofs += bits_per_line
            else:
                self.win.addstr(i, 0, '~')

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
        self.clear_status()
        self.stdscr.addstr(self.max_y - 1, 0, message)
        #self.bits_win.steal_curs()

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
        else:
            self.bits_win.win.resize(y - 1, x)

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
                self.refresh()
                continue

            self.clear_status()

            if c == ord(':'):
                cmd = self.status_query(':')
                self.do_cmd(cmd)

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
