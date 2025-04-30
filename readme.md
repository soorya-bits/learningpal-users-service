# User Service

This application is a microservice that manages user-related operations such as user creation, retrieval, and updates. It is designed to be lightweight, scalable, and easy to integrate with other services.

## Features
- User creation and management
- RESTful API endpoints
- Lightweight and containerized for easy deployment

## Prerequisites
- Docker installed on your system
- Basic knowledge of Docker commands

## Running the Application in Docker

### Steps for Windows and Mac:

1. Clone the repository:
    ```bash
    git clone https://github.com/soorya-bits/learningpal-users-service.git
    cd users-service
    ```

2. Run the appropriate script based on your operating system:
   - **For Windows**: Run the `run-users-service.bat` script:
     ```cmd
     ./deployment-scripts/run-users-service.bat
     ```
   - **For macOS**: Run the `run-users-service.sh` script:
     ```bash
     ./deployment-scripts/run-users-service.sh
     ```

3. Access the application:
    Open your browser and navigate to `http://localhost:8000/docs`.

## Notes
- Ensure Docker Desktop is running on your system.
