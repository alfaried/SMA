import os
import sys
import math
import datetime
import traceback
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
        self.cache_data = {
            'fileName' : None,
            'data' : pd.DataFrame()
        }

        try:
            # Load CSV File button
            self.loadCSVBtn.clicked.connect(self.loadCSVFile)

            # Update Chart button
            self.updateChartBtn.clicked.connect(self.updateCanvas)
        except:
             traceback.print_exc()

    def loadCSVFile(self):
        try:
            self.reinitializeCanvas()

            # ---------- Reads and process CSV file in a dataframe ---------- #
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fname = QFileDialog.getOpenFileName(self, 'Open file',
                                                os.getcwd(), 'CSV(*.csv)',
                                                options=options)

            if fname[0] == '' or fname[0] == None:
                if self.cache_data['fileName'] != None and not self.cache_data['data'].empty:
                    self.fileNameDisplay.setText(str(self.cache_data['fileName']))
                    self.plotCanvas(self.cache_data['data'])
                return

            self.cache_data['fileName'] = fname[0]
            self.fileNameDisplay.setText(str(fname[0]))

            self.data = pd.read_csv(fname[0],index_col=0,parse_dates=True)
            self.data.drop(self.data.index[self.data['Volume']==0],inplace=True)
            # ----------------------------- End ----------------------------- #

            initial_data = self.data.copy()
            initial_data = self.initializeGraphValues(initial_data)

            self.plotCanvas(initial_data)

            # ------------------ Updates date inputs in UI ------------------ #
            self.startDateEdit.setDate(initial_data.index.min().date())
            self.endDateEdit.setDate(initial_data.index.max().date())
            # ----------------------------- End ----------------------------- #
        except FileNotFoundError:
            msg = QMessageBox()
            msg.setText("Please select a valid CSV file.")
            msg.exec_()


    def updateCanvas(self):
        if hasattr(self, 'data'):
            self.reinitializeCanvas()

            # ------------- Reinitialize start date from inputs ------------- #
            start_date_tokens = self.startDateEdit.text().split("/")
            start_date_day = int(start_date_tokens[0])
            start_date_month = int(start_date_tokens[1])
            start_date_year = int(start_date_tokens[2])
            # ----------------------------- End ----------------------------- #

            # -------------- Reinitialize end date from inputs -------------- #
            end_date_tokens = self.endDateEdit.text().split("/")
            end_date_day = int(end_date_tokens[0])
            end_date_month = int(end_date_tokens[1])
            end_date_year = int(end_date_tokens[2])
            # ----------------------------- End ----------------------------- #

            update_data = self.data.copy()
            update_data = self.initializeGraphValues(update_data)

            min_date_cond = (update_data.index >= f"%s-%s-%s" % (start_date_year, start_date_month, start_date_day))
            max_date_cond = (update_data.index <= f"%s-%s-%s" % (end_date_year, end_date_month, end_date_day))
            update_data = update_data[min_date_cond & max_date_cond]

            self.plotCanvas(update_data)

        else:
            # If user clicks on "Update Chart" button before uploading a CSV
            msg = QMessageBox()
            msg.setText("Please upload a valid CSV file first.")
            msg.exec_()


    def reinitializeCanvas(self):
        for i in reversed(range(self.chartVerticalLayout.count())):
            child = self.chartVerticalLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


    def initializeGraphValues(self,data):
        # ------- Initialize global sma_1 & sma_2 value from inputs -------- #
        self.sma_1 = int(self.smaOneEdit.text())
        self.sma_2 = int(self.smaTwoEdit.text())
        # ------------------------------ End ------------------------------- #

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


    def plotCanvas(self,data):
        self.cache_data['data'] = data

        figure = Figure()
        axis = figure.add_subplot(111)
        axis.xaxis_date()

        axis.plot(data[['Close']], 'k-', linewidth=1, label="Close")
        axis.plot(data[[str(self.sma_1) + 'd']], 'b-',linewidth=1, label= str(self.sma_1) + " Day Average")
        axis.plot(data[[str(self.sma_2) + 'd']], 'c-',linewidth=1, label= str(self.sma_2) + " Day Average")
        axis.plot(data[['crossSell']], 'ro',linewidth=1, label="Cross Sell")
        axis.plot(data[['crossBuy']], 'yo',linewidth=1, label="Cross Buy")

        axis.set_xticklabels(data.index.date)
        axis.tick_params(axis='x', rotation=45)
        axis.legend()

        canvas = FigureCanvas(figure)
        canvas.draw()

        self.chartVerticalLayout.addWidget(canvas)
        self.dateRangeDisplay.setText(str(data.index.date.min()) + " to " + str(data.index.date.max()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())
