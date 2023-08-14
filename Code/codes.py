from threading import Thread
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import os,csv,pathlib,serial,re
from datetime import datetime
import locale
import winsound


#config
infotext="""
경로식당 프로그램을 시작합니다.
인원관리 프로그램은 작업이 더 필요해 기존 프로그램 사용 바랍니다.
카드 등록 방법은 기존과 동일합니다.

1분마다 자동저장 됩니다
수동저장: ㅈㅈ
끝: ㄲ + 엔터
안될 시, 한/영 키 누르고 다시시도

문의사항은 임성호 사회복무요원에게!! <3<3"""
port = 'COM3'
baud_rate = 9600


#data
class Userlist:
    def __init__(self,dict):
        self.num=dict.get('Num')
        self.name=dict.get('Name')
        self.RFID=dict.get('RFID')
        self.att=False
        self.time=""
        self.menu="일반식"
        self.card=True
    def checkdata(self,item):
        if self.num==item or self.name==item or self.RFID==item:
            return self.name


#basevar
locale.setlocale(locale.LC_CTYPE, 'korean')
weekday_dict = {
    0: '월요일',
    1: '화요일',
    2: '수요일',
    3: '목요일',
    4: '금요일',
    5: '토요일',
    6: '일요일'
}
ampm_dict = {
    'AM': '오전',
    'PM': '오후'
}
roottime=datetime.now()
longformattime=roottime.strftime("%Y년 %m월 %d일 ")+weekday_dict[roottime.weekday()]
shortformattime=roottime.strftime("%m/%d")
shortformattime2=roottime.strftime("%m월 %d일")
visitorlog=""
hotpotato=""
coldpotato=""
rawname=""
rawnum=""
rawtime=""
rawmenu=""
nocard=False
cnt=0
newinfo=""
pause=True

editname=""
editnum=""
cardbool=""
new_card=""
new_name=""
rd=""



#디렉토리 수정
path = pathlib.Path(__file__)
fpath= path.parent.parent
os.chdir(fpath)




#기본 함수
def clean(string):
    result=""
    for x in string:
        if re.search('[A-Z]',x):
            result=result + x
        if re.search('[0-9]',x):
            result=result + x
    return result

#파일 저장
def writefile(list,filename):
    keys=list[0].keys()
    with open(filename,'w',newline='',encoding="ansi") as output:
        dict_writer = csv.DictWriter(output,keys)
        dict_writer.writeheader()
        dict_writer.writerows(list)

#파일 열기
def readfile(Fname):
    n=open(Fname,"r")
    out=list(csv.DictReader(n))
    n.close
    return out

#이름 찾기
def fetchname(list,item):
    for x in list:
        k=globals()[x].checkdata(item)
        if k!=None:
            return k
    if k==None:
        return ""

#시간 표출
def whattime():
    x=datetime.now()
    t=ampm_dict[x.strftime("%p")]+x.strftime(" %I시 %M분")
    return t


#글 상자 업데이트
def add_text():
    global bodytext, visitorlog
    bodytext.config(state="normal")
    bodytext.insert("1.0",visitorlog)
    bodytext.config(state="disabled")
    bodytext.update()

def live_info():
    infoname.config(text=f"이름: {rawname}")
    infonum.config(text=f"번호: {rawnum}")
    infoatt.config(text=rawtime)
    infomenu.config(text=f"{rawmenu}")
    pplcnt.config(text=f"금일 이용자: {str(cnt)}")
    datashow.update()


ser = serial.Serial(port, baud_rate, timeout=1)
#카드 리더
def read_card():
    global hotpotato
    if currentwindow==cntframe:
        data = ser.readline().decode('utf-8').strip()
        if re.search('[0-9]',data):
            card_reader=clean(data)
            hotpotato=card_reader
    start.after(100,read_card)


#카드 정보 대기열로 이동
def check_coldpotato_poll():
    if currentwindow==cntframe:
        global hotpotato,coldpotato
        if hotpotato!="" and coldpotato=="":
            coldpotato=hotpotato
            print (f"({coldpotato})")
            hotpotato=""
            start.after(1,get_data)
        else: start.after(1,check_coldpotato_poll)
    else: start.after(1,check_coldpotato_poll)
