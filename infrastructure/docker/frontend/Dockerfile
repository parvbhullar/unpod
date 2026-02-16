FROM node:20-alpine

ARG APP_PATH=apps/web

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy shared libraries
COPY libs/shared /libs/shared
COPY libs/nextjs /libs/nextjs

# Copy application code
COPY ${APP_PATH} /app

# Build application
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
