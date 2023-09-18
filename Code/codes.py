from multiprocessing import Process, Queue
from datetime import datetime
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
from jamo import h2j, j2hcj
import serial,csv,time,locale,os,pathlib,winsound,re,webbrowser


INFOTEXT="""경로식당 프로그램을 시작합니다.
인원관리 프로그램 코딩 완료하였습니다!!
새로운 카드등록 방법은 임성호 사회복무요원에게 문의해주시길 바랍니다~~

1분마다 자동저장 됩니다
수동저장: ㅈㅈ
끝: ㄲ + 엔터
안될 시, 한/영 키 누르고 다시시도

이용현황 파일명: XXXX년 X월.csv
이용자 데이터 파일명 user_list_RFID.csv

추가적인 문의사항은 임성호 사회복무요원에게!! <3<3
sl4720@gmail.com"""
port = 'COM3'
baud_rate = 9600
SAMENAME=None
FLAGMSG="사무실로 와주시길 바랍니다"
locale.setlocale(locale.LC_CTYPE, 'korean')

def Abort_master():
    if messagebox.askokcancel("종료", "종료하시겠습니까?"):
        BASE_WINDOW.destroy()
        CARD.RUN_READER.kill()

def SOUND():
    for x in range (3):
        winsound.Beep(2000,300)

def INIT_PROGRAM():
    
    path = pathlib.Path(__file__)
    fpath= path.parent.parent
    os.chdir(fpath)

def INIT_DATA():
    name=datetime.now().strftime('%Y년 %m월.csv'.encode('unicode-escape').decode()).encode().decode('unicode-escape')
    today=datetime.now().strftime(' %m/%d')
    ULIST=[]
    file=open("user_list_RFID.csv",'rt',encoding=("ansi"))
    RAWLIST=list(csv.DictReader(file))
    file.close()
    for x in RAWLIST:
        ULIST.append(USER_DATA(x))
    try:
        save=open(name,'r',encoding=("ansi"))
    except:
        pass
    else:
        print ("save file opened")
        SAVE=list(csv.DictReader(save))
        for x in SAVE[0].keys():
            if x==today:
                for dic in SAVE:
                    for d in ULIST:
                        if d.num==dic["Num"] and d.name==dic["Name"]:
                            if dic[today]=="O":
                                if d.RFID!="":
                                    i=d.RFID
                                else:
                                    i=d.num
                                DATAIN.put(i,block=False)
                            if dic[today]=="NC":
                                nn=dic["Num"]
                                DATAIN.put(nn,block=False)
                            if dic[today]=="O (죽식)":
                                if d.RFID!="":
                                    i=d.RFID
                                else:
                                    i=d.num
                                DATAIN.put(i,block=False)
                                d.menu='죽식'
                            if dic[today]=="NC (죽식)":
                                nn=dic["Num"]
                                DATAIN.put(nn,block=False)
                                d.menu='죽식'
                
        save.close()
    try:
        flag=open("FLAG.txt",'r',encoding=("ansi"))
    except:
        pass
    else:
        readline1=flag.readline()
        readline2=flag.readline()
        if readline1!="":
            if readline2!="":
                globals()[FLAGMSG]=readline2
            l=list(readline1.split(","))
            for n in l:
                for us in ULIST:
                    if us.name==n:
                        us.flag=True
    finally:
        print(f"{DATAIN.qsize()}명 불러오기 완료.")
        return ULIST

class USER_DATA:
    def __init__(self,dict):
        self.num=dict.get('Num')
        self.name=dict.get('Name')
        self.RFID=dict.get('RFID')
        self.att=False
        self.time=""
        self.menu="일반식"
        self.card=True
        self.flag=False
    def Prepare_save(self):
        out=""
        if self.att==True:
            if self.card==True:
                out="O"
            if self.card==False:
                out="NC"
            if self.menu=="죽식":
                out=out+ " (죽식)"
        
        return out

