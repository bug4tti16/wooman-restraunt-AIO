import pandas as pd
import customtkinter as ctk
import datetime as dt
from pynput.keyboard import Key, Controller
from functools import partial
from jamo import h2j
from multiprocessing import Process, Queue
from threading import Thread
from tkinter import messagebox
from winsound import Beep
import os,pathlib,re,serial,time


class USER_DATA:
    def __init__(self,ddf:pd.DataFrame,sdf:pd.DataFrame,ind):
        self.num=ddf.loc[ddf.index[ind],'번호']
        self.name=ddf.loc[ddf.index[ind],'이름']
        self.JAMO=h2j(self.name)
        self.RFID=ddf.loc[ddf.index[ind],'카드번호']
        self.ATTENDANCE=self.ATT(sdf,ind)
    
    def ATT(self,sdf,ind):
        if dt.date.today() in sdf.columns:
            x=sdf.iloc[ind][dt.date.today()]
            return x
        else:
            return None

class DATA_FRAME:
    def __init__(self):
        self.SAVEFILE_LOCATION=os.path.join(os.path.expanduser('~'),'Documents','경로식당',dt.datetime.now().strftime('%Y년 경로식당 이용자.xlsx'))
        self.UDBINARYLOCATION=os.path.join(pathlib.Path(__file__).parent.parent,'Data','USER_DATA.bin')
        self.SVEBINARYLOCATION=os.path.join(pathlib.Path(__file__).parent.parent,'Data','SAVE_DATA.bin')
        self.USER=None
        self.SAVE=None
        self.ULIST=None
        self.GET_DATA()


    def GET_DATA(self):
        if not os.path.exists(os.path.join(os.path.expanduser('~'),'Documents','경로식당')):
            os.makedirs(os.path.join(os.path.expanduser('~'),'Documents','경로식당'))
        try:
            self.USER=pd.read_pickle(self.UDBINARYLOCATION)
        except:
             self.USER=pd.read_excel(io=self.SAVEFILE_LOCATION,sheet_name='이용자 정보',header=0,usecols=['번호','이름','카드번호'])
             pd.to_pickle(self.USER,self.UDBINARYLOCATION)
        else:
            try:
                file=pd.read_excel(io=self.SAVEFILE_LOCATION,sheet_name='이용자 정보',header=0,usecols=['번호','이름','카드번호'])
                if file.compare(self.USER).empty==False:
                    self.USER=file
                    pd.to_pickle(self.USER,self.UDBINARYLOCATION)
            except: pass

        finally:
            self.USER=self.USER.fillna('')
            try:
                self.SAVE=pd.read_pickle(self.SVEBINARYLOCATION)
            except:
                file=pd.read_excel(io=self.SAVEFILE_LOCATION,sheet_name=dt.datetime.now().strftime('%Y-%m'),header=0,usecols=None)
                file=file.fillna('')
                self.SAVE=self.MAKESAVE_FROMFILE(file)
                pd.to_pickle(self.SAVE,self.SVEBINARYLOCATION)
            finally:
                self.ULIST=[]
                for ind in self.USER.index:
                    self.ULIST.append(USER_DATA(self.USER,self.SAVE,ind))

  
    def MAKESAVE_FROMFILE(self,data:pd.DataFrame):
        col=list(data)
        newcol=[]
        for index in col:
            if type(index)==str:
                newcol.append(index)
            else:
                newcol.append(index.date())
        
        newdf=pd.DataFrame(columns=newcol)
        for i in range (len(data.index)):
            l=[]
            for item in list(data.loc[i]):
                n=0
                if type(item)==str:
                    if item=='':
                        l.append(None)
                    elif 'O' in item:
                        l.append(['','일반식',True])
                    elif 'C' in item:
                        l.append(['','일반식',False])
                    else:
                        l.append(item)
                    if ')' in item:
                        l[-1][1]='죽식'
                else:
                    l.append(str(item))
                for j in range (len(l)):
                    if type(l[j])==list:
                        l[j][0]=col[j]
            newdf.loc[len(newdf)] = l


        return newdf

    def SAVE_DATA(self):
        l=[]
        for u in self.ULIST:
            l.append(u.ATTENDANCE)
        if len(l)==len(self.SAVE):
            self.SAVE[dt.date.today()]=l
            pd.to_pickle(self.SAVE,self.SVEBINARYLOCATION)

    def SAVE_UDATA(self):
        l=[]
        for u in self.ULIST:
            self.USER.loc[self.USER['번호']==u.num]=u.num,u.name,u.RFID

    def EXPORT(self):
        c=list(self.SAVE)
        export_format=pd.DataFrame(columns=list(self.SAVE))
        for i in range (len(self.SAVE.index)):
            l=[]
            for item in list(self.SAVE.loc[i]):
                if type(item)==list:
                    if item[-1]:
                        l.append('O')
                    elif item[-1]==False:
                        l.append('NC')
                    if item[1]=='죽식':
                        l[-1]=l[-1]+" (죽식)"
                elif item==None:
                    l.append('')
                else:
                    l.append(item)
            export_format.loc[len(export_format)] = l
        try: 
            with pd.ExcelWriter(self.SAVEFILE_LOCATION,if_sheet_exists='replace',mode='a') as w:
                self.USER.to_excel(w,sheet_name='이용자 정보',header=True,index=False)
            with pd.ExcelWriter(self.SAVEFILE_LOCATION,if_sheet_exists='replace',mode='a') as w:
                export_format.to_excel(w,sheet_name=dt.datetime.now().strftime('%Y-%m'),header=True,index=False)
        
        except:
            with pd.ExcelWriter(self.SAVEFILE_LOCATION,mode='w') as w:
                self.USER.to_excel(w,sheet_name='이용자 정보',header=True,index=False)
            with pd.ExcelWriter(self.SAVEFILE_LOCATION,if_sheet_exists='replace',mode='a') as w:
                export_format.to_excel(w,sheet_name=dt.datetime.now().strftime('%Y-%m'),header=True,index=False)

