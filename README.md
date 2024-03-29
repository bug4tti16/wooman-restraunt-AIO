# 경로식당 프로그램 이용 가이드

  ## __프로그램 이용__
  |시작 화면|이용자 확인 화면|
  |---|---|
  | ![start_dark](Assets/2.1.2/title_dark.png) | ![count_dark](Assets/2.1.2/count_dark.png) |
  | ![start_dark](Assets/2.1.2/title_light.png) | ![count_dark](Assets/2.1.2/count_light.png) |

   ## __특이사항 알림__
 |사용|미사용|
 |---|---|
 | ![flag_off](Assets/2.1.2/count_flag.png) | ![flag_on](Assets/2.1.2/count_noflag.png) |

 |특이사항 파일 작성 요령|저장 위치|
 |---|---|
 | ![flag_file](Assets/2.1.2/Flag_File.png) | ![flag_loc](Assets/2.1.2/Directory_Flag.png) |

  ## __이용자 정보 수정__

  | ![edit empty](Assets/2.1.2/edit_overview.png) | ![edit_base](Assets/2.1.2/edit_blank.png) |
  |---|---|
  
  |신규 등록||
  |---|---|
  | ![edit_new_1](Assets/2.1.2/edit_new_1.png) | ![edit_new_2](Assets/2.1.2/edit_new_2.png) |
  | ![edit_new_3](Assets/2.1.2/edit_new_3.png) | ![edit_new_4](Assets/2.1.2/edit_new_4.png) |
  
  |기존 정보 수정||
  |---|---|
  |![edit_update_1](Assets/2.1.2/edit_update.png)|![edit_update_2](Assets/2.1.2/edit_update_1.png)|
  |![edit_update_3](Assets/2.1.2/edit_update_2.png)|![edit_update_4](Assets/2.1.2/edit_update_3.png)|
  
  |이용자 목록 정열||
  |---|---|
  | ![edit_sort_1](Assets/2.1.2/edit_sort.png) | ![edit_sort_2](Assets/2.1.2/edit_sort_1.png) |



## 이전 주요 업데이트

<details>
  <summary>01-19-2024 업데이트</summary>

  - 플래그 기능 추가 (특이사항 표출)

</details>

<details>
  <summary>01-16-2024 업데이트</summary>


  - 버전 2.1.2 업데이트
  - 이용자 명단 수정 기능 추가

</details>

<details>
  <summary>01-07-2024 업데이트</summary>


  - 버전 2.1.1 업데이트
  - 이용자 취소안됨 오류 수정
  - 전반적 성능 개선

</details>

<details>
  <summary>01-04-2024 업데이트</summary>

# __업데이트 2.0.0__

## __UI 업데이트__

| 시작 페이지 |
|---|
|![UI1](Assets/2.0.0/NEWLANDING.png)|

## __검색 기능 개선__

| 입력 전 | 입력 후 |
|---|---|
| ![UI2](Assets/2.0.0/NEWCOUNT.png) | ![UI3](Assets/2.0.0/NEWCOUNT2.png) |

## __시각적 디자인 단순화__

| 입력 취소 | 메뉴 변경 |
|---|---|
|![UI4](Assets/2.0.0/NEWCOUNT3.png)|![UI5](Assets/2.0.0/NEWCOUNT4.png)|
  
## __출력 파일 업데이트__

| 이용자 명단 | 이용 여부 |
|---|---|
|![savefile image 1](Assets/2.0.0/NEWSAVE.png)|![savefile image 2](Assets/2.0.0/NEWSAVE2.png)|


    
</details>


<details>
  <summary>11-13-2023 업데이트 </summary>


- 버전 2.0 시범 운행
- UI업데이트
- 데이터베이스 형식 개선
- 로컬 파일 백업 기능 추가
- 단축키 기능 간소화
- 저장 파일 개선

</details>

<details>
  <summary>9-18-2023 업데이트</summary>

- 사용 설명서 내장
도구 -> 도움말
- 초성 검색 기능 추가
_*동명이인 처리 참고_
- 저장 파일 MSO 엑셀 친화적으로 변경
_*날자 오류 수정_
- 플래그 메세지 업데이트 오류 수정

</details>


<details>
  <summary>이전 버전 정보</summary>
  
## __문제 해결__
### __프로그램 실행이 안되요!!! OTL__
### 해결 1
__user_list_RFID.csv__ 파일 존재 확인
### 해결 2
__user_list_RFID.csv__ 파일 실행 및 형식 확인
![user data](Assets/Legacy/user_data_file.png)
#### __중요__
저장 시 CSV 파일로 저장!! -> 다른 이름으로 저장
![user data save](Assets/Legacy/saving.png)
###  해결 3
메모장으로 열기 -> 다른 이름으로 열기 -> __인코딩 : ANSI__
![user data encoding](Assets/Legacy/no_open1.png)
![user data encoding](Assets/Legacy/no_open2.png)
### 해결 4
__update code__ 실행
![first run](Assets/Legacy/scripts_folder.png)
### 해결 5
__모듈 업데이트__ 실행
![first run](Assets/Legacy/scripts_folder.png)

## 프로그램 실행 전
### 올바른 파일 형태
user_list_RFID.csv 파일 있음

![correct image](Assets/Legacy/Correct!!.png)
### 잘못된 파일 형태
user_list_RFID.csv 파일 없음

![wrong image](Assets/Legacy/wrong!!.png)
### __처음 실행 시__
__모듈 업데이트__ 실행

![first run](Assets/Legacy/scripts_folder.png)
## 프로그램 실행 후
### __기본 창__
![welcome page](Assets/Legacy/start_page2.png)
### __시작 창__
![welcome page](Assets/Legacy/start_page.png)
![attendance](Assets/Legacy/start3.png)
#### __동명이인, 이름 일부 입력 시 처리 방식__
![same name](Assets/Legacy/same_name.png)
#### __도구 창 메뉴__
금일 이용자 방문 여부 방문 시간 표출
![Loobar](Assets/Lecacy/too.png)

### __이용자 관리 창__
#### 기본 창
![info page](Assets/Legacy/edit_page.png)
#### 이용자 정보 변경
_정보 변경 시 날자별 백업파일 생산_
![data edit](Assets/Legacy/change_name.png)
#### 저장 파일 형식
파일명 : __0000년 0월.csv__

![save file](Assets/Legacy/save_format.png)
##### 키워드 부연
O : 카드 지참
NC : 카드 미지참

-(죽식) : 죽식 선택

### __플래그 소개__
_기능 설명: 메세지와 알림음 발생_
![flag running](Assets/Legacy/flag_in_action.png)
#### 플래그 파일 형태
파일명 : __FLAG.txt__

__*중요*__

인코딩 : utf-8

![flag format](Assets/Legacy/flag_format.png)
저장 방법 : __인코딩__ -> __ansi__ | __파일명__ : __FLAG.txt__
![flag save](Assets/Legacy/flag_save.png)

</details>
