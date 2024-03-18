import time
from datetime import datetime as curtime

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from manager import KiwoomManager as km

class program(QThread) :
    
    result_ready = pyqtSignal(str)
    enrolled_ready = pyqtSignal(str)
    stockInfo_ready = pyqtSignal(dict)

    def __init__(self, parent = None):
        super().__init__(parent)

        self.account = None
        self.userId = None
        self.userName = None
        self.serverGubun = None
        self.keyboard = None
        self.firewall = None
        self.deposit = None

        self.screen = '1000'
        self.conditionScreen = '1001'
        self.lookupScreen = '1002'
        self.buyScreen = '1100'
        self.sellScreen = '1200'
        self.tableScreen = '1300'

        self.buySize = 10
        self.stockInfo = {}
        self.enrolled = {'codes':[]}
        
        self.toBuyConditionList = []
        self.toSellConditionList = ['RsiAvgRsiShort(Sell)']
        
        self.checkStartSell = False

        self.line = "-------------------------------------"
        self.stopped = False

        self.manager = km()
        
    def run(self):
        self.manager.startProxy()
        while not self.stopped:
            self.getInfo()
            self.getDeposit()
            self.getAccountStatus()
            time.sleep(0.5)
            self.findToBuy()
            self.checkUntil15()
            self.stop()
    
    def stop(self):
        self.stopped = True
        self.manager.stopProxy()

###########################################################################################
#   Initial Methods
#   1) getInfo
#   2) getDeposit
#   3) getAccountStatus
###########################################################################################

    def getInfo(self) :
        
        methodName = "GetLoginInfo"

        self.manager.put_method((methodName, "ACCNO"))
        self.account = self.manager.get_method()[0]
        self.manager.put_method((methodName, "USER_ID"))
        self.userId = self.manager.get_method()
        self.manager.put_method((methodName, "USER_NAME"))
        self.userName = self.manager.get_method()
        self.manager.put_method((methodName, "KEY_BSECGB"))
        self.keyboard = self.manager.get_method()
        self.manager.put_method((methodName, "FIREN_SECGB"))
        self.firewall = self.manager.get_method()
        self.manager.put_method((methodName, "GetServerGubun"))
        self.serverGubun = int(self.manager.get_method())
        
        txt = self.line
        txt += f"\nAccount : {self.account}"
        txt += f"\nUser Id : {self.userId}"
        txt += f"\nUser Name : {self.userName}"
        txt += f"\nServer : 모의투자" if self.serverGubun == 1 else "Server : 실거래"
        
        self.emitTxt(txt)
        return "getInfo"
    
    def getDeposit(self) :
        # next = 0 : search once
        
        input = {
            '계좌번호' : self.account,
            '비밀번호입력매체구분' : '00',
            '조회구분' : '2'
        }
        
        cmd = {
            'trcode' : 'opw00001',
            'rqname' : 'getDeposit',
            'screen' : self.lookupScreen,
            'input' : input,
            'output' : ['주문가능금액'],
            'next' : 0
        }
        
        self.manager.put_tr(cmd)
        data = self.manager.get_tr()

        self.deposit = int(data[0]['주문가능금액'][0])
        self.emitTxt(self.line + f"\n예수금 : {self.deposit}")
        return "getDeposit"

    def getAccountStatus(self):
        
        input = {
            '계좌번호' : self.account,
            '비밀번호입력매체구분' : '00',
            '상장폐지조회구분' : 0
        }
        
        cmd = {
            'trcode' : 'opw00004',
            'rqname' : 'getAccountStatus',
            'screen' : self.lookupScreen,
            'input' : input,
            'output' : ['종목코드', '종목명', '보유수량', '평균단가', '손익율'],
            'next' : 0
        }
        
        self.manager.put_tr(cmd)
        time.sleep(0.2)
        data = self.manager.get_tr()

        txt = self.line
        if data[0].empty :
            txt += "\n보유하고 있는 주식이 없습니다."
        else :
            for index, row in data[0].iterrows():
                name = row['종목명']
                code = row['종목코드'][1:] # 앞에 A가 붙어있음.
                stockCount = int(row['보유수량'])
                avgPrice = abs(float(row['평균단가']))
                profit = round(float(row['손익율'])/10000,2)

                self.stockInfo[code] = [stockCount, avgPrice]
                
                txt += f"\n종목명 : {name}, 코드 : {code}, 보유량: {stockCount}, 평균단가 : {avgPrice}, 손익율 : {profit}"
        self.emitTxt(txt)
        self.emitStockInfo()
        return "getAccountStatus"
        

        

