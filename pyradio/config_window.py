# -*- coding: utf-8 -*-
import curses
from copy import deepcopy
from textwrap import wrap

from .common import *
from .encodings import *
import logging

logger = logging.getLogger(__name__)

import locale
locale.setlocale(locale.LC_ALL, '')    # set your locale

class PyRadioConfigWindow(object):

    parent = None
    _win = None

    _title = 'PyRadio Configuration'

    selection = __selection = 1

    _headers = []

    _num_of_help_lines = 0
    _help_text = []
    _help_text.append(None)
    _help_text.append(['Specify the player to use with PyRadio, or the player detection order.', '|',
    'This is the eqivelant to the -u , --use-player command line parameter.', '|',
    'Example:', '  player = vlc', 'or', '  player = vlc,mpv, mplayer', '|',
    'Default value: mpv,mplayer,vlc'])
    _help_text.append(['This is the playlist to open if none is specified.', '|',
    'You can scecify full path to CSV file, or if the playlist is in the config directory, playlist name filename without extension or playlist number as reported by -ls command line option.', '|', 'Default value: stations'])
    _help_text.append(['This is the equivalent to the -p , --play command line parameter.', '|',
    'The station number within the default playlist to play.', '|',
    'Value is 0..number of stations, -1 (or False) means no auto play, "random" means play a random station.', '|', 'Default value: False'])
    _help_text.append(['This is the encoding used by default when reading data provided by a station such as song title, etc. If reading said data ends up in an error, "utf-8" will be used instead.',
    '|', 'Default value: utf-8'])
    _help_text.append(['PyRadio will wait for this number of seconds to get a station/server message indicating that playback has actually started.', '|',
    'If this does not happen within this number of seconds after the connection is initiated, PyRadio will consider the station unreachable, and display the "Failed to connect to: station" message.', '|', 'Press "h"/Left or "l"/Right to change value.',
    '|', 'Valid values: 5 - 60', 'Default value: 10'])
    _help_text.append(None)
    _help_text.append(['The theme to be used by default.', '|', 'Hardcoded themes:',
    '  * dark (8 colors)', '  * light (8 colors)',
    '  * dark_16_colors (16 colors)',
    '      dark theme alternative',
    '  * light_16_colors (16 colors)',
    '      light theme alternative',
    '  * black_on_white (256 colors)',
    '  * white_on_black (256 colors)',
    '|', 'The option is automatically applied and saved.',
    '|', 'Default value = dark'])
    _help_text.append(['If False, theme colors will be used.',
    "If True and a compositor is running, the stations' window background will be transparent. If True and a compositor is not running, the terminal's background color will be used.", '|', 'The option is automatically applied and saved.',
    '|', 'Default value: False'])
    _help_text.append(None)
    _help_text.append(['Specify whether you will be asked to confirm every station deletion action.',
    '|', 'Default value: True'])
    _help_text.append(['Specify whether you will be asked to confirm playlist reloading, when the playlist has not been modified within Pyradio.',
    '|', 'Default value: True'])
    _help_text.append(['Specify whether you will be asked to save a modified playlist whenever it needs saving.', '|', 'Default value: False'])

    def __init__(self, parent, config,
            toggle_transparency_function,
            show_theme_selector_function):
        self.parent = parent
        self._cnf = config
        self._toggle_transparency_function = toggle_transparency_function
        self._show_theme_selector_function = show_theme_selector_function
        self._saved_config_options = config.opts
        self._config_options = deepcopy(config.opts)
        if self._saved_config_options == self._config_options:
            logger.info('options are the same')
        else:
            logger.info('options are not the same')
        self.number_of_items = len(self._config_options) - 2
        for i, n in enumerate(list(self._config_options.values())):
            if n[1] == '':
                self._headers.append(i)
        self.init_config_win()
        self.refresh_config_win()

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val
        self.init_config_win()

    @property
    def selection(self):
        return self.__selection

    @selection.setter
    def selection(self, val):
        if val < 1:
            val = len(self._headers) - 1
        elif val >= self.number_of_items:
            val = 1
        if val in self._headers:
            self.__selection = val + 1
        else:
            self.__selection = val
        #self.refresh_config_win()

    def init_config_win(self):
        self._win = None
        self.maxY, self.maxX = self.__parent.getmaxyx()
        self._second_column = int(self.maxX / 2 )
        self._win = curses.newwin(self.maxY, self.maxX, 1, 0)
        self._populate_help_lines()

    def refresh_config_win(self):
        self._win.bkgdset(' ', curses.color_pair(3))
        self._win.erase()
        self._win.box()
        self._print_title()
        #self._win.addstr(0,
        #    int((self.maxX - len(self._title)) / 2),
        #    self._title,
        #    curses.color_pair(4))
        min_lines = len(self._config_options)
        if min_lines < self._max_number_of_help_lines:
            min_lines = self._max_number_of_help_lines
        if self.maxX < 80 or self.maxY < min_lines + 3:
            self._too_small = True
        else:
            self._too_small = False
        if self._too_small:
            msg = 'Window too small to display content!'
            if self.maxX < len(msg) + 2:
                msg = 'Window too small!'
            self._win.addstr(int(self.maxY / 2),
                int((self.maxX - len(msg)) / 2),
                msg, curses.color_pair(5))
        else:
            self._win.addstr(1, self._second_column, 'Option Help', curses.color_pair(4))
        self.refresh_selection()

    def _print_title(self):
        self._win.box()
        if self._config_options == self._saved_config_options:
            dirty_title = ' '
        else:
            dirty_title = ' *'
        X = int((self.maxX - len(self._title) - len(dirty_title) + 1) / 2)
        self._win.addstr(0, X, dirty_title, curses.color_pair(5))
        self._win.addstr(self._title + ' ', curses.color_pair(4))

    def refresh_selection(self):
        self._print_title()
        if not self._too_small:
            for i, it in enumerate(list(self._config_options.values())):
                if i < self.number_of_items:
                    if i == self.__selection:
                        col = hcol = curses.color_pair(6)
                        self._print_options_help()
                    else:
                        col = curses.color_pair(5)
                        hcol = curses.color_pair(4)
                    hline_width = self._second_column - 2
                    self._win.hline(i+1, 1, ' ', hline_width, col)
                    if i in self._headers:
                        self._win.addstr(i+1, 1, it[0], curses.color_pair(4))
                    else:
                        self._win.addstr(i+1, 3, it[0], col)
                        if isinstance(it[1], bool):
                            self._win.addstr('{}'.format(it[1]), hcol)
                        else:
                            self._win.addstr('{}'.format(it[1][:self._second_column - len(it[0]) - 6 ]), hcol)
        self._win.refresh()

    def _get_col_line(self, ind):
        if ind < self._headers:
            self._column = 3
            self._line = ind + 2
        else:
            self._column = self._second_column + 2
            self._line = ind - self._headers + 2

    def _put_cursor(self, jump):
        self.__selection += jump
        if jump > 0:
            if self.__selection in self._headers:
                self.__selection += 1
            if self.__selection >= self.number_of_items:
                self.__selection = 1
        else:
            if self.__selection in self._headers:
                self.__selection -= 1
            if self.__selection < 1:
                self.__selection = self.number_of_items - 1

    def _populate_help_lines(self):
        self._help_lines = []
        self._max_number_of_help_lines = 0
        for z in self._help_text:
            if z is None:
                self._help_lines.append(None)
            else:
                all_lines = []
                for k in z:
                    lines = []
                    lines = wrap(k, self.maxX - self._second_column - 2)
                    all_lines.extend(lines)
                self._help_lines.append(all_lines)
                if len(all_lines) > self._max_number_of_help_lines:
                    self._max_number_of_help_lines = len(all_lines)

    def _print_options_help(self):
        for i, x in enumerate(self._help_lines[self.selection]):
            if i + 2 == self.maxY:
                break
            self._win.addstr(i+2, self._second_column, ' ' * (self._second_column - 1), curses.color_pair(5))
            self._win.addstr(i+2, self._second_column, x.replace('|',''), curses.color_pair(5))
        if len(self._help_lines[self.selection]) < self._num_of_help_lines:
            for i in range(len(self._help_lines[self.selection]), self._num_of_help_lines):
                try:
                    self._win.addstr(i+2, self._second_column, ' ' * (self._second_column - 1), curses.color_pair(5))
                except:
                    pass
        self._num_of_help_lines = len(self._help_lines[self.selection])
        """
        # Uncomment if trouble with help lines
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('self._num_of_help_lines = {}'.format(self._num_of_help_lines))
        """

    def keypress(self, char):
        if self._too_small:
            return 1, []
        val = list(self._config_options.items())[self.selection]
        if val[0] == 'connection_timeout':
            if char in (curses.KEY_RIGHT, ord('l')):
                t = int(val[1][1])
                if t < 60:
                    t += 1
                    self._config_options[val[0]][1] = str(t)
                    self._win.addstr(self.selection+1,
                        3 + len(val[1][0]),
                        str(t) + ' ', curses.color_pair(6))
                    self._print_title()
                    self._win.refresh()
                return -1, []

            elif char in (curses.KEY_LEFT, ord('h')):
                t = int(val[1][1])
                if t > 5:
                    t -= 1
                    self._config_options[val[0]][1] = str(t)
                    self._win.addstr(self.selection+1,
                        3 + len(val[1][0]),
                        str(t) + ' ', curses.color_pair(6))
                    self._print_title()
                    self._win.refresh()
                return -1, []

        if char in (ord('k'), curses.KEY_UP):
            self._put_cursor(-1)
            self.refresh_selection()
        elif char in (ord('j'), curses.KEY_DOWN):
            self._put_cursor(1)
            self.refresh_selection()
        elif char in (curses.KEY_NPAGE, ):
            if self.__selection + 4 >= self.number_of_items and \
                    self.__selection < self.number_of_items - 1:
                self.__selection = self.number_of_items - 5
            self._put_cursor(4)
            self.refresh_selection()
        elif char in (curses.KEY_PPAGE, ):
            if self.__selection - 4 < 1 and self.__selection > 1:
                self.__selection = 5
            self._put_cursor(-4)
            self.refresh_selection()
        elif char in (ord('g'), curses.KEY_HOME):
            self.__selection = 1
            self.refresh_selection()
        elif char in (ord('G'), curses.KEY_END):
            self.__selection = self.number_of_items - 1
            self.refresh_selection()
        elif char in (ord('r'), ):
            self._config_options = deepcopy(self._saved_config_options)
            self.refresh_selection()
        elif char in (curses.KEY_EXIT, 27, ord('q'), ord('h'), curses.KEY_LEFT):
            self._win.nodelay(True)
            char = self._win.getch()
            self._win.nodelay(False)
            if char == -1:
                """ ESCAPE """
                return 1, []
        elif char in (ord('s'), ):
            # save and exit
            return 0, [1]
        elif char in (curses.KEY_ENTER, ord('\n'),
                ord('\r'), ord(' '), ord('l'), curses.KEY_RIGHT):
            # alter option value
            vals = list(self._config_options.items())
            sel = vals[self.selection][0]
            if sel == 'player':
                #self.opts['player'][1] = sp[1].lower().strip()
                return SELECT_PLAYER_MODE, []
            elif sel == 'default_encoding':
                pass
                return SELECT_ENCODING_MODE, []
                #self.opts['default_encoding'][1] = sp[1].strip()
            elif sel == 'theme':
                self._show_theme_selector_function()
            elif sel == 'default_playlist':
                pass
            elif sel == 'default_station':
                pass
                #st = sp[1].strip()
                #if st == '-1' or st.lower() == 'false':
                #    self.opts['default_station'][1] = 'False'
                #elif st == 'random':
                #    self.opts['default_station'][1] = None
                #else:
                #    pass
                #    #self.opts['default_station'][1] = st
            elif sel == 'confirm_station_deletion' or \
                    sel == 'confirm_playlist_reload' or \
                    sel == 'auto_save_playlist':
                #self._cnf.auto_save_playlist = not self._config_options[sel][1]
                self._config_options[sel][1] = not self._config_options[sel][1]
                self.refresh_selection()
            elif sel == 'use_transparency':
                self._toggle_transparency_function()
                self.refresh_selection()
        return -1, []

