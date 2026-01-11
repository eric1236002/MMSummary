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

# Copy build files from stage 1
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config if needed, or use default
# EXPOSE 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