###########################################################################################
#   run Methods
#   1) findToBuy
#   2) checkUntil15
###########################################################################################

    def findToBuy(self) :
        now = curtime.now()
        
        cmd = {
            'screen' : self.conditionScreen,
            'func_name' : 'GetConditionNameList'
        }
        
        self.emitTxt(self.line + f"\n[{now.hour}{now.minute}] 저장된 조건을 불러오는중.....")
        
        self.manager.put_cond(cmd)
        conditions = self.manager.get_cond(method = True)
        
        for index in range(len(conditions)) :
            cIndex = conditions[index][0]
            cName = conditions[index][1]

            if cName == 'RsiAvgRsiShort(buy)' :
                self.buySignal(cName, cIndex, conditions)
                
        return "findToBuy"
                
    def checkUntil15(self) :
        
        step = 0
        self.emitTxt(self.line + f"\nNow check any conditions to buy or sell stocks")
        self.setRealRemoveAll() # 이전에 등록한 모든 것 해제
        while True:
            
            step += 1
            
            over15 = self.check15()
            now = curtime.now()
            if over15:
                self.emitTxt(self.line + f"\nTime : [{now.hour}:{now.minute} Quit Program....]")
                self.stop()
                break
            
            self.checkBuyPoint()
            self.checkSellPoint()
            #self.getConditionInOut() -- 정리중
            
            time.sleep(5)
            self.emitTxt(f"\n[{now.hour}:{now.minute}] step:{step}")
        
        return "checkUntil15"
        
        
                        
###########################################################################################
#   Related Buy Stocks
#   1) buySignal
#   2) buy
###########################################################################################

    def buySignal(self, cName, cIndex, conditions) :
            codes = self.satisfiedCodes(cName, cIndex, 0)

            largeValuable = set(self.findConditionMatchingCodes(conditions, '대형저평가우량주')).intersection(set(codes))
            valuable = set(self.findConditionMatchingCodes(conditions, '가치주')).intersection(set(codes))
            goodProfitable = set(self.findConditionMatchingCodes(conditions, '수익성좋은기업')).intersection(set(codes))

            couldBuy = largeValuable.union(valuable).union(goodProfitable)
            couldBuy = list(couldBuy.difference(set(self.stockInfo.keys())))

            self.emitTxt(self.line)
            if len(couldBuy) > 0 :
                self.emitTxt("\nFind appropriate Stocks...........")
                
                time.sleep(0.5)
                couldBuy = self.sortCodesWithGiven(couldBuy, '영업이익')

            if couldBuy is None or len(couldBuy) == 0 :
                self.emitTxt("\nThere is no appropriate Stocks...........")
                self.emitTxt("\nToday Don't Buy Anything...........")
                return
            
            topRated = couldBuy[:5] if len(couldBuy) > 5 else couldBuy
            topRatedName = []
            for code in topRated :
                name = self.getName(self.buyScreen, code)
                topRatedName.append(name)

            self.emitTxt(f"\nTo buy List is : {topRatedName}")
            
            self.waitUntil9()
            
            self.setRealReg(topRated)
            time.sleep(0.2)
            self.buy(topRated, topRatedName)
            

    def buy(self, codeList = [], names = []) :
        self.emitTxt(self.line + f"\nNow Buy Stocks..........")

        for index, code in enumerate(codeList):
            if self.stockInfo.get(code) is not None: # 현재 보유 목록에 존재하면 skip
                continue
            
            name = names[index]

            price = self.getRealTimeData(code, name, '10')
            
            if price != -1 and self.deposit > price * self.buySize:
            
                self.marketPriceOrder(code, 1, self.buySize)
                self.changeDeposit(name, code, self.buySize, order = 'Buy')
                self.setRealRegRemove(code)
                self.addStockInfo(code)
                
        self.emitStockInfo()

        return
    
    def checkBuyPoint(self):
        return
         

