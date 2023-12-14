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
import os,pathlib,re,serial,time,sqlite3



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


df=DATA_FRAME().SAVE
dblocation=os.path.join(os.path.expanduser('~'),'Documents','경로식당','data.db')
con=sqlite3.connect(dblocation)
cur = con.cursor()

col=list(df)

for i in df.index:
    num=int(df['번호'][i])
    print (num)
    for x in col:
        if type(df[x][i])==list:
            date=df[x][i][0].isoformat(sep=' ',timespec="seconds")
            print (date)
            if df[x][i][2]:
                cur.execute(f"""
                INSERT INTO  log (UID, Time, Actions)
                VALUES ('{num}', '{date}', 1)""")
            if df[x][i][2]==False:
                cur.execute(f"""
                INSERT INTO  log (UID, Time, Actions)
                VALUES ('{num}', '{date}', 2)""")
            if '죽' in df[x][i][1]:
                cur.execute(f"""
                INSERT INTO  log (UID, Time, Actions)
                VALUES ('{num}', '{date}', 3)""")
   
cur.execute('commit;')
                