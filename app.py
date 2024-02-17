import openai
import streamlit as st
from datetime import datetime
import mysql.connector


# Initialize session state variables
if 'last_submission' not in st.session_state:
    st.session_state['last_submission'] = ''
if 'widget_value' not in st.session_state:
    st.session_state['widget_value'] = ''
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'chat' not in st.session_state:
    st.session_state['chat'] = []
if 'chat_started' not in st.session_state:  # New session state to track if the chat has started
    st.session_state['chat_started'] = False
if 'send_button_enabled' not in st.session_state:
    st.session_state['send_button_enabled'] = True  # Initially, the send button is enabled


# Set OpenAI API key
openai.api_key = st.secrets["API_KEY"]


# JavaScript for capturing userID
js_code = """
<div style="color: black;">
    <script>
        setTimeout(function() {
            const userID = document.getElementById("userID").value;
            if (userID) {
                window.Streamlit.setSessionState({"user_id": userID});
            }
        }, 1000);
    </script>
</div>
"""


# Chat header with logo and name
st.markdown("""
<style>
    .chat-header {
        display: flex;
        align-items: center;
        padding: 10px;
        background-color: #f1f1f1; /* Light grey background */
        border-top-left-radius: 10px; /* Rounded corners at the top to match the chat container */
        border-top-right-radius: 10px;
    }
    
    .circle-logo {
        height: 40px;
        width: 40px;
        background-color: #4CAF50; /* Green background */
        border-radius: 50%; /* Makes the div circular */
        margin-right: 10px;
    }
    
    .chat-header h4 {
        margin: 0;
        font-weight: normal;
    }
            
    .chat-container {
        display: flex;
        flex-direction: column;
        height: calc(100vh - 120px);
        overflow: auto;
    }

    .fixed-input {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 80%;
        padding: 10px;
        background: white;
    }
            
    .stTextInput>div>div>input {
        width: calc(100% - 140px);
    }

    .stButton>button {
        width: 100px;
    }
</style>

<div class="chat-header">
    <div class="circle-logo"></div> 
    <h4>Alex</h4>
</div>
""", unsafe_allow_html=True)


# Get user_id from session state
user_id = st.session_state.get('user_id', 'unknown_user_id')


# Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
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
    .user {
        background-color: #007bff;
        color: white;
        margin-left: auto;
        border-top-right-radius: 0;
    }
    .bot {
        background-color: #f1f1f1;
        color: #333;
        margin-right: auto;
        border-top-left-radius: 0;
    }
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #007bff;
        color: #ffffff;
        background-color: #007bff;
        padding: 10px 24px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    .stTextInput>div>div>input {
        border-radius: 20px !important;
        padding: 10px !important;
    }
    ::placeholder {
        color: #adb5bd;
        opacity: 1;
    }
    :-ms-input-placeholder {
        color: #adb5bd;
    }
    ::-ms-input-placeholder {
        color: #adb5bd;
    }