class LIVE_FRAMES(ctk.CTkScrollableFrame):
    def __init__(self,container):
        super().__init__(container,fg_color='transparent',width=400)
    
    def NEW_FRAME(self,DATA,bool):
        f=ctk.CTkFrame(self)
        ctk.CTkLabel(f,text=DATA.ATTENDANCE[0].strftime("%H시 %M분 %S초"),font=('suit',16)).pack(pady=(10,0),padx=5,anchor='w') #time
        ctk.CTkLabel(f,text=f"{str(DATA.num)}번 {DATA.name}님",font=('suit',36,'bold')).pack(pady=(10,0),padx=5,anchor='w') #num name
        ctk.CTkLabel(f,text=f"{DATA.ATTENDANCE[1]}",font=('suit',16,'bold')).pack(pady=(10,0),padx=5,anchor='e') #menu
        if bool:
            f.configure(fg_color='#fb8c6f')
        f.pack(side='bottom',fill='x',padx=(50,100),pady=(30,15))
    
    def SINGLE_MESSAGE(self,message,bool):
        f=ctk.CTkFrame(self)
        ctk.CTkLabel(f,text=message,font=('suit',24,'bold')).pack(pady=(10,10),padx=5)
        if bool:
            f.configure(fg_color='#fb8c6f')
        f.pack(side='bottom',fill='x',padx=(50,100),pady=(30,15))
    
    def DEMO(self):
        ctk.CTkButton(self,text="test",command=partial(self.NEW_FRAME,("1",'이름',dt.datetime.now().strftime("%H시 %M분 %S초"),'죽식'))).pack()

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
                self.BUTTON[x].configure(text=f"{userlist[x].num}: {userlist[x].name}")
                self.BUTTON[x].configure(command=partial(self.RETURN_UID,userlist[x]))
                self.BUTTON[x].configure(state='normal')

        else:        
            for x in range (len(userlist)):
                self.BUTTON[x].configure(text=f"{userlist[x].num}: {userlist[x].name}")
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
            self.CHECK_NUM(int(entered),ul)
        else:
            if entered!='':
                self.CHECK_NAME(h2j(entered),ul)

    #번호 확인
    def CHECK_NUM(self,NUM,ul):
        for x in ul:
            if x.num==NUM:
                self.RETURN_UID(x)
    #이름 확인
    def CHECK_NAME(self,NAME,ul):
        output=[]
        for x in ul:
            if NAME==h2j(x.name):
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
            if len(TYPE)<=len(users.JAMO):
                for x in range (len(TYPE)):
                    if list(TYPE)[x]==list(users.JAMO)[x]:
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
            self.QUEUE.put(UID.num,block=False)
        self.CLEAR_BUTTONS()
        self.CLEAR_ENTRY()

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
            print('no device connected')
            time.sleep(2)
            self.START_READER(queue)
        else:
            go=True
            while go==True:
                try:
                    rd=ser.readline().decode('utf-8').strip()
                except:
                    print("lost connection")
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
        self.DATA=DATA_FRAME()
        self.USERDIR=os.path.join(os.path.expanduser('~'),'Documents','경로식당','이용자 정보',"user_list_RFID.csv")
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
        self.GETCOUNT()
        self.CLOCK.pack(side='left',anchor='sw',padx=10,pady=10)
        self.COUNTLABEL.pack(side='left',anchor='se',padx=10,pady=10)
        self.CLC()
        self.TR_W()
        self.BODYFRAME=ctk.CTkFrame(self,fg_color='transparent')
        self.SEARCH=SEARCH_FRAME(self.BODYFRAME,self,self.DATA.ULIST,16,self.QUEUE)
        self.LOG=LIVE_FRAMES(self.BODYFRAME)
        self.BF_W()
        self.CURRENT=None
        self.DATA_HANDLING()
        Thread(target=self.AUTOSAVE()).run
        self.bind("<Control-KeyPress-s>",self.MANUALSAVE)
        self.bind("<Control-KeyPress-z>",self.CANCEL)
        self.bind("<Control-KeyPress-w>",self.CHANGE_MENU)
        self.protocol("WM_DELETE_WINDOW", partial(self.ABORT,root))
        self.READY_DATA()

    def SOUND(self):
        for x in range (3):
            Beep(2000,300)

    def READY_DATA(self):
        for u in self.DATA.ULIST:
            if u.ATTENDANCE!=None:
                self.LOG.NEW_FRAME(u,False)

    def ABORT(self,root):
        if messagebox.askokcancel("종료", "종료하시겠습니까?"):
            self.destroy()
            self.CARD.kill()
            root.state(newstate='normal')

    def GETCOUNT(self):
        df=self.DATA.SAVE
        n=0
        try: df[dt.date.today()]
        except: self.COUNTLABEL.configure(text=f'0명  |  죽식: 0명')
        else:
            for ind in df.index:
                if type(df[dt.date.today()][ind])==list and df[dt.date.today()][ind][1]=='죽식':
                    n+=1
        
            self.COUNTLABEL.configure(text=f'{self.DATA.SAVE[dt.date.today()].count()}명  |  죽식: {n}명')

    def TR_W(self):
        ctk.CTkLabel(self.TOP_RIBBON,text='경로식당 인원관리',font=('suit',36,'bold')).pack(side='right',anchor='ne',padx=10,pady=10)
        self.TOP_RIBBON.pack(fill='x',expand=True,anchor='n')
        
    def CLC(self):
        time=dt.datetime.now()
        stft=time.strftime('%d월 %m일\n%H시 %M분')
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
            for u in self.DATA.ULIST:
                if type(d)==str and d in u.RFID:
                    self.CURRENT=u
                    self.CARD_HANDLER(u)
                    exists=True
                    break
                elif u.num==d:
                    self.CURRENT=u
                    self.TYPEIN_HANDLER(u)
                    break
            if type(d)==str and exists==False:
                self.SOUND()
                self.NOCARDHANDLER(d)
        finally:
            self.after(100,self.DATA_HANDLING)
    
    def CARD_HANDLER(self,uid):
        if type(uid.ATTENDANCE)!=list or uid.ATTENDANCE[0].date()<dt.date.today():
            uid.ATTENDANCE=[dt.datetime.now(),'일반식',True]
            self.LOG.NEW_FRAME(uid,False)
            self.DATA.SAVE_DATA()
            self.GETCOUNT()

        else:
            self.LOG.NEW_FRAME(uid,True)
        
    def TYPEIN_HANDLER(self,uid):
        if type(uid.ATTENDANCE)!=list or uid.ATTENDANCE[0].date()<dt.date.today():
            uid.ATTENDANCE=[dt.datetime.now(),'일반식',False]
            self.LOG.NEW_FRAME(uid,False)
            self.DATA.SAVE_DATA()
            self.GETCOUNT()

        else:
            self.LOG.NEW_FRAME(uid,True)

    def CANCEL(self,event):
        if self.CURRENT!=None:
            self.CURRENT.ATTENDANCE=None
            self.LOG.SINGLE_MESSAGE(f'{self.CURRENT.name}님 취소되었습니다.',True)
            self.CURRENT=None
            self.DATA.SAVE_DATA()
            self.GETCOUNT()
    
    def CHANGE_MENU(self,event):
        if self.CURRENT!=None:
            if self.CURRENT!=None:
                if self.CURRENT.ATTENDANCE[1]=='일반식':
                    self.CURRENT.ATTENDANCE[1]='죽식'

                else:
                    self.CURRENT.ATTENDANCE[1]='일반식'

                self.LOG.SINGLE_MESSAGE(f'{self.CURRENT.name}님 메뉴 변경.',True)
                self.LOG.NEW_FRAME(self.CURRENT,True)
                self.DATA.SAVE_DATA()
                self.GETCOUNT()

    def AUTOSAVE(self):
        self.DATA.EXPORT()
        self.LOG.SINGLE_MESSAGE(f'{dt.datetime.now().strftime("%H시 %M분 %S초")}: 저장되었습니다.\n(자동저장)',False)
        self.after(60000,self.AUTOSAVE)
    
    def MANUALSAVE(self,event):
        self.DATA.EXPORT()
        self.LOG.SINGLE_MESSAGE(f'{dt.datetime.now().strftime("%H시 %M분 %S초")}: 저장되었습니다\n(수동저장)',False)

    def NOCARDHANDLER(self,data):
        n=ctk.CTkInputDialog(text=("이름 혹은 번호 입력"),title="미등록 카드")
        d=n.get_input()
        if d==None or '':
            messagebox('경고','등록을 취소합니다.')
        elif re.search('[0-9]',d):
            for u in self.DATA.ULIST:
                if u.num==int(d):
                    if messagebox.askokcancel('경고',f'{u.num}번 {u.name}님의 정보를 교체합니다.'):
                        u.RFID=f"#{data}"
                        self.DATA.SAVE_UDATA()
                        break
                    else:
                        messagebox('경고','등록을 취소합니다.')
        else:
            for u in self.DATA.ULIST:
                if u.name==d:
                    if messagebox.askokcancel('경고',f'{u.num}번 {u.name}님의 정보를 교체합니다.'):
                        u.RFID=f"#{data}"
                        self.DATA.SAVE_UDATA()
                        break
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

임성호 사회복무요원은 훈련소에 있습니다. ㅠㅠ""")
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
