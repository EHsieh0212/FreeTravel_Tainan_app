import tkinter as tk
from tkinter import *
import tkinter.font as tkFont
from tkinter import messagebox
from functools import partial
import datetime
from sklearn import cluster
import googlemaps
global result2
global result3
global lst1,cancellst1
result2 = 0
result3 = 0
lst1 = 0
cancellst1 = 0
gmaps = googlemaps.Client(key= 'AIzaSyDzvDHAHJyLbaseDLZeJ8mXpqLqfb6_lNc')


''' 調色盤 #將rgb格式轉成hex格式 '''
rgb1 = (47, 156, 149)
bgcolor1 = '#%02x%02x%02x' % rgb1
rgb2 = (150, 107, 157)
bgcolor2 = '#%02x%02x%02x' % rgb2
rgb3 = (242, 255, 222)
bgcolor3 = '#%02x%02x%02x' % rgb3
rgb4 = (253, 255, 252)
bgcolor4 = '#%02x%02x%02x' % rgb4
rgb5 = (249, 87, 56)
bgcolor5 = '#%02x%02x%02x' % rgb5
rgb6 = (255, 159, 28)
bgcolor6 = '#%02x%02x%02x' % rgb6
rgb7 = (201, 134, 134)
bgcolor7 = '#%02x%02x%02x' % rgb7
rgb8 = (71, 160, 37)
bgcolor8 = '#%02x%02x%02x' % rgb8



schedulergb1 = (57, 174, 169)
schedulecolor1 = '#%02x%02x%02x' % schedulergb1
schedulergb2 = (216, 247, 147)
schedulecolor2 = '#%02x%02x%02x' % schedulergb2
schedulergb3 = (85, 120, 131)
schedulecolor3 = '#%02x%02x%02x' % schedulergb3
schedulergb4 = (163, 240, 196)
schedulecolor4 = '#%02x%02x%02x' % schedulergb4
schedulergb5 = (231, 226, 71)
schedulecolor5 = '#%02x%02x%02x' % schedulergb5
schedulergb6 = (186, 219, 157)
schedulecolor6 = '#%02x%02x%02x' % schedulergb6



''' 旅客物件 global functions '''
# 一景點id ('id')
def place_id(place):
    geocode_result = gmaps.geocode("臺南市")
    tainan_loc = geocode_result[0]['geometry']['location']
    a_id = gmaps.places(place, location=tainan_loc, radius=30000)['results'][0][
        'place_id']  # 關鍵字搜索以台南定位為中心半徑30公里範圍內之第一筆搜得資料 (台南市直徑約76公里)
    return a_id


# 一景點開放時間 ({weekday_index: [opentime, endtime]}, ) (沒開放: 顯示"rest") (沒資料: 顯示"no_data")
def place_opening_hour(place):
    a_id = place_id(place)
    try:
        d = gmaps.place(a_id, language="zh-tw")['result']['opening_hours']['weekday_text']
        result = dict()
        for i in range(len(d)):
            s = d[i].split(': ')
            try:
                k = s[1].split(' – ')
                start = datetime.datetime.strptime(k[0], '%H:%M').time()
                end = datetime.datetime.strptime(k[1], '%H:%M').time()
            except:
                if s[1] == '24 小時營業':
                    start = datetime.time(0, 0)
                    end = datetime.time(23, 0)
                else:
                    start = 'rest'
                    end = 'rest'
            result[i] = [start, end]
    except:
        result = 'no_data'
    return result


# 一景點地址
def place_address(place):
    placeId = place_id(place)
    detail_results = gmaps.place(placeId, language="zh-tw")
    try:
        address = detail_results['result']['formatted_address']
    except:
        address = 'no address'
    return address


# 一景點電話
def place_phone_number(place):
    placeId = place_id(place)
    detail_results = gmaps.place(placeId, language="zh-tw")
    try:
        phone_number = detail_results['result']['formatted_phone_number'].replace(" ", "-")
    except:
        phone_number = 'no phone number'
    return phone_number


# 一串景點的經緯度 ([lat1, lng1], [lat2, lng2], ...) #float data
def places_location(attraction_list):
    locations = []
    for i in range(len(attraction_list)):
        placeId = place_id(attraction_list[i])
        detail_results = gmaps.place(placeId, language="zh-tw")
        location = detail_results['result']['geometry']['location']
        loc = [location['lat'], location['lng']]
        locations.append(loc)
    return locations


#兩地點於google map計算之行車距離(km)
def car_travel_distance(attraction1, attraction2):
    distance=gmaps.distance_matrix(attraction1, attraction2, mode='driving')["rows"][0]["elements"][0]["distance"]["value"]
    return distance


