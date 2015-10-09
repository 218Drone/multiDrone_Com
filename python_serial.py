'''
我用的是“线程轮寻”方式。 
就是打开串口后，启动一个线程来监听串口数据的进入，有数据时，就做数据的处理（也可以发送一个事件，并携带接收到的数据）。 
我没有用到串口处理太深的东西。 
客户的原程序不能给你，不过我给你改一下吧。 
里面的一些东西，已经经过了处理，要运行，可能你要自己改一下，把没有用的东西去掉。 
我这里已经没有串口设备了，不能调了，你自己处理一下吧，不过基本的东西已经有了。 
'''
import sys,threading,time; 
import serial; 
import binascii,encodings; 
import re; 
import socket; 

class ReadThread: 
    def __init__(self, Output=None, Port=0, Log=None, i_FirstMethod=True): 
        self.l_serial = None; 
        self.alive = False; 
        self.waitEnd = None; 
        self.bFirstMethod = i_FirstMethod; 
        self.sendport = ''; 
        self.log = Log; 
        self.output = Output; 
        self.port = Port; 
        self.re_num = None; 

    def waiting(self): 
        if not self.waitEnd is None: 
            self.waitEnd.wait(); 

    def SetStopEvent(self): 
        if not self.waitEnd is None: 
            self.waitEnd.set(); 
        self.alive = False; 
        self.stop(); 

    def start(self): 
        self.l_serial = serial.Serial(); 
        self.l_serial.port = self.port; 
        self.l_serial.baudrate = 9600; 
        self.l_serial.timeout = 2; 

        self.re_num = re.compile('\d'); 

        try: 
            if not self.output is None: 
                self.output.WriteText(u'打开通讯端口\r\n'); 
            if not self.log is None: 
                self.log.info(u'打开通讯端口'); 
            self.l_serial.open(); 
        except Exception, ex: 
            if self.l_serial.isOpen(): 
                self.l_serial.close(); 

            self.l_serial = None; 

            if not self.output is None: 
                self.output.WriteText(u'出错：\r\n    %s\r\n' % ex); 
            if not self.log is None: 
                self.log.error(u'%s' % ex); 
            return False; 

        if self.l_serial.isOpen(): 
            if not self.output is None: 
                self.output.WriteText(u'创建接收任务\r\n'); 
            if not self.log is None: 
                self.log.info(u'创建接收任务'); 
            self.waitEnd = threading.Event(); 
            self.alive = True; 
            self.thread_read = None; 
			#创建一个线程，然后监听？
            self.thread_read = threading.Thread(target=self.FirstReader); 
            self.thread_read.setDaemon(1); 
            self.thread_read.start(); 
            return True; 
        else: 
            if not self.output is None: 
                self.output.WriteText(u'通讯端口未打开\r\n'); 
            if not self.log is None: 
                self.log.info(u'通讯端口未打开'); 
            return False; 

    def InitHead(self): 
        #串口的其它的一些处理 
        try: 
            time.sleep(3); 
            if not self.output is None: 
                self.output.WriteText(u'数据接收任务开始连接网络\r\n'); 
            if not self.log is None: 
                self.log.info(u'数据接收任务开始连接网络'); 
            self.l_serial.flushInput(); 
            self.l_serial.write('\x11'); 
            data1 = self.l_serial.read(1024); 
        except ValueError,ex: 
            if not self.output is None: 
                self.output.WriteText(u'出错：\r\n    %s\r\n' % ex); 
            if not self.log is None: 
                self.log.error(u'%s' % ex); 
            self.SetStopEvent(); 
            return; 

        if not self.output is None: 
            self.output.WriteText(u'开始接收数据\r\n'); 
        if not self.log is None: 
            self.log.info(u'开始接收数据'); 
            self.output.WriteText(u'===================================\r\n'); 

    def SendData(self, i_msg): 
        lmsg = ''; 
        isOK = False; 
        if isinstance(i_msg, unicode): 
            lmsg = i_msg.encode('gb18030'); 
        else: 
            lmsg = i_msg; 
        try: 
           #发送数据到相应的处理组件 
            pass 
        except Exception, ex: 
            pass; 
        return isOK; 
	#串口线程中调用的方法
    def FirstReader(self): 
        data1 = ''; 
        isQuanJiao = True; 
        isFirstMethod = True; 
        isEnd = True; 
        readCount = 0; 
        saveCount = 0; 
        RepPos = 0; 
        #read Head Infor content 
        self.InitHead(); 

        while self.alive: 
            try: 
                data = ''; 
                n = self.l_serial.inWaiting(); 
                if n: 
                    data = data + self.l_serial.read(n); 
                    #print binascii.b2a_hex(data), 

                for l in xrange(len(data)): 
                    if ord(data[l])==0x8E: 
                        isQuanJiao = True; 
                        continue; 
                    if ord(data[l])==0x8F: 
                        isQuanJiao = False; 
                        continue; 
                    if ord(data[l]) == 0x80 or ord(data[l]) == 0x00: 
                        if len(data1)>10: 
                            if not self.re_num.search(data1,1) is None: 
                                saveCount = saveCount + 1; 
                                if RepPos==0: 
                                    RepPos = self.output.GetInsertionPoint(); 
                                self.output.Remove(RepPos,self.output.GetLastPosition()); 

                                self.SendData(data1); 
                        data1 = ''; 
                        continue; 
            except Exception, ex: 
                if not self.log is None: 
                    self.log.error(u'%s' % ex); 

        self.waitEnd.set(); 
        self.alive = False; 

    def stop(self): 
        self.alive = False; 
		#join（）的作用是，在子线程完成运行之前，这个子线程的父线程将一直被阻塞。
        self.thread_read.join(); 
        if self.l_serial.isOpen(): 
            self.l_serial.close(); 
            if not self.output is None: 
                self.output.WriteText(u'关闭通迅端口：[%d] \r\n' % self.port); 
            if not self.log is None: 
                self.log.info(u'关闭通迅端口：[%d]' % self.port); 

    def printHex(self, s): 
        s1 = binascii.b2a_hex(s); 
        print s1; 

#测试用部分 
if __name__ == '__main__': 
    rt = ReadThread(); 
    f = open("sendport.cfg", "r") 
    rt.sendport = f.read() 
    f.close() 
    try: 
        if rt.start(): 
            rt.waiting(); 
            rt.stop(); 
        else: 
            pass;             
    except Exception,se: 
        print str(se); 

    if rt.alive: 
        rt.stop(); 

    print 'End OK .'; 
    del rt;