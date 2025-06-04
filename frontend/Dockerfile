# Frontend Dockerfile for AskRAG
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user for security
RUN addgroup -g 1001 -S askrag && \
    adduser -S askrag -u 1001 -G askrag

# Set permissions
RUN chown -R askrag:askrag /usr/share/nginx/html && \
    chown -R askrag:askrag /var/cache/nginx && \
    chown -R askrag:askrag /var/log/nginx && \
    chown -R askrag:askrag /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R askrag:askrag /var/run/nginx.pid

USER askrag

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80 || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
