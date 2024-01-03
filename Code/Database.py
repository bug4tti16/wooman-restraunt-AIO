import pandas as pd
import customtkinter as ctk
import datetime as dt
from calendar import Calendar
from pynput.keyboard import Key, Controller
from functools import partial
from jamo import h2j,j2h
from multiprocessing import Process, Queue
from tkinter import messagebox
from winsound import Beep
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
        m=[x for x in c.itermonthdates(td.year, td.month) if x.month == td.month and x.weekday()<5]
        n=self.cur.execute(
            """SELECT MAX(num)
            FROM users""").fetchall()[0][0]
        
        #number
        data={'번호':[],
           '이름':['']*n}
        
        #name
        for i in range (n):
            data['번호'].append(i+1)
        name=self.con.execute(
            f"""SELECT num,name
            FROM users""")
        for row in name:
            data['이름'][row['num']-1]=row['name']
        
        #data
        for d in m:
            data.update({d:['']*n})
            e=self.con.execute(
                f"""SELECT num,output_format
                FROM parsed_data
                WHERE DATE(date)='{d}'""")
            for row in e:
                data[d][row['num']-1]=row['output_format']
        
        
        
        df=pd.DataFrame(data=data)
        try:
            with pd.ExcelWriter(self.OutputLocation,if_sheet_exists='replace',mode='a') as w:
                df.to_excel(w,sheet_name=dt.datetime.now().strftime('%Y-%m'),header=True,index=False)
        except:
            with pd.ExcelWriter(self.OutputLocation,mode='w') as w:
                df.to_excel(w,sheet_name=dt.datetime.now().strftime('%Y-%m'),header=True,index=False)
            
    def Check_Input(self,data):
        try:
            int(data)
        except:
            check=self.cur.execute(
                f"""SELECT num
                FROM users
                WHERE card='#{data}' OR name='{data}'""").fetchall()
        else:
            check=self.cur.execute(
                f"""SELECT num
                FROM users
                WHERE num={data}""").fetchall()
        if check==[]:
            return None
        if len(check)>1:
            return None
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
            f"""UPDATE OR REPLACE users
            SET card='#{cardno}'
            WHERE num={num}"""
        )
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

        
    #엔터 입력시
    def ENTER_PRESSED(self):
        Controller().press(Key.right)
        entered=self.ENTRY.get()
        try:
            e=int(entered)
        except:
            pass
        else:
            self.CHECK_NUM(e)

    #번호 확인
    def CHECK_NUM(self,num):
        for x in self.ulist:
            if x[0]==num:
                self.RETURN_UID(x)
        
    #타자 입력시
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

    #이름 확인 (자모)
    def CHECK_SYLABLE(self,TYPE):
        output=[]
        output2=[]
        for users in self.ulist:
            cnt=0
            if len(TYPE)<=len(h2j(users[1])):
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

    
    #이름 표출
    def RETURN_UID(self,UID):
        if UID!=None:
            self.QUEUE.put(UID[0],block=False)
        self.CLEAR_BUTTONS()
        self.CLEAR_ENTRY()


