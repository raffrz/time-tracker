# syntax=docker/dockerfile:1
# Build com contexto na raiz do monorepo (ver local-apps/docker-compose.yml).

########################################
# Stage 1: build estatico (React/Vite)
########################################
FROM node:20-alpine AS build
WORKDIR /app
COPY packages/time-tracker-front/package.json packages/time-tracker-front/package-lock.json ./
RUN npm ci
COPY packages/time-tracker-front/ ./
RUN npm run build

########################################
# Stage 2: nginx serve o build e repassa /api/ para a API
########################################
FROM nginx:alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
