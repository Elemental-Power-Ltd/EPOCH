
FROM node:25 AS build

WORKDIR /app
COPY package.json package-lock.json ./
COPY tsconfig.json tsconfig.node.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# the nginx:alpine image contains a script to apply envsubst to files in /etc/nginx/templates
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
# set localhost as the default URL for the services, these can be overwritten at runtime in docker-compose.yml
ENV EP_OPTIMISATION_SERVICE_URL=http://localhost:8761
ENV EP_DATA_SERVICE_URL=http://localhost:8762
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]