class CARD_READER:
    def __init__(self,queue):
        self.RUN_READER=Process(target=self.Start_reader,args=(queue,))
        self.RUN_READER.start()

    def Clean(self,string):
        result=""
        for x in string:
            if re.search('[A-Z]',x):
                result=result + x
            if re.search('[0-9]',x):
                result=result + x
        return result
    
    def Start_reader(self,queue):
        try:
            ser = serial.Serial(port, baud_rate, timeout=None)
        except:
            print('no device connected')
            time.sleep(2)
            self.Start_reader(queue)
        else:
            go=True
            while go==True:
                try:
                    rd=ser.readline().decode('ansi').strip()
                except:
                    print("lost connection")
                    time.sleep(2)
                    self.Start_reader(queue)
                    go=False
                else:
                    if rd!="":
                        ret=self.Clean(rd)
                        if ret!="":
                            queue.put(ret,block=False)

class START_FRAME(tk.Frame):
    def __init__(baseframe,container):
        super().__init__(container)

        basetextframe=tk.Frame(baseframe)
        basetext=tk.Text(basetextframe)
        basetext.insert(tk.INSERT,INFOTEXT)
        basetext.config(state="disabled")

        basetext.pack(fill=tk.BOTH,expand=tk.TRUE)

        basebtnframe=tk.Frame(baseframe)
        basecntscrnbt=tk.Button(basebtnframe,text="시작",command=baseframe.GOTO_Count)
        baseeditbt=tk.Button(basebtnframe,text="이용자관리",command=baseframe.GOTO_EDIT)
        baseabortbt=tk.Button(basebtnframe,text="종료",command=Abort_master)

        basecntscrnbt.pack(side=tk.TOP,padx=10,pady=10,fill=tk.X)
        baseeditbt.pack(side=tk.TOP,padx=10,pady=10,fill=tk.X)
        baseabortbt.pack(side=tk.TOP,padx=10,pady=10,fill=tk.X)

        basetextframe.pack(side=tk.LEFT,padx=10,pady=10,fill=tk.BOTH,expand=tk.TRUE)
        basebtnframe.pack(side=tk.LEFT,anchor=tk.N,padx=10,pady=10,fill=tk.Y)

    def GOTO_Count(baseframe):
        baseframe.pack_forget()
        BASE_WINDOW.bind("<Return>",lambda event:COUNT_WINDOW.Enterbox())
        BASE_WINDOW.bind("m",lambda event:COUNT_WINDOW.Menu_button())
        BASE_WINDOW.bind("ww",lambda event:COUNT_WINDOW.Manualsave())
        COUNT_WINDOW.pack(fill=tk.BOTH,expand=tk.TRUE)
    
    def GOTO_EDIT(baseframe):
        baseframe.pack_forget()
        BASE_WINDOW.bind("<Return>",lambda event:EDIT_WINDOW.Search())
        EDIT_WINDOW.pack(fill=tk.BOTH,expand=tk.TRUE)

