# Base image
FROM node:14-alpine

# Set the working directory
WORKDIR /code

# Copy package.json and package-lock.json
COPY package*.json ./package.json

# Install dependencies
RUN npm install react-scripts
RUN npm install

# Copy the entire project
COPY ./web ./

# Build the React app
RUN npm run build

# Expose port 3000
EXPOSE 3000

# Run the React app
CMD ["npm", "start"]