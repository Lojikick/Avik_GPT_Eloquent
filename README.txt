# AvikGPT - AI-Powered Customer Service Agent

A full-stack AI chatbot application with user authentication, persistent chat history, and RAG (Retrieval-Augmented Generation) capabilities.

## ✨ Features

- **Guest Mode**: Try the app without registration (single chat session)
- **User Authentication**: Register to save unlimited chat conversations
- **Persistent History**: All chats are saved and accessible across devices
- **AI-Powered Responses**: Uses Google's Gemini AI with document retrieval
- **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS

## 🚀 Quick Demo (Docker)

### Prerequisites
- Docker and Docker Compose installed
- Docker running on Desktop
- API keys for the services below

### Required API Keys
1. **MongoDB Atlas** (free): [mongodb.com/atlas](https://mongodb.com/atlas)
2. **Google AI Studio** (free): [aistudio.google.com](https://aistudio.google.com)
3. **Pinecone** (free tier): [pinecone.io](https://pinecone.io)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd avikgpt
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your API keys:
   ```bash
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/chatbot_db
   GOOGLE_API_KEY=your_google_ai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   ```

3. **Run the application**
   ```bash
   docker-compose up --build
   ```

4. **Open your browser**
   ```
   http://localhost:3000
   ```

The app will start in production mode with both frontend and backend running!

## 🔧 Development

To run locally without Docker:

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
├── frontend/          # Next.js React application
├── backend/           # FastAPI Python server
├── docker-compose.yml # Container orchestration
└── .env.example      # Environment template
```


## 🚀 AWS Deployment Further Instructions

For AWS Deployment, I would run the web-app on an EC2 instance using the Docker container. To do this I would
- Launch an EC2 instance, using Ubuntu and t3.medium storage
- SSH into the EC2 instance and setup Docker
- Clone the github repo, establish an .env file with all production environment variables + api keys
- Build the app using the Docker compose file
- Setup a Nginx reverse proxy to route client traffic to the web servers and handle load balancing

For additional security, I would create proper security groups to protect SSH access,
and a proper domain to handle requests for the React frontend and FastAPI backend servers. For additional scale we can setup
auto-scale groups based on either CPU usage or the number of requests


## 🎯 How to Use

### Guest Mode
- Open the app and start chatting immediately
- Limited to one active conversation
- No registration required

### Registered User
1. Click "Sign Up" in the banner or sidebar
2. Create an account with email/password
3. Enjoy unlimited chat sessions
4. Access chat history from any device

## 🛠 Tech Stack

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **JWT Authentication** - Secure login

### Backend
- **FastAPI** - Python web framework
- **MongoDB** - Database for users and chats
- **Pinecone** - Vector database for document retrieval
- **LangChain** - AI framework
- **Google Gemini** - Language model


## 📝 License

MIT License - feel free to use this project for learning or building your own applications.

## ⚡ Quick Troubleshooting

**App won't start?**
- Check that all API keys are valid in `.env`
- Ensure Docker is running
- Try `docker-compose down` then `docker-compose up --build`

**Can't create account?**
- Verify MongoDB connection string is correct
- Check that database allows connections from your IP

**AI responses not working?**
- Verify Google AI API key is valid
- Check Pinecone API key and index name

---

Built with ❤️ using modern web technologies