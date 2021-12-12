import pyupbit
import time
from slacker import Slacker

class Api():
    def __init__(self):
        self.available_list = list()
        self.uri = "wss://api.upbit.com/websocket/v1"
        self.access = ""    #추가
        self.secret = ""    #추가

        self.total_list = list()
        self.res = list()
        self.btc_data = list()
        self.krw_market_coin_data = list()
        self.btc_market_coin_data = list()
        self.min_krw = float()

        self.hit_dict = dict()
        self.past_hit_list = list()
        self.hit_list = list()
        self.earning = int()
        self.stupid_list = list()
        self.counter = 1

        self.fee = 0.996502749375 # 0.9995*0.9995*0.9975 뒤에 좀 버림

        self.upbit = pyupbit.Upbit(self.access, self.secret)

        self.available()

        self.total_list.append("KRW-BTC")
        for name in self.available_list:
            krw_market_ticker = "KRW-" + name
            self.total_list.append(krw_market_ticker)
            btc_market_ticker = "BTC-" + name
            self.total_list.append(btc_market_ticker)

        print(self.total_list)
        print(self.upbit.get_balance("KRW"))
        while True:
            a = time.time()
            self.orderbook(self.total_list)
            self.checker()
            b = time.time()
            if((b-a)<0.1):
                time.sleep(0.1-b+a)



    def available(self):
        krw_list = pyupbit.get_tickers(fiat="KRW")
        btc_list = pyupbit.get_tickers(fiat="BTC")
        temp_list = list()

        for i in btc_list:
            temp = i[4:]
            temp_list.append(temp)

        for i in krw_list:
            temp = i[4:]
            if temp in temp_list:
                self.available_list.append(temp)

    def orderbook(self, fullname):
        self.res = pyupbit.get_orderbook(tickers=fullname)


    def checker(self):
        self.btc_data.append(self.res[0]['orderbook_units'][0]['ask_price'])
        self.btc_data.append(self.res[0]['orderbook_units'][0]['bid_price'])
        self.btc_data.append(self.res[0]['orderbook_units'][0]['ask_size'])
        self.btc_data.append(self.res[0]['orderbook_units'][0]['bid_size'])
        del self.res[0]


        self.best1 = 0.5
        self.best2 = 0.5
        self.name1 = str()
        self.name2 = str()

        for i, item in enumerate(self.res):
            if (i%2 == 0):    #krw market
                self.krw_market_coin_data.append(item['orderbook_units'][0]['ask_price'])
                self.krw_market_coin_data.append(item['orderbook_units'][0]['bid_price'])
                self.krw_market_coin_data.append(item['orderbook_units'][0]['ask_size'])
                self.krw_market_coin_data.append(item['orderbook_units'][0]['bid_size'])
            else:   #btc market
                self.btc_market_coin_data.append(item['orderbook_units'][0]['ask_price'])
                self.btc_market_coin_data.append(item['orderbook_units'][0]['bid_price'])
                self.btc_market_coin_data.append(item['orderbook_units'][0]['ask_size'])
                self.btc_market_coin_data.append(item['orderbook_units'][0]['ask_size'])


                eq1 = self.fee * self.krw_market_coin_data[1] / (self.btc_market_coin_data[0] * self.btc_data[0])
                eq2 = self.fee * (self.btc_market_coin_data[1] * self.btc_data[1]) / self.krw_market_coin_data[0]

                if (((eq1-1)*100 > 1) & (self.find_min(1) * (eq1-1) > 10000)):     #erased ((eq1-1)*100 > 2.0) |
                    self.min_krw = 0.99 * self.find_min(1) # 0.9965 -> 0.99 -> 0.9
                    self.trader1(item['market'])
                    print("aaa")
                    print(item['market'])
                    print("percent", (eq1 - 1) * 100)
                    print("need krw", self.min_krw * (eq1-1))
                    print("==========")
                    self.msg2(["a", self.upbit.get_balance("KRW"), item['market'], (eq2 - 1) * 100])
                    #print(self.min_krw)

                    #print("profit = ", format(self.min_krw *(eq1-1), ".5f"))

                    self.slot(item['market'], [1, self.min_krw, format(self.min_krw * (eq1-1), ".5f"), (eq1-1)*100])


                if (((eq2-1)*100 > 1) & (self.find_min(2) * (eq2-1) > 10000)): #erased ((eq2-1)*100 > 2.0) |
                    self.min_krw = 0.99 * self.find_min(2)  # 0.9965 -> 0.99
                    self.trader2(item['market'])
                    print("bbb")
                    print(item['market'])
                    print("percent", (eq2 - 1) * 100)
                    print("need krw", self.min_krw * (eq2 - 1))
                    print("===========")
                    self.msg2(["b", self.upbit.get_balance("KRW"), item['market'], (eq2 - 1) * 100])
                    #print(self.min_krw)

                    #print("profit = ", format(self.min_krw * (eq2-1), ".5f"))

                    self.slot(item['market'], [1, self.min_krw, format(self.min_krw * (eq2-1), ".5f"), (eq2-1)*100])


                self.krw_market_coin_data = []
                self.btc_market_coin_data = []

        self.krw_market_coin_data = []
        self.btc_market_coin_data = []
        self.btc_data = []

        #print(self.past_hit_list, self.hit_list)


        #for item in self.past_hit_list:
        #    if item not in self.hit_list:
        #        print(self.hit_dict)
        #        print(item)
        #        self.send_slack(item, self.hit_dict[item])
        #        del self.hit_dict[item]

        #self.past_hit_list = self.hit_list

        #self.hit_list = []



    def trader1(self, name):
        name = name[4:]
        seed = 0.9965 * self.upbit.get_balance("KRW")

        a = time.time()
        if((self.min_krw > seed) & (seed * 0.8 > self.btc_data[0] * 0.0005)):
            self.upbit.buy_market_order("KRW-BTC", self.krw_market_unit(self.btc_data[0], seed * 0.8))


            #btc = self.upbit.get_balance("BTC")
            btc = self.wait("BTC")
            self.upbit.buy_market_order("BTC-" + name, format(btc, ".8f"))
            #coin = self.upbit.get_balances(name)
            coin = self.wait(name)
            self.upbit.sell_market_order("KRW-" + name, format(coin, ".8f"))


        elif((self.min_krw < seed) & (self.min_krw * 0.8 > self.btc_data[0] * 0.0005)):
            self.upbit.buy_market_order("KRW-BTC", self.krw_market_unit(self.btc_data[0], self.min_krw * 0.8))

            #btc = self.upbit.get_balance("BTC")
            btc = self.wait("BTC")
            self.upbit.buy_market_order("BTC-" + name, format(btc, ".8f"))
            #coin = self.upbit.get_balances(name)
            coin = self.wait(name)
            self.upbit.sell_market_order("KRW-" + name, format(coin, ".8f"))

        else:
            print("fail")
        b = time.time()
        print("time on trading", b-a)
        time.sleep(0.1)
        updated_seed = self.upbit.get_balance("KRW")

        print(updated_seed)

    def trader2(self, name):
        name = name[4:]
        seed = 0.9965 * self.upbit.get_balance("KRW")

        a = time.time()
        if ((self.min_krw > seed) & (seed * 0.8 > self.btc_data[1] * 0.0005)):
            self.upbit.buy_market_order("KRW-"+name, self.krw_market_unit(self.krw_market_coin_data[0], seed * 0.8))

            #coin = self.upbit.get_balance(name)
            coin = self.wait(name)
            self.upbit.sell_market_order("BTC-" + name, format(coin, ".8f"))
            #btc = self.upbit.get_balance("BTC")
            btc = self.wait("BTC")
            self.upbit.sell_market_order("KRW-BTC", format(btc, ".8f"))

        elif((self.min_krw < seed) & (self.min_krw * 0.8 > self.btc_data[1] * 0.0005)):
            self.upbit.buy_market_order("KRW-"+name, self.krw_market_unit(self.krw_market_coin_data[0], self.min_krw * 0.8))

            #coin = self.upbit.get_balance(name)
            coin = self.wait(name)
            self.upbit.sell_market_order("BTC-" + name, format(coin, ".8f"))
            #btc = self.upbit.get_balance("BTC")
            btc = self.wait("BTC")
            self.upbit.sell_market_order("KRW-BTC", format(btc, ".8f"))

        else:
            print("fail")
        b = time.time()

        print("time on trading", b - a)
        updated_seed = self.upbit.get_balance("KRW")
        time.sleep(1)
        print(updated_seed)

    def krw_market_unit(self, won, seed):

        if(won>2000000):
            unit = 1000
        elif(won>1000000):
            unit = 500
        elif(won>500000):
            unit = 100
        elif(won>100000):
            unit = 50
        elif(won>10000):
            unit = 10
        elif(won>1000):
            unit = 5
        elif(won>100):
            unit = 1
        elif(won>10):
            unit = 0.1
        else:
            unit = 0.01

        cutseed = int(seed/unit) * unit
        return cutseed

    def slot(self, name, info):
        self.hit_list.append(name)
        #print(self.hit_dict)
        if name not in self.hit_dict:
            self.hit_dict[name] = info
        else:
            self.hit_dict[name][0] = self.hit_dict[name][0]+1
            if(self.hit_dict[name][1]<info[1]):
                self.hit_dict[name][1] = (self.hit_dict[name][1] + info[1])/2
            if(float(self.hit_dict[name][2])<float(info[2])):
                self.hit_dict[name][2] = (float(self.hit_dict[name][2]) + float(info[2]))/2

    def find_min(self, type):
        temp_list = list()
        if (type == 1):
            temp_list.append(self.btc_data[0] * self.btc_data[2])
            temp_list.append(self.krw_market_coin_data[1] * self.krw_market_coin_data[3])
            temp_list.append(self.btc_market_coin_data[0] * self.btc_market_coin_data[2] * self.btc_data[0])
        else:
            temp_list.append(self.btc_data[1] * self.btc_data[3])
            temp_list.append(self.krw_market_coin_data[0] * self.krw_market_coin_data[2])
            temp_list.append(self.btc_market_coin_data[1] * self.btc_market_coin_data[3] * self.btc_data[1])
        return min(temp_list)


    def wait(self, name):
        while True:
            balance = self.upbit.get_balance(name)
            if balance > 0.0:
                break

        return balance

    def send_slack(self, name, item):
        token = "xoxb-1641927790484-1632866116069-xqKhzXYvHnJZH2ru8k6RHnWI"
        slack = Slacker(token)

        self.counter = self.counter + 1
        if ((float(item[2])>500.0) & (item[0]>5.0) & (name not in self.stupid_list)):

            #self.earning = self.earning + 5000.0    #구마댕 5000원 가정

            self.earning = self.earning + float(item[2])    # 원래 식
            self.stupid_list.append(name)

        if (self.counter == 50):
            self.counter = 0
            self.stupid_list = []


        msg = name + " /timestamp:" + str(item[0]) + " /needed money:" + str(item[1]) + " /profit:" + str(item[2]) + "/퍼센트:" + str(item[3])
        msg = msg + "///총 수익:" + str(int(self.earning))
        print(msg)

        slack.chat.post_message("#anomaly", msg, as_user=True)

    def msg2(self, info):
        token = "xoxb-1641927790484-1632866116069-xqKhzXYvHnJZH2ru8k6RHnWI"
        slack = Slacker(token)

        msg = str(info[0]) + "//"+ str(info[1]) + "//"+ str(info[2]) + "//"+ str(info[3])
        slack.chat.post_message("#anomaly", msg, as_user=True)