#카드 정보로 불러오기
def get_data():
    global alarm,pause,nocard,hotpotato,coldpotato, name_list,rawmenu,rawname,rawnum,rawtime,visitorlog,infoatt,infonum,infoname,infomenu,cnt

    if coldpotato!="" or None:
        he=fetchname(name_list,coldpotato)
        if he!="":
            raw=globals()[he]
            rawname=raw.name
            rawnum=raw.num
            rawmenu=raw.menu
            if raw.att==True:
                visitorlog=f"{rawname}: 이미 이용하신 이용자 입니다. [{raw.time}에 이용]\n"
                for x in range (3):
                    winsound.Beep(900,300)
            if raw.att==False:
                raw.att=True
                raw.time=whattime()
                rawtime=f"{raw.time}에 이용"
                visitorlog=f"{rawname}님 확인되었습니다.\n"
                cnt+=1
                if nocard:
                    raw.card=False
                    print(raw.card)
        if he=="":
            for x in range (3):
                winsound.Beep(2000,300)
            visitorlog="등록되지 않은 이용자입니다.\n"
            if nocard==False:
                def okbtent(event):
                    okbtf()
                def okbtf():
                    global pause, coldpotato,visitorlog,start
                    newinfo=inp.get()
                    name=fetchname(name_list,newinfo)
                    if name=="" or None:
                        visitorlog=f"등록 실패: {visitorlog}"
                        warning.destroy()

                    else:
                        def agree(event):
                            agreebt()
                        def agreebt():
                            global visitorlog
                            globals()[name].RFID=coldpotato
                            x=readfile("user_list_RFID.csv")
                            writefile(x,f"user_list_backup_{shortformattime2} {whattime()}.csv")
                            for d in x:
                                if d["Name"]==name:
                                    d["RFID"]=coldpotato
                                    break
                            writefile(x,"user_list_RFID.csv")
                            visitorlog=f"{name}님 카드 정보 등록\n"
                            warning.destroy()
                        def nobt():
                            global  visitorlog
                            visitorlog="카드 등록 취소\n"
                            warning.destroy()
                            
                        warning.unbind("<Return>")
                        lab.destroy()
                        inp.destroy()
                        okbt.destroy()
                        check_label=tk.Label(warning,text=f"{name}님의 정보가 등록/교체됩니다.")
                        check_btnframe=tk.Frame(warning)
                        check_y=tk.Button(check_btnframe,text="예",command=agreebt)
                        check_n=tk.Button(check_btnframe,text="아니요",command=nobt)
                        check_y.pack(side=tk.LEFT, padx=5,pady=10)
                        check_n.pack(side=tk.LEFT, padx=5,pady=10)
                        check_label.pack()
                        check_btnframe.pack(padx=5)
                        warning.bind("<Return>",agree)

                warning=tk.Toplevel(start)
                warning.title("등록되지 않은 카드")
                lab=tk.Label(warning,text="이용자 정보 등록")
                inp=tk.Entry(warning)
                okbt=tk.Button(warning,text="입력",command=okbtf)
                lab.pack(padx=5,pady=5)
                inp.pack(padx=5,pady=5)
                okbt.pack(padx=5,pady=5)
                warning.bind("<Return>",okbtent)
                start.wait_window(warning)
        coldpotato=""
    if visitorlog!="":
        add_text()
        visitorlog=""
        live_info()
    nocard=False
    start.after(1,check_coldpotato_poll)






#정보 등록
user_list_raw=readfile("user_list_RFID.csv")
name_list=[]
for x in user_list_raw:
    globals()[x.get('Name')]=Userlist(x)
    name_list.append(x.get('Name'))



f="user_list.csv"
if os.path.isfile(f):
    x=readfile(f)
    keyz=x[0].keys()
    for k in keyz:
        if k==shortformattime:
            for d in x:
                raw=globals()[d["Name"]]
                for char in d[shortformattime]:
                    if char=="O" or "N":
                        raw.att=True
                        visitorlog=visitorlog+f"{d['Name']} 확인되었습니다.\n"
                        cnt+=1
                    if char=="N":
                        raw.card=False
                    if char=="죽":
                        raw.menu="죽식"
    visitorlog=f"정보 불러오기 끝 {str(cnt)}명\n{visitorlog}"
print(f"visitorlog:\n{visitorlog}")


def startgui():
    global start
    start.mainloop()