class COUNT_FRAME(tk.Frame):
    def __init__(cntframe,container):
        super().__init__(container)
        bodyframe=tk.Frame(cntframe)
        cntframe.bodytext=ScrolledText(bodyframe,state="disabled")
        cntframe.bodytext.pack(fill=tk.BOTH,expand=tk.TRUE)

        infoframe=tk.Frame(cntframe)
        infoframetitle=tk.Label(infoframe,text="이용자 정보")

        datashow=tk.Frame(infoframe,borderwidth=1.5,relief="raised")
        cntframe.infoname=tk.Label(datashow,text=f"이름: ",justify=tk.LEFT,anchor=tk.W)
        cntframe.infonum=tk.Label(datashow,text=f"번호: ",justify=tk.LEFT,anchor=tk.W)
        cntframe.infoatt=tk.Label(datashow,text="이용 시간:",justify=tk.LEFT,anchor=tk.W)
        cntframe.infomenu=tk.Label(datashow,text=f"[죽식 이용자: 0명]",justify=tk.LEFT,anchor=tk.W)
        cntframe.pplcnt=tk.Label(datashow,text=f"금일 이용자: ")

        cntframe.pplcnt.pack(side=tk.BOTTOM,fill=tk.X,expand=tk.TRUE)
        cntframe.infomenu.pack(side=tk.BOTTOM,fill=tk.X,expand=tk.TRUE)
        cntframe.infoatt.pack(side=tk.BOTTOM,fill=tk.X,expand=tk.TRUE)
        cntframe.infoname.pack(side=tk.BOTTOM,fill=tk.X,expand=tk.TRUE)
        cntframe.infonum.pack(side=tk.BOTTOM,fill=tk.X,expand=tk.TRUE)

        infobtnframe=tk.Frame(infoframe,border=1.5,relief="groove")
        menubt=tk.Button(infobtnframe,text="죽식 선택",command=cntframe.Menu_button)
        cntframe.infoinput=tk.Entry(infobtnframe)
        infoenter=tk.Button(infobtnframe,text="입력",command=cntframe.Enterbox)
        cancelbtn=tk.Button(infobtnframe,text="등록취소",command=cntframe.Cancelbutton)
        svbt=tk.Button(infobtnframe,text="저장",command=cntframe.Manualsave)

        infoenter.pack(side=tk.BOTTOM,pady=5,padx=5,fill=tk.BOTH,expand=tk.TRUE)
        cntframe.infoinput.pack(side=tk.BOTTOM,padx=5,fill=tk.BOTH,expand=tk.TRUE)
        svbt.pack(side=tk.BOTTOM,padx=5,fill=tk.BOTH,expand=tk.TRUE)
        cancelbtn.pack(side=tk.BOTTOM,padx=5,fill=tk.BOTH,expand=tk.TRUE)
        menubt.pack(side=tk.BOTTOM,padx=5,pady=5,fill=tk.BOTH,expand=tk.TRUE)

        infoframetitle.pack(side=tk.TOP,pady=5,fill=tk.X,expand=tk.TRUE)
        datashow.pack(side=tk.TOP,fill=tk.X)
        infobtnframe.pack(side=tk.BOTTOM,anchor=tk.S,fill=tk.X,expand=tk.TRUE)

        bodyframe.pack(side=tk.LEFT,padx=5,pady=5,fill=tk.BOTH,expand=tk.TRUE)
        infoframe.pack(side=tk.RIGHT,padx=5,pady=5,fill=tk.BOTH)
        cntframe.TOT_CNT=0
        cntframe.MENU_CNT=0
        cntframe.CURRENT=None
        cntframe.Look_for_Data()
        cntframe.Autosave()

        for x in USER_DIR:
            if x.menu=="죽식":
                cntframe.MENU_CNT+=1

    def Write_File(cntframe,list,filename):
        keys=list[0].keys()
        with open(filename,'w',newline='',encoding="ansi") as output:
            dict_writer = csv.DictWriter(output,keys)
            dict_writer.writeheader()
            dict_writer.writerows(list)
            output.close()

    def GET_TIME(cntframe):
        x=datetime.now()
        t=x.strftime("%H시 %M분".encode('unicode-escape').decode()).encode().decode('unicode-escape')
        return t
    
    def Autosave(cntframe):
        if cntframe.winfo_ismapped():
            cntframe.Save_visitorlog()
            st=f"{cntframe.GET_TIME()}: 저장됨 (자동저장)"
            cntframe.bodytext.config(state="normal")
            cntframe.bodytext.insert("1.0",f"{st}\n")
            cntframe.bodytext.config(state="disabled")
        cntframe.after(60000,cntframe.Autosave)
    
    def Manualsave(cntframe):
        if cntframe.winfo_ismapped():
            cntframe.Save_visitorlog()
            st=f"{cntframe.GET_TIME()}: 저장됨 (수동저장)"
            cntframe.bodytext.config(state="normal")
            cntframe.bodytext.insert("1.0",f"{st}\n")
            cntframe.bodytext.config(state="disabled")
    
    def Save_visitorlog(cntframe):
        dt=datetime.now()
        bun=dt.strftime("%Y년 %m월 %d일 backup.csv".encode('unicode-escape').decode()).encode().decode('unicode-escape')
        fn=dt.strftime("%Y년 %m월.csv".encode('unicode-escape').decode()).encode().decode('unicode-escape')
        today=dt.strftime(" %m/%d")
        try:
            s=open(fn,'r',encoding=("ansi"))
        except:
            badlist=True
        else:
            badlist=False
            sd=list(csv.DictReader(s))
            for d in sd:
                for u in USER_DIR:
                    if u.num==d["Num"]:
                        if u.name!=d["Name"]:
                            badlist=True
                            break
                    if badlist==True:
                        break
            if badlist:
                cntframe.Write_File(sd,bun)
            if badlist==False:
                for d in sd:
                    for u in USER_DIR:
                        if u.num==d["Num"]:
                            d.update({today:u.Prepare_save()})
                cntframe.Write_File(sd,fn)
        finally:
            if badlist:
                l=[]
                for u in USER_DIR:
                    d={'Num':u.num,
                       "Name":u.name,
                       today:u.Prepare_save()}
                    l.append(d)
                cntframe.Write_File(l,fn)

    def Update_DATA(cntframe,LIST):#[st,name,num,menu,time]
        cntframe.bodytext.config(state="normal")
        cntframe.bodytext.insert("1.0",f"{LIST[0]}\n")
        cntframe.bodytext.config(state="disabled")
        cntframe.infoname.config(text=f"이름: {LIST[1]}")
        cntframe.infomenu.config(text=f"{LIST[3]} [죽식: {str(cntframe.MENU_CNT)} 명]")
        cntframe.infonum.config(text=f"번호: {LIST[2]}")
        cntframe.infoatt.config(text=f"이용 시간:{LIST[4]}")
        cntframe.pplcnt.config(text=f"금일 이용자: {str(cntframe.TOT_CNT)} 명")
    
    def Look_for_Data(cntframe):
        if cntframe.winfo_ismapped():
            try:
                d=DATAIN.get_nowait()
            except:
                cntframe.after(100,cntframe.Look_for_Data)
            else:
                if d!="":
                    print (f"fetching item from queue: {d}")
                    cntframe.Data_Handling(d)
        else:
            cntframe.after(100,cntframe.Look_for_Data)

    def Enterbox(cntframe):
        inp=cntframe.infoinput.get()
        cntframe.infoinput.delete(0,tk.END)
        if inp!="":
            DATAIN.put(inp,block=False)
    
    def Cancelbutton(cntframe):
        if cntframe.CURRENT!=None:
            cntframe.CURRENT.att=False
            if cntframe.CURRENT.menu=='죽식':
                cntframe.MENU_CNT-=1
            cntframe.CURRENT.menu='일반식'
            cntframe.CURRENT.time=''
            cntframe.CURRENT.card=True
            st=f"{cntframe.CURRENT.name}: 취소되었습니다."
            cntframe.CURRENT=None
            cntframe.TOT_CNT-=1
            cntframe.Update_DATA([st,"","","",""])

    def Menu_button(cntframe):
        if cntframe.CURRENT!=None:
            if cntframe.CURRENT.menu=="일반식":
                cntframe.CURRENT.menu="죽식"
                cntframe.MENU_CNT+=1
            else:
                cntframe.CURRENT.menu="일반식"
                cntframe.MENU_CNT-=1
            st=f'{cntframe.CURRENT.name}: 메뉴 변경'
            cntframe.infoinput.delete(0,tk.END)
            cntframe.Update_DATA([st,cntframe.CURRENT.name,cntframe.CURRENT.num,cntframe.CURRENT.menu,cntframe.CURRENT.time])

    def Same_name(cntframe,d):
        def selection():
            globals()[SAMENAME]=None
            sel=lb.curselection()
            if sel!=():
                n=sel[0]
                globals()[SAMENAME]=d[n]
                p.destroy()
        globals()[SAMENAME]=None
        p=tk.Toplevel(BASE_WINDOW)
        p.title("동명이인 존재")
        l=tk.Label(p,text="동명이인이 존재합니다.")
        lb=tk.Listbox(p)
            
        for x in d:
            lb.insert(tk.END,f"{x.num}: {x.name}")
        bt=tk.Button(p,text="선택",command=selection)
        l.pack()
        lb.pack()
        bt.pack()
        BASE_WINDOW.wait_window(p)

    def Data_Handling(cntframe,data):
        def No_data(d):
            def okbtf():
                newinfo=inp.get()
                rep=None
                mname=[]
                cnt=0
                for x in USER_DIR:
                    if newinfo == x.num:
                        rep=x
                        break
                    if newinfo == x.name:
                        rep=x
                        mname.append(x)
                        cnt+=1
                if cnt>1:
                    cntframe.Same_name(mname)
                    if globals()[SAMENAME]!=None:
                        rep=globals()[SAMENAME]
                if rep==None:
                    warning.destroy()
                    cntframe.bodytext.config(state="normal")
                    cntframe.bodytext.insert("1.0",f"{newinfo}: 등록 실패\n")
                    cntframe.bodytext.config(state="disabled")
                if rep!=None:
                    msgbx=messagebox.askyesno(title='경고',message=f"{rep.name}님의 정보가 등록/교체됩니다.")
                    if msgbx:
                        rep.RFID=d
                        cntframe.bodytext.config(state="normal")
                        cntframe.bodytext.insert("1.0",f"{rep.name}: 등록되었습니다\n")
                        cntframe.bodytext.config(state="disabled")
                        f=open("user_list_RFID.csv",'r',encoding=("ansi"))
                        fd=list(csv.DictReader(f))
                        dt=datetime.now()
                        bun=dt.strftime("user_list_RFID_backup(%Y년 %m월 %d일).csv".encode('unicode-escape').decode()).encode().decode('unicode-escape')
                        cntframe.Write_File(fd,bun)
                        ld=[]
                        for x in USER_DIR:
                            dd={"Num":x.num,"Name":x.name,"RFID":x.RFID}
                            ld.append(dd)
                        cntframe.Write_File(ld,"user_list_RFID.csv")
                        DATAIN.put(rep.RFID,block=False)
                        warning.destroy()
                    else:
                        cntframe.bodytext.config(state="normal")
                        cntframe.bodytext.insert("1.0",f"등록이 취소되었습니다\n")
                        cntframe.bodytext.config(state="disabled")
                        warning.destroy()

            warning=tk.Toplevel(BASE_WINDOW)
            warning.title("등록되지 않은 카드")
            lab=tk.Label(warning,text="이용자 정보 등록")
            inp=tk.Entry(warning)
            okbt=tk.Button(warning,text="입력",command=okbtf)
            lab.pack(padx=5,pady=5)
            inp.pack(padx=5,pady=5)
            okbt.pack(padx=5,pady=5)
            warning.bind("<Return>",lambda event:okbtf())
            BASE_WINDOW.wait_window(warning)
            

        name=[]
        namecnt=0
        uid=None
        for x in USER_DIR:
            if x.RFID==data:
                uid=x
                break
            if x.num==data:
                print (f"Number {data} attained")
                uid=x
                uid.card=False
                break
            if x.name==data:
                uid=x
                name.append(x)
                namecnt+=1
            if namecnt>1:
                cntframe.Same_name(name)
                if globals()[SAMENAME]!=None:
                    uid=globals()[SAMENAME]
        if uid==None:
            if len(data)==10:
                SOUND()
                No_data(data)
            else:
                if re.search('[0-9]',data):
                    st=f"등록되지 않은 이용자 입니다"
                    cntframe.bodytext.config(state="normal")
                    cntframe.bodytext.insert("1.0",f"{st}\n")
                    cntframe.bodytext.config(state="disabled")
                    SOUND()
                else:
                    l=[]
                    for x in USER_DIR:
                        cnt=0
                        judata=list(j2hcj(h2j(x.name)))
                        jdata=list(j2hcj(h2j(data)))
                        for char in judata:
                            for c in jdata:
                                if c==char:
                                    cnt+=1
                                    judata.remove(char)
                                    jdata.remove(c)
                                    break
                        if cnt>1:
                            l.append(x)



                    if l!=[]:
                        cntframe.Same_name(l)
                        if globals()[SAMENAME]==None:
                            st=f"{data}: 등록되지 않은 이용자 입니다"
                            cntframe.bodytext.config(state="normal")
                            cntframe.bodytext.insert("1.0",f"{st}\n")
                            cntframe.bodytext.config(state="disabled")
                            SOUND()
                        else:
                            g=globals()[SAMENAME]
                            dat=g.num
                            DATAIN.put(dat,block=False)
                            print (f"loaded queue({dat})")

                    else:
                        st=f"{data}: 등록되지 않은 이용자 입니다"
                        cntframe.bodytext.config(state="normal")
                        cntframe.bodytext.insert("1.0",f"{st}\n")
                        cntframe.bodytext.config(state="disabled")
                        SOUND()

        else:
            print(f"{uid.RFID} {uid.name}: data passed")
            if namecnt==1:
                uid.card==False
            
            if uid.att==True:
                st=f"이미 이용하신 이용자 입니다. {uid.name}님 {uid.time}에 이용."
                cntframe.CURRENT=uid
                cntframe.Update_DATA([st,cntframe.CURRENT.name,cntframe.CURRENT.num,cntframe.CURRENT.menu,cntframe.CURRENT.time])
                if uid.flag==True:
                    msg=F'{uid.name}님 {FLAGMSG}'
                    cntframe.bodytext.config(state="normal")
                    cntframe.bodytext.insert("1.0",f"{msg}\n")
                    cntframe.bodytext.config(state="disabled")
                    SOUND()

            if uid.att==False:
                st=f"{uid.num}번 {uid.name}님 확인되었습니다."
                uid.att=True
                uid.time=cntframe.GET_TIME()
                print ("sending to update")
                cntframe.TOT_CNT+=1
                cntframe.Update_DATA([st,uid.name,uid.num,uid.menu,uid.time])
                cntframe.CURRENT=uid
                if uid.flag==True:
                    msg=F'{uid.name}님 {FLAGMSG}'
                    cntframe.bodytext.config(state="normal")
                    cntframe.bodytext.insert("1.0",f"{msg}\n")
                    cntframe.bodytext.config(state="disabled")
                    SOUND()

            

        cntframe.after(10,cntframe.Look_for_Data)
                    
