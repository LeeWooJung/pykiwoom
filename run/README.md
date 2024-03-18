# program.py

## path

```python
import sys
sys.path.append('../pykiwoom')
```

## program class

### __init__


* 계좌 정보 : account, userId, deposit 등
* screen  
    - conditionScreen : 조건식 관련 Screen
    - lookupScreen : TR 등에 대한 검색 관련 Screen
    - buyScreen : 매수 관련 Screen
    - sellScreen : 매도 관련 Screen
    - tableScreen : 현재 보유 주식 table 관련 Screen
* 다른 정보
    - stockInfo : 보유중인 주식 정보 저장
    - enrolled : 구독중인 주식 정보 저장
* manager : Pykiwoom Manager 객체
* * *
### run()

* 프로그램 시작 및 초기화
* 메인 기능 호출
* 모든 작업이 완료되면 프로그램 종료
* * *
### stop()

* 모든 작업이 완료되면 프로그램을 종료

> ## ***Initial Methods***
> getInfo()  
> getDeposit()  
> getAccountStatus()  
### getInfo()

* 키움 API의 **GetLogInfo** 사용하여 사용자의 정보 획득
* * *
### getDeposit()

* TR: **opw00001**
* Screen: lookupScreen
* 사용자의 예수금 정보를 조회(주문 가능 금액)
* * *
### getAccountStatus()

* TR: **opw00004**
* Screen: lookupScreen
* 사용자의 계좌 상태 조회 및 주식 정보 획득
* StockInfo : 종목별 보유량, 평균단가 저장
* * *
> ## ***Main Methods***
> findToBuy()  
> checkUntil15()  
### findToBuy()

* API call : **GetConditionNameList**
    - 저장된 조건식을 불러옴
* Method Call : **buySignal(cName, cIndex, conditions)**
    - 현재 지정된 조건식에 만족하는 ticker에 대한 buySignal 호출
* * *
### checkUntil15()

* Method Call : **setRemoveAll()**
    - 이전에 구독한 모든 주식 해제요청
* Method Call : **check15()**
    - 15시 이후에 True를 반환하여 메소드 종료
* Method Call : **checkBuyPoint()**
    - 매수 조건을 만족하는 주식을 찾음
* Method Call : **checkSellPoint()**
    - 매도 조건을 만족하는 주식을 찾음
* * *
> ## ***Related Buy Stocks***
> buySignal()  
> buy()  
### buySignal(cName, cIndex, conditions)

* Method Call : **satisfiedCodes(cName, cIndex, 0)**
    - 조건 이름(cName)과 부합하는 주식을 찾아서 반환
* Method Call : **findConditionMatchingCodes(conditions, '조건이름')**
    - 추천 조건식에 해당하는 '대형 저평가 우량주', '가치주', '수익성 좋은 기업'에 해당하는 종목 필터링
* Method Call : **sortCodesWithGiven(couldBuy, '영업이익')**
    - 구해진 주식을 '영업이익'을 기준으로 정렬
* API Call : **GetMasterCodeName**
    - 구해진 주식에 대한 이름을 가져옴
* Method Call : **waitUntil19()**
    - 9시가 될 때까지 기다림
* Method Call : **setRealReg(topRated)**
    - 구해진 주식에 대한 구독 신청(Server에 실시간 정보를 달라고 요청)
* Method Call : **buy(topRated, topRatedName)**
    - 구매 진행
* * *
### buy(codeList, names)

* Method Call : **getRealTimeData(code, name, '10')**
    - fid '10' 을 넣어서 주식에 대한 현재가를 받아옴
* Method Call : **marketPriceOrder(code, 1, self.buySize)**
    - 해당 주식을 현재가로 매수
* Method Call : **changeDeposit(name, code, self.buySize, order = 'Buy')**
    - 매수 후 '구매가능금액' 업데이트
* Method Call : **setRealRemove(code)**
    - 해당 주식에 대한 구독 해제 신청
* Method Call : **addStockInfo(code)**
    - 현재 보유 주식 정보 업데이트
* * *
### checkBuyPoint()

매수에 대한 Signal을 확인하기 위한 메소드

* 작성중
* * *
> ## ***Related Sell Stocks***
> orderSell()  
> sellAllStocks()  
> checkSellPoint()  
> priceSignal()  
> sellSignal()  
### orderSell(code, name, numStock)

* Method Call : **marketPriceOrder(code, 2, numStock)**
    - 주어진 주식에 대한 매도 주문
* Method Call : **ChangeDeposit(name, code, numStock, order = 'Sell')**
    - 매도 후 '주문 가능 금액' 업데이트
* Method Call : **setRealRegRemove(code)**
    - 매도 후 구독 해제 신청
* * *
### sellAllStocks()

* 작성중
* * *
### checkSellPoint()

매도에 대한 Signal을 확인하기 위한 메소드

* Method Call : **priceSignal()**
* * *
### priceSignal()

