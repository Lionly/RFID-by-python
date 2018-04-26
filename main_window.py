# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui, QtCore
from mc import *

# 方法一 直接加载 UI 文件
# import PyQt4.uic
# ui_file = 'rfid_edit.ui'
# (class_ui, class_base) = PyQt4.uic.loadUiType(ui_file)
#
#
# class MainWindow(class_base, class_ui):
#
#     def __init__(self):
#         super(MainWindow, self).__init__()
#
#         self.setupUi(self)


# 方法二 pyuic4 your_file.ui -o output.py
import rfid_edit_ui


class MainWindow(QtGui.QMainWindow, rfid_edit_ui.Ui_MainWindow):

    mc = None

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        if self.mc is None:
            self.statusbar.showMessage(u'读卡器未连接')
            # QtGui.QMessageBox(u'读卡器未连接')
        # 设置信号槽
        self.action_connect.triggered.connect(self.connect_mc)
        self.btn_init.clicked.connect(lambda: self.query_mc())
        self.connect(self, QtCore.SIGNAL('connect_mc'), self.connect_mc)

    def connect_mc(self):
        # 连接读卡器
        try:
            self.statusbar.showMessage(u'开始连接...')
            self.text_init.clear()
            self.table_init.clearSpans()
            self.mc = MC()
            self.statusbar.showMessage(u'读卡器已连接')
            print {'code': 1, 'msg': 'OK'}
        except NoUSBPrinterError, e:
            print e.message
            self.statusbar.showMessage(u'读卡器未连接' + e.message)
            self.warning(u'连接失败')
        except KeyError, e:
            print {'code': -4, 'msg': 'not find key: ' + e.message}
        except UnicodeEncodeError, e:
            print {'code': -3, 'msg': e.reason}
        finally:
            return

    def query_mc(self):
        # 开始查询
        if self.mc is None:
            self.warning(u'读卡器未连接')
            return
        code, msg = self.mc.init()
        print code, msg
        if code != 1:
            self.warning(msg)
            return
        hex_string = bytes_to_hex(msg)
        self.text_init.append(hex_string)

    def warning(self, msg):
        QtGui.QMessageBox.warning(self, u'警告', msg)

    def closeEvent(self, *args, **kwargs):
        if self.mc is not None:
            self.mc.close()
        print 'close'
        super(self.__class__, self).closeEvent(*args, **kwargs)


def bytes_to_hex(byte_arr):
    return ''.join('%02X' % int(b) for b in byte_arr)
    # self.text_init.append(hex_string)


def book_code_to_hex(book_code):
    hex_str = '%02X' % (ord(book_code[:1]) - 64) \
        + '%04X' % int(book_code[1:5]) \
        + '%04X' % int(book_code[5:-1]) \
        + '%02X' % int(book_code[-1:]) \
        + '000000005744'
    hex_arr = bytearray()
    hex_arr.fromhex(hex_str)
    return list(hex_arr.reverse())


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    # ex.emit(QtCore.SIGNAL('connect_mc'))
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
