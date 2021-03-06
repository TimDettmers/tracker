from winlaunch import current_windows
from PyQt4 import QtGui, QtCore

import keyboard
import bashmagic
import time
import datetime
import sys

from os.path import join
from threading import Thread

productivity_interval = 60*5
interval = 60*60
base = './'
filename = '/home/tim/data.txt'

keys = [0,1,2,3,4,5]
codes = [48, 49, 50, 51, 52, 53]
code2key = {}
code2key[48] = 0
code2key[49] = 1
code2key[50] = 2
code2key[51] = 3
code2key[52] = 4
code2key[53] = 5

key2code = {}
key2code[0] = 48
key2code[1] = 49
key2code[2] = 50
key2code[3] = 51
key2code[4] = 52
key2code[5] = 53

width = 1920
offsets = [250, 250, 750]
displays = 3

class KeyEvent:
    key1 = None
    key2 = None

    @staticmethod
    def add_key(key):
        if key in codes:
            if KeyEvent.key1 is None:
                KeyEvent.key1 = key
                return

            if key == KeyEvent.key1:
                KeyEvent.key2 = key
                QtGui.qApp.quit()
            else:
                KeyEvent.key1 = key

def handle_key_event():
    while KeyEvent.key2 not in code2key:
        app = QtGui.QApplication(sys.argv)
        widgets = []
        for display_no in range(displays):
            for i, key in enumerate(keys):
                widgets.append(mymainwindow(500 + (i*100) + (width*display_no), 100+ (i*100) + (offsets[display_no]), str(key)))
                widgets[-1].show()

        app.exec_()

    productivity = code2key[KeyEvent.key1]
    KeyEvent.key1 = None
    KeyEvent.key2 = None
    return productivity



class mymainwindow(QtGui.QLabel):
    def __init__(self, x, y, text):
        QtGui.QWidget.__init__(self)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint
            )
        #self.setLineWrapMode(QtGui.QTextEdit.FixedPixelWidth)
        self.setGeometry(x,y, 100,100)
        font = self.font()
        font.setFamily("Courier")
        font.setPointSize(20)
        fgcolor = QtGui.QColor('#474640')
        bgcolor = QtGui.QColor('#3AD7AF')
        P = self.palette()
        P.setColor(QtGui.QPalette.Background, bgcolor)
        P.setColor(QtGui.QPalette.Foreground, fgcolor)
        self.setPalette(P)

        self.setFont(font)
        if isinstance(text, tuple):
            text = "".join(text)
            self.num_keys = 2
        else:
            self.num_keys = 1
        self.setText(text)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.num_key_events = 0
        self.text = text


        #QtCore.QTimer.singleShot(300, self.close)

    def center(self):
        frameGm = self.frameGeometry()
        screen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
        centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        centerPoint = QtCore.QPoint(centerPoint.x()+self.offset, centerPoint.y())
        self.move(centerPoint)

    def mousePressEvent(self, event):
        if KeyEvent.key1 is None:
            KeyEvent.key1 = key2code[int(self.text)]
            return

        if KeyEvent.key1 == key2code[int(self.text)]:
            KeyEvent.key2 = key2code[int(self.text)]
            QtGui.qApp.quit()
        else:
            KeyEvent.key1 = key2code[int(self.text)]

    def keyPressEvent(self, e):
        KeyEvent.add_key(e.key())

class Tracker(Thread):
    def __init__(self, poll_interval=1):
        super(Tracker, self).__init__()
        self.daemon = True
        self.poll_interval = poll_interval
        self.aggregated_data = {}
        self.current_time = datetime.datetime.now()
        self.last_productivity_prompt = datetime.datetime.now()
        self.productivity = []
        self.computed_productivity = False

    def run(self):
        while True:
            if self.computed_productivity:
                time.sleep(1)
                self.computed_productivity = False
                continue

            current_time = datetime.datetime.now()
            if (current_time - self.last_productivity_prompt).seconds > productivity_interval:
                productivity = handle_key_event()
                self.productivity.append((datetime.datetime.now(), productivity))
                self.last_productivity_prompt = current_time
                self.computed_productivity = True
                continue

            if (current_time - self.current_time).seconds > interval:
                self.print_stats(True)
                self.current_time = datetime.datetime.now()

            name = bashmagic.get_active_window_name()
            if name is None: continue
            name = name.strip()
            path = bashmagic.get_active_window_path()
            if path not in self.aggregated_data: self.aggregated_data[path] = {}
            if name not in self.aggregated_data[path]: self.aggregated_data[path][name] = 0

            self.aggregated_data[path][name] += self.poll_interval
            time.sleep(self.poll_interval)


    def print_stats(self, save=False):
        print('stats')
        data = []
        data.append('='*75)
        data.append(str(datetime.datetime.now()))
        for path in self.aggregated_data:
            aggregated_duration = 0
            for name, duration in self.aggregated_data[path].items():
                aggregated_duration += duration

            m, s = divmod(aggregated_duration, 60)
            h, m = divmod(m, 60)
            data.append('{0}\t{1:02d}:{2:02d}:{3:02d}'.format(path, h, m, s))

            data.append('')
        data.append('='*75)

        for line in data:
            print(line)

        for dt, prod in self.productivity:
            print(prod)


        if save:
            print('')
            print('='*80)
            print('SAVING DATA!')
            print('='*80)
            print('')
            with open(join(base, filename), 'a') as f:
                for line in data:
                    f.write(line + '\n')
                f.write('\n')
                for dt, productivity in self.productivity:
                    f.write('{0}: {1}\n'.format(dt, productivity))
                f.write('='*80)
            self.aggregated_data = {}
            self.productivity = []








t = Tracker(1)
t.start()
t.join()