def save():
    f="user_list.csv"
    if os.path.isfile(f):
        x=readfile(f)
    else:
        x=readfile("user_list_RFID.csv")
        for d in x:
            del d["RFID"]

    for d in x:
        check=""
        raw=globals()[d.get("Name")]
        if raw.att==True and raw.card==True:
            check="O"
        if raw.att==True and raw.card==False:
            check="NC"
        if raw.menu=="죽식":
            check=check+"(죽)"
        d[shortformattime]=check
    writefile(x,f)
        
def autosave():
    global visitorlog
    if cnt!=0 and cnt%10==0:
        save()
        visitorlog=f"{whattime()}: 저장 완료 (자동저장)\n"
        add_text()
    start.after(60000,autosave)

def updateinfobox():
    global name_label,num_label,rfid_label
    name_label.configure(text=f"이름: {editname}")
    num_label.configure(text=f"번호: {editnum}")
    rfid_label.configure(text=f"카드 등록여부: {cardbool}")
    infoframe.update()


def savehot(event):
    savebt()
def savebt():
    global visitorlog
    save()
    visitorlog=f"{whattime()}: 저장 완료 (수동저장)\n"
    add_text()

def startcnt():
    global currentwindow,cntframe
    currentwindow.pack_forget()
    cntframe.pack(fill=tk.BOTH,expand=tk.TRUE)
    currentwindow=cntframe

def listbox_data():
    global editlist
    x=readfile("user_list_RFID.csv")
    editlist.delete(0,tk.END)
    for d in x:
        editlist.insert(tk.END,f"{d['Num']}. {d['Name']}")
    editlist.update()

def edit_base():
    global editlist,editname,editnum, cardbool, udl
    if currentwindow==editframe:
        x=editlist.curselection()
        if x!=():
            st=editlist.get(x[0])
            l=st.split(". ")
            raw=globals()[l[1]]
            editname=raw.name
            editnum=raw.num
            if raw.RFID!="":
                cardbool="등록됨"
            else: cardbool="미등록"
            updateinfobox()
    start.after(100,edit_base)



def edit_button():
    global editnum,editname,new_card,new_name


    def newcard():
        global new_card, name_list
        while True:
            x=read_card()
            if x!="":
                check=fetchname(name_list,x)
                if check=="":
                    new_card=x
                    RFIDLabel.configure(text=new_card)
                    print(new_card)
                    break
                else:
                    new_card=""
                    RFIDLabel.configure(text="이미 등록된 카드입니다!!")
                    print(new_card)
                    break


    def delcard():
        global new_card
        new_card="del"
        RFIDLabel.configure(text="카드 정보가 삭제됩니다.")
    
    def sve():
        global rd
        rd=editwin_nameenter.get()
        editpop.destroy()
        bf=tk.Frame(editwarn)
        lab=tk.Label(editwarn,text="데이터가 수정됩니다!!!\n진행하시겠습니까?")
        Yb=tk.Button(bf,text="예",command=realsve)
        Nb=tk.Button(bf,text="아니오",command=editwarn.destroy)
        Yb.pack(side=tk.RIGHT)
        Nb.pack(side=tk.RIGHT)
        lab.pack()
        bf.pack()

    
    def realsve():
        global new_card,rd,udl
        data=readfile("user_list_RFID.csv")
        writefile(data,f"user_list_Backup_{shortformattime2} {whattime()}.csv")
        
        for x in data:
            if x["Num"]==editnum:
                if rd!="":
                    x["Name"]=rd
                if new_card!="":
                    x["RFID"]=new_card
                if new_card=="del":
                    x["RFID"]=""
        writefile(data,"user_list_RFID.csv")
        new_card=""
        rd=""
        listbox_data()
        editwarn.destroy()
    
        

        


    
    if editname!="":
        new_card=f"카드정보: {cardbool}"
        editwarn=tk.Toplevel(start)
        editpop=tk.Frame(editwarn)
        editwarn.title("이용자 정보 수정")
        editwin_title=tk.Label(editpop,text=f"이용자정보 수정\n{editnum}번")
        enterboxframe=tk.Label(editpop)

        editwin_nameenter=tk.Entry(enterboxframe)
        nameenter_Label=tk.Label(enterboxframe,text="이름",justify=tk.LEFT,anchor=tk.W)
        editwin_nameenter.pack(side=tk.RIGHT, fill=tk.X, expand=tk.TRUE)
        nameenter_Label.pack(side=tk.RIGHT)

        edit_buttonframe=tk.Frame(editpop)
        delete_button=tk.Button(edit_buttonframe,text="삭제")
        enter_Buttom=tk.Button(editpop,text="저장",command=sve)
        delete_button.pack(side=tk.LEFT, fill=tk.X, expand=tk.TRUE)
        
        RFIDLabel=tk.Label(editpop,text=new_card)
        RFIDButton=tk.Button(editpop,text="카드등록",command=newcard)
        RFIDdelete=tk.Button(editpop,text="카드삭제",command=delcard)
        cancel_button=tk.Button(editpop,text="취소",command=editpop.destroy)

        editwin_title.pack(padx=5,pady=5)
        enterboxframe.pack(padx=5,fill=tk.BOTH,expand=tk.TRUE)
        RFIDLabel.pack(padx=5,pady=5,fill=tk.X)
        RFIDdelete.pack(padx=5,fill=tk.X)
        RFIDButton.pack(padx=5,pady=5,fill=tk.X)
        enter_Buttom.pack(padx=5,fill=tk.X)
        cancel_button.pack(padx=5,pady=5,fill=tk.X)
        editpop.pack()

