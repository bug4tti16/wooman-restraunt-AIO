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
import os,pathlib,re,serial,time, sqlite3

class DATABASE():
    def __init__(self):
        self.DBLocation=os.path.join(pathlib.Path(__file__).parent.parent,'Data','data.db')
        self.OutputLocation=os.path.join(os.path.expanduser('~'),'Documents','경로식당',dt.datetime.now().strftime('%Y년 경로식당 이용자.xlsx'))
        self.Connect=sqlite3.connect(self.DBLocation)
        self.Cursor=self.Connect.cursor()
        self.Today=dt.date.today()
    
    def AddCard(self,cardno,num):
        self.Cursor.execute(f"UPDATE users SET Card='{"#"+ cardno}' WHERE _id={num};")
        self.Cursor.execute('COMMIT;')

    def AddUser(self,num,name,cardno):
        self.Cursor.execute(f"UPDATE users SET Card='{"#"+ cardno}',Name='{name}' WHERE _id={num};")
        self.Cursor.execute('COMMIT;')

    def GetUserlist(self):
        out=self.Cursor.execute(f"SELECT _id, Name FROM users").fetchall()
        return list(out)

    def Export(self):
        c=Calendar()
        td=self.Today
        output=[]
        keys=['번호','이름']
        m=[x for x in c.itermonthdates(td.year, td.month) if x.month == td.month]
        for x in self.Cursor.execute(f"SELECT _id, Name FROM users").fetchall():
            output.append([x[0],x[1]])

        for d in m:
            keys.append (d)
            log=self.Cursor.execute(f"SELECT UID, Cbool, Cancel, Menu FROM log WHERE DATE(Time)='{d}' ORDER BY Time")

            for row in log:
                l=output[row[0]-1]
                if len(l)<len(keys):
                    if row[1]==0:
                        l.append('O')
                    if row[1]==1:
                        l.append('NC')
                else:
                    if row[2]==1:
                        l.remove(l[-1])
                    if row[3]==1:
                        if '죽' in l[-1]:
                            l[-1].replace(' (죽식)','')
                        else:
                            l[-1]+=' (죽식)'
    
            for i in output:
                if len(i)<len(keys):
                    i.append('')
    
        df=pd.DataFrame(output,columns=keys)
        try:
            with pd.ExcelWriter(self.OutputLocation,if_sheet_exists='replace',mode='a') as w:
                df.to_excel(w,sheet_name=dt.datetime.now().strftime('%Y-%m'),header=True,index=False)
        except:
            with pd.ExcelWriter(self.OutputLocation,mode='w') as w:
                df.to_excel(w,sheet_name=dt.datetime.now().strftime('%Y-%m'),header=True,index=False)

    def Count(self):
        d=self.Today
        output=[]
        realout=[]
        cnt=0
        mcnt=0
        for x in self.Cursor.execute(f"SELECT _id, Name FROM users").fetchall():
            output.append([x[0],x[1]])

        log=self.Cursor.execute(f"SELECT UID, Cbool, Cancel, Menu, Time FROM log WHERE DATE(Time)='{d}' ORDER BY Time")
        for row in log:
            l=output[row[0]-1]
            if len(l)==2:
                if row[1]!=None:
                    l.append(dt.datetime.fromisoformat(row[4]))
                    l.append('일반식')
                    cnt+=1
            else:
                if row[2]==1:
                    cnt-=1
                    if '죽' in l[-1]:
                        mcnt-=1
                    l.remove(l[-1])
                    l.remove(l[-1])
                if row[3]==1:
                    if '죽' in l[-1]:
                        l[-1]='일반식'
                        mcnt-=1
                    else:
                        l[-1]='죽식'
                        mcnt+=1
    
        for i in output:
            if len(i)==4:
                realout.append(i)
        return ([realout,cnt,mcnt])

class SEARCH_FRAME(ctk.CTkFrame):
    def __init__(self,container,entrycontainer,users,number_of_buttons,queue):
        super().__init__(container,width=300)
        self.QUEUE=queue
        self.N=number_of_buttons
        self.ENTRY=ctk.CTkEntry(entrycontainer,font=('suit',16,'bold'),placeholder_text='입력...')
        self.BUTTON=self.BUTTONS(number_of_buttons)
        self.ENTRY.bind('<Return>',lambda event:self.ENTER_PRESSED(users))
        self.ENTRY.bind('<KeyRelease>',lambda event:self.KEY_PRESSED(users))
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
                self.BUTTON[x].configure(text=f"{userlist[x][0]}: {userlist[x][1]}")
                self.BUTTON[x].configure(command=partial(self.RETURN_UID,userlist[x]))
                self.BUTTON[x].configure(state='normal')

        else:        
            for x in range (len(userlist)):
                self.BUTTON[x].configure(text=f"{userlist[x][0]}: {userlist[x][1]}")
                self.BUTTON[x].configure(command=partial(self.RETURN_UID,userlist[x]))
                self.BUTTON[x].configure(state='normal')
    def CLEAR_BUTTONS(self):
        for x in self.BUTTON:
            x.configure(text='',command=None,state='disabled')
    
    def CLEAR_ENTRY(self):
        Controller().press(Key.right)
        self.ENTRY.delete(0,'end')

        
    #엔터 입력시
    def ENTER_PRESSED(self,ul):
        Controller().press(Key.right)
        entered=(self.ENTRY.get())
        if re.search('[0-9]',entered):
            self.CHECK_NUM(entered,ul)
        else:
            if entered!='':
                self.CHECK_NAME(h2j(entered),ul)

    #번호 확인
    def CHECK_NUM(self,NUM,ul):
        try:
            n=int(NUM)
        except:
            pass
        else:
            for x in ul:
                if x[0]==n:
                    self.RETURN_UID(x)
    #이름 확인
    def CHECK_NAME(self,NAME,ul):
        output=[]
        for x in ul:
            if NAME==h2j(x[1]):
                output.append(x)
        if len(output)>1:
            self.UPDATE_BUTTONS(output)
        if len(output)==1:
            self.RETURN_UID(output[0])
        
    #타자 입력시
    def KEY_PRESSED(self,ul):
        self.CLEAR_BUTTONS()
        entered=h2j(self.ENTRY.get())
        if entered=="":
            pass
        else:
            if re.search('[0-9]',entered):
                pass
            else:
                self.CHECK_SYLABLE(entered,ul)


    #이름 확인 (자모)
    def CHECK_SYLABLE(self,TYPE,ul):
        output=[]
        output2=[]
        for users in ul:
            cnt=0
            if len(TYPE)<=len(h2j(users[1])):
                for x in range (len(TYPE)):
                    if list(TYPE)[x]==list(h2j(users[1]))[x]:
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
    def __init__(self,container):
        super().__init__(container,fg_color='transparent',width=400)
    
    def NEW_FRAME(self,DATA,highlight):
        #DATA=[num,name,datetime,menu]
        f=ctk.CTkFrame(self)
        ctk.CTkLabel(f,text=DATA[2].strftime("%H시 %M분 %S초"),font=('suit',16)).pack(pady=(10,0),padx=5,anchor='w') #time
        ctk.CTkLabel(f,text=f"{str(DATA[0])}번 {DATA[1]}님",font=('suit',36,'bold')).pack(pady=(10,0),padx=5,anchor='w') #num name
        ctk.CTkLabel(f,text=f"{DATA[3]}",font=('suit',16,'bold')).pack(pady=(10,0),padx=5,anchor='e') #menu
        if highlight:
            f.configure(fg_color='#fb8c6f')
        f.pack(side='bottom',fill='x',padx=(50,100),pady=(30,15))
    
    def SINGLE_MESSAGE(self,message,highlight):
        f=ctk.CTkFrame(self)
        ctk.CTkLabel(f,text=message,font=('suit',24,'bold')).pack(pady=(10,10),padx=5)
        if highlight:
            f.configure(fg_color='#fb8c6f')
        f.pack(side='bottom',fill='x',padx=(50,100),pady=(30,15))
    
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
        self.USERTEMP=[0,0]
        self.DATABASE=DATABASE()
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
        self.UL=self.DATABASE.GetUserlist()
        self.SEARCH=SEARCH_FRAME(self.BODYFRAME,self,self.UL,16,self.QUEUE)
        self.LOG=LIVE_FRAMES(self.BODYFRAME)
        self.BF_W()
        self.CURRENT=None
        self.INITIALWORKS()
        self.DATA_HANDLING()
        self.bind("<Control-KeyPress-z>",self.CANCEL)
        self.bind("<Control-KeyPress-w>",self.CHANGE_MENU)
        self.protocol("WM_DELETE_WINDOW", partial(self.ABORT,root))
        

    def INITIALWORKS(self):
        d=self.DATABASE.Count()
        self.USERTEMP[0]=d[1]
        self.USERTEMP[1]=d[2]
        if d[0]!=[]:
            for x in d[0]:
                self.LOG.NEW_FRAME(x,False)
        self.GETCOUNT()


    def SOUND(self):
        for x in range (3):
            Beep(2000,300)

    def ABORT(self,root):
        if messagebox.askokcancel("종료", "종료하시겠습니까?"):
            self.DATABASE.Export()
            self.destroy()
            self.CARD.kill()
            root.state(newstate='normal')

    def GETCOUNT(self):
        self.COUNTLABEL.configure(text=f'{sum(self.USERTEMP)}명  |  죽식: {self.USERTEMP[1]}명')

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

            if type(d)==int:
                C=1
                fetch=self.DATABASE.Cursor.execute(f"SELECT _id, Name FROM users WHERE _id={d}").fetchall()
            if type(d)==str:
                C=0
                fetch=self.DATABASE.Cursor.execute(f"SELECT _id, Name FROM users WHERE Card='#{d}'").fetchall()
                if fetch==[]:
                    self.SOUND()
                    self.NOCARDHANDLER(d)
            if fetch!=[]:
                td=dt.date.today()
                cancel=self.DATABASE.Cursor.execute(f"SELECT COUNT(*) FROM log WHERE UID={fetch[0][0]} AND DATE(Time)='{td}' AND Cancel=1").fetchall()[0][0]
                check=self.DATABASE.Cursor.execute(f"SELECT Time FROM log WHERE UID={fetch[0][0]} AND DATE(Time)='{td}' AND Cbool IS NOT NULL").fetchall()
                menucheck=self.DATABASE.Cursor.execute(f"SELECT COUNT(*) FROM log WHERE UID={fetch[0][0]} AND DATE(Time)='{td}' AND Menu=1").fetchall()[0][0]
                self.CURRENT=fetch[0][0]
                if len(check)-cancel==0:
                    out=[fetch[0][0],fetch[0][1],dt.datetime.now(),'일반식']
                    self.DATABASE.Cursor.execute(f"INSERT INTO log (UID, Time, Cbool) VALUES ('{out[0]}', '{out[2].isoformat(sep=' ',timespec="seconds")}', {C})")
                    self.DATABASE.Cursor.execute("COMMIT;")
                    self.USERTEMP[0]+=1
                    self.GETCOUNT()
                    self.LOG.NEW_FRAME(out,False)
                        
                else:
                    out=[fetch[0][0],fetch[0][1],dt.datetime.fromisoformat(check[0][0]),'일반식']
                    if menucheck%2==1:
                        out[3]='죽식'
                    self.LOG.NEW_FRAME(out,True)
                            
        finally:
            self.after(100,self.DATA_HANDLING)
    


    def CANCEL(self,event):
        if self.CURRENT!=None:
            td=dt.date.today()
            self.DATABASE.Cursor.execute(f"INSERT INTO log (UID, Time, Cancel) VALUES ({self.CURRENT}, '{dt.datetime.now().isoformat(sep=' ',timespec="seconds")}', 1)")
            fetch=self.DATABASE.Cursor.execute(f"SELECT _id, Name FROM users WHERE _id={self.CURRENT}").fetchall()
            menucheck=self.DATABASE.Cursor.execute(f"SELECT COUNT(*) FROM log WHERE UID={fetch[0][0]} AND DATE(Time)='{td}' AND Menu=1").fetchall()[0][0]
            self.USERTEMP[0]-=1
            if menucheck%2==1:
                self.USERTEMP[1]-=1
            self.CURRENT=None
        
            self.LOG.SINGLE_MESSAGE(f'{fetch[0][1]}님 취소되었습니다.',True)
            self.GETCOUNT()
    
    def CHANGE_MENU(self,event):
        if self.CURRENT!=None:
            td=dt.date.today()
            self.DATABASE.Cursor.execute(f"INSERT INTO log (UID, Time, Menu) VALUES ({self.CURRENT}, '{dt.datetime.now().isoformat(sep=' ',timespec="seconds")}', 1)")
            check=self.DATABASE.Cursor.execute(f"SELECT Time FROM log WHERE UID={self.CURRENT} AND DATE(Time)='{td}' AND Cbool IS NOT NULL").fetchall()
            fetch=self.DATABASE.Cursor.execute(f"SELECT _id, Name FROM users WHERE _id={self.CURRENT}").fetchall()
            menucheck=self.DATABASE.Cursor.execute(f"SELECT COUNT(*) FROM log WHERE UID={fetch[0][0]} AND DATE(Time)='{td}' AND Menu=1").fetchall()[0][0]
            out=[fetch[0][0],fetch[0][1],dt.datetime.fromisoformat(check[0][0]),'일반식']
            if menucheck%2==1:
                out[3]='죽식'
                self.USERTEMP[1]+=1
            else:
                self.USERTEMP[1]-=1
            self.LOG.SINGLE_MESSAGE(f'{fetch[0][1]}님 메뉴 변경.',True)
            self.LOG.NEW_FRAME(out,True)
            self.GETCOUNT()


    def NOCARDHANDLER(self,data):
        n=ctk.CTkInputDialog(text=("이름 혹은 번호 입력"),title="미등록 카드")
        d=n.get_input()
        if d==None or '':
            messagebox('경고','등록을 취소합니다.')
        elif re.search('[0-9]',d):
            try:
                u=self.DATABASE.Cursor.execute(f"SELECT _id, Name FROM users WHERE _id={int(d)}")[0]
            except:
                messagebox('경고','등록되지 않은 이용자 입니다.')
            else:
                if messagebox.askokcancel('경고',f'{u[0]}번 {u[1]}님의 정보를 교체합니다.'):
                    self.DATABASE.AddCard(data,u[0])
                else:
                    messagebox('경고','등록을 취소합니다.')
        else:
            try:
                u=self.DATABASE.Cursor.execute(f"SELECT _id, Name FROM users WHERE Name='{d}'")[0]
            except:
                messagebox('경고','등록되지 않은 이용자 입니다.')
            else:
                if messagebox.askokcancel('경고',f'{u[0]}번 {u[1]}님의 정보를 교체합니다.'):
                    self.DATABASE.AddCard(data,u[0])
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

1분마다 자동저장 됩니다

수동 저장 control + s
죽식 변환 control + w(ㅈ)
등록 취소 control + z

이용자 정보 파일 위치: 내 문서 -> XXXX년 경로식당 이용자.xlsx
이용자 정보 수정: 엑설파일에서 직접 수정

임성호 사회복무요원은 살아 있습니다. ㅠㅠ""")
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


class EDIT_WINDOW(ctk.CTkToplevel):
    def _init_():
        pass

if __name__ == '__main__':

    ctk.set_default_color_theme("green")
    ctk.set_appearance_mode('dark')
    root=ctk.CTk()
    root.title('경로식당 인원관리')

    sp=START_PAGE(root)
    sp.pack(expand=True,fill='both')
    root.mainloop()