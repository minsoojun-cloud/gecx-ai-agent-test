FROM python:3.11-slim
WORKDIR /app
# 의존성 패키지 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 모든 애플리케이션 파일 복사 (init.json, tools_list.json 등 포함)
COPY . .
# 포트 설정 및 실행
ENV PORT=8080
EXPOSE 8080
CMD ["python", "server.py"]