###########################################################################################
#   Related Sell Stocks
#   1) orderSell : 주어지는 코드에 대한 주문 진행
#   2) sellAllStocks : 보유한 모든 주식 현재가로 판매
#   3) checkSellPoint : 매도 포인트를 확인하고 주문 진행하는 메소드 모음
#   4) priceSignal : 지갑 내에 있는 주식의 평단과 현재가를 비교하여 매도 주문
#   5) sellSignal
###########################################################################################
                        
    def orderSell(self, code, name, numStock):
        self.emitTxt(self.line + f"\nOrder Sell : {name}")
        
        self.marketPriceOrder(code, 2, numStock)
        
        now = curtime.now()
        self.emitTxt(f"\n[{now.hour}:{now.minute}] Order Success..........")

        self.changeDeposit(name, code, numStock = numStock, order = 'Sell')
        del self.stockInfo[code]
        self.setRealRegRemove(code)

        time.sleep(1)
        self.emitStockInfo()

        return
    
    def sellCurrentStock(self):
        pass
    
    def sellAllStocks(self):
        
        self.emitTxt(self.line)
        self.emitTxt("Sell All Stocks Start")
        
        codes = list(self.stockInfo.keys())
        self.setRealReg(codes)
        
        for code in codes:
            info = self.stockInfo[code]
            numStock = info[0]
            name = self.getName(self.sellScreen, code)
            
            price = self.getRealTimeData(code, name, '10') # 시가
            self.emitTxt(f"name: {name}, numStock = {numStock}, currentPrice = {price}")
            
            self.orderSell(code, name, numStock)
        return
    
    def checkSellPoint(self) :

        self.priceSignal()
                
        return
    
    def priceSignal(self):
        self.emitTxt(self.line + f"\nCheck price signal in my wallet............")
        
        codes = list(self.stockInfo.keys())

        if len(codes) == 0:
            self.emitTxt(f"\nThere is no stock in my wallet............")
            return
        
        if not self.checkStartSell:
            self.setRealReg(codes)
            self.checkStartSell = True

        for code, info in self.stockInfo.items():
            numStock = info[0]
            avgPrice = info[1]
            
            name = self.getName(self.sellScreen, code)
            price = self.getRealTimeData(code, name, '10') # 시가
            self.emitTxt(f"numStock = {numStock}, avgPrice = {int(avgPrice)}, currentPrice = {price}")

            if price != -1 and price < avgPrice * 0.9 :
                self.orderSell(code, name, numStock)
            elif price != -1 and price > avgPrice * 1.1 :
                self.orderSell(code, name, numStock)
        return
    

    def sellSignal(self, cName, cIndex, conditions) :
            codes = self.satisfiedCodes(cName, cIndex, 0)

            for code in codes :
                if self.stockInfo.get(code) is not None : # code를 보유중일 때
                    pass # 더 다른 조건 확인 및 stock 팔기

