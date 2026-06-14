FROM node:26.3.0-slim

WORKDIR /app

COPY package*.json .
RUN npm ci

COPY . .

EXPOSE 4200