class EDIT_FRAME(tk.Frame):
    def __init__(self,container):
        super().__init__(container)
        self.INFO_LISTBOX=tk.Listbox(self)
        LISTBOXSCROLL=tk.Scrollbar(self.INFO_LISTBOX)
        LISTBOXSCROLL.pack(side=tk.RIGHT,fill=tk.Y,anchor="e")
        self.INFO_LISTBOX.pack(side=tk.RIGHT,fill=tk.BOTH,expand=tk.TRUE, padx=5,pady=10)
        self.Load_info()
        self.SELECTED=None
        INFO_INTERFACE=tk.Frame(self)
        INFO_INTERFACE.pack(side=tk.RIGHT,fill=tk.Y, padx=5,pady=10)
        INFO_DISPLAY=tk.Frame(INFO_INTERFACE)
        INFO_DISPLAY.pack(fill=tk.X,expand=tk.TRUE)
        INFO_BUTTON=tk.Frame(INFO_INTERFACE)
        INFO_BUTTON.pack(fill=tk.X,expand=tk.TRUE)
        self.INFO_ENTER=tk.Entry(INFO_BUTTON)
        INFO_EDITBT=tk.Button(INFO_BUTTON,text="정보 수정",command=self.Edit)
        INFO_DELBT=tk.Button(INFO_BUTTON,text="이용자 삭제",command=self.Delete)
        INFO_SEARCHBT=tk.Button(INFO_BUTTON,text="검색",command=self.Search)
        INFO_RFIDBT=tk.Button(INFO_BUTTON,text="카드 등록",command=self.Card)
        self.INFO_ENTER.pack(fill=tk.X)
        INFO_SEARCHBT.pack(fill=tk.X)
        INFO_EDITBT.pack(fill=tk.X)
        INFO_RFIDBT.pack(fill=tk.X)
        INFO_DELBT.pack(fill=tk.X)
        self.NAME=tk.Label(INFO_DISPLAY,text="이름: ",justify=tk.LEFT,anchor=tk.W)
        self.NUM=tk.Label(INFO_DISPLAY,text="번호",justify=tk.LEFT,anchor=tk.W)
        self.RFIDBOOL=tk.Label(INFO_DISPLAY,text="카드 등록: ",justify=tk.LEFT,anchor=tk.W)
        self.NUM.pack(fill=tk.X)
        self.NAME.pack(fill=tk.X)
        self.RFIDBOOL.pack(fill=tk.X)
        self.INFO_LISTBOX.bind('<<ListboxSelect>>', lambda event:self.Selected())

        

    def Load_info(self):
        self.INFO_LISTBOX.delete(0,tk.END)
        for x in USER_DIR:
            self.INFO_LISTBOX.insert(tk.END,f"{x.num}: {x.name}")
    
    def Search(self):
        EN=self.INFO_ENTER.get()
        self.INFO_ENTER.delete(0,tk.END)
        if EN!="":
            for x in range (len(USER_DIR)):
                if USER_DIR[x].name==EN or USER_DIR[x].num==EN:
                    self.INFO_LISTBOX.select_clear(0,tk.END)
                    self.INFO_LISTBOX.select_set(x)
                    self.INFO_LISTBOX.see(x)
                    self.Selected()
                    break
    
    def Edit(self):
        def Enter():
            x=inpname.get()
            inpname.delete(0,tk.END)
            if x!="":
                if messagebox.askokcancel("경고",f"정보를 수정합니다.\n{self.SELECTED.name} -> {x}"):
                    self.SELECTED.name=x
                    self.SELECTED.RFID=""
                    ld=[]
                    for x in USER_DIR:
                        dd={"Num":x.num,"Name":x.name,"RFID":x.RFID}
                        ld.append(dd)
                    COUNT_WINDOW.Write_File(ld,"user_list_RFID.csv")
                    p.destroy()
                    self.Load_info()


    
        if self.SELECTED!=None:
            if messagebox.askokcancel("경고",f"{self.SELECTED.name}님의 정보를 수정합니다."):
                p=tk.Toplevel(BASE_WINDOW)
                lnum=tk.Label(p,text=f"번호: {self.SELECTED.num}")
                lnum.pack(padx=5,pady=5)
                nameframe=tk.Frame(p)
                nameframe.pack(padx=5,pady=5)


                lname=tk.Label(nameframe,text="이름")
                inpname=tk.Entry(nameframe)
                lname.pack(side=tk.LEFT)
                inpname.pack(side=tk.LEFT,fill=tk.X,expand=tk.TRUE)
                p.bind("<Return>",lambda event:Enter())
                BASE_WINDOW.wait_window(p)
                p.bind("<Return>",lambda event:COUNT_WINDOW.Enterbox())
            
    def Selected(self):
        x=self.INFO_LISTBOX.curselection()
        self.SELECTED=USER_DIR[x[0]]
        self.Display_current()
    
    def Display_current(self):
        if self.SELECTED!=None:
            self.NAME.config(text=f"이름: {self.SELECTED.name}")
            self.NUM.config(text=f"번호: {self.SELECTED.num}")
            if self.SELECTED.RFID!="":
                self.RFIDBOOL.config(text=f"카드 등록: 등록됨")
            else:
                self.RFIDBOOL.config(text=f"카드 등록: 등록되지 않음")

    def Delete(self):
        if self.SELECTED!=None:
            if messagebox.askokcancel("경고",f"이용자 정보를 삭제합니다.\n{self.SELECTED.name}"):
                self.SELECTED.name=""
                self.SELECTED.RFID=""
                ld=[]
                for x in USER_DIR:
                    dd={"Num":x.num,"Name":x.name,"RFID":x.RFID}
                    ld.append(dd)
                COUNT_WINDOW.Write_File(ld,"user_list_RFID.csv")
                self.Load_info()

    def Card(self):
        def reader():
            try:
                k=DATAIN.get_nowait()
            except:
                p.after(100,reader)
            else:
                self.SELECTED.RFID=k
                ld=[]
                for x in USER_DIR:
                    dd={"Num":x.num,"Name":x.name,"RFID":x.RFID}
                    ld.append(dd)
                COUNT_WINDOW.Write_File(ld,"user_list_RFID.csv")
                p.destroy()
                self.Load_info()


        if self.SELECTED!=None:
            while True:
                try:
                    TRASH=DATAIN.get_nowait()
                except:
                    break

            p=tk.Toplevel(BASE_WINDOW)
            p.title="카드 등록"
            l=tk.Label(p,text="카드 등록")
            l.pack()
            reader()
            BASE_WINDOW.wait_window(p)