# 一串地點中，離某地點最近的景點、距離
def nearest_place_to_swh(place, attraction_list):
    min_distance = 30000
    min_place = ''
    for i in range(len(attraction_list)):
        distance2 = car_travel_distance(place, attraction_list[i])
        if distance2 < min_distance:
            min_distance = distance2
            min_place = attraction_list[i]
    return min_place, min_distance


# 排序一cluster的內部
def sort_a_cluster(all_cluster, cluster_key, first_place):
    a_cluster = [first_place]
    tmp = all_cluster[cluster_key].copy()
    tmp.remove(first_place)
    while len(tmp) != 0:
        min_distance = 30000
        min_next_place = ''
        for i in range(len(tmp)):
            distance = car_travel_distance(a_cluster[-1], tmp[i])
            if distance < min_distance:
                min_distance = distance
                min_next_place = tmp[i]
        a_cluster.append(min_next_place)
        tmp.remove(min_next_place)
    return a_cluster



''' 旅客物件'''
class Traveler:
    def __init__(self, days, start_time, end_time, hotel, attractions):
        self.total_travel_days = days
        self.start_time = start_time
        self.end_time = end_time
        self.start_weekday = start_time.weekday()
        self.end_weekday = end_time.weekday()
        self.hotel = hotel
        self.attraction_list = attractions

    # 旅遊時段數量
    def count_interval(self):
        if self.start_time.time() < datetime.time(10, 0):  # 開始：早上10點之前抵達 (不包含10點)→ 早上&下午玩(玩整天)
            if self.end_time.time() < datetime.time(13, 0):  # 結束：中午13點之前離開→ 少玩一天
                interval = (self.total_travel_days - 1) * 2
            elif datetime.time(13, 0) <= self.end_time.time() < datetime.time(18, 0):  # 結束：中午13點~下午18點離開→ 早上玩
                interval = self.total_travel_days * 2 - 1
            else:  # 結束：下午18點後離開→ 早上&下午玩(玩整天)
                interval = self.total_travel_days * 2

        elif datetime.time(10, 0) <= self.start_time.time() < datetime.time(13, 0):  # 開始:早上10~13點間抵達→ 扣早上
            if self.end_time.time() < datetime.time(13, 0):
                interval = (self.total_travel_days - 1) * 2 - 1
            elif datetime.time(13, 0) <= self.end_time.time() < datetime.time(18, 0):
                interval = self.total_travel_days * 2 - 2
            else:
                interval = self.total_travel_days * 2 - 1

        elif datetime.time(13, 0) <= self.start_time.time() < datetime.time(15, 0):  # 開始: 下午13~15點間抵達→ 扣早上
            if self.end_time.time() < datetime.time(13, 0):
                interval = (self.total_travel_days - 1) * 2 - 1
            elif datetime.time(13, 0) <= self.end_time.time() < datetime.time(18, 0):
                interval = self.total_travel_days * 2 - 2
            else:
                interval = self.total_travel_days * 2 - 1

        else:  # 開始: 下午15點後抵達→ 扣早上&下午(少玩一天)
            if self.end_time.time() < datetime.time(13, 0):
                interval = (self.total_travel_days - 2) * 2
            elif datetime.time(13, 0) <= self.end_time.time() < datetime.time(18, 0):
                interval = (self.total_travel_days - 1) * 2 - 1
            else:
                interval = (self.total_travel_days - 1) * 2
        return interval


        # 依據該名旅客遊玩時段數量，將景點分群。 ({index1: ['place1','place2']}, {index2:.....} )
#    def cluster_places(self):
#        attraction_location_list = places_location(self.attraction_list)
#        kmeans_fit = cluster.KMeans(n_clusters=self.count_interval()).fit(attraction_location_list)
#        cluster_labels = kmeans_fit.labels_
#        clusters = {}
#        for i in range(len(cluster_labels)):
#            if cluster_labels[i] not in clusters:
#                clusters[cluster_labels[i]] = [self.attraction_list[i]]
#            else:
#                clusters[cluster_labels[i]].append(self.attraction_list[i])
#        return clusters



