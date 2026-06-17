# --- base deps ---
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm install

# --- dev (hot reload) ---
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# --- build ---
FROM deps AS build
ARG VITE_API_BASE=/api/v1
ENV VITE_API_BASE=$VITE_API_BASE
COPY . .
RUN npm run build

# --- prod (nginx static) ---
FROM nginx:1.27-alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
