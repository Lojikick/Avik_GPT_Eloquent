AvikGPT - AI-Powered Customer Service Agent

Introducing AvikGPT! - An Customer service AI chatbot application with user authentication, persistent chat history, and RAG (Retrieval-Augmented Generation) capabilities.

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

To run locally without Docker, follow the Instructions below


### Backend

create a new .env file with the same requirements, store it in the backend folder

```bash
cd backend
python -m venv chatbotenv
source chatbotenv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npx next dev -p 3000
```

## 📁 Project Structure

```
├── frontend/          # Next.js React application
├── backend/           # FastAPI Python server
├── docker-compose.yml # Container orchestration

```

## 🚀 Assignment Writeup:

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

(Note: Text below is long I know, but all written by me! No AI used for this part haha)

I first approached this problem by implementing the FastAPI backend, the first task being implementing the RAG Chat pipeline. I first figured out how to retrieve similar
vector embeddings to a query from the PineconeDB, then setup a chain between the PineconeDB and my LLM, Gemini 2.5 via Langchain. I wrapped this pipeline up in a proper API call
to get a response from a prompt using FastAPI, and then moved on to build a simple frontend

I then built a simple chat interface in Next.JS and setup an api.ts file to handle api calls. I based my UI on ChatGPT's style. Once I was able to get single responses from client requests, I moved onto implementing
chat history persistence, which would require a database. I decided to use mongodb, as setting up a connection to a cluster in MongoDB atlas was pretty quick. Plus, mongo being NoSQL is
easier to scale for large reads right out of the box. I setup collections to store user_data, message_data, and session_data. Each message object would have a reference to its session and be marked
as either an AI or a user response. 

I set up more robust CRUD style apis and isolated the RAG and Session related functions into different files for better organization. Then, I created an API to fetch all 
the messages for a given session, which the frontend could now read and display to the user with a scroll-bar. I re-used this same function in my main prompt_query api to convert the messages into langchain 
AI/Human message objects, thus creating the message context which can now be passed into the query to get responses with memory. 

Then I went onto implement the Sidebar and homepage components, which would allow users to traverse created chats and create new ones respectively. I created a new MainApp component, which would manage component state and 
display all relevant components that users would use to interact with the app. I had the sidebar always positioned in the left, which would load the user's recent session id's. The Homepage would allow users to type in a 
initial prompt, which upon entering, would trigger the MainPage to create a new session id, and then re-route to the Chat view with the initial message ready to go in a new chat session

I then established a state for the main window of the website, and swapped between the homepage and the chat component based on the current view state (homestate| chat), which would be updated via callbacks and interactions with the Sidebar. 

I also altered the chat-component to take in a session_id as a prop, which would be a global variable maintained by the MainApp component,
This way, the client would be able to pull the reference of a recent chat's id from the sidebar. With these changes, the single user functionalities for chat history. I made these choices to keep
all of the components accessible within a single main component, which would make things easier for implementing authentication and access later.

I then went on to handle the authentication system. I setup a authentication context file, which would handle the user login status and other global variables such as the current user id.
I wanted most of the functionalities to be handled in the backend as much as possible, so I set the main global variables (user_id, login_status, anonymous_status) to be saved in this frontend file, and then
the heavy operations such as authentication, token creation, to be handled in the database. The app routinely checks if a user is logged in upon a load.
If a user was not logged in and doesnt have a JWT toekn, this file would set the the user context to anonymous, and give the user a temporary anonymous id. 

The actual restriction of content based on the user status also occurs in the backend. Upon creating a new chat session in the homepage, I changed the API responsible for generating a new 
api to check if the user ID contains the "_anon" tag given to anonymous ids, and to just clear the database and start a fresh conversation with the same session. This came in handy as when the user
is able to create a new account, upon the id_initialization, I assigned the previously anonymous sessions to be owned by the newly registered session ids, thus moving session data.
Now the user is able to engage with all privilages of the app, until they log out.

Finally, I set the app up for production in AWS. I setup a .env file for local use to store the environment variables, the pinecone api key, the gemini api key, and the mongo db url,
I then setup two dockerfiles to containerize the frontend and backend services of the app, and used docker compose to create a final production-ready docker image. Overall, I think I built a 
efficient and flexible MVP of a pretty solid app.

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