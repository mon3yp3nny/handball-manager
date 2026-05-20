# Build stage
FROM node:20-alpine AS builder

# Vite reads VITE_* env vars at build time and inlines them into the bundle.
# Pass them as build args so the same Dockerfile works locally and on Cloud Build.
ARG VITE_API_URL="https://handball-backend-218596927281.europe-west1.run.app/api/v1"
ARG VITE_GOOGLE_CLIENT_ID=""
ARG VITE_APPLE_CLIENT_ID=""
ENV VITE_API_URL=$VITE_API_URL \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID \
    VITE_APPLE_CLIENT_ID=$VITE_APPLE_CLIENT_ID

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
