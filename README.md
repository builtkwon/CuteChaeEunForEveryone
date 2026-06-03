# CuteChaeEun — 디지털 액자 QR 사진 생성기

멀리 사는 가족의 디지털 액자에 올릴 사진에 **QR 코드를 자동 합성**해, 액자를 보는 가족이 원본 사진을 바로 다운로드할 수 있게 해주는 모바일 웹 앱입니다.

## 주요 기능

- **로그인 불필요** — 접속 즉시 사용 가능
- **모자이크 QR** — QR 코드가 사진 색상에 자연스럽게 녹아드는 방식으로 합성
- **위치 선택** — 좌상단 / 우상단 / 좌하단 / 우하단 중 선택
- **자동 압축** — 대용량 사진(50MB 이하) 자동 처리
- **영구 저장** — Cloudflare R2에 저장, QR 링크 영구 유지
- **모바일 최적화** — 카메라 직접 촬영 및 갤러리 선택 지원

## 동작 흐름

```
① 모바일 브라우저로 접속
② 사진 선택 + QR 위치 선택
③ 서버가 자동으로:
   - 대용량 사진이면 자동 압축
   - Cloudflare R2에 원본 업로드 → 영구 링크 생성
   - 링크가 담긴 QR 코드 생성 (quiet zone 제거, 모자이크 합성)
   - 사진 지정 위치에 QR 합성
④ 완성된 사진 저장 → Uhale 액자 앱에 업로드
⑤ 가족이 액자 앞에서 QR 스캔 → 원본 사진 다운로드
```

## 기술 스택

| 역할 | 기술 |
|------|------|
| 백엔드 | Python / FastAPI |
| 이미지 처리 | Pillow (QR 합성, 압축, 모자이크) |
| QR 생성 | qrcode |
| 클라우드 스토리지 | Cloudflare R2 (S3 호환) |
| 프론트엔드 | Jinja2 + Tailwind CSS (CDN) |
| 호스팅 | Render.com (HTTPS 자동) |

## 로컬 실행

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env.example`을 복사해 `.env` 파일 생성 후 값 입력:

```bash
cp .env.example .env
```

```
SECRET_KEY=랜덤하고-긴-문자열
R2_ACCOUNT_ID=Cloudflare_계정_ID
R2_ACCESS_KEY_ID=R2_액세스_키_ID
R2_SECRET_ACCESS_KEY=R2_시크릿_키
R2_BUCKET_NAME=버킷_이름
R2_PUBLIC_URL=https://pub-xxxx.r2.dev
```

### 3. 서버 실행

```bash
uvicorn app.main:app --reload
```

브라우저에서 `http://localhost:8000` 접속

## Cloudflare R2 설정

1. [cloudflare.com](https://cloudflare.com) 가입
2. **R2 Object Storage** → 버킷 생성
3. **Settings → Public Development URL** 활성화 → 퍼블릭 URL 복사
4. **Manage R2 API Tokens** → 토큰 생성 (Object Read & Write)
5. Account ID, Access Key ID, Secret Access Key 복사

## 배포 (Render.com)

1. 이 저장소를 Render.com Web Service로 연결
2. 환경변수 6개 등록 (`.env.example` 참고)
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 프로젝트 구조

```
photo-qr-frame/
├── app/
│   ├── main.py                  # FastAPI 라우터
│   ├── qr_composer.py           # QR 생성 · 모자이크 합성 · 압축
│   ├── backends/
│   │   ├── base.py              # 인터페이스 (CloudStorage, ResultStore)
│   │   ├── r2_storage.py        # Cloudflare R2 구현체
│   │   └── memory_store.py      # 메모리 저장소 (TTL 1시간)
│   ├── services/
│   │   ├── photo_service.py     # 처리 파이프라인 오케스트레이터
│   │   └── result_repository.py # 결과 조회 서비스
│   └── templates/
│       ├── index.html           # 업로드 화면
│       └── result.html          # 결과 화면
├── config.py                    # 환경변수 로딩
├── render.yaml                  # Render.com 배포 설정
├── Procfile
├── requirements.txt
└── .env.example
```

## 보안

- 파일 크기 제한: 50MB (자동 압축으로 10MB 이하로 조정)
- MIME 타입 검증 + Pillow 실제 이미지 검증 (악성 파일 차단)
- R2 key 파일명 sanitization (경로 조작 방지)
- 결과 파일 TTL 1시간 자동 만료
- 보안 헤더 적용 (X-Content-Type-Options, X-Frame-Options, Referrer-Policy)

## 라이선스

MIT
