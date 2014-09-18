#!/usr/bin/env python
import sys
import optparse
import curses

from bwgui import BitWalkGui

class BitWalk(object):
    def __init__(self, vals, args):
        self.vals = vals
        self.args = args

        self.stdscr = None
        self.running = True

    def do_cmd(self, cmd):
        if cmd == 'q':
            self.running = False

    def run(self, stdscr):
        bwg = BitWalkGui(self, stdscr)

        for i, path in enumerate(self.args):
            if i == 0:
                bwg.buffers[0].open(path)
            else:
                bwg.new_buffer(path)

        while self.running:
            c = stdscr.getch()
            bwg.clear_status()

            if c == curses.KEY_RESIZE:
                bwg.resize()
            elif c == ord(':'):
                cmd = bwg.status_query(':')
                self.do_cmd(cmd)
            elif c == curses.KEY_UP:
                bwg.up()
            elif c == curses.KEY_DOWN:
                bwg.down()
            elif c == curses.KEY_LEFT:
                bwg.left()
            elif c == curses.KEY_RIGHT:
                bwg.right()
            elif c == ord('/'):
                search = bwg.status_query('/')
                bwg.get_active_buffer().search(search)
            elif c == ord('n'):
                bwg.get_active_buffer().search()
            elif c == ord('N'):
                bwg.status_msg('TODO')

def main():
    usage = 'usage: %prog [options] [file ..]'
    op = optparse.OptionParser(usage)
    (vals, args) = op.parse_args()

    bw = BitWalk(vals, args)
    curses.wrapper(bw.run)

if __name__ == '__main__':
    main()
