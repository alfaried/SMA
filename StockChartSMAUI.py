import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
from PyQt5 import uic
# more imports
import math
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.rcParams["figure.autolayout"] = True
from matplotlib.dates import date2num
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg \
    import FigureCanvasQTAgg as FigureCanvas

import datetime # for date objects

qtCreatorFile = "StockChartSMA.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class Main(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # button to load CSV
        self.loadCSVBtn.clicked.connect(self.PB)
        self.updateChartBtn.clicked.connect(self.updateChart)
    

    def updateChart(self):

        if hasattr(self, 'data'):
            start_date_text = self.startDateEdit.text()
            start_date_tokens = start_date_text.split("/")
            start_date_day = int(start_date_tokens[0])
            start_date_month = int(start_date_tokens[1])
            start_date_year = int(start_date_tokens[2])

            end_date_text = self.endDateEdit.text()
            end_date_tokens = end_date_text.split("/")
            end_date_day = int(end_date_tokens[0])
            end_date_month = int(end_date_tokens[1])
            end_date_year = int(end_date_tokens[2])

            start_date = datetime.date(start_date_year, start_date_month, start_date_day)
            end_date = datetime.date(end_date_year, end_date_month, end_date_day)
            
            print(start_date, end_date)

            
            for i in reversed(range(self.chartVerticalLayout.count())): 
                child = self.chartVerticalLayout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            self.data2 = self.data.copy()

            min_date_cond = (self.data2.index >= f"%s-%s-%s" % (start_date_year, start_date_month, start_date_day))
            max_date_cond = (self.data2.index <= f"%s-%s-%s" % (end_date_year, end_date_month, end_date_day))
            self.data2 = self.data2[min_date_cond & max_date_cond]
            print("Query:", min_date_cond, max_date_cond)
            print("Actual DF:", self.data2.index.min(), self.data2.index.max())
            print(len(self.data2))

            self.fig1 = Figure()
            self.ax1 = self.fig1.add_subplot(111)
            self.ax1.xaxis_date()

            self.ax1.plot(self.data2[['Close']], 'k-', linewidth=1, label="Close")
            self.ax1.plot(self.data2[['20d']], 'b-',linewidth=1, label="20 Day Average")
            self.ax1.plot(self.data2[['50d']], 'c-',linewidth=1, label="50 Day Average")
            self.ax1.plot(self.data2[['crossSell']], 'ro',linewidth=1, label="Cross Sell")
            self.ax1.plot(self.data2[['crossBuy']], 'yo',linewidth=1, label="Cross Buy")

            self.canvas1 = FigureCanvas(self.fig1)
            self.chartVerticalLayout.addWidget(self.canvas1)
            self.canvas1.draw()

            self.dateRangeDisplay.setText(str(self.data2.index.min()) + " to " + str(self.data2.index.max()))

    def PB(self):
        #--------------------START------------------------------

        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fname = QFileDialog.getOpenFileName(self, 'Open file',
                                                os.getcwd(), 'CSV(*.csv)',
                                                options=options)
            

            
            for i in reversed(range(self.chartVerticalLayout.count())): 
                child = self.chartVerticalLayout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            self.fileNameDisplay.setText(str(fname[0]))

            self.data = pd.read_csv(fname[0],index_col=0,parse_dates=True)
            self.data.drop(self.data.index[self.data['Volume']==0],inplace=True)
            self.data['20d'] = np.round(self.data['Close'].rolling(window=20).mean(),3)
            self.data['50d'] = np.round(self.data['Close'].rolling(window=50).mean(),3)
            r = self.data.iloc[:15, :]
            d = date2num(r.index.date)

            x = self.data['20d']-self.data['50d']
            x[x>0] = 1
            x[x<=0] = 0
            y = x.diff()
            idxSell = y.index[y<0]
            idxBuy = y.index[y>0]
            self.data['crossSell'] = np.nan
            self.data.loc[idxSell,'crossSell'] = self.data.loc[idxSell,'Close']
            self.data['crossBuy'] = np.nan
            self.data.loc[idxBuy,'crossBuy'] = self.data.loc[idxBuy,'Close']

            self.fig1 = Figure()
            self.ax1 = self.fig1.add_subplot(111)
            self.ax1.xaxis_date()

            self.ax1.plot(self.data[['Close']], 'k-', linewidth=1, label="Close")
            self.ax1.plot(self.data[['20d']], 'b-',linewidth=1, label="20 Day Average")
            self.ax1.plot(self.data[['50d']], 'c-',linewidth=1, label="50 Day Average")
            self.ax1.plot(self.data[['crossSell']], 'ro',linewidth=1, label="Cross Sell")
            self.ax1.plot(self.data[['crossBuy']], 'yo',linewidth=1, label="Cross Buy")

            self.canvas1 = FigureCanvas(self.fig1)
            self.chartVerticalLayout.addWidget(self.canvas1)
            self.canvas1.draw()

            self.dateRangeDisplay.setText(str(self.data.index.min()) + " to " + str(self.data.index.max()))

            #-------------------- END ------------------------------
        except FileNotFoundError:
            msg = QMessageBox()
            msg.setText("Please select a valid CSV file!")
            msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())
