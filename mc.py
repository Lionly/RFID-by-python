#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from ctypes import *

import subprocess


def book_code_to_hex(book_code):
    book_code = book_code.replace('-', '')
    if len(book_code) < 7:
        raise Error('book code error')
    hex_str = '574400000000%02X%04X%04X%02X' % \
        (ord(book_code[:1]) - 64, int(book_code[1:5]), int(book_code[5:-1]), int(book_code[-1:]))
    return bytearray.fromhex(hex_str)


def hex_to_book_code(epc):
    if len(epc) != 12:
        raise Error('not mine tag')
    return '%s%04d-%d-%d' % (chr(int(epc[7:8]) + 64), int(epc[8:10]), int(epc[10:12]), int(epc[12:]))


def bytes_to_hex(byte_arr):
    return ''.join('%02X' % b for b in byte_arr)


def password(s='20160601'):
    if len(s) < 8:
        s.zfill(8)
    else:
        s = s[:8]
    l = [ord(c) for c in s]
    return (c_ubyte*8)(*l)


class MC:
    """ UHF Reader 09 """
    handle = None
    # COM 端口
    port = c_long()
    comadr = 0x00
    FrmHandle = c_long()

    def __init__(self, comadr=0xFF, baud=5):
        """ init """
        if self.handle is None:
            self.handle = WinDLL('UHFReader09.dll')
        # 定义函数 - AutoOpenComPort():自动连接串口
        # long WINAPI AutoOpenComPort(
        #       long Port, 输出变量，COM1—COM12与读写器连接的串口号
        #       unsigned char * ComAdr, 输入/输出变量，读写器的地址
        #       unsigned char * Baud , 输入变量,波特率
        #       long FrmHandle); 输出变量，返回与读写器连接端口对应的句柄
        self.Open = self.handle.AutoOpenComPort
        self.Open.restype = c_long  # 定义返回值类型
        self.Open.argtypes = [POINTER(c_long), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_long)]  # 定义参数类型
        # 定义函数 - CloseComPort():关闭串口连接
        # long WINAPI CloseComPort(void);
        self.close = self.handle.CloseComPort
        self.close.restype = c_long  # 定义返回值类型
        # self.close.argtypes = [c_voidp]
        # 定义函数 - Inventory_G2 ()：G2询查命令
        # long WINAPI  Inventory_G2 (
        #   unsigned char *ComAdr, 输入变量，读写器地址
        #   unsigned char *EPClenandEPC, 指向输出数组变量
        #   long * Totallen, 输出变量，EPClenandEPC 的字节数
        #   long * CardNum, 输出变量，电子标签的张数
        #   long FrmHandle); 输入变量，与读写器连接端口对应的句柄
        self._init_G2 = self.handle.Inventory_G2
        self._init_G2.restype = c_long  # 定义返回值类型
        self._init_G2.argtypes = [POINTER(c_ubyte), POINTER(c_ubyte *1024), POINTER(c_long), POINTER(c_long), c_long]
        # 定义函数 - WriteEPC_G2 ()：G2写EPC号命令
        # long WINAPI WriteEPC_G2(
        #   unsigned char * ComAdr, 输入变量，读写器地址。
        #   unsigned char * Password, 指向输入数组变量
        #   unsigned char * WriteEPC, 指向输入数组变量
        #   unsigned char * WriteEPClen, 输入变量，一个字节。WriteEPC的字节长度。范围2~30字节，必须为偶数，即2、4、6…30
        #   unsigned char * errorcode, 输出变量，一个字节，读写器返回响应状态为0xFC时，返回错误代码
        #   long FrmHandle);
        self._write_EPC = self.handle.WriteEPC_G2
        self._write_EPC.restype = c_long  # 定义返回值类型
        self._write_EPC.argtypes = [POINTER(c_ubyte), POINTER(c_ubyte*4), POINTER(c_ubyte*12), POINTER(c_ubyte), POINTER(c_ubyte), c_long]
        # 定义函数 - ReadCard_G2 ()：G2读取数据命令
        # long  WINAPI  ReadCard_G2 (
        #   unsigned char *ComAdr, 输入变量，读写器地址
        #   unsigned char * EPC, 指向输入数组变量
        #   unsigned char * Mem, 输入变量，一个字节。选择要读取的存储区
        #                        0x00: 保留区；0x01：EPC存储器；0x02：TID存储器；0x03：用户存储器。
        #   unsigned char * WordPtr, 输入变量，一个字节。指定要读取的字起始地址。0x01表示从第2个字开始读
        #   unsigned char * Num, 输入变量，一个字节。要读取的字的个数。1-120
        #   unsigned char * Password, 指向输入数组变量
        #   unsigned char maskadr, 输入变量，EPC掩模起始字节地址
        #   unsigned char maskLen, 输入变量，掩模字节数
        #   unsigned char maskFlag, 输入变量，掩模使能标记 maskFlag =1：掩模使能 maskFlag =0：掩模禁止
        #   unsigned char * Data , 指向输出数组变量
        #   unsigned char * EPClength, 输入变量，一个字节。EPC号的字节长度
        #   unsigned char * errorcode, 输出变量，一个字节，读写器返回响应状态为0xFC时，返回错误代码
        #   long FrmHandle); 输入变量，与读写器连接端口对应的句柄
        self._read = self.handle.ReadCard_G2
        self._read.restype = c_long  # 定义返回值类型
        self._read.argtypes = [POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte),
                               POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte),
                               c_ubyte, c_ubyte, c_ubyte,
                               POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte),
                               c_long]  # 定义参数类型
        # 定义函数 - WriteCard_G2 ()：G2写命令
        # long  WINAPI  WriteCard_G2 (
        #   unsigned char *ComAdr, 输入变量，读写器地址
        #   unsigned char * EPC, 指向输入数组变量
        #   unsigned char * Mem, 输入变量，一个字节。选择要读取的存储区
        #                        0x00: 保留区；0x01：EPC存储器；0x02：TID存储器；0x03：用户存储器。
        #   unsigned char * WordPtr, 输入变量，一个字节。指定要读取的字起始地址。0x01表示从第2个字开始读
        #   unsigned char * Writedatalen, 输入变量，一个字节。待写入的字节数
        #   unsigned char * Writedata, 指向输出数组变量
        #   unsigned char * Password, 指向输入数组变量
        #   unsigned char maskadr, 输入变量，EPC掩模起始字节地址
        #   unsigned char maskLen, 输入变量，掩模字节数
        #   unsigned char maskFlag, 输入变量，掩模使能标记 maskFlag =1：掩模使能 maskFlag =0：掩模禁止
        #   long WrittenDataNum, 输出变量，已经写入的字的个数。（以字为单位）
        #   unsigned char * EPClength, 输入变量，一个字节。EPC号的字节长度
        #   unsigned char * errorcode, 输出变量，一个字节，读写器返回响应状态为0xFC时，返回错误代码
        #   long FrmHandle); 输入变量，与读写器连接端口对应的句柄
        self._write = self.handle.WriteCard_G2
        self._write.restype = c_long  # 定义返回值类型
        self._write.argtypes = [POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte),
                               POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte),
                               c_ubyte, c_ubyte, c_ubyte, c_long,
                               POINTER(c_ubyte), POINTER(c_ubyte), c_long]  # 定义参数类型
        # 定义函数 -
        # 初始化 连接
        if comadr != self.comadr:
            self.comadr = comadr
        # p = subprocess.Popen("rfid.exe", shell=True)
        # p.wait()
        device = self.Open(byref(self.port), byref(c_ubyte(self.comadr)), c_ubyte(baud), byref(self.FrmHandle))
        # 设置
        if device != 0:
            print 'Open Error:', hex(device)
            raise NoUSBPrinterError('Open Error')
        else:
            print 'open done'

    def init(self):
        """ Print barcode """
        # 写 EPC A0001-2222-3
        psd = password('00000000')[4:]
        epc = book_code_to_hex('A0001-2222-3')
        err = c_ubyte()
        res2 = self._write_EPC(c_ubyte(self.comadr), (c_ubyte*4)(*psd), (c_ubyte*12)(*epc), c_ubyte(8), byref(err),
                               self.FrmHandle)
        print res2, hex(res2), err

        if res2 != 1:
            return 0, u'格式化 err'
        # 读
        EPC_buffer = (c_ubyte * 1024)()
        EPC_len = c_long()
        card_num = c_long()
        res = self._init_G2(c_ubyte(self.comadr), byref(EPC_buffer), byref(EPC_len), byref(card_num), self.FrmHandle)
        if card_num.value == 0:
            return 0, u'未读到卡'
        if card_num.value > 1:
            return -1, u'一次仅能放一张卡'
        byte_arr = EPC_buffer[1: EPC_len.value]

        if res != 1:
            return 0, u'init err'
        prx = byte_arr[:2]
        if bytes_to_hex(prx) == '5744':
            return -2, u'已经格式化'
        # 写 密码
        new_psd = password()
        count = c_ubyte()
        res3 = self._write(c_ubyte(self.comadr), (c_ubyte*12)(*byte_arr), c_ubyte(0x00), c_ubyte(0x00), c_ubyte(8),
                           (c_ubyte*8)(*new_psd), (c_ubyte*4)(*psd), c_ubyte(0x00), c_ubyte(0x00), c_ubyte(0),
                           byref(count), EPC_len.value, byref(err), self.FrmHandle)
        print res3, hex(res3), err

        if res3 != 1:
            return 0, u'改密码 err'
        return 1, byte_arr


# Errors

class Error(Exception):
    """ Base class for errors """
    def __init__(self, msg, status=None):
        Exception.__init__(self)
        self.msg = msg
        self.resultcode = 1
        if status is not None:
            self.resultcode = status

    def __str__(self):
        return self.msg


# Result/Exit codes
# 0  = success
# 10 = No Barcode type defined
# 20 = Barcode size values are out of range
# 30 = Barcode text not supplied
# 40 = Image height is too large
# 50 = No string supplied to be printed
# 60 = Invalid pin to send Cash Drawer pulse
# 70 = 未找到 USB 打印机 可能 未开启、未插电、计算机未识别、、、


class NoUSBPrinterError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        # self.msg = u"未找到 USB 打印机 可能 未开启、未插电、计算机未识别"
        self.msg = msg
        self.resultcode = 70

    def __str__(self):
        # return u"未找到 USB 打印机 可能 未开启、未插电、计算机未识别"
        return "Not Found USB Printer"


class BarcodeTypeError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = "No Barcode type is defined"
        self.resultcode = 10

    def __str__(self):
        return "No Barcode type is defined"


if __name__ == '__main__':
    psd = book_code_to_hex('A0001-2222-3')
    print len(psd), type(psd), (c_ubyte *12)(*psd)