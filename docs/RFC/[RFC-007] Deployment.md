# Deployment

## 목적
개발/프로덕션 환경을 분리하고 브랜치/태그 기반 자동 배포를 구축한다.

## 규칙
- SSH 연결은 Cloudflare Tunnel을 사용한다.
- Development: develop 브랜치 push 시 배포 (Docker 태그: `:dev`)
- Production: v*.*.* 태그 push 시 배포 (Docker 태그: `:latest`, `:v*.*.*`)
- Release Tag는 main 브랜치에서만 생성한다.
- GitHub Environments로 환경별 Secrets를 관리한다.

### 배포 플로우
1. Build: Docker 이미지 빌드 및 Docker Hub push
2. Deploy: SSH로 배포 스크립트 및 .env 파일 전송
3. Run: 이미지 pull 및 컨테이너 실행

![배포 아키텍처](/docs/RFC/img/9-1.png)

### 보안
- .env 파일은 Git/Docker 이미지에 포함되지 않는다.
- SSH 개인키는 GitHub Secrets에서 관리한다.
- 환경별 독립된 Secrets를 사용한다.

## 적용 범위
프로젝트 전체 배포 프로세스에 적용된다.