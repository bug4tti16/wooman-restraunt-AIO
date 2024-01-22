import pandas as pd
import customtkinter as ctk
import datetime as dt
from calendar import Calendar
from pynput.keyboard import Key, Controller
from functools import partial
from jamo import h2j
from multiprocessing import Process, Queue
from tkinter import messagebox
from winsound import Beep
from operator import itemgetter
import os,pathlib,re,serial,time, sqlite3, time
class Database:
    DBLocation=os.path.join(pathlib.Path(__file__).parent.parent,'Data','data.db')
    OutputLocation=os.path.join(os.path.expanduser('~'),'Documents','경로식당',dt.datetime.now().strftime('%Y년 경로식당 이용자.xlsx'))
    Selected=None

    def __init__(self):
        self.con=sqlite3.connect(self.DBLocation)
        self.cur=self.con.cursor()
        self.con.row_factory=sqlite3.Row
        self.Current=None
    
    def Stop(self):
        self.con.close()

    def Start_program(self):
        d=self.cur.execute(
            """SELECT num,name,date,menu
            FROM parsed_data
            WHERE DATE(date)=DATE('now')
            ORDER BY date ASC"""
        ).fetchall()
        return d

    def Output_format_one(self):
        self.cur.execute(
            """DELETE FROM parsed_data
            WHERE DATE(date)=date('now')""")
        self.con.commit()
        code=f"""WITH cancel_tbl AS(
            SELECT num, MAX(time) AS cancel_time
            FROM cancel_log
            WHERE DATE(time)=DATE('now')
            GROUP BY num
            ORDER BY cancel_time
        )
        INSERT INTO parsed_data (num,name,date,menu,card,output_format)
        SELECT log.num AS num,
            users.name AS name,
            MIN(log.input_time) AS time,
            CASE WHEN SUM(log.chmenu)%2=1 THEN 1 ELSE 0 END AS menu,
            CASE WHEN log.nocard=1 THEN 1 ELSE 0 END AS card,
            (CASE WHEN log.nocard=1 THEN 'NC' ELSE 'O' END)||(CASE WHEN SUM(log.chmenu)%2=1 THEN ' (죽식)' ELSE '' END) AS output_format
        FROM log
        LEFT JOIN cancel_tbl ON log.num=cancel_tbl.num AND DATE(log.input_time)=DATE(cancel_tbl.cancel_time)
        LEFT JOIN users ON log.num=users.num
        WHERE DATE(log.input_time)=DATE('now') AND cancel_tbl.cancel_time ISNULL
        GROUP BY log.num
        UNION SELECT log.num AS num,
            users.name AS name,
            MIN(log.input_time) AS time,
            CASE WHEN SUM(log.chmenu)%2=1 THEN 1 ELSE 0 END AS menu,
            CASE WHEN log.nocard=1 THEN 1 ELSE 0 END AS card,
            (CASE WHEN log.nocard=1 THEN 'NC' ELSE 'O' END)||(CASE WHEN SUM(log.chmenu)%2=1 THEN ' (죽식)' ELSE '' END) AS output_format
        FROM log
        INNER JOIN cancel_tbl ON log.num=cancel_tbl.num AND DATE(log.input_time)=DATE(cancel_tbl.cancel_time)
        LEFT JOIN users ON log.num=users.num
        WHERE DATE(log.input_time)=DATE('now') AND log.input_time>cancel_tbl.cancel_time
        GROUP BY log.num

        ORDER BY time ASC"""
        self.cur.execute(code)
        self.con.commit()

    def Get_user_stat(self):
        l=self.cur.execute(
            """WITH sel AS (
				SELECT num, COUNT(*) as total, CAST(TOTAL(menu) AS INT) AS total_menu
				FROM parsed_data
				WHERE date>DATETIME('now','start of month')
				GROUP BY num)
			SELECT u.num,u.name,
			    CASE WHEN u.card='#' THEN 1 ELSE 0 END,
			    CASE WHEN sel.total IS NULL THEN 0 ELSE sel.total END,
			    CASE WHEN sel.total_menu IS NULL THEN 0 ELSE sel.total_menu END
			FROM users AS u
			LEFT JOIN sel ON u.num=sel.num"""
        ).fetchall()
        return l

    def Get_user_stat_monthly(self,date):
        l=self.cur.execute(
            f"""WITH sel AS (
				SELECT num, COUNT(*) as total, CAST(TOTAL(menu) AS INT) AS total_menu
				FROM parsed_data
				WHERE date>'{date.isoformat()}'
				GROUP BY num)
			SELECT u.num,
			    CASE WHEN sel.total IS NULL THEN 0 ELSE sel.total END,
			    CASE WHEN sel.total_menu IS NULL THEN 0 ELSE sel.total_menu END
			FROM users AS u
			LEFT JOIN sel ON u.num=sel.num"""
        ).fetchall()
        return l

    def Output_format_all(self):
        code=f"""WITH cancel_tbl AS(
            SELECT num, MAX(time) AS cancel_time
            FROM cancel_log
            GROUP BY num, DATE(time)
            ORDER BY cancel_time)
        )
        INSERT INTO parsed_data (num,name,date,menu,card,output_format)
        SELECT log.num AS num,
            users.name AS name,
            MIN(log.input_time) AS time,
            CASE WHEN SUM(log.chmenu)%2=1 THEN 1 ELSE 0 END AS menu,
            CASE WHEN log.nocard=1 THEN 1 ELSE 0 END AS card,
            (CASE WHEN log.nocard=1 THEN 'NC' ELSE 'O' END)||(CASE WHEN SUM(log.chmenu)%2=1 THEN ' (죽식)' ELSE '' END) AS output_format
        FROM log
        LEFT JOIN cancel_tbl ON log.num=cancel_tbl.num AND DATE(log.input_time)=DATE(cancel_tbl.cancel_time)
        LEFT JOIN users ON log.num=users.num
        WHERE cancel_tbl.cancel_time ISNULL
        GROUP BY log.num, DATE(log.input_time)
        UNION SELECT log.num AS num,
            users.name AS name,
            MIN(log.input_time) AS time,
            CASE WHEN SUM(log.chmenu)%2=1 THEN 1 ELSE 0 END AS menu,
            CASE WHEN log.nocard=1 THEN 1 ELSE 0 END AS card,
            (CASE WHEN log.nocard=1 THEN 'NC' ELSE 'O' END)||(CASE WHEN SUM(log.chmenu)%2=1 THEN ' (죽식)' ELSE '' END) AS output_format
        FROM log
        INNER JOIN cancel_tbl ON log.num=cancel_tbl.num AND DATE(log.input_time)=DATE(cancel_tbl.cancel_time)
        LEFT JOIN users ON log.num=users.num
        WHERE log.input_time>cancel_tbl.cancel_time
        GROUP BY log.num, DATE(log.input_time)

        ORDER BY time ASC"""
        self.cur.execute(code)
        self.con.commit()
    
    def Export_to_file(self):
        c=Calendar()
        td=dt.date.today()
        m=[x for x in c.itermonthdates(td.year, td.month) if x.month == td.month and x.weekday()<5 and x <= td]
        months=[dt.datetime(td.year,x,1) for x in range(1,td.month +1)]
        n=self.cur.execute(
            """SELECT MAX(num)
            FROM users""").fetchall()[0][0]
        
        #number
        data={'번호':[],
           '이름':['']*n}
        data2={'번호':[],
           '이름':['']*n}
        
        #name
        for i in range (n):
            data['번호'].append(i+1)
            data2['번호'].append(i+1)
        name=self.con.execute(
            f"""SELECT num,name
            FROM users""")
        for row in name:
            data['이름'][row['num']-1]=row['name']
            data2['이름'][row['num']-1]=row['name']
        


        #data
        for d in m:
            data.update({d:['']*n})
            e=self.con.execute(
                f"""SELECT num,output_format
                FROM parsed_data
                WHERE DATE(date)='{d}'""")
            for row in e:
                data[d][row['num']-1]=row['output_format']

        for date in months:
            data2.update({date.strftime("%m월 이용"):[0]*n})
            data2.update({date.strftime("%m월 죽식"):[0]*n})
            c=self.Get_user_stat_monthly(date)
            for i in c:
                data2[date.strftime("%m월 이용")][i[0]-1]=i[1]
                data2[date.strftime("%m월 죽식")][i[0]-1]=i[2]
            
        
        
        
        df=pd.DataFrame(data=data)
        df2=pd.DataFrame(data=data2)
        try:
            with pd.ExcelWriter(self.OutputLocation,if_sheet_exists='replace',mode='a') as w:
                df.to_excel(w,sheet_name=dt.datetime.now().strftime('%Y-%m'),header=True,index=False)
        except:
            with pd.ExcelWriter(self.OutputLocation,mode='w') as w:
                df.to_excel(w,sheet_name=dt.datetime.now().strftime('%Y-%m'),header=True,index=False)

        try:
            with pd.ExcelWriter(self.OutputLocation,if_sheet_exists='replace',mode='a') as w:
                df2.to_excel(w,sheet_name="월별 이용 통계",header=True,index=False)
        except:
            with pd.ExcelWriter(self.OutputLocation,mode='w') as w:
                df2.to_excel(w,sheet_name="월별 이용 통계",header=True,index=False)
            
    def Check_Input(self,data,*arg):
        if len(str(data))==10:
            check=self.cur.execute(
                f"""SELECT num,name
                FROM users
                WHERE card='#{data}'""").fetchall()
        elif re.search('[0-9]',str(data)):
            check=self.cur.execute(
                f"""SELECT num,name
                FROM users
                WHERE num={data}""").fetchall()
        else:
            check=self.cur.execute(
                f"""SELECT num,name
                FROM users
                WHERE name='{data}'""").fetchall()
        if check==[]:
            return None
        elif len(check)>1:
            return None
        elif True in arg:
            return check[0]
        else:
            return check[0][0]
    
    def Check_att(self,data,b):
        check=self.cur.execute(
            f"""SELECT num,name,date,menu
            FROM parsed_data
            WHERE num={data} AND DATE(date)=DATE('now')"""
        ).fetchall()
        if check!=[]:
            l=list(check[0])
            if b:
                l.append(False)
            else:
                l.append(True)
            return l
    
    def Append_to_log(self,data,*arg):
        if 'menu' in arg:
            self.cur.execute(
                f"""INSERT INTO log(num,chmenu)
                VALUES ({data},1)""")
        elif 'cancel' in arg:
            self.cur.execute(
                f"""INSERT INTO cancel_log(num)
                VALUES ({data})""")
            self.Current=None
        elif "nocard" in arg:
            self.cur.execute(
                f"""INSERT INTO log(num,nocard)
                VALUES ({data},1)""")
        else:
            self.cur.execute(
                f"""INSERT INTO log(num)
                VALUES ({data})""")
        self.cur.execute('COMMIT;')
        self.Output_format_one()
    
    def Get_Count(self):
        c=self.cur.execute(
            """SELECT COUNT(*),
            SUM(MENU)
            FROM parsed_data
            WHERE DATE(date)=DATE('now')"""
        ).fetchall()[0]
        o=[]
        for x in c:
            if x==None:
                o.append(0)
            else:
                o.append(x)
        return o

    def Get_ulist(self):
        out=[]
        l=self.cur.execute(
            """SELECT num, name
            FROM USERS"""
        ).fetchall()
        for x in l:
            out.append((x[0],h2j(x[1]),x[1]))
        return out

    def Return_udata(self,data):
        n=self.cur.execute(
            f"""SELECT name
            FROM users
            WHERE num={data}"""
        ).fetchall()[0][0]
        return n

    def AddCard(self,num,cardno):
        self.cur.execute(
            f"""UPDATE users
            SET card='#'
            WHERE card='#{cardno}'"""
        )
        self.con.commit()
        self.cur.execute(
            f"""UPDATE users
            SET card='#{cardno}'
            WHERE num={num}"""
        )
        self.con.commit()
    
    def AddUser(self,num,name):
        self.cur.execute(
            """INSERT INTO users(num,name,card)
            VALUES (?,?,?)""",(int(num),name,'#'))
        self.con.commit()
    
    def UpdateUserinfo(self,num,name):
        self.cur.execute(
            f"""UPDATE users
            SET (name,card)=('{name}','#')
            WHERE num={int(num)}""")
        self.con.commit()
    
    def Delete_user(self,num):
        self.cur.execute(
            f"""DELETE FROM users
            WHERE num={int(num)}""")
        self.con.commit()
    

