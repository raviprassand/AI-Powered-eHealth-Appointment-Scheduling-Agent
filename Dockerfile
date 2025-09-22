FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Set environment variable for production build
ENV NODE_ENV=production

# Build the app
RUN npm run build

# Install simple static file server
RUN npm install -g serve

# Expose port 8080 (Cloud Run requirement)
EXPOSE 8080

# Serve the built app with React Router support
CMD ["serve", "-s", "dist", "-l", "8080"]