class LIVE_FRAMES(ctk.CTkScrollableFrame):
    Menu=['일반식','죽식']
    FRAMES=[]
    def __init__(self,container):
        super().__init__(container,fg_color='transparent',width=400)
    
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
        self.CLOCK.pack(side='left',anchor='sw',padx=10,pady=10)
        self.COUNTLABEL.pack(side='left',anchor='se',padx=10,pady=10)
        self.CLC()
        self.TR_W()
        self.BODYFRAME=ctk.CTkFrame(self,fg_color='transparent')
        self.UL=self.DATABASE.Get_ulist()
        self.SEARCH=SEARCH_FRAME(self.BODYFRAME,self,self.UL,16,self.QUEUE)
        self.LOG=LIVE_FRAMES(self.BODYFRAME)
        self.BF_W()
        self.INITIALWORKS()
        self.DATA_HANDLING()
        self.bind("<Control-KeyPress-z>",self.CANCEL)
        self.bind("<Control-KeyPress-w>",self.CHANGE_MENU)
        self.protocol("WM_DELETE_WINDOW", partial(self.ABORT,root))
        

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
            self.destroy()
            self.CARD.kill()
            root.state(newstate='normal')

    def GETCOUNT(self):
        cnt=self.DATABASE.Get_Count()
        self.COUNTLABEL.configure(text=f'{cnt[0]}명  |  죽식: {cnt[1]}명')

    def TR_W(self):
        ctk.CTkLabel(self.TOP_RIBBON,text='경로식당 인원관리',font=('suit',36,'bold')).pack(side='right',anchor='ne',padx=10,pady=10)
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
                
            elif type(d)==str:
                self.NOCARDHANDLER(d)
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
            messagebox('경고','등록을 취소합니다.')
        else:
            num=self.DATABASE.Check_Input(d)
            if num!=None:
                l=[num,self.DATABASE.Return_udata(num)]
                if messagebox.askokcancel("경고",f"{l[0]}번 {l[1]}님의 정보를 교체합니다."):
                    self.DATABASE.AddCard(l[0],data)
                    self.LOG.SINGLE_MESSAGE(f"{l[0]}번 {l[1]}님 카드 등록 완료. 카드 찍어주세요.",True)
                else:
                    messagebox('경고','등록을 취소합니다.')

class START_PAGE(ctk.CTkFrame):
    def __init__(self,container):
        container.resizable(False,False)
        container.geometry('900x600')
        super().__init__(container)
        self.pack_configure(fill='both',expand=True)
        self.LABEL=self.LABEL_BASE()
        self.FRAME= self.FRAME_BASE()
        self.TEXTBOX=ctk.CTkTextbox(self.FRAME[0])
        self.BUTTONS=self.BUTTON_BASE()

        self.LABEL[0].configure(text="우만종합사회복지관",font=('suit',32,'bold'))
        self.LABEL[1].configure(text="경로식당 이용자관리 프로그램",font=('suit',16,'bold'))
        self.LABEL[2].configure(text=dt.datetime.now().strftime('%Y년 %m월 %d일'),font=('suit',16,'bold'))

        self.TEXTBOX.insert(ctk.INSERT,"""경로식당 프로그램 2.0 시험운행.

                            
죽식 변환 control + w(ㅈ)
등록 취소 control + z

이용자 정보 파일 위치: 내 문서 -> XXXX년 경로식당 이용자.xlsx
이용자 정보 수정: 프로그램 제작중 임성호 사회복무요원에게 문의
                            
                            """)
        self.TEXTBOX.configure(state='disabled',font=('suit',16,'bold'))
        self.TEXTBOX.pack(fill='both',expand=True,padx=20,pady=5)

        self.BUTTONS[0].configure(text="시작",command=partial(self.STARTCOUNT,container))
        self.BUTTONS[1].configure(text="등록",state='disabled')
        self.BUTTONS[2].configure(text='종료',command=partial(self.ABORT,container))
        for l in ([self.BUTTONS[0],self.BUTTONS[1]]):
            l.pack(side='right',expand=False,anchor='e',padx=5)
        self.BUTTONS[2].pack(side='left',expand=False,anchor='w',padx=5)

        self.LABEL[0].pack(pady=(20,0))
        self.LABEL[1].pack()
        self.LABEL[2].pack(pady=(10,5))
        self.FRAME[0].pack(fill='both',expand=True)
        self.FRAME[1].pack(fill='x',padx=15,pady=10,anchor='s')
        
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
        c=COUNTPAGE(container)
        container.state(newstate='iconic')

    def ABORT(self,container):
        container.destroy()

if __name__ == '__main__':

    ctk.set_default_color_theme("green")
    ctk.set_appearance_mode('dark')
    root=ctk.CTk()
    root.title('경로식당 인원관리')

    sp=START_PAGE(root)
    sp.pack(expand=True,fill='both')
    root.mainloop()