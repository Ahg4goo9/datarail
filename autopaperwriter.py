#!/usr/bin/env python

import sys
from  PyQt4 import QtGui, QtCore
from hdf import hdf5
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from numpy import random, arange, sin, pi

class PaperWriter(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setGeometry(0, 0, 800, 400)
        self.setWindowTitle('autopaperwriter')

        self.plotb = QtGui.QPushButton('plot')
        self.connect(self.plotb, QtCore.SIGNAL('clicked()'), self.plot)

        self.mmc = MyMplCanvas(self, width=5, height=8, dpi=100)

        self.combox = QtGui.QComboBox()
        self.combox.addItem('Choose x-axis')
        self.comboy = QtGui.QComboBox()
        self.comboy.addItem('Choose y-axis')
        self.comboz = QtGui.QComboBox()
        self.comboz.addItem('for different')
        

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.combox)
        hbox.addWidget(self.comboy)
        hbox.addWidget(self.comboz)
        hbox.addWidget(self.plotb)
       
        vbox = QtGui.QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(self.mmc)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        
        self.h = hdf5('my project')
        f, self.dset = self.h.create('Project Data', ['inh',[1, 2, 7.0, 12,
            34]], ['EGF',['a', 'b', 'c']], ['Perk',[1.0]])
        
        len = 1
        for dim in self.dset.shape:
            len = len * dim

        self.dset = arange(len).reshape(self.dset.shape)

        self.h.dset[...] = self.dset

        for box in [self.combox, self.comboy, self.comboz]:
            for identifier in sorted(self.h.read_mapping()):
                box.addItem(identifier)
            self.connect(box, QtCore.SIGNAL('activated(QString)'),
                self.onActivated)
            box.adjustSize()
        f.close()

    def onActivated(self, text):
        self.plot()

    def plot(self):
        if not (self.combox.currentText() == 'Choose x-axis' or
                self.comboy.currentText() == 'Choose y-axis' or
                self.comboz.currentText() == 'for different'):
            
            legend = str(self.comboz.currentText())
            xaxis = str(self.combox.currentText())
            yaxis = str(self.comboy.currentText())
            mapping = self.h.read_mapping()
            labels = []
            data = {}
            for i, value in enumerate(mapping[legend][1]):
                labels.append(legend + '=' + str(value))
                data[i] = []
                data[i].append(mapping[xaxis][1])
                y_values = []
                for x in mapping[xaxis][1]:
                    y_values.append(self.h.get_data({legend:value, xaxis:x}))
                        
                data[i].append(y_values)
            #TODO
            print data
            if not len(labels) == len(data):
                q = QtGui.QDialog(self)
                q.show()
            else:
                self.mmc.compute_different_figure(data, labels)

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.figu = fig
        self.axes = fig.add_subplot(111)

        # We want the axes cleared every time plot() is called
        self.axes.hold(False)
        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.axes.plot(t, s)
    
    def compute_different_figure(self, data, labels):
        """ data should be in pairs (x, y)

        """
        lines = []
        self.axes.cla()
        self.axes.hold(True)
        for k, v in data.iteritems():
            lines.extend(self.axes.plot(v[0], v[1]))
        self.axes.hold(False)
        self.figu.legend(lines, labels, 'upper right')
        self.draw()

app = QtGui.QApplication(sys.argv)

p = PaperWriter()
p.show()
sys.exit(app.exec_())
