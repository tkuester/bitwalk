#!/usr/bin/env python
import sys
import optparse
import curses

class BitWalk(object):
    def __init__(self, vals, args):
        self.vals = vals
        self.args = args

        self.stdscr = None
        self.main_win = None

        self.fp = None
        self.file_name = None
        self.file_len = 1

        self.running = False
        self.bit_spacing = 8

    def status_msg(self, message):
        self.clear_status()
        self.stdscr.addstr(self.max_y-1, 0, message)
        self.stdscr.noutrefresh()

    def status_query(self, message):
        self.status_msg(message)
        curses.doupdate()

        curses.echo()
        curses.curs_set(1)
        ret = self.stdscr.getstr()
        curses.noecho()
        curses.curs_set(0)

        return ret
        
    def clear_status(self):
        self.stdscr.move(self.max_y-1, 0)
        self.stdscr.clrtoeol()
        self.stdscr.noutrefresh()

    def set_title(self, adtl=''):
        self.stdscr.addstr(0, 0, ' [bitwalk] %s %s' % (self.file_name, adtl), curses.A_REVERSE)
        self.stdscr.chgat(-1, curses.A_REVERSE)
        self.stdscr.noutrefresh()

    def open(self, file_name=None):
        # Get file name from user
        if file_name == None:
            file_name = self.status_query('File Name: ')

        # Try to open file, display error to user if necessary
        try:
            self.fp = open(file_name, 'rb', 4096*32)
        except IOError as e:
            msg = "Couldn't open '%s': %s" % (file_name, str(e))
            self.status_msg(msg)
            return

        self.file_name = file_name

        self.fp.seek(0, 2)
        self.file_len = self.fp.tell()

        self.set_title()
        self.clear_status()
        self.scroll(1)

    def scroll(self, line_no=None):
        if self.fp is None:
            return

        (max_y, max_x) = self.main_win.getmaxyx()
        bits_per_line = int((max_x - 4) / (self.bit_spacing + 1)) * self.bit_spacing

        if line_no:
            self.line_no = line_no

        max_line = (self.file_len / bits_per_line)
        if line_no > max_line:
            self.line_no = max_line
        elif self.line_no < 1:
            self.line_no = 1

        offset = (self.line_no - 1) * bits_per_line
        if(offset > self.file_len):
            offset = self.file_len

        self.set_title('%d%%' % int((1.0 * offset / self.file_len) * 100))

        self.fp.seek(offset)
        self.main_win.erase()
        self.main_win.border()

        i = 0
        for y in xrange(max_y - 2):
            self.main_win.move(y + 1, 2)

            try:
                dat = self.fp.read(bits_per_line)
            except IOError as e:
                break 
            
            # TODO: If this line == last line, **

            for bit in dat:
                if bit == '\x00':
                    self.main_win.addch('0')
                elif bit == '\x01':
                    self.main_win.addch('1')

                i += 1
                if i == self.bit_spacing:
                    self.main_win.addch(' ')
                    i = 0

        self.main_win.noutrefresh()

    def resize(self):
        (self.max_y, self.max_x) = self.stdscr.getmaxyx()
        curses.resizeterm(self.max_y, self.max_x)

        if self.main_win is None:
            self.main_win = curses.newwin(self.max_y - 2, self.max_x, 1, 0)

        self.main_win.clear()
        self.main_win.resize(self.max_y-2, self.max_x)
        self.main_win.border()
        self.scroll()

        self.clear_status()
        self.status_msg('%d by %d' % (self.max_y, self.max_x))

        self.main_win.noutrefresh()
        self.stdscr.noutrefresh()

    def setup(self):
        curses.curs_set(0)
        if curses.has_colors():
            curses.start_color()

        # Title bar
        self.resize()

        if len(self.args) == 1:
            self.open(self.args[0])

        curses.doupdate()

    def do_cmd(self, cmd):
        cmd = cmd.strip()

        if cmd is '':
            self.clear_status()
            return

        if cmd == 'q':
            self.running = False
        elif cmd.startswith('o '):
            self.open(cmd[2:])
        else:
            self.status_msg('Invalid command: %s' % cmd)

    def run(self, stdscr):
        self.stdscr = stdscr
        self.running = True

        self.setup()

        while self.running:
            self.clear_status()

            c = self.stdscr.getch()

            if c == curses.KEY_RESIZE:
                self.resize()
            elif c == ord(':'):
                cmd = self.status_query(':')
                self.do_cmd(cmd)
            elif c == curses.KEY_UP:
                self.scroll(self.line_no - 1)
            elif c == curses.KEY_DOWN:
                self.scroll(self.line_no + 1)
            elif c == curses.KEY_NPAGE:
                self.scroll(self.line_no + self.max_y/2)
            elif c == curses.KEY_PPAGE:
                self.scroll(self.line_no - self.max_y/2)

            curses.doupdate()

        if self.fp:
            self.fp.close()

def main():
    usage = 'usage: %prog [options] [file]'
    op = optparse.OptionParser(usage)
    (vals, args) = op.parse_args()

    if len(args) > 1:
        op.error('Only one file at a time')

    bw = BitWalk(vals, args)
    curses.wrapper(bw.run)

if __name__ == '__main__':
    main()