class GUI(tk.Tk):
    def __init__(self):
        self.QUEUE=Queue()
        super().__init__()
        self.title("경로식당 프로그램")
        self.option_add("*font","명조 18")
        self.state("zoomed")
        menubar=tk.Menu(self)
        tool_menu=tk.Menu(menubar,tearoff=False)
        tool_menu.add_command(label="금일 이용자 검색",command=self.Finder)
        tool_menu.add_command(label='도움말',command=lambda event:webbrowser.open('https://github.com/bug4tti16/wooman-restraunt-AIO/blob/main/README.md'))
        menubar.add_cascade(label="도구",menu=tool_menu,underline=0)
        self.config(menu=menubar)
        self.protocol("WM_DELETE_WINDOW", Abort_master)
        self.bind("R<Return>",lambda event:Abort_master())

        
    def Finder(self):

        def Enter():
            enter=e.get()
            if enter!="":
                e.delete(0,tk.END)
                uid=None
                namecnt=0
                name=[]
                for u in USER_DIR:
                    if enter==u.num:
                        uid=u
                        break
                    if enter==u.name:
                        uid=u
                        namecnt+=1
                        name.append(u)
                if namecnt>1:
                    uid=None
                    COUNT_FRAME.Same_name(name)
                    if SAMENAME!=None:
                        uid=SAMENAME
                if uid==None:
                    name=enter
                    msg="이용자 정보 없음"
                    
                if uid!=None:
                    name=uid.name
                    if uid.att:
                        
                        msg=f"{uid.time}에 이용"
                    else:
                        msg=f"식당 미이용"
                b=messagebox.askokcancel(name,msg)
                if b==True or b==False:
                    pop.wm_transient(BASE_WINDOW)
                    e.focus()

    
        pop=tk.Toplevel(self)
        pop.title("금일 이용자 검색")
        l=tk.Label(pop,text="금일 이용자 검색")
        e=tk.Entry(pop)
        l.pack()
        e.pack()
        e.focus()
        pop.bind("<Return>",lambda event:Enter())
        self.wait_window(pop)




        

                    
                
                        




if __name__=="__main__":
    DATAIN=Queue()
    INIT_PROGRAM()
    USER_DIR=INIT_DATA()
    CARD=CARD_READER(DATAIN)
    BASE_WINDOW=GUI()
    COUNT_WINDOW=COUNT_FRAME(BASE_WINDOW)
    START_WINDOW=START_FRAME(BASE_WINDOW)
    EDIT_WINDOW=EDIT_FRAME(BASE_WINDOW)
    START_WINDOW.pack(fill=tk.BOTH,expand=tk.TRUE)
    BASE_WINDOW.mainloop()
