FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG BUILD_HASH=dev
ARG VITE_SHOW_AUTH=false
ARG VITE_CARTO_API_KEY
RUN BUILD_HASH=$BUILD_HASH VITE_SHOW_AUTH=$VITE_SHOW_AUTH VITE_CARTO_API_KEY=$VITE_CARTO_API_KEY npm run build
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
