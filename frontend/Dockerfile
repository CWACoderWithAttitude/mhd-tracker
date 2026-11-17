FROM node:26-alpine

WORKDIR /app

COPY package.json .

RUN npm install
COPY . .
#RUN npm run test
RUN npm run build

EXPOSE 8080

CMD [ "npm", "run", "dev" ]