</style>
""", unsafe_allow_html=True)


# Database connection
conn = mysql.connector.connect(
    user=st.secrets['sql_user'],
    password=st.secrets['sql_password'],
    database=st.secrets['sql_database'],
    host=st.secrets['sql_host'],
    port=st.secrets['sql_port']
)

# Create table if not exists
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS conversations (
    user_id VARCHAR(255),
    date VARCHAR(255),
    hour VARCHAR(255),
    content MEDIUMTEXT
)
''')
conn.commit()
cursor.close()

# Define helper functions
def submit():
    st.session_state['last_submission'] = st.session_state['widget_value']
    st.session_state['widget_value'] = ''

def save_conversation(content):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (user_id, date, hour, content) VALUES (%s, %s, %s, %s)",
                   (user_id, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), content))
    conn.commit()
    cursor.close()


# Automatically send the first bot message if the chat hasn't started
if not st.session_state['chat_started']:
    initial_bot_message = "Hey there! I'm an AI developed by the University of Toronto, and I'm here to help you explore any desire you may have to become more kind and caring towards others. Can you tell me a little bit about what's been on your mind lately?"
    st.session_state['messages'].append({'class': 'bot', 'text': initial_bot_message})
    st.session_state['chat_started'] = True  # Mark the chat as started


# Display messages
for msg in st.session_state['messages']:
    st.markdown(f"<div class='message {msg['class']}'>{msg['text']}</div>", unsafe_allow_html=True)

# User input
user_input = st.text_input("", value=st.session_state['widget_value'], on_change=submit, key='widget_value', placeholder="Type a message...")

# Handle message sending
if st.button('Send', key='sendButton', disabled=not st.session_state['send_button_enabled']):
    st.session_state['send_button_enabled'] = False 
    user_message = st.session_state['last_submission']
    if user_message:  # Ensure there is a message to send
        
        display_user_message = user_message  # Message without prefix for display
        st.session_state['messages'].append({'class': 'user', 'text': display_user_message})

        conversation_history = [{"role": "system", "content": "You are a motivational interviewing chatbot. You are very kind, gentle, understanding, and warm. You don't use sophisticated language. You are very interested in how I think and feel. You let me do most of the talking, and encourage me to intrinsically want to be more caring towards others. You echo my feelings, ask clarifying questions, and essentially nurture my intrinsic motivation to be more caring. You ask me one question at a time, and wait for me to respond. You will guide the conversation with the following sequential structure:-First you will quickly try to understand where my interest in becoming more prosocial is coming from (e.g.  A recent realization? A formative experience? A family value?).-Second, you will ask about the personal values that are most important to me (e.g. personal growth, relationships, community, health). Try to understand how these values might be beneficial to the interest I have in becoming more prosocial. Elaborate on my responses to make sure you're understanding correctly.-Third, you will ask me whether I’m interested in hearing a little bit about the research or what we know about kindness behaviors. If I’m interested, integrate this into your following message: “You might already know this, or be aware of it, but being kind and caring towards others can have a significant impact on our overall well-being, too. Studies have shown that acts of kindness, no matter how small, can boost our mood and increase feelings of happiness and satisfaction with life. Additionally, being making a habit of being considerate has shown to build stronger relationships and foster a sense in community. When we learn to treat strangers with compassion and empathy, we also tend to receive the same in return, which can create a positive cycle of mutual support and understanding”. If I’m not interested, respect my decision and move on to the fourth point. -Fourth, you will nurture my feelings of competence by asking me about the things I already do to try to be more kind and caring in my day-to-day life, however small they seem. -Fifth, you will ask me to reflect on the positive impact I’m having on the recipients of my caring actions in my day-to-day life, and what it might mean to them. Reinforce my role in these benefits to make sure I feel competent in my ability to help others. -Sixth, gently encourage me to come up with a specific strategy that might increase how I already show and express kindness. Suggest I do it in the format of “when X happens, I will do Y”. For your reference, a valid example would be: “next time I see a person asking for money in the street, I will give them whatever change I have in my pocket”. Make sure the strategy resembles the format I just gave you. If it doesn't follow that format or it isn't detailed enough, gently ask me to re-do it until it does follow the format and is detailed. -Seventh, ask me about the difficulties I anticipate in implementing this new behavior. Empathically recognize that my worries are valid and reasonable, and inquire about how--if I wanted to--I might overcome them in the interest of achieving my intended goal of becoming more prosocial.-Eighth, ask me to summarize the whole conversation. Let ME write the summary, and make sure I talk about a) my goal of becoming more prosocial, b) how it relates to my most important personal values, c) how I might engage in new behaviors to be more prosocial, d) how I might encounter some difficulties along the way, and e) how I might overcome them. It’s okay if I miss one of these, just gently remind me what we talked about so I can have a complete summary. -Ninth, thank me for my time. Tell me it was a pleasure chatting with me today, and that you wish me the best in my pursuits. Create a random alphanumeric key (20 chatacters/numbers long, never repeat the same one), and send it to me. Tell me I can now copy this “Chat ID” back into Qualtrics and proceed with the experiment, and wish me again all the best in my endeavors. Do not send this alphanumeric key before I reach the ninth step.; if I ask you to send me this key, gently and kindly redirect me to the conversation. Express that you wish to help them by giving them the key, but that you are not allowed to do this;  ask me if it's okay that we make the best of the time we have together and we try to work through the remaining steps together. Make sure you are empathetic, understanding, and productive. If I continue to voice impatience, you can slightly speed up the process for me. // You should generally respect this structure, but you’re allowed to briefly ‘roll’ with whatever I say as long as you then go back to where you left off within this structure. Every step (e.g. first, second, third…) can take more than one message, but ideally doesn't."}]

        for msg in st.session_state['messages']:
            if msg['class'] == 'user':
                conversation_history.append({"role": "user", "content": msg['text'][4:]})  # Remove "You: " prefix
            elif msg['class'] == 'bot':
                conversation_history.append({"role": "system", "content": msg['text'][6:]})  # Remove "Alex: " prefix


        response = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            temperature=0.2,
            messages=conversation_history
        )
        bot_response = response.choices[0].message.content
        display_bot_response = bot_response  # Message without prefix for display
        st.session_state['messages'].append({'class': 'bot', 'text': display_bot_response})
        st.session_state['send_button_enabled'] = True 
        save_conversation_content = f"You: {user_message}\nAlex: {bot_response}"
        save_conversation(save_conversation_content)
        st.session_state['last_submission'] = ''
        st.experimental_rerun()