''' 演算法三global functions '''
def cluster_places(attraction_list, count_interval):  # 回傳 {index1: ['place1','place2'] ; index2:.....}
    if len(attraction_list) < count_interval:  # 如果剩下的行程時間數量大於剩下的景點，減少分群
        count_interval = len(attraction_list)
    attraction_location_list = places_location(attraction_list)
    kmeans_fit = cluster.KMeans(n_clusters=count_interval).fit(attraction_location_list)
    cluster_labels = kmeans_fit.labels_
    clusters = {}
    for i in range(len(cluster_labels)):
        if cluster_labels[i] not in clusters:
            clusters[cluster_labels[i]] = [attraction_list[i]]
        else:
            clusters[cluster_labels[i]].append(attraction_list[i])
    return clusters


# partlist 為去除當天上午/下午沒開店家 要根據weekday 及 time_zone_mark
def remove_attraction(attraction_list, weekday, time_zone_mark):
    partlist = attraction_list.copy()
    if time_zone_mark == 0:
        for i in attraction_list:
            try:
                start, end = place_opening_hour(i)[weekday]
                if start == 'rest'or start > datetime.time(12, 0):  # 12點以後才開門 代表這間店早上沒開
                    partlist.remove(i)
            except:
                continue
    else:
        for i in attraction_list:
            try:
                start, end = place_opening_hour(i)[weekday]
                if end == 'rest' or end < datetime.time(12, 0):  # 12點以前關門 代表這間店下午沒開
                    partlist.remove(i)
            except:
                continue
    return partlist


#main
def Schedule2(traveler):
    result = []
    attraction_list = traveler.attraction_list
    hotel = traveler.hotel

    count_interval = traveler.count_interval()
    remaining_interval = count_interval

    starttime = traveler.start_time.time()
    endtime = traveler.end_time.time()

    day_number = traveler.total_travel_days
    weekday = traveler.start_time.weekday()  # 星期幾開始
    if starttime < datetime.time(13, 0):  # 開始是上下午？標記 (上午: 0 / 下午: 1)
        time_zone_mark = 0
    else:
        time_zone_mark = 1

    for i in range(count_interval):
        # partlist 為全部剩下景點扣掉當天上/下午沒開的
        partlist = remove_attraction(attraction_list, weekday, time_zone_mark)

        cluster = cluster_places(partlist, remaining_interval)
        print('assign an interval, every turn\'s cluster: ', cluster)
        if i == 0 or time_zone_mark == 0:  # 早上或第一個行程
            the_min_distance = 30000
            # 看哪個cluster有和hotel最近的景點
            for i in cluster.keys():
                min_distance = nearest_place_to_swh(hotel, cluster[i])[1]
                cluster_key = i
                if min_distance < the_min_distance:
                    the_min_distance = min_distance
                    cluster_key = i
            # 排序下一個cluster內部：第一個地點 = 和hotel之最近地點
            first_place = nearest_place_to_swh(hotel, cluster[cluster_key])[0]
            print('morning first place: ', first_place)
            new_cluster = sort_a_cluster(cluster, cluster_key, first_place)
            # 把新的cluster加到result之中
            result.append(new_cluster)
            # 刪除已經排過的景點
            for attraction in new_cluster:
                attraction_list.remove(attraction)
        else:  # 下午且非第一個行程
            the_min_distance = 30000
            # 看哪個cluster有和上一個cluster最近的景點
            for i in cluster.keys():
                min_distance = nearest_place_to_swh(result[-1][-1], cluster[i])[1]
                cluster_key = i
                if min_distance < the_min_distance:
                    the_min_distance = min_distance
                    cluster_key = i
            # 排序下一個cluster內部：第一個地點 = 和hotel之最近地點
            first_place = nearest_place_to_swh(result[-1][-1], cluster[cluster_key])[0]
            print('afternoon first place: ', first_place)
            new_cluster = sort_a_cluster(cluster, cluster_key, first_place)
            # 把新的cluster加到result之中
            result.append(new_cluster)
            # 刪除已經排過的景點
            for attraction in new_cluster:
                attraction_list.remove(attraction)

        # 跑完一上/下午行程後,上午變下午 下午變隔天早上  可遊玩時間區間-1
        if time_zone_mark == 0:
            time_zone_mark = 1
        else:
            time_zone_mark = 0
            weekday += 1
            if weekday == 7:
                weekday = 0
        remaining_interval -= 1

    # 最後加入地點、電話、地址 並輸出  每行為每個上/下午之行程
    for i in range(len(result)):
        for j in range(len(result[i])):
            result[i][j] = [result[i][j], place_phone_number(result[i][j])+ '###' + place_address(result[i][j])]

    #     print(result[i])
    # print(attraction_list)

    first_play_time = -1
    # 早上-1 下午1,沒有玩就0
    if starttime > datetime.time(10, 0):
        if starttime > datetime.time(15, 0):
            first_play_time = 0
        else:
            first_play_time = 1

    result_copy = result[:]
    lst_copy = [day_number,[traveler.start_time.year, traveler.start_time.month, traveler.start_time.day, traveler.start_time.hour, traveler.start_time.minute],
                          [traveler.end_time.year, traveler.end_time.month, traveler.end_time.day,traveler.end_time.hour, traveler.end_time.minute]]

    #lst_copy = [3, [2019, 3, 3, 12, 5], [2019, 3, 5, 12, 30]]
    for i in range(0, day_number):
        if first_play_time != 0:
            if i == 0 and first_play_time == 1:
                lst_copy.append([result_copy[i]])
                del result_copy[0]
            else:
                try:
                    lst_copy.append([result_copy[0], result_copy[1]])
                    del result_copy[0]
                    del result_copy[0]
                except:
                    try:
                        lst_copy.append([result_copy[0]])
                        del result_copy[0]
                    except:
                        lst_copy.append([])
        else:
            lst_copy.append([])

    return lst_copy, attraction_list





