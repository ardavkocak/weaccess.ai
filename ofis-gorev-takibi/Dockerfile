# syntax=docker/dockerfile:1

# ─────────────────────────────────────────────────────────────────────────────
# Ofis Görev Takip Sistemi — üretim imajı
#
# İki aşamalı (multi-stage) build:
#   1) builder  → derleme araçlarıyla bağımlılıkları kurar. better-sqlite3 native
#                 bir modüldür (C++); node-gyp + python + g++ ister. Bu araçlar
#                 YALNIZCA bu aşamada bulunur, son imaja sızmaz.
#   2) runtime  → yalnızca derlenmiş node_modules + uygulama kodu. Küçük, araçsız,
#                 root olmayan kullanıcıyla çalışır.
#
# Node 20 LTS: package.json engines ">=18" ile uyumlu, uzun süre desteklenir.
# ─────────────────────────────────────────────────────────────────────────────

# ---------- 1) Bağımlılık derleme aşaması ----------
FROM node:20-bookworm-slim AS builder

# better-sqlite3'ün derlenmesi için gereken araçlar.
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Önce yalnızca manifest'leri kopyala: kaynak değişse bile bağımlılık katmanı
# (pahalı olan) yeniden derlenmez — Docker katman önbelleği çalışır.
COPY package.json package-lock.json ./

# npm ci: package-lock.json'a birebir sadık, tekrarlanabilir kurulum.
# --omit=dev: yalnızca üretim bağımlılıkları. better-sqlite3 burada derlenir.
RUN npm ci --omit=dev

# ---------- 2) Çalıştırma aşaması ----------
FROM node:20-bookworm-slim AS runtime

# tzdata: cron ifadeleri ve mesaj saatleri Europe/Istanbul'a göre çalışır.
# Sunucu farklı bir bölgede olsa bile ofis saati doğru kalsın.
RUN apt-get update && apt-get install -y --no-install-recommends \
      tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production \
    TZ=Europe/Istanbul \
    PORT=3000 \
    DATABASE_FILE=data/ofis.sqlite

WORKDIR /app

# Derlenmiş bağımlılıkları builder'dan al (yeniden derleme yok).
COPY --from=builder /app/node_modules ./node_modules

# Uygulama kaynağı. .dockerignore sayesinde node_modules, .env, data/ vb. gelmez.
COPY package.json ./
COPY src ./src
COPY public ./public
COPY scripts ./scripts

# Veritabanının ve oturumların yazıldığı klasör. Volume ile kalıcı hale gelir;
# node kullanıcısı yazabilsin diye sahibi ayarlanır.
RUN mkdir -p /app/data && chown -R node:node /app

# Root olarak çalışma: bir güvenlik açığı olsa bile konteynerde yetki sınırlı olsun.
USER node

EXPOSE 3000

# Basit sağlık kontrolü: giriş sayfası 200/302 dönüyorsa uygulama ayakta.
# slim imajda curl/wget yok; Node'un kendi http modülüyle kontrol ediyoruz.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD node -e "require('http').get('http://127.0.0.1:'+(process.env.PORT||3000)+'/giris',r=>process.exit(r.statusCode<500?0:1)).on('error',()=>process.exit(1))"

CMD ["node", "src/server.js"]