def newuser():
    global new_card
    editpop=tk.Toplevel(start)
    editpop.title("신규 이용자 등록")
    editwin_title=tk.Label(editpop,text=f"신규 이용자 등록")
    enterboxframe=tk.Label(editpop)
    enterboxentryframe=tk.Frame(enterboxframe)
    enterboxlabelframe=tk.Frame(enterboxframe)
    editwin_nameenter=tk.Entry(enterboxentryframe)
    editwin_numenter=tk.Entry(enterboxentryframe)
    nameenter_Label=tk.Label(enterboxentryframe,text="이름",justify=tk.LEFT,anchor=tk.W)
    numenter_Label=tk.Label(enterboxentryframe,text="번호",justify=tk.LEFT,anchor=tk.W)
    edit_buttonframe=tk.Frame(editpop)
    delete_button=tk.Button(edit_buttonframe,text="삭제")
    enter_Buttom=tk.Button(edit_buttonframe,text="입력")
    RFIDButton=tk.Button(editpop,text="카드등록")
    

def startedit():
    global currentwindow,editframe
    currentwindow.pack_forget()
    editframe.pack(fill=tk.BOTH,expand=tk.TRUE)
    currentwindow=editframe
    listbox_data()
def gohome():
    global currentwindow,baseframe
    currentwindow.pack_forget()
    baseframe.pack(fill=tk.BOTH,expand=tk.TRUE)
    currentwindow=baseframe

def cancelbt():
    global rawname,rawmenu,rawnum,rawtime,visitorlog
    if rawname!="" or None:
        raw=globals()[rawname]
        raw.att=False
        raw.time=""
        raw.menu="일반식"
        visitorlog=f"{rawname}님 취소되었습니다.\n"
        add_text()
        visitorlog=""
def menuchhot(event):
    menuch()
def menuch():
    global rawmenu,rawname
    print("menu change button pressed")
    if rawname!="" or None:
        raw=globals()[rawname]
        if raw!=None or "":
            if rawmenu=="죽식":
                rawmenu="일반식"
                raw.menu="일반식"

            if rawmenu=="일반식":
                rawmenu="죽식"
                raw.menu="죽식"

            rawmenu=raw.menu
            
    infomenu.config(text=f"{rawmenu}")


def aborthot(event):
    abortbt()
def abortbt():
    start.destroy()

def enterpress(event):
    enterinfo()
def enterinfo():
    global infoinput,hotpotato, nocard
    hotpotato=infoinput.get()
    infoinput.delete(0,tk.END)
    nocard=True

def search():
    def when():
        i=sear_input.get()
        sear_input.destroy()
        sear_button.config(state="disabled")
        name=fetchname(name_list,i)
        if name==None or "":
            sear.destroy()
            start.after(1,search)
        else:
            raw=globals()[name]
            if raw.att==True:
                t=f"{raw.name}: {raw.time}에 이용"
            else:
                t=f"{raw.name}: 식당 미이용"

        sear_label.configure(text=t)
        sear_label.update()
    
    sear=tk.Toplevel(start)
    sear_label=tk.Label(sear,text="금일 이용자 검색")
    sear_input=tk.Entry(sear)
    sear_btnframe=tk.Frame(sear)
    sear_close=tk.Button(sear_btnframe,text="종료",command=sear.destroy)
    sear_button=tk.Button(sear_btnframe,text="검색",command=when)
    sear_button.pack(side=tk.RIGHT,padx=5,fill=tk.X)
    sear_close.pack(side=tk.RIGHT,padx=5,fill=tk.X)
    sear_label.pack(pady=5)
    sear_input.pack(padx=5)
    sear_btnframe.pack(pady=5)
    start.wait_window(sear)
    







