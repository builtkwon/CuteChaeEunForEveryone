# CuteChaeEun — 디지털 액자 QR 사진 생성기

멀리 사는 가족의 디지털 액자에 올릴 사진에 **QR 코드를 자동 합성**해, 액자를 보는 가족이 원본 사진을 바로 다운로드할 수 있게 해주는 모바일 웹 앱입니다.

## 동작 흐름

```
① 모바일 브라우저로 접속
② Google 계정으로 로그인
③ 사진 선택 + QR 위치 선택
④ 서버가 자동으로:
   - Google Drive에 원본 사진 업로드
   - 다운로드 링크가 담긴 QR 코드 생성
   - 사진 귀퉁이에 QR 코드 합성
⑤ 완성된 사진 저장 → Uhale 액자 앱에 업로드
⑥ 가족이 액자 앞에서 QR 스캔 → 원본 다운로드
```

## 기술 스택

| 역할 | 기술 |
|------|------|
| 백엔드 | Python / FastAPI |
| 인증 | Google OAuth 2.0 |
| 클라우드 스토리지 | Google Drive API |
| QR 생성 | qrcode + Pillow |
| 프론트엔드 | Jinja2 + Tailwind CSS (CDN) |
| 호스팅 | Render.com (HTTPS 자동) |

## 로컬 실행

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 열어 아래 두 값을 입력합니다.

```
GOOGLE_CLIENT_ID=Google Cloud Console에서 발급한 클라이언트 ID
GOOGLE_CLIENT_SECRET=Google Cloud Console에서 발급한 클라이언트 시크릿
SECRET_KEY=자동생성됨_변경불필요
BASE_URL=http://localhost:8000
```

### 3. Google Cloud Console 설정

1. [console.cloud.google.com](https://console.cloud.google.com) → 프로젝트: `CuteChaeEun`
2. **Google Drive API** 사용 설정
3. OAuth 클라이언트 ID 발급 (웹 애플리케이션)
4. 승인된 리디렉션 URI 추가:
   - `http://localhost:8000/auth/callback` (로컬)
   - `https://<Render 배포 URL>/auth/callback` (운영)

### 4. 서버 실행

```bash
uvicorn app.main:app --reload
```

브라우저에서 `http://localhost:8000` 접속

## 배포 (Render.com)

1. 이 저장소를 Render.com Web Service로 연결
2. 환경변수 등록 (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SECRET_KEY`, `BASE_URL`)
3. `BASE_URL`은 Render가 발급한 HTTPS URL로 설정
4. Google Cloud Console에서 해당 URL을 리디렉션 URI에 추가

## 프로젝트 구조

```
photo-qr-frame/
├── app/
│   ├── main.py                  # FastAPI 라우터
│   ├── auth.py                  # Google OAuth
│   ├── qr_composer.py           # QR 생성 + 이미지 합성
│   ├── backends/
│   │   ├── base.py              # 인터페이스 (교체 포인트)
│   │   ├── drive_storage.py     # Google Drive 구현체
│   │   └── memory_store.py      # 메모리 저장소 구현체
│   ├── services/
│   │   └── photo_service.py     # 비즈니스 로직 오케스트레이터
│   └── templates/
│       ├── index.html           # 업로드 화면
│       └── result.html          # 결과 화면
├── config.py
├── render.yaml
├── Procfile
├── requirements.txt
└── .env.example
```

## 환경변수 목록

| 변수 | 설명 | 필수 |
|------|------|------|
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | 필수 |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 클라이언트 시크릿 | 필수 |
| `SECRET_KEY` | 세션 암호화 키 (랜덤 문자열) | 필수 |
| `BASE_URL` | 서버 기본 URL (로컬: `http://localhost:8000`) | 필수 |

## 라이선스

MIT