'''主架構'''
class Team16(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.grid()
        self._frame = None
        self.switch_frame(StartPage)

    def switch_frame(self, frame_class):
        """Destroys current frame and replaces it with a new one."""
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.grid(row=0, column=0)
    
    #取得該class之data
    def get_page(self, page_name):
        for page in self.frames.values():
            if str(page.__class__.__name__) == page_name:
                return page
        return None



'''第一頁'''
class StartPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.grid()
        self.label1 = tk.Label(self, text = "journey",font=("Bradley Hand ITC",100))
        self.label1.grid(row=0,column=0,padx=200,pady=150)        
        button1 = tk.Button(self, text="Explore", font=("Bodoni MT Black",15), height=1, width=10, bg=bgcolor1,fg="white",command=lambda: master.switch_frame(InputPage))
        button1.grid(row=1,column=0,pady=10)


'''第二頁'''
class InputPage(tk.Frame):

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.grid()
        self.create_widgets()
        self.locationlist = []  #暫存的景點
        self.inputlist = []     #給traveler的資料
   
    def create_widgets(self):
        # 字型設定
        font1 = tkFont.Font(size=32, family="華康POP3體W12(P)")
        font2 = tkFont.Font(size=16, family="華康POP3體W12(P)")
        font3 = tkFont.Font(size=12, family="Noto Sans TC Black")

        # Build Object/建立物件
        self.lb1 = tk.Label(self, height=1, width=31, bg=bgcolor1, text="台南走透透", font=font1, fg="white")
        self.lb3 = tk.Label(self, height=1, width=10, bg=bgcolor6, text="旅程開始時間", font=font2, fg=bgcolor4)
        self.lb3a = tk.Label(self, height=1, width=3, bg=bgcolor6, text="西元", font=font2, fg=bgcolor4)        
        #輸入年
        self.txt1a = tk.Entry(self, width=6, font=font3)
        self.lb3b = tk.Label(self, height=1, width=3, bg=bgcolor6, text="年", font=font2, fg=bgcolor4)
        #輸入月
        self.txt1b = tk.Entry(self, width=6, font=font3)
        self.lb3c = tk.Label(self, height=1, width=3, bg=bgcolor6, text="月", font=font2, fg=bgcolor4)
        #輸入日
        self.txt1c = tk.Entry(self, width=6, font=font3)
        self.lb3d = tk.Label(self, height=1, width=3, bg=bgcolor6, text="日", font=font2, fg=bgcolor4)
        #輸入時
        self.txt1d = tk.Entry(self, width=6, font=font3)
        self.lb3e = tk.Label(self, height=1, width=3, bg=bgcolor6, text="時", font=font2, fg=bgcolor4)
        self.txt1e = tk.Entry(self, width=6, font=font3)
        #輸入分
        self.lb3f = tk.Label(self, height=1, width=3, bg=bgcolor6, text="分", font=font2, fg=bgcolor4)

        self.lb4 = tk.Label(self, height=1, width=10, bg=bgcolor5, text="結束旅程時間", font=font2, fg=bgcolor4)
        self.lb4a = tk.Label(self, height=1, width=3, bg=bgcolor5, text="西元", font=font2, fg=bgcolor4)
        self.txt2a = tk.Entry(self, width=6, font=font3)
        self.lb4b = tk.Label(self, height=1, width=3, bg=bgcolor5, text="年", font=font2, fg=bgcolor4)
        self.txt2b = tk.Entry(self, width=6, font=font3)
        self.lb4c = tk.Label(self, height=1, width=3, bg=bgcolor5, text="月", font=font2, fg=bgcolor4)
        self.txt2c = tk.Entry(self, width=6, font=font3)
        self.lb4d = tk.Label(self, height=1, width=3, bg=bgcolor5, text="日", font=font2, fg=bgcolor4)
        self.txt2d = tk.Entry(self, width=6, font=font3)
        self.lb4e = tk.Label(self, height=1, width=3, bg=bgcolor5, text="時", font=font2, fg=bgcolor4)
        self.txt2e = tk.Entry(self, width=6, font=font3)
        self.lb4f = tk.Label(self, height=1, width=3, bg=bgcolor5, text="分", font=font2, fg=bgcolor4)

        self.lb5 = tk.Label(self, height=1, width=10, bg=bgcolor7, text="住宿地點", font=font2, fg=bgcolor4)
        self.txt3 = tk.Entry(self, width=15, font=font3)

        self.lb6 = tk.Label(self, height=1, width=10, bg=bgcolor8, text="想去的景點", font=font2, fg=bgcolor4)
        self.ent1 = tk.Entry(self, width=15, font=font3)
        self.txt4 = tk.Listbox(self, height=10, width=20, font=font3)     
        #新增行程按鈕
        self.but1a = tk.Button(self, height=1, width=5, bg=bgcolor8, text="新增", font=font2, fg=bgcolor4,
                               command=self.clickadd)
        #移除行程按鈕
        self.but1b = tk.Button(self, height=1, width=5, bg=bgcolor8, text="移除", font=font2, fg=bgcolor4,
                               command=self.clickdelete)
        #排程按鈕: (1) 跳至下頁 (2) 抓取資料
        self.but2 = tk.Button(self, height=1, width=5, bg="red", text="排程", font=font2, fg=bgcolor4,
                               command= lambda: [self.getinput(), self.master.switch_frame(Schedule)])

        #排版
        self.lb1.grid(row=0, column=0, columnspan=20, rowspan=2, padx=15, pady=15)
        self.lb3.grid(row=5, column=1, padx=15, pady=15)
        self.lb3a.grid(row=5, column=4, pady=15)
        self.txt1a.grid(row=5, column=5, pady=15)
        self.lb3b.grid(row=5, column=6, pady=15)
        self.txt1b.grid(row=5, column=7, pady=15)
        self.lb3c.grid(row=5, column=8, pady=15)
        self.txt1c.grid(row=5, column=9, pady=15)
        self.lb3d.grid(row=5, column=10, pady=15)
        self.txt1d.grid(row=5, column=11, pady=15)
        self.lb3e.grid(row=5, column=12, pady=15)
        self.txt1e.grid(row=5, column=13, pady=15)
        self.lb3f.grid(row=5, column=14, pady=15)

        self.lb4.grid(row=7, column=1, padx=15, pady=15)
        self.lb4a.grid(row=7, column=4, pady=15)
        self.txt2a.grid(row=7, column=5, pady=15)
        self.lb4b.grid(row=7, column=6, pady=15)
        self.txt2b.grid(row=7, column=7, pady=15)
        self.lb4c.grid(row=7, column=8, pady=15)
        self.txt2c.grid(row=7, column=9, pady=15)
        self.lb4d.grid(row=7, column=10, pady=15)
        self.txt2d.grid(row=7, column=11, pady=15)
        self.lb4e.grid(row=7, column=12, pady=15)
        self.txt2e.grid(row=7, column=13, pady=15)
        self.lb4f.grid(row=7, column=14, pady=15)

        self.lb5.grid(row=9, column=1, pady=15)
        self.txt3.grid(row=9, column=4, columnspan=3, pady=15)

        self.lb6.grid(row=11, column=1, pady=15)
        self.ent1.grid(row=11, column=4, columnspan=3, pady=15)
        self.but1a.grid(row=11, column=7, columnspan=3)
        self.but1b.grid(row=12, column=7, columnspan=3)
        self.txt4.grid(row=11, column=10, columnspan=4, rowspan=10)
        self.but2.grid(row=3, column=14, columnspan=2, pady=15)
        
    #最終地點
    def clickadd(self):  # 將所輸入文字存入Listbox，完成後並將Entry內文字清除
        var = self.ent1.get()
        self.locationlist.append(var)
        self.txt4.insert('end', var)
        self.ent1.delete(0, 'end')

    def clickdelete(self):  # 點擊按鈕後將選項刪除
        selected = self.txt4.get(self.txt4.curselection())
        self.locationlist.remove(selected)
        self.txt4.delete(self.txt4.curselection())
            
        
    # 將其他資料輸出成給Traveler的list
    def getinput(self):  
        b = self.txt1a.get()
        c = self.txt1b.get()
        d = self.txt1c.get()
        e = self.txt1d.get()
        f = self.txt1e.get()

        g = self.txt2a.get()
        h = self.txt2b.get()
        i = self.txt2c.get()
        j = self.txt2d.get()
        k = self.txt2e.get()

        start = datetime.datetime(int(b), int(c), int(d), int(e), int(f))
        end = datetime.datetime(int(g), int(h), int(i), int(j), int(k))
        day = (end.day -start.day) + 1
        hotel = self.txt3.get()
        self.inputlist.append(day)        
        self.inputlist.append(start)
        self.inputlist.append(end)
        self.inputlist.append(hotel)
        self.inputlist.append(self.locationlist)
        result = self.inputlist
        print(result)
        traveler1 = Traveler(result[0], result[1], result[2], result[3], result[4])
        print(traveler1)
        print(traveler1.attraction_list)

        global result2,lst1,cancellst1


        result2 = Schedule2(traveler1)
        lst1 = result2[0]
        cancellst1 = result2[1]
        print(lst1)
        

'''第三頁'''
class Schedule(tk.Frame):

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.grid()
        self.create()        
        # 演算法
        # inputpage_data = self.controller.get_page('InputPage')
        # result = inputpage_data.inputlist
        # traveler1 = Traveler(result[0], result[1], result[2], result[3], result[4])
        # result2 = Schedule2(traveler1)
        # self.lst = result2[0]
        # self.cancellst = result2[1]
  
    #按下景點按鈕，顯示詳細資料
    def clickBtnIntro(self, name): 
        #取得上一頁資料
        global lst1, cancellst1
        lst = lst1
        
        font1 = tkFont.Font(size=13, family="華康POP3體W12(P)")
        self.intro = Toplevel()
        self.intro.geometry('550x200')
        self.intro.title("景點詳細介紹")

        self.intro.detail1 = tk.Label(self.intro, text=name, height=1, width=10, bg=schedulecolor3, fg="white", font=font1)
        for h in range(3, len(lst)):
            for f in range(len(lst[h])):
                for u in range(len(lst[h][f])):
                    if name == lst[h][f][u][0]:
                        raw_data = lst[h][f][u][1].split('###')
                        self.intro.detail4 = tk.Label(self.intro, text=raw_data[0], height=2, width=35, bg=schedulecolor3, fg="white", font=font1)
                        self.intro.detail5 = tk.Label(self.intro, text=raw_data[1], height=2, width=35, bg=schedulecolor3, fg="white", font=font1)
        self.intro.detail2 = tk.Label(self.intro, text="電話", height=1, width=10, bg=schedulecolor3, fg="white", font=font1)
        self.intro.detail3 = tk.Label(self.intro, text="地址", height=1, width=10, bg=schedulecolor3, fg="white", font=font1)

        self.intro.detail1.grid(row=0, column=0, padx=15, pady=15, columnspan=2, sticky=tk.SE + tk.NW)		
        self.intro.detail2.grid(row=1, column=0, padx=15, pady=5, sticky=tk.SE + tk.NW)
        self.intro.detail3.grid(row=2, column=0, padx=15, pady=5, sticky=tk.SE + tk.NW)		
        self.intro.detail4.grid(row=1, column=1, padx=15, pady=5, sticky=tk.SE + tk.NW)
        self.intro.detail5.grid(row=2, column=1, padx=15, pady=5, sticky=tk.SE + tk.NW)		

    

    #創造排程頁面  (lst  cancellst)
    def create(self):
        global lst1, cancellst1
        lst = lst1
        cancellst = cancellst1
    
        #判斷遊玩時間
        start = datetime.datetime(lst[1][0], lst[1][1], lst[1][2], lst[1][3], lst[1][4])
        end = datetime.datetime(lst[2][0], lst[2][1], lst[2][2], lst[2][3], lst[2][4])
        s = datetime.datetime(lst[1][0], lst[1][1], lst[1][2], 8, 0)
        m = datetime.datetime(lst[1][0], lst[1][1], lst[1][2], 13, 0)
        e18 = datetime.datetime(lst[1][0], lst[1][1], lst[1][2], 18, 0)
        if start < s:
            start_time = start
            if end > e18:
                end_time = datetime.datetime(lst[1][0], lst[1][1], lst[1][2], lst[2][3], lst[2][4])
            else:
                end_time = datetime.datetime(lst[1][0], lst[1][1], lst[1][2], 18, 0)
        else:
            start_time = s
            if end > e18:
                end_time = datetime.datetime(lst[1][0], lst[1][1], lst[1][2], lst[2][3], lst[2][4])
            else:
                end_time = datetime.datetime(lst[1][0], lst[1][1], lst[1][2], 18, 0)
         
               
                
        # 時間差  ([hour, minute, second])      
        delta = end_time - start_time
        diff = delta / 30  
        timediff = str(diff).split(':')
        cnt = 0
        dict = {}
        for p in range(3, len(lst)):
            for q in range(len(lst[p])):
                for o in range(len(lst[p][q])):
                    dict[lst[p][q][o][0]] = lst[p][q][o][1]
                    cnt += 1
        
        font1 = tkFont.Font(size=13, family="華康POP3體W12(P)")
        if len(cancellst)!=0:
            self.clbl = tk.Label(self, text='下次再去吧！', height=1, width=15, font=font1, bg=schedulecolor1, fg="white")
            self.clbl.grid(row=1, column=int(lst[0]) + 3, padx=50, pady=1, sticky=tk.SE + tk.NW)
            for n in range(len(cancellst)):
                self.clbl1 = tk.Label(self, text=cancellst[n], height=1, width=15, bg=schedulecolor3, fg="white", font=font1)
                self.clbl1.grid(row=2+n, column=int(lst[0]) + 3, padx=50, pady=1, sticky=tk.SE + tk.NW)        
                
        #視窗標頭
        self.firstlbl = tk.Label(self, text='Schedule', font=font1 ,fg=schedulecolor3)
        self.firstlbl.grid(row=0, column=0, sticky=tk.SE + tk.NW, pady=3)

        #每一天的標頭
        for p in range(lst[0]):
            datediff = datetime.timedelta(days=1)
            dt = start_time + datediff * p
            self.datelbl = tk.Label(self, text=dt.strftime('%Y-%m-%d'), font=font1, bg=schedulecolor1, fg="white")
            self.datelbl.grid(row=0, column=1 + p, sticky=tk.SE + tk.NW, padx=1, pady=3)

        #縱列: 時間
        for i in range(int(timediff[1]) + 1):
            t = start_time + datetime.timedelta(minutes=30 * i)
            self.lbl = tk.Label(self, text=t.strftime('%H:%M'), height=1, width=5, font=font1, bg=schedulecolor1, fg="white")
            self.lbl.grid(row=i + 1, column=0, sticky=tk.SE + tk.NW, pady=1)
        
        #每天為單位，開始assign每天的cluster
        for j in range(3, len(lst)):
            
            #k = 早上
            for k in range(len(lst[j])):  
                self.blk = tk.Text(self, height=1, width=10, bg=schedulecolor4, font=font1)
                #
                if k == 0:
                    if j == 3:
                        if start <= m: 
                            a = str(start - start_time).split(':')
                            aa = int(a[1]) + int(a[0]) * 60
                            b = m - start_time
                            b1 = str(b).split(':')
                            bb = int(b1[1]) + int(b1[0]) * 60
                            self.blk.grid(row=int(aa / 30) + 1, column=j - 2, rowspan=int(bb / 30) + 1,
                                          sticky=tk.SE + tk.NW, padx=1)
                        '''
                        else:
                            a2 = str(start - start_time).split(':')
                            aa = int(a2[1]) + int(a2[0]) * 60
                            b = e18 - start
                            b1 = str(b).split(':')
                            bb = int(b1[1]) + int(b1[0]) * 60
                            self.blk.grid(row=int(aa / 30) + 1, column=j - 2, rowspan=int(bb / 30) + 1, sticky=tk.SE + tk.NW)
                        '''
                    elif j == len(lst) - 1 and end < m:
                        a = str(s - start_time).split(':')
                        aa = int(a[1]) + int(a[0]) * 60
                        b = end - s
                        b1 = str(b).split(':')
                        bb = int(b1[1]) + int(b1[0]) * 60
                        self.blk.grid(row=int(aa / 30) + 1, column=j - 2, rowspan=int(bb / 30) + 1,
                                      sticky=tk.SE + tk.NW, padx=1)
                    
                    #其他天
                    else:
                        a = str(s - start_time).split(':')
                        aa = int(a[1]) + int(a[0]) * 60
                        b = m - s
                        b1 = str(b).split(':')
                        bb = int(b1[1]) + int(b1[0]) * 60
                        self.blk.grid(row=int(aa / 30) + 1, column=j - 2, rowspan=int(bb / 30) + 1,
                                      sticky=tk.SE + tk.NW, padx=1)
                
                else:
                    
                    if j == 3 and start >= m:
                        a2 = str(start - start_time).split(':')
                        aa = int(a2[1]) + int(a2[0]) * 60
                        b = e18 - start
                        b1 = str(b).split(':')
                        bb = int(b1[1]) + int(b1[0]) * 60
                        self.blk.config(bg=schedulecolor6)
                        self.blk.grid(row=int(aa / 30) + 1, column=j - 2, rowspan=int(bb / 30) + 1,
                                      sticky=tk.SE + tk.NW, padx=1)
                    
                    elif j != len(lst) - 1:
                        a2 = str(m - start_time).split(':')
                        aa = int(a2[1]) + int(a2[0]) * 60
                        b = e18 - m
                        b1 = str(b).split(':')
                        bb = int(b1[1]) + int(b1[0]) * 60
                        self.blk.config(bg=schedulecolor6)
                        self.blk.grid(row=int(aa / 30) + 1, column=j - 2, rowspan=int(bb / 30) + 1,
                                      sticky=tk.SE + tk.NW, padx=1)
                    
                    else:
                        if end > m:
                            a2 = str(m - start_time).split(':')
                            aa = int(a2[1]) + int(a2[0]) * 60
                            b = end - m
                            print('end', end)
                            print('m', m)
                            print('b: ', bb)
                            b1 = str(b).split(':')
                            print('b1: ', b1)
                            bb = int(b1[1]) + int(b1[0]) * 60
                            self.blk.config(bg=schedulecolor6)
                            self.blk.grid(row=int(aa / 30) + 1, column=j - 2, rowspan=int(bb / 30) + 1,
                                          sticky=tk.SE + tk.NW, padx=1)
                        '''
                        else:
                            a = str(s - start_time).split(':')
                            aa = int(a[1]) + int(a[0]) * 60
                            b = end - s
                            b1 = str(b).split(':')
                            bb = int(b1[1]) + int(b1[0]) * 60
                        '''
                #
                for r in range(len(lst[j][k])):
                    self.blk = tk.Button(self, text=lst[j][k][r][0], height=1, width=8, font=font1, bg=schedulecolor2,
                                         command=partial(self.clickBtnIntro, lst[j][k][r][0]))
                    if k == 0:
                        if j == 3:
                            self.blk.grid(row=int(aa / 30) + r * 2 + 1, column=j - 2)
                            if r != len(lst[j][k]) - 1:
                                self.lb = tk.Label(self, text='▼▼▼', bg=schedulecolor4, fg="black", font=font1, )
                                self.lb.grid(row=int(aa / 30) + r * 2 + 2, column=j - 2)
                        else:
                            self.blk.grid(row=int(aa / 30) + r * 2 + 1, column=j - 2)
                            if r != len(lst[j][k]) - 1:
                                self.lb = tk.Label(self, text='▼▼▼', bg=schedulecolor4, fg="black", font=font1, )
                                self.lb.grid(row=int(aa / 30) + r * 2 + 2, column=j - 2)
                    else:
                        if j == 3 and start > m:
                            c = start - start_time
                            c1 = str(c).split(':')
                            cc = int(c1[1]) + int(c1[0]) * 60
                            self.blk.grid(row=int(cc / 30) + r * 2 + 1, column=j - 2)
                            if r != len(lst[j][k]) - 1:
                                self.lb = tk.Label(self, text='▼▼▼', bg=schedulecolor6, fg="black", font=font1, )
                                self.lb.grid(row=int(cc / 30) + r * 2 + 2, column=j - 2)
                        else:
                            c = m - start_time
                            c1 = str(c).split(':')
                            cc = int(c1[1]) + int(c1[0]) * 60
                            self.blk.grid(row=int(cc / 30) + r * 2 + 1, column=j - 2)
                            if r != len(lst[j][k]) - 1:
                                self.lb = tk.Label(self, text='▼▼▼', bg=schedulecolor6, fg="black", font=font1)
                                self.lb.grid(row=int(cc / 30) + r * 2 + 2, column=j - 2)

        self.backbtn = tk.Button(self, text='Back to InputPage', font=font1, bg="gray", fg="white",
                                 command=lambda: self.master.switch_frame(InputPage))
        self.backbtn.grid(row=int(timediff[1]) + 1, column=int(lst[0]) + 3, sticky=tk.SE + tk.NW, padx=50)
        
        
        

if __name__ == "__main__":
    app = Team16()
    app.geometry('850x600')
    app.title("台南走透透")
    app.mainloop()