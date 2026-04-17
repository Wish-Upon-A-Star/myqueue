# 작업 큐 탐색기

Windows에서 바로 실행하는 개인용 작업 큐/메모 프로그램입니다.

현재 기본 버전은 `Python + customtkinter`로 만든 단일 실행 파일입니다. Electron은 사용하지 않습니다. 기본 Tkinter 테이블 UI를 버리고 카드형 작업 탐색 UI로 구성했습니다.

## 바로 실행

아래 파일을 더블클릭하세요.

```text
dist/TaskExplorer.exe
```

이 파일은 PyInstaller `--onefile --windowed`로 만든 단일 exe입니다.

## 주요 기능

- 작업을 트리 구조로 관리
- 작업 추가, 이름 수정, 삭제
- 선택한 작업과 하위를 현재 위치에 그대로 복사
- 완료, 중요, 오늘 할 일 토글
- 우선순위 지정과 정렬
- 할 일과 메모 구분
- 현재 위치 기준 `전체 보기 / 할 일만 / 메모만` 필터
- 오늘 할 일, 중요, 완료 보기
- 4분할 보기
- 작성일/완료일 기준 보기
- 저장 목록 생성, 열기, 삭제
- 저장 목록끼리 드래그해서 순서 변경
- 선택한 작업을 저장 목록에 추가하거나 목록에서만 제거
- 폴더 생성, 열기, 삭제
- 폴더끼리 드래그해서 순서 변경
- 드래그해서 작업을 다른 작업/폴더 아래로 이동
- 작업을 왼쪽 저장 목록에 드롭해서 목록에 추가
- 작업을 왼쪽 폴더에 드롭해서 폴더 아래로 이동
- 선택 항목 하위 전체 메모화
- 메모를 다음 행동으로 전환
- 작업별 메모 작성
- JSON 상태 저장/불러오기
- txt 트리 내보내기
- 트리 텍스트 붙여넣기 추가
- 간단한 색상 구분 UI

## 트리 붙여넣기 예시

프로그램에서 `트리 붙여넣기`를 누르고 아래처럼 입력한 뒤 `붙여넣기 추가`를 누르면 현재 위치에 기본 할 일로 추가됩니다.

```text
소켓 객체
├── 상태
├── 주소 정보
├── 버퍼
└── 옵션
```

## 데이터 저장

프로그램은 실행 파일이 있는 폴더의 아래 파일을 자동으로 읽고 저장합니다.

```text
task-explorer-state.json
```

기존 HTML 버전에서 저장한 JSON도 `JSON 불러오기`로 가져올 수 있습니다.

## 개발 실행

Python이 있으면 소스 상태로 실행할 수 있습니다.

```powershell
python task_explorer_native.py
```

## exe 다시 만들기

Python 3.14 기준으로 확인했습니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pyinstaller customtkinter
.\.venv\Scripts\python.exe -m PyInstaller --onefile --windowed --name TaskExplorer --collect-data customtkinter task_explorer_native.py
```

결과:

```text
dist/TaskExplorer.exe
```

## 파일 구성

```text
dist/TaskExplorer.exe       바로 실행하는 단일 exe
task_explorer_native.py     customtkinter 네이티브 앱 소스
legacy/task_explorer.html   이전 HTML 버전 백업
```

## 주의

개인 작업 데이터 JSON은 저장소에 포함하지 않습니다. 중요한 데이터는 프로그램 안의 `JSON 저장`으로 따로 백업하세요.