#basic window
start=tk.Tk()
start.title("경로식당 프로그램")
start.option_add("*font","명조 18")
start.state("zoomed")
menubar=tk.Menu(start)
tool_menu=tk.Menu(menubar,tearoff=False)
tool_menu.add_command(label="금일 이용자 검색",command=search)
tool_menu.add_command(label="저장",command=savebt)
tool_menu.add_command(label='종료',command=abortbt)
menubar.add_cascade(label="도구",menu=tool_menu,underline=0)
start.config(menu=menubar)

#startpage
baseframe=tk.Frame(start,height=400,width=600)
basetitle=tk.Label(baseframe,text="경로식당 프로그램 시작")

basetextframe=tk.Frame(baseframe)
basetext=tk.Text(basetextframe)
basetext.insert(tk.INSERT,longformattime+infotext)
basetext.config(state="disabled")

basetext.pack(fill=tk.BOTH,expand=tk.TRUE)

basebtnframe=tk.Frame(baseframe)
basecntscrnbt=tk.Button(basebtnframe,text="시작",command=startcnt)
baseeditbt=tk.Button(basebtnframe,text="이용자관리",command=startedit,state="disabled")
baseabortbt=tk.Button(basebtnframe,text="종료",command=abortbt)

basecntscrnbt.pack(side=tk.TOP,padx=10,pady=10,fill=tk.X)
baseeditbt.pack(side=tk.TOP,padx=10,pady=10,fill=tk.X)
baseabortbt.pack(side=tk.TOP,padx=10,pady=10,fill=tk.X)

basetextframe.pack(side=tk.LEFT,padx=10,pady=10,fill=tk.BOTH,expand=tk.TRUE)
basebtnframe.pack(side=tk.LEFT,anchor=tk.N,padx=10,pady=10,fill=tk.Y)


baseframe.pack(fill=tk.BOTH,expand=tk.TRUE)
currentwindow=baseframe

#countframe
cntframe=tk.Frame(start)
cntframetitle=tk.Label(cntframe,text="금일 이용자")
bodyframe=tk.Frame(cntframe)
bodytext=ScrolledText(bodyframe,state="disabled")
bodytext.pack(fill=tk.BOTH,expand=tk.TRUE)
add_text()

infoframe=tk.Frame(cntframe,height=400,width=600)
infoframetitle=tk.Label(infoframe,text="이용자 정보")

datashow=tk.Frame(infoframe,borderwidth=1.5,relief="raised")
infoname=tk.Label(datashow,text=f"이름: {rawname}",justify=tk.LEFT,anchor=tk.W)
infonum=tk.Label(datashow,text=f"번호: {rawnum}",justify=tk.LEFT,anchor=tk.W)
infoatt=tk.Label(datashow,text=rawtime,justify=tk.LEFT,anchor=tk.W)
infomenu=tk.Label(datashow,text=f"{rawmenu}",justify=tk.LEFT,anchor=tk.W)
pplcnt=tk.Label(datashow,text=f"금일 이용자: {str(cnt)}")

pplcnt.pack(side=tk.BOTTOM,fill=tk.X,expand=tk.TRUE)
infomenu.pack(side=tk.BOTTOM,fill=tk.X,expand=tk.TRUE)
infoatt.pack(side=tk.BOTTOM,fill=tk.X,expand=tk.TRUE)
infoname.pack(side=tk.BOTTOM,fill=tk.X,expand=tk.TRUE)
infonum.pack(side=tk.BOTTOM,fill=tk.X,expand=tk.TRUE)

infobtnframe=tk.Frame(infoframe,border=1.5,relief="groove")
menubt=tk.Button(infobtnframe,text="죽식 선택",command=menuch)
infoinput=tk.Entry(infobtnframe)
infoenter=tk.Button(infobtnframe,text="입력",command=enterinfo)
cancelbtn=tk.Button(infobtnframe,text="등록취소",command=cancelbt)
svbt=tk.Button(infobtnframe,text="저장",command=savebt)

