# Base image
FROM node:14-alpine

# Set the working directory
WORKDIR /code

# Copy package.json and package-lock.json
COPY ./dev/web/package.json ./
COPY ./dev/web/package-lock.json ./

# Install dependencies

RUN npm install

# Copy the entire project
COPY ./dev/web ./
RUN npx browserslist@latest --update-db
# Expose port 3000
EXPOSE 3000

# Run the React app
CMD ["npm", "start"]