class PyRadioSelectPlayer(object):

    maxY = 6
    maxX = 25
    selection = [ 0, 0 ]

    _title = ' Player Selection '

    _win = None

    _players =  ( 'mpv', 'mplayer', 'vlc' )
    _working_players = [ [], [] ]

    # REMINDER: column 1 is     acive players - displayed right
    #           column 0 is available players - displayed left
    _column = 1

    def __init__(self, maxY, maxX, player):
        self._parent_maxY = maxY
        self._parent_maxX = maxX
        self.player = player
        self._orig_player = player
        self._populate_working_players()
        self._validate_column()
        self.init_window()

    def init_window(self):
        self._win = None
        self._win = curses.newwin(self.maxY, self.maxX,
                int((self._parent_maxY - self.maxY) / 2),
                int((self._parent_maxX - self.maxX) / 2))

    def refresh_win(self):
        self._win.bkgdset(' ', curses.color_pair(3))
        self._win.erase()
        self._win.box()
        self._win.addstr(0,
            int((self.maxX - len(self._title)) / 2),
            self._title,
            curses.color_pair(4))
        self._win.addstr(1, 2, 'Available' , curses.color_pair(4))
        self._win.addstr(1, int(self.maxX / 2 + 2), 'Active' , curses.color_pair(4))
        self.refresh_selection()

    def refresh_selection(self):
        for i in range(2, self.maxY - 1):
            self._win.hline(i, 1, ' ', self.maxX - 2, curses.color_pair(5))

        if self._working_players[0]:
            if self.selection[0] >= len(self._working_players[0]):
                self.selection[0] = 0
            for i, pl in enumerate(self._working_players[0]):
                col =curses.color_pair(5)
                if self.selection[0] == i:
                    if self._column == 0:
                        col = curses.color_pair(6)
                        self._win.hline(i+2, int(self.maxX / 2) + 1, ' ', int(self.maxX / 2) - 1, col)
                self._win.addstr(i+2, int(self.maxX / 2 + 2), pl, col)

        if self._working_players[1]:
            if self.selection[1] >= len(self._working_players[1]):
                self.selection[1] = 0
            for i, pl in enumerate(self._working_players[1]):
                col = curses.color_pair(5)
                if self.selection[1] == i:
                    if self._column == 1:
                        col = curses.color_pair(6)
                        self._win.hline(i+2, 1, ' ', int(self.maxX / 2) - 1, col)
                self._win.addstr(i+2, 2, pl, col)

        for i in range(1, self.maxY - 1):
            try:
                self._win.addch(i, int(self.maxX / 2), '│', curses.color_pair(3))
            except:
                self._win.addstr(i, int(self.maxX / 2), u'│'.encode('utf-8'), curses.color_pair(3))
        try:
            self._win.addch(self.maxY - 1, int(self.maxX / 2), '┴', curses.color_pair(3))
        except:
            self._win.addstr(self.maxY - 1, int(self.maxX / 2), u'┴'.encode('utf-8'), curses.color_pair(3))

        self._win.refresh()

    def _populate_working_players(self, these_players=''):
        if these_players:
            self._working_players[0] = these_players.replace(' ', '').split(',')
        else:
            self._working_players[0] = self._orig_player.replace(' ', '').split(',')
        self._working_players[1] = []
        for i, pl in enumerate(self._players):
            if pl not in self._working_players[0]:
                self._working_players[1].append(pl)

    def keypress(self, char):
        if char in (9, ):
            new_column = self._switch_column()
            if self._working_players[new_column]:
                self._column = new_column
                self.refresh_selection()

        elif char in (curses.KEY_RIGHT, ord('l')):
            if self._column == 0:
                if self._working_players[0]:
                    item = self._working_players[0][self.selection[0]]
                    self._working_players[0].remove(item)
                    self._working_players[0].append(item)
                    self.refresh_selection()

        elif char in (curses.KEY_UP, ord('k')):
            if self._working_players[self._column]:
                self.selection[self._column] -= 1
                if self.selection[self._column] == -1:
                    self.selection[self._column] = len(self._working_players[self._column]) - 1
                self.refresh_selection()

        elif char in (curses.KEY_DOWN, ord('j')):
            if self._working_players[self._column]:
                self.selection[self._column] += 1
                if self.selection[self._column] == len(self._working_players[self._column]):
                    self.selection[self._column] = 0
                self.refresh_selection()

        elif char in (curses.KEY_EXIT, 27, ord('q'), curses.KEY_LEFT, ord('h')):
            self._win.nodelay(True)
            char = self._win.getch()
            self._win.nodelay(False)
            if char == -1:
                """ ESCAPE """
                return 1, []

        elif char in (curses.KEY_ENTER, ord('\n'), ord('\r'),
            ord(' '), ord('l'), curses.KEY_RIGHT):
            other_column = self._switch_column()
            this_item = self._working_players[self._column][self.selection[self._column]]
            self._working_players[self._column].remove(this_item)
            self._working_players[other_column].append(this_item)
            self._validate_column()
            self.refresh_selection()

        elif char == ord('r'):
            self._populate_working_players()
            self.refresh_selection()

        elif char == ord('s'):
            if self._working_players[0]:
                self.player = ','.join(self._working_players[0])
                return 0, self._working_players[0]
        return -1, []

    def _switch_column(self):
        col = (1, 0)
        return col[self._column]

    def setPlayers(self, these_players):
        self.player = these_players
        self._populate_working_players(these_players)
        self._validate_column()

    def _validate_column(self):
        if not self._working_players[self._column]:
            self._column = self._switch_column()

