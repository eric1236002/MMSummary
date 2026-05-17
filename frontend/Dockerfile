# 這份 Dockerfile 用來把前端專案建置成靜態檔，並用 Nginx 提供服務。
# 設計重點：
# - 第一階段負責安裝依賴與打包 React/Vite 應用
# - 第二階段只保留最終產物與 Nginx，讓映像檔更小、更快啟動

# 第一階段：建置
FROM node:20-slim AS build

WORKDIR /app

# 先複製 package 檔，利用 Docker layer cache 加速依賴安裝
COPY frontend/package*.json ./
RUN npm install

# 再複製前端原始碼
COPY frontend/ ./

# 執行前端打包，輸出 dist/
RUN npm run build

# 第二階段：使用 Nginx 對外提供靜態檔案
FROM nginx:stable-alpine

# 複製自訂 Nginx 設定，讓 SPA 路由與 API 代理能正常運作
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 只把建置結果複製進最終映像，避免帶入 node_modules 等不必要檔案
COPY --from=build /app/dist /usr/share/nginx/html

# 對外開放 80 port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
