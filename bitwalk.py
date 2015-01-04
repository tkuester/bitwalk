#!/usr/bin/env python
import sys
import optparse
import curses

from bwbuffer import BitWalkBuffer

class BitWalk(object):
    def __init__(self, vals, args):
        self.vals = vals
        self.args = args

        self.running = False
        self.buffers = []
        self.active_buffer = 0

    def do_cmd(self, cmd):
        if cmd == 'q':
            self.running = False

    def clear_status(self):
        self.stdscr.move(self.max_y - 1, 0)
        self.stdscr.clrtoeol()

    def status_msg(self, message):
        self.clear_status()
        self.stdscr.addstr(self.max_y - 1, 0, message)

    def status_query(self, query):
        self.status_msg(query)

        curses.echo()
        ret = self.stdscr.getstr()
        curses.noecho()

        return ret.strip()

    def resize(self):
        (self.max_y, self.max_x) = self.stdscr.getmaxyx()
        curses.resizeterm(self.max_y, self.max_x)

    def get_active_buffer(self):
        return self.buffers[self.active_buffer]

    def run(self, stdscr):
        # Setup Curses
        self.stdscr = stdscr

        curses.noecho()
        if curses.has_colors():
            curses.start_color()

        self.resize()

        win = curses.newwin(10, 10, 0, 0)
        win.border()

        self.running = True
        while self.running:
            c = self.stdscr.getch()

            if c == curses.KEY_RESIZE:
                self.resize()
                continue

            self.clear_status()

            if c == ord(':'):
                cmd = self.status_query(':')
                self.do_cmd(cmd)

def main():
    usage = 'usage: %prog [options] file [...]'
    op = optparse.OptionParser(usage)
    (vals, args) = op.parse_args()

    if len(args) == 0:
        print 'No files to read'
        return

    bw = BitWalk(vals, args)
    curses.wrapper(bw.run)

if __name__ == '__main__':
    main()