###########################################################################################
#   Send Order/Msg/Request to Server
#   1) setRealReg : 현재가를 알고 싶은 stock에 대해 구독 신청
#   2) setRealRegRemove : 현재가를 알지 않아도 되는 stock에 대한 구독 해제
#   3) setRealRemoveAll : 구독 되어있는 모든 항목에 대한 구독 해제
#   4) marketPriceOrder : 시장가로 매수 혹은 매도 주문 진행
#   5) addStockInfo : 매수 주문한 stock을 저장
#   6) getName : 주어진 코드의 주식 이름을 반환
###########################################################################################
    """
        @method setRealReg
        @sequence
        SetRealReg : register에 등록하여 해당 code에 대한 실시간 정보를 받아옴.
                   : option 0 - 새로 코드 등록, option 1 - 기존 코드에 추가하여 등록
                   : ['10'] - 현재가 (fid list)
                   : kiwoom.self.real_fid 에 등록.
                     real_fid = {'code' : [fid_list]}
        > OnReceiveRealData
    """
    def setRealReg(self, codes) :
        txt = self.line
        option = '0'
        if len(self.enrolled['codes']) > 0:
            option = '1'
            txt += f"\nAlready enrolled codes exist. Enrolling added codes"
            
            alreadyEnrolled = set(self.enrolled['codes'])
            toEnroll = list(set(codes).difference(alreadyEnrolled))
            self.enrolled['codes'] = list(set(codes).union(toEnroll))
        else :
            toEnroll = codes
            self.enrolled['codes'] = codes

        txt += f"\nEnroll Codes......"
        self.emitTxt(txt)
        
        cmd = {
            'func_name' : 'SetRealReg',
            'screen' : self.lookupScreen,
            'code_list' : toEnroll,
            'fid_list' : ['10'],
            'opt_type' : option
        }
        
        self.manager.put_real(cmd)
        self.emitTxt(f"\nEnroll Codes Success")
        self.emitEnrolled()

    def setRealRegRemove(self, code) :
        txt = self.line
        if len(self.enrolled['codes']) > 0:
            txt += f"\nRemove enrolled code : {code}............"

            codes = set(self.enrolled['codes'])
            self.enrolled['codes'] = list(codes.difference(set([code])))
            
            cmd = {
                'func_name' : 'SetRealRemove',
                'screen' : self.lookupScreen if code != 'ALL' else 'ALL',
                'code' : code if code != 'ALL' else 'ALL'
            }
            
            self.manager.put_real(cmd) # 구독 해제

            txt += f"\nSuccess............"
            
        else:
            txt += f"\nThe code[{code}] is not registered... Something Wrong!"
        self.emitTxt(txt)
        self.emitEnrolled()

    def setRealRemoveAll(self) :

        self.emitTxt(self.line + f"\nDelete All current Codes......")
        
        self.setRealRegRemove('ALL')
        self.enrolled['codes'] = []
        self.emitEnrolled()

    """
        @method marketPriceOrder
        @sequence
        SendOrder
        > OnReceiveTRData
        > OnReceiveMsg : RQName의 결과 Msg를 출력.
        > OnReceiveChejanData : 주문접수, 체결통보, 잔고 통보를 수신할 때마다 발생
          - chejan_dqueue에 결과 넣어 놓음.
          - run GetChejanData()
    """
    def marketPriceOrder(self, code, orderType, quantity) :
        if orderType == 1 :
            ordername = "Buy"
        elif orderType == 2 :
            ordername = "Sell"
        now = curtime.now()
        self.emitTxt(f"\n[{now.hour}:{now.minute}] Send Order [{ordername}]..........")
        
        cmd = {
            'rqname' : ordername + ' ' + code,
            'screen' : self.buyScreen if orderType == 1 else self.sellScreen,
            'acc_no' : self.account,
            'order_type' : orderType,
            'code' : code,
            'quantity' : quantity,
            'price' : 0,
            'hoga_gb' : '03',
            'order_no' : ''
        }
        self.manager.put_order(cmd)
        time.sleep(0.2)
        return
    
    def addStockInfo(self, code):
        
        input = {
            '계좌번호' : self.account,
            '비밀번호입력매체구분' : '00',
            '상장폐지조회구분' : 0
        }
        
        cmd = {
            'trcode' : 'opw00004',
            'rqname' : 'getAccountStatus',
            'screen' : self.lookupScreen,
            'input' : input,
            'output' : ['종목코드', '평균단가', '보유수량'],
            'next' : 0
        }
        
        self.manager.put_tr(cmd)
        time.sleep(0.2)
        data = self.manager.get_tr()

        for _, row in data[0].iterrows():
              gotCode = row['종목코드'][1:] # 앞에 A가 붙어있음.
              if gotCode == code:
                   avgPrice = float(row['평균단가'])
                   stockCount = int(row['보유수량'])

                   self.stockInfo[code] = [stockCount, avgPrice]
                   break
        return
    
    def getName(self, screen, code) :
        
        cmd = {
            'screen' : screen,
            'func_name' : 'GetMasterCodeName',
            'input' : {'종목코드' : code}
        }
        self.manager.put_cond(cmd)
        name = self.manager.get_cond(method = True)
        
        return name