class SEARCH_FRAME(ctk.CTkFrame):
    def __init__(self,container,entrycontainer,users,number_of_buttons,queue):
        super().__init__(container,width=300)
        self.ulist=users
        self.QUEUE=queue
        self.N=number_of_buttons
        self.ENTRY=ctk.CTkEntry(entrycontainer,font=('suit',16,'bold'),placeholder_text='입력...')
        self.BUTTON=self.BUTTONS(number_of_buttons)
        self.ENTRY.bind('<Return>',lambda event:self.ENTER_PRESSED())
        self.ENTRY.bind('<KeyRelease>',lambda event:self.KEY_PRESSED())
        for x in self.BUTTON:
            x.pack(fill='x',side='bottom')
  
    def BUTTONS(self,n):
        l=[]
        for i in range (n):
            l.append(ctk.CTkButton(self,fg_color='transparent',text='',command=None,text_color=('Black','white'),state='disabled',font=('suit',16,'bold')))
        return l
    
    def UPDATE_BUTTONS(self,userlist):
        if len(userlist)>self.N:
            for x in range (self.N):
                self.BUTTON[x].configure(text=f"{userlist[x][0]}: {userlist[x][2]}")
                self.BUTTON[x].configure(command=partial(self.RETURN_UID,userlist[x]))
                self.BUTTON[x].configure(state='normal')

        else:        
            for x in range (len(userlist)):
                self.BUTTON[x].configure(text=f"{userlist[x][0]}: {userlist[x][2]}")
                self.BUTTON[x].configure(command=partial(self.RETURN_UID,userlist[x]))
                self.BUTTON[x].configure(state='normal')

    def CLEAR_BUTTONS(self):
        for x in self.BUTTON:
            x.configure(text='',command=None,state='disabled')
    
    def CLEAR_ENTRY(self):
        Controller().press(Key.right)
        self.ENTRY.delete(0,'end')

    def ENTER_PRESSED(self):
        Controller().press(Key.right)
        entered=self.ENTRY.get()
        try:
            e=int(entered)
        except:
            pass
        else:
            self.CHECK_NUM(e)

    def CHECK_NUM(self,num):
        for x in self.ulist:
            if x[0]==num:
                self.RETURN_UID(x)

    def KEY_PRESSED(self):
        e=self.ENTRY.get()
        if e=="":
            pass
        elif re.search('[0-9]',e):
            pass
        else:
            self.CLEAR_BUTTONS()
            entered=h2j(e)
            self.CHECK_SYLABLE(entered)

    def CHECK_SYLABLE(self,TYPE):
        output=[]
        output2=[]
        for users in self.ulist:
            cnt=0
            if len(TYPE)<=len(users[1]):
                for x in range (len(TYPE)):
                    if list(TYPE)[x]==list(users[1])[x]:
                        cnt+=1
                if cnt==len(TYPE):
                    output.append(users)
                if cnt>1 and cnt==len(TYPE)-1:
                    output2.append(users)
        output=output+output2
        if len(output)>0:
            self.UPDATE_BUTTONS(output)

    def RETURN_UID(self,UID):
        if UID!=None or ['','','']:
            self.QUEUE.put(UID[0],block=False)
        self.CLEAR_BUTTONS()
        self.CLEAR_ENTRY()
    
    def RESET_Buttons(self):
        self.UPDATE_BUTTONS([['','','']]*self.N)
        self.CLEAR_BUTTONS()
        