class PyRadioSelectEncodings(object):
    max_enc_len = 15

    _win = None

    _title = ' Encoding Selection '

    _num_of_columns = 4
    maxY = maxX = 10
    _column = _row = 0

    _encodings = []
    list_maxY = 0
    startPos = 0
    selection = 0

    _invalid = []

    def __init__(self, maxY, maxX, encoding):
        self._parent_maxY = maxY
        self._parent_maxX = maxX
        self.encoding = encoding
        self._orig_encoding = encoding

        self._orig_encoding = encoding
        self._encodings = get_encodings()
        self._num_of_rows = int(len(self._encodings) / self._num_of_columns)
        self.init_window()

    def init_window(self, set_encoding=True):
        self._win = None
        self._win = curses.newwin(self.maxY, self.maxX, 
                int((self._parent_maxY - self.maxY) / 2) + 1,
                int((self._parent_maxX - self.maxX) / 2))
        if set_encoding:
            self.setEncoding(self.encoding, init=True)

    def _fix_geometry(self):
        self._num_of_columns = int((self._parent_maxX - 2) / (self.max_enc_len + 2 ))
        if self._num_of_columns > 8:
            self._num_of_columns = 8
        elif self._num_of_columns > 4:
            self._num_of_columns = 4

        self.maxY = int(len(self._encodings) / self._num_of_columns) + 5
        if len(self._encodings) % self._num_of_columns > 0:
            self.maxY += 1
        if self._num_of_columns == 8:
            maxY = int(len(self._encodings) / 6) + 5
            if len(self._encodings) % 6 > 0:
                maxY += 1
            if maxY < self._parent_maxY:
                self.maxY = maxY
                self._num_of_columns = 6
        while self.maxY > self._parent_maxY - 2:
            self.maxY -= 1
        self.list_maxY = self.maxY - 5
        self.maxX = self._num_of_columns * (self.max_enc_len + 2) + 2
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('maxY,maxX = {0},{1}'.format(self.maxY, self.maxX))
            logger.debug('Number of columns = {}'.format(self._num_of_columns))
            logger.debug('Number of rows = {}'.format(self._num_of_rows))
            logger.debug('Number of visible rows = {}'.format(self.list_maxY))

    def refresh_win(self, set_encoding=True):
        """ set_encoding is False when resizing """
        self._fix_geometry()
        #self._win.resize(self.maxY, self.maxX)
        #self._win.mvwin(int((self._parent_maxY - self.maxY) / 2) + 1, int((self._parent_maxX - self.maxX) / 2))
        self.init_window(set_encoding)
        self._win.bkgdset(' ', curses.color_pair(3))
        self._win.erase()
        self._win.box()
        self._win.addstr(0,
            int((self.maxX - len(self._title)) / 2),
            self._title,
            curses.color_pair(4))
        for i in range(1, self.maxX - 1):
            try:
                self._win.addch(self.maxY -4,  i, '─', curses.color_pair(3))
            except:
                self._win.addstr(self.maxY -4 , i, u'─'.encode('utf-8'), curses.color_pair(3))
        try:
            self._win.addch(self.maxY - 4, 0, '├', curses.color_pair(3))
            self._win.addch(self.maxY - 4, self.maxX - 1, '┤', curses.color_pair(3))
        except:
            self._win.addstr(self.maxY - 4,  0, u'├'.encode('utf-8'), curses.color_pair(3))
            self._win.addstr(self.maxY - 4,  self.maxX - 1, u'┤'.encode('utf-8'), curses.color_pair(3))

        self._num_of_rows = int(len(self._encodings) / self._num_of_columns)
        self._get_invalids()
        self.refresh_selection()

    def refresh_selection(self):
        if self._parent_maxX < 4 * (self.max_enc_len + 2) + 2 or self.maxY < 10:
            self._too_small = True
        else:
            self._too_small = False
        if self._too_small:
            msg = 'Window too small to display content!'
            if self.maxX - 2 < len(msg):
                msg = 'Window too small!'
            self._win.hline(self.maxY - 4, 1, ' ', self.maxX - 2, curses.color_pair(5))
            try:
                self._win.addch(self.maxY - 4, 0, '│', curses.color_pair(3))
                self._win.addch(self.maxY - 4, self.maxX - 1, '│', curses.color_pair(3))
            except:
                self._win.addstr(self.maxY - 4,  0, u'│'.encode('utf-8'), curses.color_pair(3))
                self._win.addstr(self.maxY - 4,  self.maxX - 1, u'│'.encode('utf-8'), curses.color_pair(3))
            self._win.addstr(int(self.maxY / 2),
                int((self.maxX - len(msg)) / 2),
                msg, curses.color_pair(5))

        else:
            self._win.hline(self.maxY - 3, 1, ' ', self.maxX - 2, curses.color_pair(5))
            self._win.hline(self.maxY - 2, 1, ' ', self.maxX - 2, curses.color_pair(5))

            self._set_startPos()
            for i in range(0, self._num_of_columns):
                for y in range(0, self.list_maxY):
                    xx = i * self.max_enc_len + 2 + i * 2
                    yy = y + 1
                    pos = self.startPos + i * self._num_of_rows + y
                    if i > 0: pos += i
                    if pos == self.selection:
                        col = curses.color_pair(6)
                        self._win.addstr(self.maxY - 3, 1, ' ' * (self.maxX - 2), curses.color_pair(4))
                        self._win.addstr(self.maxY - 3, 2, '   Alias: ', curses.color_pair(4))
                        self._win.addstr(self._encodings[pos][1][:self.maxX - 14], curses.color_pair(5))
                        self._win.addstr(self.maxY - 2, 1, ' ' * (self.maxX - 2), curses.color_pair(4))
                        self._win.addstr(self.maxY - 2, 2, 'Language: ', curses.color_pair(4))
                        self._win.addstr(self._encodings[pos][2][:self.maxX - 14], curses.color_pair(5))
                    else:
                        col = curses.color_pair(5)
                    self._win.addstr(yy, xx -1, ' ' * (self.max_enc_len + 2), col)
                    if pos < len(self._encodings):
                        self._win.addstr(yy, xx, self._encodings[pos][0], col)

        self._win.refresh()

    def _get_invalids(self):
        self._invalid = []
        col = self._num_of_columns - 1
        row = self._num_of_rows
        b = self._col_row_tp_selection(col, row)
        while b >= len(self._encodings):
            self._invalid.append((col, row))
            row -= 1
            b = self._col_row_tp_selection(col, row)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('invalid = {}'.format(self._invalid))

    def _set_startPos(self):
        try:
            if self.list_maxY == self._num_of_rows + 1:
                self.startPos = 0
        except:
            pass

    def resize(self, init=False):
        col, row = self._selection_to_col_row(self.selection)
        if not (self.startPos <= row <= self.startPos + self.list_maxY - 1):
            while row > self.startPos:
                self.startPos += 1
            while row < self.startPos + self.list_maxY - 1:
                self.startPos -= 1
        ''' if the selection at the end of the list,
            try to scroll down '''
        if init and row > self.list_maxY:
            new_startPos = self._num_of_rows - self.list_maxY + 1
            if row > new_startPos:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug('setting startPos at {}'.format(new_startPos))
                self.startPos = new_startPos
        self.refresh_selection()

    def setEncoding(self, this_encoding, init=False):
        #this_encoding = 'iso8859-16'
        ret = self._is_encoding(this_encoding)
        if ret == -1:
            if logger.isEnabledFor(logging.ERROR):
                logger.error('encoding "{}" not found, reverting to "utf-8"'.format(this_encoding))
            self.encoding = 'utf-8'
            self.selection = self._is_encoding(self.encoding)
        else:
            self.selection = ret
            self.encoding = this_encoding
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('encoding "{0}" found at {1}'.format(this_encoding, ret))
        self.resize(init)
        self.refresh_selection()

    def _is_encoding(self, a_string):
        def in_alias(a_list, a_string):
            splited = a_list.split(',')
            for n in splited:
                if n.strip() == a_string:
                    return True
            return False
        for i, an_encoding in enumerate(self._encodings):
            if a_string == an_encoding[0] or in_alias(an_encoding[1], a_string):
                return i
        return -1

    def _fix_startPos(self, direction=1):
        col, row = self._selection_to_col_row(self.selection)
        startRow = self.startPos
        endRow = self.startPos + self.list_maxY - 1
        if not (startRow <= row <= endRow):
            self.startPos = self.startPos + direction
            if direction > 0:
                #if self.startPos >= self.list_maxY or row == 0:
                if row == 0:
                    self.startPos = 0
                else:
                    self.resize()
            elif direction < 0:
                if row == self._num_of_rows - 2 or row == self._num_of_rows:
                    self.startPos = self._num_of_rows - self.list_maxY + 1
                elif self.startPos < 0:
                    self.resize(init=True)
            if self.startPos < 0:
                self.startPos = 0

    def _selection_to_col_row(self, sel):
        x = int(sel / (self._num_of_rows+1))
        y = sel % (self._num_of_rows +1)
        return x, y

    def _col_row_tp_selection(self, a_column, a_row):
        return (self._num_of_rows + 1) * a_column + a_row

    def keypress(self, char):
        if char in (ord('r'), ):
            self.encoding = self._orig_encoding
            self.setEncoding(self.encoding, init=True)

        if char in (curses.KEY_UP, ord('k')):
            self.selection -= 1
            if self.selection < 0:
                self.selection = len(self._encodings) - 1
            self._fix_startPos(-1)
            self.refresh_selection()

        elif char in (curses.KEY_DOWN, ord('j')):
            self.selection += 1
            if self.selection == len(self._encodings):
                self.selection = 0
            self._fix_startPos(1)
            self.refresh_selection()

        elif char in (curses.KEY_RIGHT, ord('l')):
            self._column, self._row = self._selection_to_col_row(self.selection)
            self._column += 1
            if self._column == self._num_of_columns:
                self._column = 0
                self._row += 1
                if self._row == self._num_of_rows:
                    self._row = 0
            if (self._column, self._row) in self._invalid:
                self._column = 0
                self._row += 1
                if self._row > self._num_of_rows:
                    self._row = 0
            self.selection = self._col_row_tp_selection(self._column, self._row)
            self._fix_startPos(1)
            self.refresh_selection()

        elif char in (curses.KEY_LEFT, ord('h')):
            self._column, self._row = self._selection_to_col_row(self.selection)
            self._column -= 1
            if self._column == -1:
                self._column = self._num_of_columns - 1
                self._row -= 1
            if (self._column, self._row) in self._invalid:
                self._column -= 1
            self.selection = self._col_row_tp_selection(self._column, self._row)
            self._fix_startPos(-1)
            self.refresh_selection()

        elif char in (curses.KEY_NPAGE, ):
            if self.selection == len(self._encodings) -1:
                self.selection = 0
            else:
                self.selection += 5
                if self.selection > len(self._encodings) - 1:
                    self.selection = len(self._encodings) - 1
            self._fix_startPos(5)
            self.refresh_selection()

        elif char in (curses.KEY_PPAGE, ):
            if self.selection == 0:
                self.selection = len(self._encodings) - 1
            else:
                self.selection -= 5
                if self.selection < 0:
                    self.selection = 0
            self._fix_startPos(-5)
            self.refresh_selection()

        elif char in (curses.KEY_HOME, ord('g')):
            self.selection = 0
            self.startPos = 0
            self.refresh_selection()

        elif char in (curses.KEY_END, ord('G')):
            self.selection = len(self._encodings) - 1
            self.startPos = self._num_of_rows - self.list_maxY + 1
            self.refresh_selection()

        elif char in (curses.KEY_EXIT, 27, ord('q'), curses.KEY_LEFT, ord('h')):
            self._win.nodelay(True)
            char = self._win.getch()
            self._win.nodelay(False)
            if char == -1:
                """ ESCAPE """
                return 1, ''

        elif char in (curses.KEY_ENTER, ord('\n'),
                ord('\r'), ord(' '), ord('s')):
            return 0, self._encodings[self.selection][0] 

        return -1, ''

# pymode:lint_ignore=W901