###########################################################################################
#   Wait to Receive Msg From the Server
#   1) waitforOrderResult
#   2) getRealTimeData
###########################################################################################

    def waitforOrderResult(self) :

            size, price = 0, 0
            self.emitTxt("\nGet Buy or Sell complete data.....")
            
            while True:
                data = self.manager.get_chejan() # 체결 잔고 데이터가 들어올 때까지 무한 대기
                gubun = data['gubun']
                if gubun == '0':
                    if data.get('911') is not None and data['911'] != '':
                        size = abs(int(data['911'])) # 체결량
                    if data.get('910') is not None and data['910'] != '':
                        price = abs(float(data['910'])) # 체결가
                        
                    if size > 0 and price > 0: # 일반적으로 같이 들어온다고 함..
                        break
                    else:
                        size, price = 0, 0
                time.sleep(0.2)
            
            return size, price

    def getRealTimeData(self, code, name, fid) :
            
        now = curtime.now()
        self.emitTxt(f"\n[{now.hour}:{now.minute}] Request price of {name}..........")
            
        while True:
            data = self.manager.get_real() #queue에 값이 들어올 때까지 무한 대기
            
            if code == data['code']:
                print(data, code, name, data[fid])
                price = data[fid]
                break
        
        price = -1 if price == '' or price is None else abs(int(price))
        
        now = curtime.now()
        if price != -1:
            self.emitTxt(f"\n[{now.hour}:{now.minute}] Get Price Success..........")
        else:
            self.emitTxt(f"\n[{now.hour}:{now.minute}] Get Price Failed..........")
        return price
    
    def priceSlot(self, price, code, name):
        pass
        
    def getConditionInOut(self) :
        
        """
            1) GetConditionLoad를 다시 해야하나.
            2) GetConditionNameList()
            3) SendCondition
            4) OnReceiveRealCondition -> self.kiwoom.real_cond_dqueue에 쌓이는데 이전에 쌓였던 것들을 지우고 해야 할 듯
        """
        
        now = curtime.now()
        time15 = now.replace(hour=15, minute = 0, second = 0, microsecond = 0)
        
        delta = time15 - now
        if delta.total_seconds() <= 0:
            return
        
        #self.text.appendPlainText(f"[{now.hour}:{now.minute}] Find stocks which in & out conditions")
        
        #while self.kiwoom.real_cond_dqueue.empty():
        #    pythoncom.PumpWaitingMessages()
            
        # while not self.kiwoom.real_cond_dqueue.empty():
        #     data = self.kiwoom.real_cond_dqueue.get()
            
        #     code = re.findall(r'\d+', data['code'])[0]
        #     type = data['type'] # 편입 'I', 이탈 'D'
        #     cName = data['cond_name']
        #     index = data['cond_index']
            
        #     if type == 'I': # buy
        #         if cName in self.toBuyConditionList: # 
        #             pass
        #         else:
        #             continue
        #     elif type == 'D': # sell
        #         if cName in self.toSellConditionList:
        #             if self.stockInfo.get(code) is not None: # 해당 코드
        #                 pass
        #         else:
        #             continue
        
        return
    
