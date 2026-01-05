FROM node:20-alpine AS base

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

RUN pnpm config set store-dir /tmp/pnpm-store

COPY package.json pnpm-lock.yaml* ./

# Development stage
FROM base AS dev
RUN pnpm install --frozen-lockfile
COPY . .
EXPOSE 3000
CMD ["pnpm", "dev"]

FROM base AS builder
RUN pnpm install --frozen-lockfile
COPY . .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN pnpm build

FROM base AS prod
RUN addgroup -S appgroup && adduser -S -G appgroup appuser
RUN pnpm install --frozen-lockfile --prod
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./
USER appuser
EXPOSE 3000
CMD ["pnpm", "start"]