class LIVE_FRAMES(ctk.CTkScrollableFrame):
    FLAG=True
    Menu=['일반식','죽식']
    FRAMES=[]
    Flag_Location=os.path.join(pathlib.Path(__file__).parent.parent,'FLAG.txt')
    def __init__(self,container):
        super().__init__(container,fg_color='transparent',width=400)
        self.Flag_Location=os.path.join(pathlib.Path(__file__).parent.parent,'FLAG.txt')
        try:
            with open(self.Flag_Location,"r",encoding='utf-8') as f:
                U_raw=f.readline()
                U_string=U_raw.replace(' ','')
                self.Message=f.readline()
                self.U_list=U_string.split(",")
        except:
            self.Flag_Location=None
            self.U_list=None
        finally:
            if self.U_list==['\n'] or None:
                self.Flag_Location=None
    
    def NEW_FRAME(self,*DATA):
        #DATA=[num,name,datetime,menu]
        f=ctk.CTkFrame(self)
        ctk.CTkLabel(f,text=dt.datetime.fromisoformat(DATA[2]).strftime("%H시 %M분 %S초"),font=('suit',16)).pack(pady=(10,0),padx=5,anchor='w') #time
        ctk.CTkLabel(f,text=f"{str(DATA[0])}번 {DATA[1]}님",font=('suit',36,'bold')).pack(pady=(10,0),padx=5,anchor='w') #num name
        ctk.CTkLabel(f,text=f"{self.Menu[DATA[3]]}",font=('suit',16,'bold')).pack(pady=(10,0),padx=5,anchor='e') #menu
        if DATA[4]:
            f.configure(fg_color='#fb8c6f')
        f.pack(side='bottom',fill='x',padx=(50,100),pady=(30,15))
        self.FRAMES.append(f)
        if len(self.FRAMES)>20:
            self.FRAMES.pop(0).destroy()

        if self.Flag_Location!=None and self.FLAG==True:
            if str(DATA[0]) in self.U_list or str(DATA[1]) in self.U_list:
                self.SINGLE_MESSAGE(f"{str(DATA[1])}님 \n {self.Message}",True)

    
    def SINGLE_MESSAGE(self,message,highlight):
        f=ctk.CTkFrame(self)
        ctk.CTkLabel(f,text=message,font=('suit',24,'bold')).pack(pady=(10,10),padx=5)
        if highlight:
            f.configure(fg_color='#fb8c6f')
        f.pack(side='bottom',fill='x',padx=(50,100),pady=(30,15))
        self.FRAMES.append(f)
        if len(self.FRAMES)>20:
            self.FRAMES.pop(0).destroy()
    
    def DEMO(self):
        ctk.CTkButton(self,text="test",command=partial(self.NEW_FRAME,("1",'이름',dt.datetime.now().strftime("%H시 %M분 %S초"),'죽식'))).pack()
  

