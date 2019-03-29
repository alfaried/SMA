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
        self.loadCSVBtn.clicked.connect(self.initializeChart)
        self.updateChartBtn.clicked.connect(self.updateChart)

    def updateChart(self):
        if hasattr(self, 'data'):
            # reinitialize start date
            start_date_text = self.startDateEdit.text()
            start_date_tokens = start_date_text.split("/")
            start_date_day = int(start_date_tokens[0])
            start_date_month = int(start_date_tokens[1])
            start_date_year = int(start_date_tokens[2])

            # reinitialize end dat
            end_date_text = self.endDateEdit.text()
            end_date_tokens = end_date_text.split("/")
            end_date_day = int(end_date_tokens[0])
            end_date_month = int(end_date_tokens[1])
            end_date_year = int(end_date_tokens[2])

            start_date = datetime.date(start_date_year, start_date_month, start_date_day)
            end_date = datetime.date(end_date_year, end_date_month, end_date_day)

            # print(start_date, end_date)

            # reinitialize sma_1 and sma_2 value
            sma_1 = int(self.smaOneEdit.text())
            sma_2 = int(self.smaTwoEdit.text())

            for i in reversed(range(self.chartVerticalLayout.count())):
                child = self.chartVerticalLayout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            self.data2 = self.data.copy()

            min_date_cond = (self.data2.index >= f"%s-%s-%s" % (start_date_year, start_date_month, start_date_day))
            max_date_cond = (self.data2.index <= f"%s-%s-%s" % (end_date_year, end_date_month, end_date_day))
            self.data2 = self.data2[min_date_cond & max_date_cond]
            # print("Query:", min_date_cond, max_date_cond)
            # print("Actual DF:", self.data2.index.min(), self.data2.index.max())
            # print(len(self.data2))

            self.plotChart(self.data2,sma_1,sma_2)

    def initializeChart(self):
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

            # reinitialize sma_1 and sma_2 value
            sma_1 = int(self.smaOneEdit.text())
            sma_2 = int(self.smaTwoEdit.text())

            self.fileNameDisplay.setText(str(fname[0]))

            self.data = pd.read_csv(fname[0],index_col=0,parse_dates=True)
            self.data.drop(self.data.index[self.data['Volume']==0],inplace=True)
            self.data[str(sma_1) + 'd'] = np.round(self.data['Close'].rolling(window=sma_1).mean(),3)
            self.data[str(sma_2) + 'd'] = np.round(self.data['Close'].rolling(window=sma_2).mean(),3)

            if sma_1 < sma_2:
                x = self.data[str(sma_1) + 'd'] - self.data[str(sma_2) + 'd']
            else:
                x = self.data[str(sma_2) + 'd'] - self.data[str(sma_1) + 'd']

            x[x>0] = 1
            x[x<=0] = 0
            y = x.diff()
            idxSell = y.index[y<0]
            idxBuy = y.index[y>0]
            self.data['crossSell'] = np.nan
            self.data.loc[idxSell,'crossSell'] = self.data.loc[idxSell,'Close']
            self.data['crossBuy'] = np.nan
            self.data.loc[idxBuy,'crossBuy'] = self.data.loc[idxBuy,'Close']

            self.plotChart(self.data,sma_1,sma_2)

        except FileNotFoundError:
            msg = QMessageBox()
            msg.setText("Please select a valid CSV file!")
            msg.exec_()

    def plotChart(self,data,sma_1,sma_2):
        fig1 = Figure()
        ax1 = fig1.add_subplot(111)
        ax1.xaxis_date()

        ax1.plot(data[['Close']], 'k-', linewidth=1, label="Close")
        ax1.plot(data[[str(sma_1) + 'd']], 'b-',linewidth=1, label= str(sma_1) + " Day Average")
        ax1.plot(data[[str(sma_2) + 'd']], 'c-',linewidth=1, label= str(sma_2) + " Day Average")
        ax1.plot(data[['crossSell']], 'ro',linewidth=1, label="Cross Sell")
        ax1.plot(data[['crossBuy']], 'yo',linewidth=1, label="Cross Buy")

        ax1.set_xticklabels(data.index.date)
        ax1.tick_params(axis='x', rotation=45)

        canvas1 = FigureCanvas(fig1)
        canvas1.draw()

        self.chartVerticalLayout.addWidget(canvas1)
        self.dateRangeDisplay.setText(str(data.index.date.min()) + " to " + str(data.index.date.max()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())
