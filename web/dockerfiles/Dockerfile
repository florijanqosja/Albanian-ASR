# Base image
FROM node:14-alpine

# Set the working directory
WORKDIR /code

# Copy package.json and package-lock.json
COPY ./web/package.json ./

# Install dependencies

RUN npm install

# Copy the entire project
COPY ./web ./

# Expose port 3000
EXPOSE 3000

# Run the React app
CMD ["npm", "start"]