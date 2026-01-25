# Backend Deployment Guide

Talk Talk Vending Backend 배포 가이드입니다.

## 목차

1. [환경 설정](#환경-설정)
2. [CORS 설정](#cors-설정)
3. [Docker 배포](#docker-배포)
4. [클라우드 배포](#클라우드-배포)
5. [프로덕션 체크리스트](#프로덕션-체크리스트)

---

## 환경 설정

### 1. 환경 변수 파일 생성

```bash
cd backend
cp .env.example .env
```

### 2. 필수 환경 변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-proj-...` |
| `ENVIRONMENT` | 실행 환경 | `development`, `staging`, `production` |
| `DEBUG` | 디버그 모드 | `true` (개발), `false` (프로덕션) |
| `ALLOWED_ORIGINS` | CORS 허용 도메인 | `["https://yourdomain.com"]` |

### 3. 프로덕션용 .env 예시

```env
OPENAI_API_KEY=sk-proj-your-actual-key
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
```

---

## CORS 설정

### CORS란?

CORS(Cross-Origin Resource Sharing)는 브라우저가 다른 도메인에서 API를 호출할 때 보안을 위해 적용되는 정책입니다.

### 설정 방법

`.env` 파일에서 `ALLOWED_ORIGINS`를 JSON 배열 형식으로 설정합니다:

```env
# 단일 도메인
ALLOWED_ORIGINS=["https://yourdomain.com"]

# 다중 도메인
ALLOWED_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]

# 서브도메인 포함
ALLOWED_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com","https://app.yourdomain.com"]
```

### 환경별 권장 설정

#### 개발 환경
```env
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:3456"]
```

#### 스테이징 환경
```env
ALLOWED_ORIGINS=["https://staging.yourdomain.com"]
```

#### 프로덕션 환경
```env
ALLOWED_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
```

### 주의사항

- `["*"]` 사용 금지: 모든 도메인에서 API 호출이 가능해져 보안 취약점이 됩니다
- HTTPS 필수: 프로덕션에서는 반드시 `https://`로 시작하는 도메인만 허용
- 정확한 도메인: 와일드카드(`*.yourdomain.com`) 미지원, 모든 서브도메인을 명시적으로 나열

---

## Docker 배포

### 방법 1: Docker Compose (권장)

```bash
# 프로젝트 루트에서 실행
docker compose up -d --build
```

### 방법 2: Docker 단독 실행

```bash
cd backend

# 이미지 빌드
docker build -t talk-talk-backend .

# 컨테이너 실행
docker run -d \
  --name talk-talk-backend \
  -p 8765:8765 \
  --env-file .env \
  -e ENVIRONMENT=production \
  --restart unless-stopped \
  talk-talk-backend
```

### 컨테이너 관리

```bash
# 로그 확인
docker logs -f talk-talk-backend

# 컨테이너 재시작
docker restart talk-talk-backend

# 컨테이너 중지
docker stop talk-talk-backend

# 컨테이너 삭제
docker rm talk-talk-backend

# 헬스 체크
curl http://localhost:8765/health
```

---

## 클라우드 배포

### AWS ECS (Fargate)

#### 1. ECR에 이미지 푸시

```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 태그
docker tag talk-talk-backend:latest YOUR_ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/talk-talk-backend:latest

# 푸시
docker push YOUR_ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/talk-talk-backend:latest
```

#### 2. Task Definition 예시

```json
{
  "family": "talk-talk-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "talk-talk-backend",
      "image": "YOUR_ECR_IMAGE_URI",
      "portMappings": [
        {
          "containerPort": 8765,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "DEBUG", "value": "false"},
        {"name": "ALLOWED_ORIGINS", "value": "[\"https://yourdomain.com\"]"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-2:YOUR_ACCOUNT:secret:openai-api-key"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "python -c \"import httpx; httpx.get('http://localhost:8765/health')\" || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 10
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/talk-talk-backend",
          "awslogs-region": "ap-northeast-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run

```bash
# 빌드 및 푸시
gcloud builds submit --tag gcr.io/YOUR_PROJECT/talk-talk-backend

# 배포
gcloud run deploy talk-talk-backend \
  --image gcr.io/YOUR_PROJECT/talk-talk-backend \
  --platform managed \
  --region asia-northeast3 \
  --port 8765 \
  --memory 1Gi \
  --set-env-vars "ENVIRONMENT=production,DEBUG=false,ALLOWED_ORIGINS=[\"https://yourdomain.com\"]" \
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest" \
  --allow-unauthenticated
```

### Railway / Render / Fly.io

이러한 PaaS 플랫폼은 Dockerfile을 자동 감지하여 배포합니다:

1. GitHub 저장소 연결
2. 환경 변수 설정 (대시보드에서)
3. 자동 배포

#### Railway 예시

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인 및 배포
railway login
railway init
railway up
```

환경 변수는 Railway 대시보드에서 설정:
- `OPENAI_API_KEY`: OpenAI API 키
- `ENVIRONMENT`: `production`
- `DEBUG`: `false`
- `ALLOWED_ORIGINS`: `["https://your-frontend.railway.app"]`

---

## 프로덕션 체크리스트

배포 전 확인 사항:

### 보안

- [ ] `DEBUG=false` 설정
- [ ] `ALLOWED_ORIGINS`에 실제 프론트엔드 도메인만 포함
- [ ] `OPENAI_API_KEY`가 환경 변수로 주입됨 (코드에 하드코딩 X)
- [ ] HTTPS 적용 (로드밸런서 또는 리버스 프록시)

### 성능

- [ ] 적절한 CPU/메모리 할당
- [ ] Health check 설정
- [ ] 로깅 설정

### 모니터링

- [ ] 로그 수집 설정 (CloudWatch, Stackdriver 등)
- [ ] 알림 설정 (에러율, 응답 시간)

### 테스트

- [ ] `/health` 엔드포인트 응답 확인
- [ ] API 호출 테스트 (CORS 포함)

```bash
# 헬스 체크
curl https://your-api-domain.com/health

# CORS 테스트
curl -H "Origin: https://your-frontend.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://your-api-domain.com/api/v2/generate
```

---

## 문제 해결

### CORS 에러

**증상**: 브라우저에서 `CORS policy` 에러

**해결**:
1. `ALLOWED_ORIGINS`에 프론트엔드 도메인이 정확히 포함되어 있는지 확인
2. 프로토콜(`http://` vs `https://`) 일치 확인
3. 포트 번호 일치 확인 (예: `http://localhost:3000` ≠ `http://localhost:3456`)

### Health Check 실패

**증상**: 컨테이너가 계속 재시작됨

**해결**:
1. `start_period`를 늘려서 앱 시작 시간 확보
2. 로그 확인: `docker logs talk-talk-backend`

### OpenAI API 에러

**증상**: 500 에러 또는 API 키 관련 에러

**해결**:
1. `OPENAI_API_KEY` 환경 변수 확인
2. API 키 유효성 확인
3. 사용량 한도 확인
