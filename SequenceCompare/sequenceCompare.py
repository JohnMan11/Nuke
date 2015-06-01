"""
This tool was created to test sequences to see if they were redeliveries from the client.

It checks frame by frame until it finds a frame with a difference.

I'll probably embed this into a group or gizmo.
"""

__author__ = 'John'

import nuke
from PySide.QtGui import QHBoxLayout, QLineEdit, QMainWindow, QProgressBar, QPushButton, QVBoxLayout, QWidget


class CompareSequences(QMainWindow):
    def __init__(self):
        super(CompareSequences, self).__init__()

        self.setWindowTitle('Compare Sequences')
        self.setFixedHeight(125)

        self._ledit1 = QLineEdit()
        self._btn_pick_1 = QPushButton('...')
        self._ledit2 = QLineEdit()
        self._btn_pick_2 = QPushButton('...')
        self._btn_compare = QPushButton('Compare')
        self._progress_bar = QProgressBar(self.statusBar())

        self._setup_ui()
        self._set_connections()

    def _compare(self):
        self._toggle_ui()

        src_one = self._ledit1.text()
        src_two = self._ledit2.text()

        # TODO: put in some checks for valid sequences

        if not (src_one and src_two):
            msg = 'Please pick proper sequences.'
            print msg
            nuke.message(msg)
        else:
            read1 = nuke.createNode('Read', inpanel=False)
            read1.knob('file').fromUserText(src_one)

            read2 = nuke.createNode('Read', inpanel=False)
            read2.knob('file').fromUserText(src_two)
            read2.setXYpos(read1.xpos() + 100, read1.ypos())

            if not (read1.width() == read2.width() and read1.height() == read2.height()):
                msg = 'Sequences are not the same resolution.'
                print msg
                nuke.message(msg)
            else:
                # TODO: check for same resolution

                m = nuke.createNode('Merge2', inpanel=False)
                m.knob('operation').setValue(6)
                m.setXYpos(read1.xpos(), read2.ypos() + 100)
                m.setInput(0, read1)
                m.setInput(1, read2)

                c = nuke.createNode('CurveTool', inpanel=False)
                c.knob('operation').setValue(3)
                c.knob('ROI').fromDict(
                    {
                        'x': 0,
                        'y': 0,
                        'r': read1.width(),
                        't': read1.height()
                    }
                )

                v = nuke.createNode('Viewer')

                check = False
                frame = None

                first = read1.knob('first').value()
                last = read1.knob('last').value()

                self._progress_bar.setRange(first, last)
                for i in range(first, last + 1):
                    self._progress_bar.setValue(i)
                    nuke.execute(c, i, i)
                    data = c.knob('maxlumapixvalue').animations()
                    check = False
                    for curve in data:
                        if not curve.constant():
                            check = True
                            frame = i
                            break
                    if check:
                        break

                if not check:
                    msg = 'There is no difference.'
                else:
                    msg = 'There is a difference at frame %d.' % frame

                nuke.message(msg)

                self._progress_bar.reset()

        self._toggle_ui()

    def _pick_sequence(self):
        btn = self.sender()

        le_btn_pair = {
            self._btn_pick_1: self._ledit1,
            self._btn_pick_2: self._ledit2
        }

        clip_path = nuke.getClipname('Pick Sequence to compare')

        le_btn_pair[btn].setText(clip_path)

    def _set_connections(self):
        self._btn_pick_1.released.connect(self._pick_sequence)
        self._btn_pick_2.released.connect(self._pick_sequence)
        self._btn_compare.released.connect(self._compare)

    def _setup_ui(self):
        self._btn_pick_1.setFixedWidth(25)
        self._btn_pick_1.setToolTip('Pick first sequence.')
        self._btn_pick_2.setFixedWidth(25)
        self._btn_pick_2.setToolTip('Pick second sequence.')
        self._btn_compare.setToolTip('Compare sequences.')
        self._progress_bar.setFixedHeight(10)

        lyt_seq1 = QHBoxLayout()
        lyt_seq1.addWidget(self._ledit1)
        lyt_seq1.addWidget(self._btn_pick_1)

        lyt_seq2 = QHBoxLayout()
        lyt_seq2.addWidget(self._ledit2)
        lyt_seq2.addWidget(self._btn_pick_2)

        lyt_main = QVBoxLayout()
        lyt_main.addLayout(lyt_seq1)
        lyt_main.addLayout(lyt_seq2)
        lyt_main.addWidget(self._btn_compare)

        main_widget = QWidget()
        main_widget.setLayout(lyt_main)

        self.setCentralWidget(main_widget)

    def _toggle_ui(self):
        self._ledit1.setEnabled(not self._ledit1.isEnabled())
        self._ledit2.setEnabled(not self._ledit2.isEnabled())
        self._btn_pick_1.setEnabled(not self._btn_pick_1.isEnabled())
        self._btn_pick_2.setEnabled(not self._btn_pick_2.isEnabled())
        self._btn_compare.setEnabled(not self._btn_compare.isEnabled())


def main():
    nuke.ui = CompareSequences()
    nuke.ui.show()

if __name__ == '__main__':
    main()
