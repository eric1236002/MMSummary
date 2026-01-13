# Frontend Dockerfile - Multi-stage build
# Stage 1: Build
FROM node:20-slim AS build

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
RUN npm install

# Copy frontend code
COPY frontend/ ./

# Build the app
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:stable-alpine

# Copy custom nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy build files from stage 1
COPY --from=build /app/dist /usr/share/nginx/html

# EXPOSE 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
