import os
import sys
import math
import datetime
import matplotlib
import numpy as np
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.dates import date2num
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

plt.rcParams["figure.autolayout"] = True
qtCreatorFile = "StockChartSMA.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class Main(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # button to load CSV
        self.loadCSVBtn.clicked.connect(self.initializeChart)

        # button to update chart
        self.updateChartBtn.clicked.connect(self.updateChart)

    def updateChart(self):
        if hasattr(self, 'data'):
            self.reinitializeCanvas()

            # reinitialize start date from inputs
            start_date_tokens = self.startDateEdit.text().split("/")
            start_date_day = int(start_date_tokens[0])
            start_date_month = int(start_date_tokens[1])
            start_date_year = int(start_date_tokens[2])

            # reinitialize end date from input
            end_date_tokens = self.endDateEdit.text().split("/")
            end_date_day = int(end_date_tokens[0])
            end_date_month = int(end_date_tokens[1])
            end_date_year = int(end_date_tokens[2])

            # Not sure what this does. Seems like it doesn't affect anything
            # when commented out. Should we delete it?
            #
            # start_date = datetime.date(start_date_year, start_date_month, start_date_day)
            # end_date = datetime.date(end_date_year, end_date_month, end_date_day)

            update_data = self.data.copy()
            update_data = self.initializeGraphValues(update_data)

            min_date_cond = (update_data.index >= f"%s-%s-%s" % (start_date_year, start_date_month, start_date_day))
            max_date_cond = (update_data.index <= f"%s-%s-%s" % (end_date_year, end_date_month, end_date_day))
            update_data = update_data[min_date_cond & max_date_cond]

            self.plotChart(update_data)
            
        else:
            msg = QMessageBox()
            msg.setText("Please upload a valid CSV file first.")
            msg.exec_()

    def initializeChart(self):
        try:
            self.reinitializeCanvas()

            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fname = QFileDialog.getOpenFileName(self, 'Open file',
                                                os.getcwd(), 'CSV(*.csv)',
                                                options=options)

            self.fileNameDisplay.setText(str(fname[0]))

            self.data = pd.read_csv(fname[0],index_col=0,parse_dates=True)
            self.data.drop(self.data.index[self.data['Volume']==0],inplace=True)

            initial_data = self.data.copy()
            initial_data = self.initializeGraphValues(initial_data)

            self.plotChart(initial_data)

            # update date inputs in UI based on uploaded data
            self.startDateEdit.setDate(self.data.index.min().date())
            self.endDateEdit.setDate(self.data.index.max().date())

        except FileNotFoundError:
            msg = QMessageBox()
            msg.setText("Please select a valid CSV file.")
            msg.exec_()

    def reinitializeCanvas(self):
        for i in reversed(range(self.chartVerticalLayout.count())):
            child = self.chartVerticalLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def initializeGraphValues(self,data):
        # initialize sma_1 and sma_2 value from inputs
        self.sma_1 = int(self.smaOneEdit.text())
        self.sma_2 = int(self.smaTwoEdit.text())

        data[str(self.sma_1) + 'd'] = np.round(data['Close'].rolling(window=self.sma_1).mean(),3)
        data[str(self.sma_2) + 'd'] = np.round(data['Close'].rolling(window=self.sma_2).mean(),3)

        if self.sma_1 < self.sma_2:
            x = data[str(self.sma_1) + 'd'] - data[str(self.sma_2) + 'd']
        else:
            x = data[str(self.sma_2) + 'd'] - data[str(self.sma_1) + 'd']

        x[x>0] = 1
        x[x<=0] = 0
        y = x.diff()
        idxSell = y.index[y<0]
        idxBuy = y.index[y>0]

        data['crossSell'] = np.nan
        data.loc[idxSell,'crossSell'] = data.loc[idxSell,'Close']

        data['crossBuy'] = np.nan
        data.loc[idxBuy,'crossBuy'] = data.loc[idxBuy,'Close']

        return data

    def plotChart(self,data):
        fig1 = Figure()
        ax1 = fig1.add_subplot(111)
        ax1.xaxis_date()

        ax1.plot(data[['Close']], 'k-', linewidth=1, label="Close")
        ax1.plot(data[[str(self.sma_1) + 'd']], 'b-',linewidth=1, label= str(self.sma_1) + " Day Average")
        ax1.plot(data[[str(self.sma_2) + 'd']], 'c-',linewidth=1, label= str(self.sma_2) + " Day Average")
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