class CARD_READER(Process):
    def __init__(self,queue):
        self.PORT='COM3'
        self.BAUD_RATE=9600
        super().__init__(target=self.START_READER,name="Card Reader",args=(queue,))

    def CLEAN(self,string):
        result=""
        for x in string:
            if re.search('[A-Z]',x):
                result=result + x
            if re.search('[0-9]',x):
                result=result + x
        return result
    
    def START_READER(self,queue):
        try:
            ser = serial.Serial(self.PORT, self.BAUD_RATE, timeout=None)
        except:
            time.sleep(2)
            self.START_READER(queue)
        else:
            go=True
            while go==True:
                try:
                    rd=ser.readline().decode('utf-8').strip()
                except:
                    time.sleep(2)
                    self.START_READER(queue)
                    go=False
                else:
                    if rd!="":
                        cleanrfid=self.CLEAN(rd)
                        if cleanrfid!="":
                            queue.put(cleanrfid,block=False)

class COUNTPAGE(ctk.CTkToplevel):
    def __init__(self,root):
        self.DATABASE=Database()
        self.QUEUE=Queue()
        self.CARD=CARD_READER(self.QUEUE)
        self.CARD.start()
        super().__init__()
        self.geometry('900x600')
        self.resizable(False,False)
        self.title('경로식당 인원관리 프로그램')
        self.TOP_RIBBON=ctk.CTkFrame(self,height=200,corner_radius=0)
        self.CLOCK=ctk.CTkLabel(self.TOP_RIBBON,text="",font=('suit',16,'bold'))
        self.COUNTLABEL=ctk.CTkLabel(self.TOP_RIBBON,text='',font=('suit',36,'bold'))
        self.CLOCK.pack(side='left',anchor='w',padx=10,pady=10)
        self.COUNTLABEL.pack(side='left',anchor='e',padx=10,pady=10)
        self.SETTING_PANNEL=ctk.CTkFrame(self.TOP_RIBBON,width=100)
        self.darkmodevar=ctk.StringVar(value='on')
        self.CLC()
        self.TR_W()
        self.BODYFRAME=ctk.CTkFrame(self,fg_color='transparent')
        self.UL=self.DATABASE.Get_ulist()
        self.SEARCH=SEARCH_FRAME(self.BODYFRAME,self,self.UL,16,self.QUEUE)
        self.LOG=LIVE_FRAMES(self.BODYFRAME)
        self.flagvar=ctk.StringVar(value='on')
        self.SP_W()
        self.BF_W()
        self.INITIALWORKS()
        self.DATA_HANDLING()
        self.bind("<Control-KeyPress-z>",self.CANCEL)
        self.bind("<Control-KeyPress-w>",self.CHANGE_MENU)
        self.protocol("WM_DELETE_WINDOW", partial(self.ABORT,root))

    def SP_W(self):
        dark=ctk.CTkSwitch(self.SETTING_PANNEL,text="다크 모드",command=self.dark_mode,variable=self.darkmodevar,onvalue='on',offvalue='off')
        flag=ctk.CTkSwitch(self.SETTING_PANNEL,text="특이사항 알림",command=self.flag_toggle,variable=self.flagvar,onvalue='on',offvalue='off')
        if ctk.get_appearance_mode()=='Light':
            self.darkmodevar.set(value='off')
        if self.LOG.Flag_Location==None:
            self.flagvar.set(value='off')
            flag.configure(state='disabled')
        
        dark.pack(fill='both',expand=True, padx=5,pady=(5,0))
        flag.pack(fill='both',expand=True,padx=5,pady=(5,5))
        
    def dark_mode(self):
        if self.darkmodevar.get()=='off':
            ctk.set_appearance_mode('light')
        else:
            ctk.set_appearance_mode('dark')
        self.SEARCH.RESET_Buttons()
    def flag_toggle(self):
        if self.flagvar.get()=='on':
            self.LOG.FLAG=True
        else:
            self.LOG.FLAG=False

    def INITIALWORKS(self):
        l=self.DATABASE.Start_program()
        if l!=[]:
            for x in l:
                self.LOG.NEW_FRAME(*x,False)
        self.GETCOUNT()

    def SOUND(self):
        for x in range (3):
            Beep(2000,300)

    def ABORT(self,root):
        if messagebox.askokcancel("종료", "종료하시겠습니까?"):
            self.DATABASE.Export_to_file()
            self.DATABASE.Stop()
            self.destroy()
            self.CARD.kill()
            root.state(newstate='normal')

    def GETCOUNT(self):
        cnt=self.DATABASE.Get_Count()
        self.COUNTLABEL.configure(text=f'{cnt[0]}명  |  죽식: {cnt[1]}명')

    def TR_W(self):
        self.SETTING_PANNEL.pack(side='right',anchor='e', padx=10,pady=10)
        ctk.CTkLabel(self.TOP_RIBBON,text='경로식당 인원관리',font=('suit',36,'bold')).pack(side='right',anchor='e',padx=10,pady=10)
        self.TOP_RIBBON.pack(fill='x',expand=True,anchor='n')
        
    def CLC(self):
        time=dt.datetime.now()
        stft=time.strftime('%m월 %d일\n%H시 %M분')
        self.CLOCK.configure(text=stft)
        super().after(1000,self.CLC)

    def BF_W(self):
        self.SEARCH.pack(padx=(0,10),pady=10,side='right',fill='both',expand=True)
        self.LOG.pack(padx=10,pady=10,side='left',fill='both',expand=True)
        self.BODYFRAME.pack(fill='both',expand=True)
        self.SEARCH.ENTRY.pack(padx=10,pady=10,side='bottom',fill='x')

    def DATA_HANDLING(self):
        exists=False
        try:
            d=self.QUEUE.get_nowait()
        except: pass
        else:
            check=self.DATABASE.Check_Input(d)
            if check!=None:
                self.DATABASE.Current=check
                att=self.DATABASE.Check_att(check,False)
                if type(d)==int:
                    self.DATABASE.Append_to_log(check,'nocard')
                if type(d)==str:
                    self.DATABASE.Append_to_log(check)
                if att==None:
                    att=self.DATABASE.Check_att(check,True)
                self.LOG.NEW_FRAME(*att)
                self.GETCOUNT()
                
            elif type(d)==str and len(d)==10:
                self.NOCARDHANDLER(d)
            elif type(d)==str:
                self.LOG.SINGLE_MESSAGE("카드가 인식되지 않았습니다.",True)
        finally:
            self.after(100,self.DATA_HANDLING)

    def CANCEL(self,event):
        if self.DATABASE.Current!=None:
            name=self.DATABASE.Return_udata(self.DATABASE.Current)
            self.DATABASE.Append_to_log(self.DATABASE.Current,'cancel')
            self.LOG.SINGLE_MESSAGE(f'{name}님 취소되었습니다.',True)
            self.GETCOUNT()
    
    def CHANGE_MENU(self,event):
        if self.DATABASE.Current!=None:
            name=self.DATABASE.Return_udata(self.DATABASE.Current)
            self.DATABASE.Append_to_log(self.DATABASE.Current,"menu")
            out=self.DATABASE.Check_att(self.DATABASE.Current,False)
            self.LOG.SINGLE_MESSAGE(f'{name}님 메뉴 변경.',True)
            self.LOG.NEW_FRAME(*out)
            self.GETCOUNT()

    def NOCARDHANDLER(self,data):
        n=ctk.CTkInputDialog(text=("이름 혹은 번호 입력"),title="미등록 카드")
        d=n.get_input()
        if d==None or '':
            messagebox.showerror('경고','등록을 취소합니다.')
        else:
            num=self.DATABASE.Check_Input(d)
            if num!=None:
                l=[num,self.DATABASE.Return_udata(num)]
                if messagebox.askokcancel("경고",f"{l[0]}번 {l[1]}님의 정보를 교체합니다."):
                    self.DATABASE.AddCard(l[0],data)
                    self.LOG.SINGLE_MESSAGE(f"{l[0]}번 {l[1]}님 카드 등록 완료. \n카드 찍어주세요.",True)
                else:
                    messagebox.showerror('경고','등록을 취소합니다.')

