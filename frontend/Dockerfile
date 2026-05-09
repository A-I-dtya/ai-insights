# ─── Frontend container (Vite dev server) ────────────────────────────
FROM node:20-alpine

WORKDIR /app

# Install deps first (better caching)
COPY package.json package-lock.json* ./
RUN npm install

# Copy source
COPY . .

EXPOSE 5175

# --host makes Vite reachable outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5175"]
