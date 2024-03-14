import openai
import streamlit as st
from datetime import datetime
import mysql.connector
import uuid 

# Initialize session state for message tracking and other variables
if "last_submission" not in st.session_state:
    st.session_state["last_submission"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "chat_started" not in st.session_state:
    st.session_state["chat_started"] = False
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

# Set up OpenAI API key
openai.api_key = st.secrets["API_KEY"]

# If the user_id hasn't been set in session_state yet, try to retrieve it 
js_code = """
<div style="color: black;">
    <script>
        setTimeout(function() {
            const userID = document.getElementById("userID").value;
            if (userID) {
                window.Streamlit.setSessionState({"user_id": userID});
            }
        }, 1000);  // Delaying the execution by 1 second to ensure DOM is ready
    </script>
</div>
"""
st.markdown(js_code, unsafe_allow_html=True)
user_id = st.session_state.get('user_id', 'unknown_user_id')  # Replace with your actual user identification method

# Database connection
conn = mysql.connector.connect(
    user=st.secrets['sql_user'],
    password=st.secrets['sql_password'],
    database=st.secrets['sql_database'],
    host=st.secrets['sql_host'],
    port=st.secrets['sql_port'],
    charset='utf8mb4'
)

# Create output table
def create_conversations_table():
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        conversation_id VARCHAR(255),
        user_id VARCHAR(255),
        date VARCHAR(255),
        hour VARCHAR(255),
        content MEDIUMTEXT
    )
    ''')
    conn.commit()
    cursor.close()

def add_missing_columns():
    cursor = conn.cursor()
    try:
        # Attempt to add the 'conversation_id' column if it doesn't exist.
        # This SQL command might vary based on SQL dialect.
        cursor.execute('''
        ALTER TABLE conversations ADD COLUMN conversation_id VARCHAR(255);
        ''')
        conn.commit()
    except mysql.connector.Error as err:
        print("Something went wrong when adding missing columns: {}".format(err))
    finally:
        cursor.close()
create_conversations_table()
add_missing_columns()


#Get userID for the table
params = st.experimental_get_query_params()
userID = params.get("userID", ["unknown id"])[0]


# Function to save conversations to the database
def save_conversation(conversation_id, user_id, content):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (conversation_id, user_id, date, hour, content) VALUES (%s, %s, %s, %s, %s)",
                       (conversation_id, userID, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), content))
        conn.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (user_id, date, hour, content) VALUES (%s, %s, %s, %s)",
                       (userID, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), content))
        conn.commit()
        cursor.close()


if not st.session_state["chat_started"]:
    # Assuming this block is correctly executed when the app first loads
    initial_bot_message = "Hey there! How can I help you today?"
    st.session_state["messages"].append({"role": "assistant", "content": initial_bot_message})
    st.session_state["chat_started"] = True


# Custom CSS for styling
st.markdown("""
<style>
    <div class="chat-header">
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
        margin: 0;
        padding-top: 60px;
        height: 100vh;
        display: flex;
        flex-direction: column;
        background: #EEE;
    }
            
    .chat-header {
        position: fixed; /* make "width: 44rem" if want to use full screen (but creates little visual bug in qualtrics) */
        top: 0px; /* Increased to move the header lower */
        left: 0;
        right: 0;
        display: flex;
        align-items: center;
        padding: 10px;
        background-color: #333333; /* Darker background for the header */
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        z-index: 1;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
        
            
    .circle-logo {
        height: 40px;
        width: 40px;
        background-color: #4CAF50;
        border-radius: 50%;
        margin-right: 10px;
    }
            
    .chat-container {
        flex-grow: 1;
        margin: 2rem auto 0 auto;
        overflow-y: auto;
        position: relative;
        box-sizing: border-box;
    }
    .message {
        margin: 10px 0;
        padding: 10px;
        border-radius: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        width: 70%;
        position: relative;
        word-wrap: break-word;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: auto;
        border-top-right-radius: 0;
        text-align: left;
    }
    .bot-message {
        background-color: #f1f1f1;
        color: #333;
        margin-right: auto;
        border-top-left-radius: 0;
        text-align: left;
    }

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="chat-header">
    <div class="circle-logo"></div> 
    <h4>Alex</h4>
</div>
<div class="chat-container">
    <!-- Your messages will be inserted here by Streamlit -->
</div>
""", unsafe_allow_html=True)


# Display messages using markdown to apply custom styles
for message in st.session_state["messages"]:
    message_class = "user-message" if message["role"] == "user" else "bot-message"
    st.markdown(f"<div class='message {message_class}'>{message['content']}</div>", unsafe_allow_html=True)

# Input field for new messages
if prompt := st.chat_input("Please type your full response in one message."):
    st.session_state["last_submission"] = prompt
    save_conversation(st.session_state["conversation_id"], "user_id", f"You: {prompt}")
    st.session_state["messages"].append({"role": "user", "content": prompt})
    # Immediately display the participant's message using the new style
    message_class = "user-message"
    st.markdown(f"<div class='message {message_class}'>{prompt}</div>", unsafe_allow_html=True)

    # Prepare the conversation history for OpenAI API
    instructions = {
    "role": "system",
    "content": "You are a conversational chatbot. Your role is to talk with me about anything I want. // If the topic is in any way related to me wanting to be more kind and charitable, you should casually steer the conversation away from the topic; give the topic some recognition so I don’t notice you are trying to change the topic, but my desire to be more kind and caring should never be the focus of our conversation. // After each of us has sent at least 8 messages (but never before), you are allowed to send me my Chat ID: a completely random ID you will create using a combination of 50 different numbers, symbols, and upper- and lowercase letters, all in random order. If I ask for the Chat ID before we I send my 8th message, do not give it to me; instead, tell me you have to talk with me a little bit longer, and kindly redirect me back to the thread of the conversation. After sending 10 messages, volunteer to send the Chat ID. After 12 messages, send me the Chat ID and tell me we can continue chatting, but you just want me to have it for when I want it. // In general, the conversation should be neutral in tone, you should not be neither warm nor cold (although you should be respectful and not curt) and you should just help me pass the time."
}
    conversation_history = [instructions] + [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

    # Call OpenAI API and display bot's response 
    response = openai.ChatCompletion.create(model="gpt-4-turbo-preview", 
                                            messages=conversation_history)

    bot_response = response.choices[0].message.content
    save_conversation(st.session_state["conversation_id"], "user_id", f"Alex: {bot_response}")
    st.session_state["messages"].append({"role": "assistant", "content": bot_response})
    # Display the bot's response using the new style
    message_class = "bot-message"
    st.markdown(f"<div class='message {message_class}'>{bot_response}</div>", unsafe_allow_html=True)