class START_PAGE(ctk.CTkFrame):
    def __init__(self,container):
        Info=os.path.join(pathlib.Path(__file__).parent.parent,'Data','info.txt')
        container.resizable(False,False)
        container.geometry('900x600')
        super().__init__(container)
        self.pack_configure(fill='both',expand=True)
        self.LABEL=self.LABEL_BASE()
        self.FRAME= self.FRAME_BASE()
        self.TEXTBOX=ctk.CTkTextbox(self.FRAME[0])
        self.BUTTONS=self.BUTTON_BASE()
        self.darkmodevar=ctk.StringVar(value='on')
        self.darktoggle=self.SP_W()
        self.LABEL[0].configure(text="우만종합사회복지관",font=('suit',32,'bold'))
        self.LABEL[1].configure(text="경로식당 이용자관리 프로그램",font=('suit',16,'bold'))
        self.LABEL[2].configure(text=dt.datetime.now().strftime('%Y년 %m월 %d일'),font=('suit',16,'bold'))
        with open(Info,'r',encoding='utf-8') as f:
            lines=f.readlines()
            s="\n".join(lines)
        self.TEXTBOX.insert('end',s)
        self.TEXTBOX.configure(state='disabled',font=('suit',16,'bold'))
        self.TEXTBOX.pack(fill='both',expand=True,padx=20,pady=5)
        self.BUTTONS[0].configure(text="시작",command=partial(self.STARTCOUNT,container))
        self.BUTTONS[1].configure(text="등록",command=partial(self.STARTEDIT,container))
        self.BUTTONS[2].configure(text='종료',command=partial(self.ABORT,container))
        for l in ([self.BUTTONS[0],self.BUTTONS[1]]):
            l.pack(side='right',expand=False,anchor='e',padx=5)
        self.BUTTONS[2].pack(side='left',expand=False,anchor='w',padx=5)
        self.LABEL[0].pack(pady=(20,0))
        self.LABEL[1].pack()
        self.LABEL[2].pack(pady=(10,0))
        self.darktoggle.pack(anchor='e',pady=(0,5),padx=(20))
        self.FRAME[0].pack(fill='both',expand=True)
        self.FRAME[1].pack(fill='x',padx=15,pady=10,anchor='s')
    
    def SP_W(self):
        dark=ctk.CTkSwitch(self,text="다크 모드",command=self.dark_mode,variable=self.darkmodevar,onvalue='on',offvalue='off')
        if ctk.get_appearance_mode()=='Light':
            self.darkmodevar.set(value='off')
        return dark


    def dark_mode(self):
        if self.darkmodevar.get()=='off':
            ctk.set_appearance_mode('light')
        else:
            ctk.set_appearance_mode('dark')

    def FRAME_BASE(self):
        l=[]
        for i in range (2):
            l.append(ctk.CTkFrame(self,fg_color='transparent'))
        return l

    def LABEL_BASE(self):
        l=[]
        for i in range (3):
            l.append(ctk.CTkLabel(self))
        return l 

    def BUTTON_BASE(self):
        l=[]
        for i in range (3):
            l.append(ctk.CTkButton(
                self.FRAME[1],
                width=60,height=5,
                font=('suit',16,'bold')
                ))
        return l

    def STARTCOUNT(self,container):
        COUNTPAGE(container)
        container.state(newstate='withdrawn')
    
    def STARTEDIT(self,container):
        EDIT_Page(container)
        container.state(newstate='withdrawn')

    def ABORT(self,container):
        container.destroy()

