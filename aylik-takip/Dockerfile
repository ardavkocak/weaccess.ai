FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY . .

ENV NODE_ENV=production
ENV TESSDATA_PREFIX=/app

EXPOSE 3000

CMD ["node", "server.js"]
