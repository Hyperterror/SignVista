# SignVista frontend image (Next.js standalone output).
#   docker build -t signvista-frontend --build-arg BACKEND_URL=http://backend:8000 frontend
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS build
WORKDIR /app
# Rewrites (the /api proxy target) are resolved at build time
ARG BACKEND_URL=http://backend:8000
ARG NEXT_PUBLIC_BACKEND_PORT=8000
ARG NEXT_PUBLIC_WS_URL=
ENV BACKEND_URL=$BACKEND_URL \
    NEXT_PUBLIC_BACKEND_PORT=$NEXT_PUBLIC_BACKEND_PORT \
    NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
RUN addgroup -S nextjs && adduser -S nextjs -G nextjs
COPY --from=build --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nextjs /app/.next/static ./.next/static
COPY --from=build --chown=nextjs:nextjs /app/public ./public
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
