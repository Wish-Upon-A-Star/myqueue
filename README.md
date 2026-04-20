# 작업 큐 탐색기

작업 큐 탐색기는 큰 작업을 작은 작업으로 쪼개고, 오늘 할 일, 중요 작업, 메모, 활동 기록을 한 화면에서 관리하는 개인용 작업 관리 프로그램입니다.

현재 버전은 `Python + customtkinter` 기반의 데스크톱 앱입니다. Electron은 사용하지 않습니다.

## 다운로드와 실행

GitHub Releases에서 운영체제에 맞는 zip 파일을 내려받아 실행합니다.

- Windows: `TaskExplorer-windows.zip`
- macOS: `TaskExplorer-macos.zip`

## Windows 실행

1. `TaskExplorer-windows.zip`을 다운로드합니다.
2. 원하는 위치에 압축을 풉니다.
3. 압축을 푼 폴더 안의 `TaskExplorer.exe`를 실행합니다.

권장 실행 파일:

```text
TaskExplorer/TaskExplorer.exe
```

## macOS 실행

1. `TaskExplorer-macos.zip`을 다운로드합니다.
2. 압축을 풉니다.
3. `TaskExplorer.app`을 실행합니다.

macOS에서 `.app`은 실제로는 폴더 구조를 가진 앱 번들입니다. Windows에서 보면 폴더처럼 보일 수 있지만, macOS Finder에서는 앱처럼 실행됩니다.

## macOS에서 "손상되었기 때문에 열 수 없음" 또는 바로 삭제되는 경우

이 앱은 아직 Apple 개발자 서명과 공증을 받지 않았습니다. 그래서 macOS Gatekeeper가 다운로드한 앱에 붙은 격리 속성 때문에 실행을 막을 수 있습니다.

압축을 푼 뒤 터미널에서 아래 명령을 실행하세요.

```bash
cd ~/Downloads
xattr -dr com.apple.quarantine TaskExplorer.app
open TaskExplorer.app
```

앱을 다른 폴더에 풀었다면 `cd` 경로를 그 위치로 바꾸면 됩니다.

예시:

```bash
cd ~/Applications
xattr -dr com.apple.quarantine TaskExplorer.app
open TaskExplorer.app
```

만약 zip 파일 자체에 격리 속성이 붙어 있어서 압축 해제 후에도 계속 막히면, zip에도 먼저 적용할 수 있습니다.

```bash
cd ~/Downloads
xattr -d com.apple.quarantine TaskExplorer-macos.zip
unzip TaskExplorer-macos.zip
xattr -dr com.apple.quarantine TaskExplorer.app
open TaskExplorer.app
```

또는 Finder에서 실행할 때는 아래 순서로 시도할 수 있습니다.

1. `TaskExplorer.app`을 우클릭합니다.
2. `열기`를 누릅니다.
3. 경고창이 뜨면 다시 `열기`를 누릅니다.

이 방법은 앱을 신뢰하고 실행하겠다는 사용자의 명시적 허용입니다.

## 주요 기능

- 작업을 트리 구조로 세분화
- 작업 추가, 이름 수정, 삭제, 복사
- 드래그로 작업 순서 변경
- 드래그로 다른 작업 아래로 이동
- 현재 작업의 부모로 이동
- 오늘 할 일 표시
- 중요 작업 표시
- 완료 처리
- 우선순위 지정
- 같은 우선순위에서는 만든 순서 유지
- 오늘 할 일, 중요, 완료, 우선순위 보기
- 4분할 보기
- 메모와 할 일 구분
- 작업별 메모 작성
- 현재 작업 하위 구조 보기
- 작업 구조 txt 내보내기
- txt나 트리 텍스트 붙여넣기로 작업 구조 추가
- 날짜별 작성 기록 보기
- 완료 날짜별 보기
- 목록과 폴더 관리
- 활동 기록 보기
- 프로그램별 활동 기록
- 시간별 활동 기록
- 하루 전체 흐름 보기
- 활동 분류별 흐름 보기

## 활동 기록 기능

활동 기록은 현재 활성 창의 프로그램 이름과 창 제목을 저장해서 하루 동안 무엇을 했는지 돌아볼 수 있게 합니다.

지원하는 보기:

- 하루 흐름
- 분류별 보기
- 프로그램별 보기
- 시간별 보기

프로그램별 보기에서는 `chrome.exe` 같은 프로그램 행을 클릭하면 그 프로그램에서 열었던 창 제목 목록을 펼쳐볼 수 있습니다.

## 작업 구조 붙여넣기 예시

아래처럼 트리 모양 텍스트를 붙여넣으면 현재 위치 아래에 작업으로 추가됩니다.

```text
소켓 객체
├── 상태
├── 주소 정보
├── 버퍼
└── 옵션
```

들여쓰기 형식도 사용할 수 있습니다.

```text
부모 작업
  자식 작업 1
  자식 작업 2
    더 작은 작업
```

## 저장 위치

Windows 실행 파일 버전은 실행 폴더에 데이터를 저장합니다.

```text
TaskExplorer/task-explorer-state.json
TaskExplorer/activity-log.db
```

macOS 앱 버전은 사용자 Application Support 폴더에 데이터를 저장합니다.

```text
~/Library/Application Support/TaskExplorer/task-explorer-state.json
~/Library/Application Support/TaskExplorer/activity-log.db
```

개인 작업 데이터와 활동 기록 데이터는 GitHub 저장소와 배포 zip에 포함하지 않습니다.

## 개발 상태로 실행

Python이 설치되어 있다면 소스 상태로 실행할 수 있습니다.

```powershell
python task_explorer_native.py
```

## Windows 실행 파일 다시 만들기

권장 Python 버전은 Python 3.12입니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --name TaskExplorer task_explorer_native.py
```

결과:

```text
dist/TaskExplorer/TaskExplorer.exe
```

## macOS 앱 다시 만들기

Windows에서는 macOS `.app`을 직접 만들 수 없습니다. macOS에서 직접 빌드하거나 GitHub Actions를 사용해야 합니다.

macOS에서 직접 빌드:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

결과:

```text
dist/TaskExplorer.app
dist/TaskExplorer-macos.zip
```

GitHub Actions에서 빌드:

1. GitHub 저장소의 `Actions` 탭으로 이동합니다.
2. `Build macOS app` 워크플로를 선택합니다.
3. `Run workflow`를 실행합니다.
4. 완료 후 `TaskExplorer-macos` artifact를 다운로드합니다.

## 배포 파일 구성

```text
TaskExplorer-windows.zip             Windows 실행 파일 패키지
TaskExplorer-macos.zip               macOS 앱 패키지
TaskExplorer-macos-build-source.zip  macOS에서 직접 빌드할 수 있는 최소 소스 패키지
```

## 주의

이 프로그램은 개인 작업 데이터와 활동 기록을 로컬에 저장합니다. 배포용 zip에는 개인 데이터가 들어가지 않도록 구성되어 있습니다.

중요한 데이터는 프로그램의 JSON 저장 기능이나 파일 복사로 별도 백업하는 것을 권장합니다.