현재 보유중인 주식의 현재가를 기준으로 매도 Signal을 확인하는 메소드

* Method Call : **setRealReg(codes)**
    - 보유중인 주식에 대한 매도 signal을 확인하기 위해 구독 신청
* API Call : **GetMasterCodeName**
    - 보유중인 주식에 대한 이름을 반환받기 위한 Api Call
* Method Call : **getRealTimeData(code, name, '10')**
    - fid '10'을 넣어 주식의 현재가를 반환받음
* Method Call : **orderSell(code, name, numStock)**
    - 조건에 맞는 주식에 대한 매도 주문
* * *
### sellSignal()

매도 시그널을 확인하기 위한 메소드

* 작성중
* * *
> ## ***Send Order/Msg/Request to Server***
> setRealReg()  
> setRealRegRemove()  
> setRealRemoveAll()  
> marketPriceOrder()  
> addStockInfo()  
> getName()  
### setRealReg(codes)

키움 증권에 구독신청을 하기 위한 메소드

* 현재 구독중인 주식이 있을 때 option '1'을 사용하여 추가 구독
* 현재 구독중인 주식이 없을 때 option '0'을 사용하여 새로 구독
* fid : '10'을 넣어 실시간 현재 가에 대한 구독만 신청
* * *
### setRealRegRemove(code)

키움 증권에 구독해제를 하기 위한 메소드

* 현재 구독중인 주식이 있는지 확인 후 구독 해제 신청
* * *
### setRealRemoveAll()

키움 증권에 모든 주식에 대한 구독을 해제하기 위한 메소드
* * *
### marketPriceOrder(code, orderType, quantity)

orderType(Buy, Sell)에 따라 매수 혹은 매도 신청을 하기 위한 메소드
* * *
### addStockInfo(code)

현재 보유중인 주식에 대한 정보를 추가하기 위한 메소드

* TrCode : **opw00004**
* manager를 호출하여 '종목코드', '평균단가', '보유수량'에 대한 TR 정보를 획득
* * *
### getName(screen, code)

주어진 주식 code(ticker)의 이름을 반환하기 위한 메소드
* * *
> ## ***Wait to Receive Msg From the Server***
> waitforOrderResult()  
> getRealTimeData()  
> priceSlot()  
> getConditionInOut()  
### waitforOrderResult()

매수 혹은 매도 주문 후, 체결 정보를 받아오기 위한 메소드

* manager를 호출하여 체결 정보에 대해 받아옴
* fid '911' : 체결량, '910' : 체결가
* return: size(체결량), price(체결가)
* * *
### getRealTimeData(code, name, fid)

요청된 실시간 주식 정보를 받아오기 위한 메소드

* manager를 호출하여 실시간 '현재가'에 대해 받아옴.
* 아직은 '현재가'에 대한 기능만 구현
* * *
### priceSlot(price, code, name)

기능 구현 전
* * *
### getConditionInOut()

기능 구현 전
* * *
> ## ***Functionial Methods***
> findConditionMatchingCodes()  
> sortCodesWithGiven()  
> changeDeposit()  
> waitUntil9()  
> check15()  
> emitTxt()  
> emitEnrolled()
> emitStockInfo()
### findConditionMatchingCodes(conditions, cName)

키움 증권에 저장된 조건과 주어진 조건이 일치하면 해당 조건에 부합하는 코드를 반환하는 메소드

* Method Call : **satisfiedCodes**
    - 주어진 조건에 부합하는 코드를 가져오는 메소드
* * *
### sortCodesWithGiven(codeList, info = None)

주어지는 info (ex. 영업이익, 매출액 등)를 기준으로 주식을 정렬하는 메소드

* TrCode : **opt10001**
* manager를 호출하여 해당 주식의 정보를 가져옴
* * *
### satisfiedCodes(cName, cIndex, search = 0)

주어지는 조건과 일치하는 주식을 반환하는 메소드

* API Call : **SendCondition**
    - manager를 호출하여 주어지는 조건에 부합하는 주식을 찾음
* API Call : **SendConditionStop**
    - manager를 호출하여 조건에 부합하는 주식을 찾는 것을 멈춤
* * *
### changeDeposit(name, code, numStock, order = 'Buy')

매수 혹은 매도 후, 현재 '주문 가능한 금액'을 업데이트

* Method Call : **waitforOrderResult()**
    - 주문 후 체결 결과(체결량, 체결가)에 대해 반환
* * *
### waitUntil9()

9시 이후에 매수 혹은 매도를 실행할 수 있도록 기다리게 하는 메소드
* * *
### check15()

15시 이후에 프로그램을 종료하게 하기 위한 메소드
* * *
### emitTxt(txt)

주어진 txt를 window 화면에 출력하기 위한 메소드
* * *
### emitEnrolled()

현재 구독중인 주식 정보에 대해 출력하기 위한 메소드

### emitStockInfo()

현재 보유중인 주식 정보에 대해 출력하기 위한 메소드