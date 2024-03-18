from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from manager import KiwoomManager as km
from program import program

import sys
from multiprocessing import freeze_support
from datetime import datetime as curtime

class window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 1200, 600)
        self.setWindowTitle("키움 주식 매매 프로그램")
        
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        
        gridLayout = QGridLayout(centralWidget)
        
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.textLabel = QLabel("Program Output")
        
        self.enrolledTxt = QPlainTextEdit()
        self.enrolledTxt.setReadOnly(True)
        self.enrolledLabel = QLabel("Subscribe Output")
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["주식코드", "이름", "보유수량", "현재가"])
        self.table.doubleClicked.connect(self.tableDoubleClicked)
        self.tableLabel = QLabel("Current own stocks")
        
        self.sellAllButton = QPushButton("Sell All Stocks")
        self.sellAllButton.clicked.connect(self.sellAllButtonClicked)
        
        gridLayout.addWidget(self.textLabel, 0, 0)
        gridLayout.addWidget(self.enrolledLabel, 0, 1)
        gridLayout.addWidget(self.tableLabel, 0, 2)
        
        gridLayout.addWidget(self.text, 1, 0)
        gridLayout.addWidget(self.enrolledTxt, 1, 1)
        gridLayout.addWidget(self.table, 1, 2)
        gridLayout.addWidget(self.sellAllButton, 2, 2)

        self.thread = program()
        self.thread.result_ready.connect(self.update_result)
        self.thread.enrolled_ready.connect(self.update_enrolled)
        self.thread.stockInfo_ready.connect(self.update_stockInfo)
        self.thread.start()

    def update_result(self, text):
        self.text.appendPlainText(text)
        
    def update_enrolled(self, text):
        self.enrolledTxt.appendPlainText(text)
        
    def update_stockInfo(self, stockInfo):
        self.table.setRowCount(len(stockInfo))
        row = 0
        for code, info in stockInfo.items():
            self.table.setItem(row, 0, QTableWidgetItem(code))
            col = 1
            for _, value in info.items():
                self.table.setItem(row, col, QTableWidgetItem(value))
                col += 1
            row += 1
        
    def sellAllButtonClicked(self):
        reply = QMessageBox.question(self, 'Sell All Stocks', '모든 주식을 현재가로 판매하시겠습니까?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.thread.sellAllStocks()

    def closeEvent(self, event):
        self.thread.stop()
        super().closeEvent(event)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resizeTxtAreas(event.size())
    
    def resizeTxtAreas(self, size):
        self.text.setGeometry(10, 10, int(size.width() / 2) - 15, int(size.height()) - 20)
        self.enrolledTxt.setGeometry(int(size.width() / 2) + 5, 10, int(size.width() / 2) - 15, size.height() - 20)
        
    def tableDoubleClicked(self, index):
        row = index.row()
        code = self.table.item(row, 0).text()
        name = self.table.item(row, 1).text()
        numStock = self.table.item(row, 2).text()
        
        reply = QMessageBox.question(self, 'Sell Stock',f"{name}을 현재 가격으로 모두 판매하시겠습니까? (수량 : {numStock})",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.thread.orderSell(self, code, name, int(numStock))
            

def job():
    
    app = QApplication(sys.argv)
    Window = window()
    Window.show()
    sys.exit(app.exec_())   


if __name__ == "__main__" :
    
    freeze_support()
    
    job()
    
    # schedule.every().day.at("08:55").do(job)
    
    # while True:
    #     now = curtime.now()
    #     print(f"[{now.month}/{now.day}] {now.hour}:{now.minute}.....")
    #     schedule.run_pending()
    #     time.sleep(20)