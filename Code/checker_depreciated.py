import os
import csv
import serial
import easygui
import re
import sys
import pathlib

#카드번호 포맷 함수
def clean(string):
    result=""
    for x in string:
        if re.search('[A-Z]',x):
            result=result + x
        if re.search('[0-9]',x):
            result=result + x
    return result

#카드 번호 존재확인
def check(list,string,item):
    k=False
    for x in list:
        if string==x.get(item):
            k=True
    return (k)

#카드 번호 등록
def update(list,string,newdata,para1,para2):
    for x in list:
        if string==x.get(para1):
            x.update({para2:newdata})

#저장
def save(list,filename):
    keys=list[0].keys()
    with open(filename,'w',newline='') as output:
        dict_writer = csv.DictWriter(output,keys)
        dict_writer.writeheader()
        dict_writer.writerows(list)




path = pathlib.Path(__file__)
parent= path.parent.parent
os.chdir(parent)

while True:
    cont=True
    
    while cont==True:
        title="경로 식당 이용자 카드 시스템"
        msg="\n\n파일 생성: 새로운 엑셀 파일 만들기 \n이용자 등록: 새로운 이용자 추가 (**덮어쓰기 에러) \n이용자 검색: 이용자별 카드번호, RFID 확인"
        choices=["파일 생성", "이용자 등록", "이용자 검색","종료"]

        selection=easygui.buttonbox(msg,title,choices)

        if selection=="파일 생성":
            msg="이 절차는 기존 유저 목록을 초기화 합니다!!"
            title="경고"
            if easygui.ccbox(msg,title):
                pass
            else:
                break
            if easygui.ccbox("user_list_RFID.csv 파일이 삭제됩니다.",title):
                pass
            else:
                break
            #기존 파일 삭제
            if os.path.isfile("user_list_RFID.csv"):
                os.remove("user_list_RFID.csv")
            
            
            msg="기존 리스트를 불러오겠습니까?"
            if easygui.ynbox(msg):
                file=easygui.fileopenbox("파일 선택","","*.csv")
                if file!=None:
                    fname=open(file,'r')
                    data=list(csv.DictReader(fname))
                    fname.close()
                    key=list(data[0].keys())
                    title="데이터 지정"
                    msg1="회원번호 데이터 지정"
                    msg2="회원명 데이터 지정"
                    msg3="카드 데이터 지정"
                    T=easygui.ynbox("RFID 카드 데이터가 있나요?")
                    choice1=easygui.choicebox(msg1,title,key)
                    choice2=easygui.choicebox(msg2,title,key)
                    
                    if T==True:
                        choice3=easygui.choicebox(msg3,title,key)
                        for x in data:
                            for y in key:
                                if y!=choice1 and y!=choice2 and y!=choice3:
                                    x.pop(y)
                                if y==choice1 and y!="Num":
                                    k=x[choice1]
                                    x.update({"Num":k})
                                    x.pop(y)
                                if y==choice2 and y!="Name":
                                    k=x[choice2]
                                    x.update({"Name":k})
                                    x.pop(y)
                                if y==choice3 and y!="RFID":
                                    k=x[choice3]
                                    x.update({"RFID":k})
                                    x.pop(y)
                    
                    if T==False:
                        for x in data:
                            for y in key:
                                if y!=choice1 and y!=choice2:
                                    x.pop(y)
                                if y==choice1 and y!="Num":
                                    k=x[choice1]
                                    x.update({"Num":k})
                                    x.pop(y)
                                if y==choice2 and y!="Name":
                                    k=x[choice2]
                                    x.update({"Name":k})
                                    x.pop(y)
                                x.update({"RFID":""})
                    
                    save(data,"user_list_RFID.csv")
                    msg="user_list_RFID.csv 생성 완료\n경로식당 폴더 확인"
                    easygui.msgbox(msg)
            else:
                data=[{"Num":"","Name":"","RFID":""}]
                save(data,"user_list_RFID.csv")

        if selection=="이용자 등록":
            sanity_check=os.path.isfile("user_list_RFID.csv")
            if sanity_check==False:
                msg="이용자 파일이 없습니다. 파일 생성을 해주세요!!"
                easygui.msgbox(msg)
            if sanity_check==True:
                file="user_list_RFID.csv"
                fname=open(file,'r')
                data=list(csv.DictReader(fname))
                fname.close()
                msg="신규 이용자 정보를 입력해 주세요"
                title="신규 이용자 등록"
                fieldNames=["이름","카드번호"]
                while True:
                    value=easygui.multenterbox(msg,title,fieldNames)
                    if value==None:
                        break
                    if value[0]!="" and value[1]!="":
                        name=str(value[0])
                        num=str(value[1])
                        gut=False
                        for x in data:
                            if x["Num"]==num:
                                msg4="이미 등록된 정보가 있습니다.\n덮어쓰시겠습니까?"
                                title3="경고"
                                if easygui.ynbox(msg4,title3):
                                    x["Num"]=num
                                    x["Name"]=name
                                    if data[0]=={"Num":"","Name":"","RFID":""}:
                                        data.pop(0)
                                    save(data,"user_list_RFID.csv")
                                    msg5="변경 내용이 저장되었습니다"
                                    gut=True
                                    easygui.msgbox(msg5,"알림")
                                    break
                                else:
                                    gut=True
                                    easygui.msgbox("이용자 등록이 취소되었습니다","알림")
                                    break
                                
                        if gut==False:
                            data.append({"Num":num,"Name":name,"RFID":""})
                            if data[0]=={"Num":"","Name":"","RFID":""}:
                                data.pop(0)
                            save(data,"user_list_RFID.csv")
                            msg5="변경 내용이 저장되었습니다"
                            easygui.msgbox(msg5)
                            break
                        break
                            
                    else:
                        error="데이터를 입력해 주세요"
                        easygui.msgbox(error,"입력 오류")
            
        if selection=="종료":
            list1=[]
            list2=[]
            newlist=["Num,Name,RFID\n"]
            file=open("user_list_RFID.csv","r")
            for x in file:
                list1.append(x)
            file.close()
            for x in list1:
                raw=x.split(",")[0]
                if raw!="Num":
                    num=int(raw)
                    list2.append(num)
            list2.sort()
            count=0
            for x in range (list2[-1]):
                count=count+1
                for y in list1:
                    raw=y.split(",")[0]
                    if raw!="Num":
                        num=int(raw)
                        if count==num:
                            newlist.append(y)
            filenew=open("User_list_RFID.csv","w")
            for x in newlist:
                filenew.write(x)
            filenew.close()
            os._exit(0)

        if selection=="이용자 검색":
            file="user_list_RFID.csv"
            fname=open(file,'r')
            data=list(csv.DictReader(fname))
            fname.close()
            title=selection
            while True:
                msg="카드번호 혹은 이름을 입력하시오."
                Valid_data=False
                num=False
                input = easygui.enterbox(msg,title)
                if input==None:
                    break
                for x in input:
                    if re.search('[0-9]',x):
                        num=True
                        break
                if num==True:
                    if check(data,input,"Num"):
                        Valid_data=True
                else:
                    if check(data,input,"Name"):
                        Valid_data=True
                if Valid_data!=True:
                    easygui.msgbox("해당 이용자가 없습니다\n"+"입력값: "+input,"경고")
                if Valid_data==True and num==True:
                    for x in data:
                        if x.get("Num")==input:
                            Name=x.get("Name")
                            Num=x.get("Num")
                            break
                if Valid_data==True and num!=True:
                    count=1
                    same=[]
                    for x in data:
                        if x.get("Name")==input:
                            count=count+1
                            same.append(x.get("Num"))
                    if count==1:
                        for x in data:
                            if x.get("Name")==input:
                                Name=x.get("Name")
                                Num=x.get("Num")
                                break
                    if count>1:
                        msg="동명이인이 있습니다. 이용자 번호를 선택하십시오."
                        sel=easygui.choicebox(msg,"경고",choices=same)
                        if sel==None:
                            break
                        for x in data:
                            if x.get("Num")==sel:
                                Name=x.get("Name")
                                Num=x.get("Num")
                                break


                if Valid_data==True:
                    msg="이용자 정보\n이름: "+ Name +"\n이용자 번호: " + Num
                    choices=["처음으로","이 이용자 데이터 수정","다른 이용자 검색","이용자 정보 삭제"]
                    prompt=easygui.buttonbox(msg,title,choices=choices)
                
                if prompt=="처음으로":
                    break
                
                if prompt=="이 이용자 데이터 수정":
                    Run=True
                    while True:
                        msg=Name+"의 데이터 수정."
                        input_list=["이름","번호"]
                        val=easygui.multenterbox(msg,title,fields=input_list)
                        if val==None:
                            break
                        for x in data:
                            if x.get("Num")==Num:
                                if val[0]=="" and val[1]!="":
                                    if easygui.ynbox("정보가 교제됩니다.\n"+Num+" -> "+val[1], "경고"):
                                        x["Num"]=val[1]
                                        run=False
                                        break
                                    else:
                                        break
                                if val[1]=="" and val[0]!="":
                                    if easygui.ynbox("정보가 교제됩니다.\n"+Name+" -> "+val[0], "경고"):
                                        x["Name"]=val[0]
                                        run=False
                                        break
                                    else:
                                        break
                                if val[0]!="" and val[1]!="":
                                    if easygui.ynbox("정보가 교제됩니다.\n"+ Num + ", " + Name + " -> " + val[1] + ", " + val[0], "경고"):
                                        x["Num"]=val[1]
                                        x["Name"]=val[0]
                                        run=False
                                        break
                                    else:
                                        break
                                if val[0]=="" and val[1]=="":
                                    easygui.msgbox("정보를 입력하십시오.","경고")
                                    break
                        if run==False:
                            save(data,"user_list_RFID.csv")
                            easygui.msgbox("변경내용이 저장되었습니다.","알림")
                            break
                    if run==False:
                        break
                        
                if prompt=="이용자 정보 삭제":
                    while True:
                        if easygui.ynbox("이용자 정보가 삭제됩니다","경고"):
                            for x in data:
                                if x.get("Num")==Num:
                                    data.remove(x)
                                    break
                            save(data,"user_list_RFID.csv")
                            easygui.msgbox("이용자 정보가 삭제되었습니다","알림")
                            break
                        else:
                            break
                    
                    