class EDIT_Page(ctk.CTkToplevel):
    def __init__(self,container):
        self.Database=Database()
        super().__init__()
        self.geometry('900x600')
        self.resizable(False,False)
        self.title('경로식당 이용자 정보 수정')
        self.TOP_RIBBON=ctk.CTkFrame(self,height=200,corner_radius=0)
        self.CLOCK=ctk.CTkLabel(self.TOP_RIBBON,text="",font=('suit',16,'bold'))
        self.CLOCK.pack(side='left',anchor='sw',padx=10,pady=10)
        self.CLC()
        self.TR_W()
        self.Table=ctk.CTkScrollableFrame(self,fg_color='transparent')
        self.Entry=ctk.CTkEntry(self,font=('suit',16,'bold'),placeholder_text='입력...')
        self.Buttonframe=ctk.CTkFrame(self)
        self.UserList=self.Make_user_list(self.Database.Get_user_stat())
        self.Showing=self.UserList
        for x in range (6):
            self.Table.columnconfigure(x,weight=1,uniform='column')
            self.Buttonframe.columnconfigure(x,weight=1,uniform='column')
        self.Entry.bind('<Return>',lambda event:self.KEY_PRESSED())
        self.protocol("WM_DELETE_WINDOW", partial(self.Abort,container))
        self.Make_Buttons()
        self.UPDATE_TABLE()
        self.TBL_W()
    
    def Abort(self,container):
        if messagebox.askokcancel("종료", "종료하시겠습니까?"):
            self.Database.Stop()
            self.destroy()
            container.state(newstate='normal')

    def CLC(self):
        time=dt.datetime.now()
        stft=time.strftime('%m월 %d일')
        self.CLOCK.configure(text=stft)

    def TR_W(self):
        ctk.CTkLabel(self.TOP_RIBBON,text='경로식당 이용자 편집',font=('suit',36,'bold')).pack(side='right',anchor='ne',padx=10)
        self.TOP_RIBBON.pack(fill='x',anchor='n')

    def TBL_W(self):
        self.Buttonframe.pack(padx=(20,15),pady=(10,0),side='top',fill='x')
        self.Table.pack(padx=(15,0),pady=10,side='top',fill='both',expand=True)
        self.Entry.pack(padx=10,pady=10,side='top',fill='x')

    def RESET(self):
        self.Showing=self.UserList
        self.UPDATE_TABLE()

    def Make_Buttons(self):
        l=['번호',' 이름 ','카드 등록','금월 이용','죽식 이용']
        for i in range(5):
            ctk.CTkButton(self.Buttonframe,
                          fg_color='transparent',
                          text=l[i],
                          command=partial(self.Sort,i),
                          text_color=('Black','white'),
                          font=('suit',16,'bold')
                          ).grid(row=0,column=i)
        ctk.CTkButton(self.Buttonframe,
                        text='신규 등록',
                        command=self.New_user,
                        font=('suit',16,'bold')
                        ).grid(row=0,column=5)
    
    def Make_user_list(self,data):
        out=[]
        cardout=('카드 등록','카드 미등록')
        for u in data:
            num=ctk.CTkLabel(self.Table,text=f' {str(u[0])} ',font=('suit',16,'bold'))
            name=ctk.CTkLabel(self.Table,text=u[1],font=('suit',16,'bold'))
            card=ctk.CTkLabel(self.Table,text=cardout[u[2]],font=('suit',16,'bold'))
            stat1=ctk.CTkLabel(self.Table,text=str(u[3]),font=('suit',16,'bold'))
            stat2=ctk.CTkLabel(self.Table,text=str(u[4]),font=('suit',16,'bold'))
            button=ctk.CTkButton(self.Table,fg_color='transparent',text='수정',font=('suit',16,'bold'),command=partial(self.Edit,u),text_color=('Black','white'))
            out.append((num,name,card,stat1,stat2,button,u[0],u[1],u[2],u[3],u[4]))
        return out
    
    def Sort(self,ind):
        if ind<2:
            s=sorted(self.Showing,key=itemgetter(ind+6))
            if self.Showing!=s:
                self.Showing=s
            else:
                self.Showing.sort(key=itemgetter(ind+6),reverse=True)
        else:
            s=sorted(sorted(self.Showing,key=itemgetter(6)),key=itemgetter(ind+6),reverse=True)
            if self.Showing!=s:
                self.Showing=s
            else:
                s=sorted(sorted(self.Showing,key=itemgetter(6)),key=itemgetter(ind+6))
                self.Showing=s
        self.UPDATE_TABLE()

    def KEY_PRESSED(self):
        e=self.Entry.get()
        if e=="" or e=='0':
            self.RESET()
        elif re.search('[0-9]',e):
            self.Check_Num(e)
        else:
            entered=h2j(e)
            self.CHECK_SYLABLE(entered)
        
    def Check_Num(self,entered):
        for user in self.UserList:
            if str(user[6])==entered:
                out=[user]
                break
        self.Showing=out
        self.UPDATE_TABLE()

    def CHECK_SYLABLE(self,TYPE):
        output=[]
        output2=[]
        for users in self.UserList:
            cnt=0
            if len(TYPE)<=len(h2j(users[7])):
                for x in range (len(TYPE)):
                    if list(TYPE)[x]==list(h2j(users[7]))[x]:
                        cnt+=1
                if cnt==len(TYPE):
                    output.append(users)
                if cnt>1 and cnt==len(TYPE)-1:
                    output2.append(users)
        output=output+output2
        self.Showing=output
        self.UPDATE_TABLE()
    
    def Clear_Table(self):
        for x in self.Table.winfo_children():
            x.grid_forget()

    def UPDATE_TABLE(self):
        self.Clear_Table()
        if len(self.Showing)>50:
            for i in range(50):
                for j in range (6):
                    self.Showing[i][j].grid(row=i,column=j)
            ctk.CTkButton(self.Table,
                            fg_color='transparent',
                            text='더보기',
                            command=partial(self.Show_More,50),
                            text_color=('Black','white'),
                            font=('suit',16,'bold')
                            ).grid(row=50,column=5)
        else:
            for i in range(len(self.Showing)):
                for j in range (6):
                    self.Showing[i][j].grid(row=i,column=j)
    
    def Show_More(self,ind):
        self.Clear_Table()
        indx=ind+50
        if len(self.Showing)>=indx:
            for i in range(50):
                for j in range (6):
                    self.Showing[ind+i][j].grid(row=i,column=j)
            ctk.CTkButton(self.Table,
                            fg_color='transparent',
                            text='더보기',
                            command=partial(self.Show_More,indx+1),
                            text_color=('Black','white'),
                            font=('suit',16,'bold')
                            ).grid(row=50,column=5)
            self.update_idletasks()
        else:
            for i in range(indx-len(self.Showing)):
                for j in range (6):
                    self.Showing[ind+i][j].grid(row=i,column=j)
            
            ctk.CTkButton(self.Table,
                            fg_color='transparent',
                            text='처음으로',
                            command=partial(self.UPDATE_TABLE,),
                            text_color=('Black','white'),
                            font=('suit',16,'bold')
                            ).grid(row=indx-len(self.Showing),column=5)
    
    def Edit(self,data):
        top=ctk.CTkToplevel()
        top.attributes('-topmost', 'true')
        top.geometry('300x200')
        top.title('이용자 정보 수정')
        for i in range (3):
            top.columnconfigure(i,weight=1,uniform='text')
        for i in range (4):
            top.rowconfigure(i,weight=1,uniform='place')
        ctk.CTkLabel(top,text='이용자 정보 수정',font=('suit',16,'bold')).grid(row=0,column=0,columnspan=3, padx=20,pady=(10,5))
        ctk.CTkLabel(top,text='이름',font=('suit',16,'bold')).grid(row=2,column=0,columnspan=1,sticky='w',padx=10)
        ctk.CTkLabel(top,text='번호',font=('suit',16,'bold')).grid(row=1,column=0,columnspan=1,sticky='w',padx=10)
        name=ctk.CTkEntry(top,placeholder_text='이름',font=('suit',16,'bold'),width=200)
        name.grid(row=2,column=1,columnspan=2,pady=(0,10),sticky='e',padx=10)
        num=ctk.CTkEntry(top,placeholder_text='번호',font=('suit',16,'bold'),width=200)
        num.insert(0,str(data[0]))
        num.configure(state='disabled')
        num.grid(row=1,column=1,columnspan=2,padx=10,sticky='e')
        ctk.CTkButton(top, width=60,height=5,text='등록',command=lambda:self.Add_user(top,num.get(),name.get()),font=('suit',16,'bold')).grid(row=3,column=2,pady=(0,10))
        ctk.CTkButton(top,width=60,height=5,text='취소',command=lambda:top.destroy(),font=('suit',16,'bold')).grid(row=3,column=1,padx=(20,0),pady=(0,10))
        ctk.CTkButton(top,width=60,height=5,text='삭제',command=lambda:self.Delete(top,num.get(),data[1]),font=('suit',16,'bold')).grid(row=3,column=0,padx=10,pady=(0,10))
    
    def Delete(self,toplevel,num,name):
        toplevel.destroy()
        if messagebox.askyesno(title='이용자 정보 삭제',message=f'이용자 정보를 삭제합니다.\n{str(num)}번 {str(name)}'):
            self.Database.Delete_user(int(num))
            self.Reset_list()
        else:
            messagebox.showinfo(title="경고",message="취소되었습니다.")




    def New_user(self):
        top=ctk.CTkToplevel()
        top.attributes('-topmost', 'true')
        top.geometry('300x200')
        top.title('신규 이용자 등록')
        for i in range (3):
            top.columnconfigure(i,weight=1,uniform='text')
        for i in range (4):
            top.rowconfigure(i,weight=1,uniform='place')
        ctk.CTkLabel(top,text='신규 이용자 등록',font=('suit',16,'bold')).grid(row=0,column=0,columnspan=3, padx=20,pady=(10,5))
        ctk.CTkLabel(top,text='이름',font=('suit',16,'bold')).grid(row=2,column=0,columnspan=1,sticky='w',padx=10)
        ctk.CTkLabel(top,text='번호',font=('suit',16,'bold')).grid(row=1,column=0,columnspan=1,sticky='w',padx=10)
        name=ctk.CTkEntry(top,placeholder_text='이름',font=('suit',16,'bold'),width=200)
        name.grid(row=2,column=1,columnspan=2,pady=(0,10),sticky='e',padx=10)
        num=ctk.CTkEntry(top,placeholder_text='번호',font=('suit',16,'bold'),width=200)
        num.grid(row=1,column=1,columnspan=2,padx=10,sticky='e')
        ctk.CTkButton(top, width=60,height=5,text='등록',command=lambda:self.Add_user(top,num.get(),name.get()),font=('suit',16,'bold')).grid(row=3,column=2,pady=(0,10))
        ctk.CTkButton(top,width=60,height=5,text='취소',command=lambda:top.destroy(),font=('suit',16,'bold')).grid(row=3,column=1,pady=(0,10))
    
    def Add_user(self,toplevel,num,name):
        toplevel.destroy()
        if num=='' or name=='':
            messagebox.showinfo(title="경고",message="잘못된 입력입니다.")
            self.New_user()
        elif re.search('[0-9]',num):
            check=self.Database.Check_Input(int(num),True)
            if check==None:
                self.New_user2(num,name)
            else:
                self.Replace(check,name)
        else:
            messagebox.showinfo(title="경고",message="잘못된 입력입니다.")
            self.New_user()
    
    def New_user2(self,num,name):
        if messagebox.askyesno(title='신규 이용자 등록',message=f'신규 이용자 등록합니다.\n{str(num)}번 {str(name)}'):
            self.Database.AddUser(num,name)
            self.Reset_list()
    
    def Replace(self,check,name):
        if messagebox.askyesno(title='이용자 정보 교체',message=f'{str(check[0])}번 {str(check[1])}님의 정보가 교체됩니다.\n{str(check[1])} -> {str(name)}'):
            self.Database.UpdateUserinfo(check[0],name)
            self.Reset_list()
    
    def Reset_list(self):
        self.UserList=self.Make_user_list(self.Database.Get_user_stat())
        self.RESET()



        





if __name__ == '__main__':

    ctk.set_default_color_theme("green")
    ctk.set_appearance_mode('dark')
    root=ctk.CTk()
    root.title('경로식당 인원관리')

    sp=START_PAGE(root)
    sp.pack(expand=True,fill='both')
    root.mainloop()