infoenter.pack(side=tk.BOTTOM,pady=5,padx=5,fill=tk.BOTH,expand=tk.TRUE)
infoinput.pack(side=tk.BOTTOM,padx=5,fill=tk.BOTH,expand=tk.TRUE)
svbt.pack(side=tk.BOTTOM,padx=5,fill=tk.BOTH,expand=tk.TRUE)
cancelbtn.pack(side=tk.BOTTOM,padx=5,fill=tk.BOTH,expand=tk.TRUE)
menubt.pack(side=tk.BOTTOM,padx=5,pady=5,fill=tk.BOTH,expand=tk.TRUE)

infoframetitle.pack(side=tk.TOP,pady=5,fill=tk.X,expand=tk.TRUE)
datashow.pack(side=tk.TOP,fill=tk.X)
infobtnframe.pack(side=tk.BOTTOM,anchor=tk.S,fill=tk.X,expand=tk.TRUE)


infoframetitle.pack(padx=10,pady=10,fill=tk.X)
bodyframe.pack(side=tk.LEFT,padx=5,pady=5,fill=tk.BOTH,expand=tk.TRUE)
infoframe.pack(side=tk.RIGHT,padx=5,pady=5,fill=tk.BOTH)


#editframe
editframe=tk.Frame(start)
edit_title=tk.Label(editframe,text="경로식당 이용자 정보 수정")
edit_title.pack(fill=tk.X,padx=10,pady=10)

edit_bodyframe=tk.Frame(editframe)
edit_bodyframe.pack(fill=tk.BOTH,expand=tk.TRUE)

listboxframe=tk.Frame(edit_bodyframe,borderwidth=1.5,relief="sunken")
editlist=tk.Listbox(listboxframe, selectmode=tk.SINGLE)
scrollbar=tk.Scrollbar(editlist)
editlist.configure(yscrollcommand = scrollbar.set)
scrollbar.pack(side=tk.RIGHT,fill=tk.Y,expand=tk.TRUE,anchor=tk.E)
editlist.pack(side=tk.RIGHT,fill=tk.BOTH,expand=tk.TRUE)

infodp=tk.Frame(edit_bodyframe,borderwidth=1.5,relief="groove")

infoframe_edit=tk.Frame(infodp,borderwidth=1.5,relief="raised")
name_label=tk.Label(infoframe_edit,text=f"이름: {editname}",justify=tk.LEFT,anchor=tk.W)
num_label=tk.Label(infoframe_edit,text=f"번호: {editnum}",justify=tk.LEFT,anchor=tk.W)
rfid_label=tk.Label(infoframe_edit,text=f"카드 등록여부: {cardbool}",justify=tk.LEFT,anchor=tk.W)
edit_btn=tk.Button(infoframe_edit, text="이용자 정보 수정",command=edit_button)
name_label.pack(fill=tk.BOTH,padx=10,pady=10,expand=tk.TRUE)
num_label.pack(fill=tk.BOTH,padx=10,pady=10,expand=tk.TRUE)
rfid_label.pack(fill=tk.BOTH,padx=10,pady=10,expand=tk.TRUE)
edit_btn.pack(fill=tk.X,padx=10,pady=10,expand=tk.TRUE)

edit_btnframe=tk.Frame(infodp)
backbuttom=tk.Button(edit_btnframe,text="처음으로",command=gohome)
abortbt_edit=tk.Button(edit_btnframe,text="종료",command=abortbt)
abortbt_edit.pack(side=tk.BOTTOM,padx=10,pady=10,fill=tk.X,expand=tk.TRUE)
backbuttom.pack(side=tk.BOTTOM,padx=10,pady=10,fill=tk.X,expand=tk.TRUE)
infoframe_edit.pack(fill=tk.BOTH,padx=10,pady=10,expand=tk.TRUE)
edit_btnframe.pack(fill=tk.X,padx=10,pady=10,expand=tk.TRUE)




listboxframe.pack(side=tk.RIGHT,fill=tk.BOTH,padx=10,pady=10,expand=tk.TRUE)
infodp.pack(side=tk.RIGHT,padx=10,pady=10,fill=tk.Y)
















start.bind("<Return>",enterpress)
start.bind("ww",savehot)
start.bind("R<Return>",aborthot)
start.bind("m",menuchhot)


gui_t=Thread(target=startgui)
gui_t2=Thread(target=check_coldpotato_poll)
read_t=Thread(target=read_card)
save_t=Thread(target=autosave)
edit_t=Thread(target=edit_base)

gui_t2.run()
save_t.run()
edit_t.run()
read_t.run()
gui_t.run()