###########################################################################################
#   Functionial Method
#   1) findConditionMatchingCodes
#   2) sortCodesWithGiven
#   3) changeDeposit
#   4) waitUntil9
#   5) check15
#   6) emitTxt
#   7) emitEnrolled
###########################################################################################

    def findConditionMatchingCodes(self, conditions, cName) :
            find = False
            self.emitTxt(self.line + f"\nFind Condition name : {cName}...........")

            for index in range(len(conditions)) :
                cIndex = conditions[index][0]
                Name = conditions[index][1]

                if cName == Name :
                    find = True
                    break

            if find :
                self.emitTxt(f"\nCondition name FIND! [{cName}]")
            else :
                self.emitTxt(f"\nCan't Find... [{cName}]")
                return None
            
            return self.satisfiedCodes(cName, cIndex, 0)

    def sortCodesWithGiven(self, codeList = [], info = None) :
            if info is None :
                self.emitTxt(f"\nYou need to give info...........")
                return None
            if len(codeList) == 0:
                self.emitTxt(f"\nThere is no code to SORT...........")
                return None
            
            cmd = {
                'trcode' : 'opt10001',
                'rqname' : 'sortCodesWithGiven',
                'screen' : self.conditionScreen,
                'output' : [info],
                'next' : 0
            }
            
            values = []
            for code in codeList:
                
                input = {
                    '종목코드' : code
                }
                
                cmd['input'] = input
                
                self.manager.put_tr(cmd)
                time.sleep(0.5)
                data = self.manager.get_tr()

                profit = data[0][info][0]
                values.append(-99999 if profit == '' else float(profit))

            values, codeList = zip(*sorted(zip(values, codeList), reverse = True))

            # 값이 양수인 것들만 return
            result = []
            for index, value in enumerate(values) :
                if value > 0 :
                    result.append(codeList[index])

            return result
    
    def satisfiedCodes(self, cName, cIndex, search = 0) :
            # search 0 : 일반 조회, 1 : 실시간 조회, 2 : 연속 조회
            
            cmd = {
                'screen' : self.conditionScreen,
                'cond_name' : cName,
                'index' : cIndex,
                'func_name' : 'SendCondition',
                'search' : search
            }
            
            self.manager.put_cond(cmd)
            data = self.manager.get_cond()
            codes = data['code_list']
            
            cmd = {
                'screen' : self.conditionScreen,
                'cond_name' : cName,
                'index' : cIndex,
                'func_name' : 'SendConditionStop'
            }
            
            self.manager.put_cond(cmd)

            return codes
    
    """
        @method changeDeposit
        @sequence
            marketPriceOrder : 주문
            > changeDeposit : 주문 후 체결될 때까지 기다리고, 체결 후 deposit 변환
        
        @caution
        완벽하게 진행 됐을 때를 가정해서 정의한 함수. 완벽하게 진행되지 않을 때는 그냥 deposit을 가져오는 방법을 사용.
    """
    def changeDeposit(self, name, code, numStock, order = 'Buy') :

        now = curtime.now()
        while True:
            size, price = self.waitforOrderResult()

            if size == 0 and price == 0:
                self.emitTxt(f"\nThere is something wrong when buying {code}")
                continue
            
            now = curtime.now()
            self.emitTxt(f"\n[{now.hour}:{now.minute}] {order} Success ::: [{name}][{price} {size}/{numStock}]")

            if size == numStock:
                if order == 'Buy':
                    self.deposit -= size * price
                else: # order = 'Sell'
                    self.deposit += size * price
                self.emitTxt(f"\n[Deposit] : {self.deposit}")
                break
            
        return
    
    def waitUntil9(self):
        now = curtime.now()
        time9 = now.replace(hour=9, minute = 0, second = 0, microsecond = 0)

        while True :
            delta = time9 - now
            if delta.total_seconds() <= 0:
                return
            self.emitTxt(f"\nWait until 9 / remained Secs : {delta.total_seconds()}...........")
            time.sleep(10)
            now = curtime.now()
    
    def check15(self):
        now = curtime.now()
        time15 = now.replace(hour=15, minute = 0, second = 0, microsecond = 0)
        
        self.emitTxt(f"\nCheck time..... [{now.hour}:{now.minute}]")
        
        delta = time15 - now
        if delta.total_seconds() <= 0:
            return True
        else :
            return False
        
    def emitTxt(self, txt):
        self.result_ready.emit(txt)
        
    def emitEnrolled(self):
        now = curtime.now()
        txt = f"[{now.hour}:{now.minute}] Subscribing Codes are ......"
        
        for code in self.enrolled['codes']:
            name = self.getName(self.lookupScreen, code)
            txt += f"\nCode : {code}, Name : {name}"
        
        self.enrolled_ready.emit(txt)
        
    def emitStockInfo(self):
        toSend = {}
        codes = list(self.stockInfo.keys())
        self.setRealReg(codes)
        for code, info in self.stockInfo.items():
            toSend[code] = {}
            
            numStock = info[0]
            name = self.getName(self.tableScreen, code)
            #price = self.getRealTimeData(code, name, '10') # 현재가
            price = 0
            
            toSend[code]['name'] = name
            toSend[code]['numStock'] = str(numStock)
            toSend[code]['price'] = str(price)
            
        self.stockInfo_ready.emit(toSend)