FROM mcr.microsoft.com/playwright:v1.57.0-noble

ENV NODE_ENV=production

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY services ./services

RUN mkdir -p /app/services/public

EXPOSE 3001

CMD ["npm", "run", "start:server"]
