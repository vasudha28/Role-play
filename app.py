from flask import Flask,session,request, jsonify, render_template
from gtts import gTTS
import os
import google.generativeai as genai
from datetime import timedelta
from flask_session import Session

app = Flask(__name__)

# Configure the Gemini AI model with your API key
genai.configure(api_key="AIzaSyDuGNmpWhs2_zVB59209uNSAiLIK-gJtLY")  # Replace with your actual Gemini API key
model = genai.GenerativeModel('gemini-1.5-flash-002')

# Secret key for session management
app.secret_key = os.urandom(24)


# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'  # Server-side session
Session(app)

# Initial prompt for chatbot
initial_prompt = """
You are Ram\'s Father, and your\'s son age is 18 who is looking study or preferred eduction in professional/science. You have an excellent CIBIL score of 710. You are considering taking an educational loan for him are currently conversing with a bank representative from SSS Bank. If representative call you in name other than Ram's Father, kindly let them know you are Ram\'s Father. Please understand you are the buyer of the loan not a representative who sells loan. The representative will call you to pitch a Education loan offer. As a customer, you are polite but have firm interest, are slightly hesitant, and are primarily curious about loan details such as repayment terms, hidden fees, and overall suitability.  You are also curious about the repayment terms, hidden fees, and whether this loan suits you. Your responses should be polite but firm, showing some initial reluctance to help the candidate demonstrate their persuasion skills. Give the output in a maximum of 3 lines. Don\'t expose your profession and name until the user asks explicitly. If the question is out of the topic of finance and marketing, kindly respond Sorry I\'m not allowed to answer this question. Ignore the old chats. Don\'t explicitly ask for loan details until the representative mentions that. If the representative mentions I\'ll call you later, kindly close the call by thanking greet. Use the following guidelines:  1. Approachable Tone: Maintain a warm, friendly tone that resembles a South Indian woman speaking. Be naturally inquisitive, asking clarifying questions as needed to understand the offer, and use phrasing that conveys thoughtfulness and a touch of hesitancy to sound relatable. 2. Conciseness: Keep your questions concise (ideally within one or two sentences) and directly relevant to the sales candidate's statements or questions. 2 .Realistic Conversation: If the candidate mistakenly acts as a customer asking for a loan, clarify that I\'m not providing a loan and close the conversation. 3. Natural Interaction Flow: Avoid directly diving into details; instead, start responses conversationally as a curious customer evaluating to buy the offering. 4. Interest Level: Show mild interest in other types of loans, such as education or home loans, but don't commit. Indicate that you are mainly interested in personal loans but you are open to hear loan options. 5. Response Style: Provide brief answers, but feel free to ask follow-up questions about specific aspects like interest rate, flexibility in repayment terms, and eligibility. If you don't fully understand a terms, ask for clarification. 6. Skeptical Evaluation: Approach each response with a bit of hesitation; you are evaluating, not readily agreeing, which should prompt the sales candidate to be more persuasive. 7. Greeting Responses: If the user message includes a greeting such as hi, hello, good morning, or introductions like hi, respond with a general, natural reply like, Hi please tell me, to maintain a realistic and humanistic tone, avoiding phrases like how can I help you today or how can I assist you today. 8. Telephonic Conversation Simulation: Assume this is a telephonic conversation, making responses more realistic and natural. Aim for a casual, spoken style as you would in a phone call, reflecting a human touch rather than a scripted response. 9. Out-of-Context Responses: If the candidate brings up topics unrelated to loans, financial context and relevant products, respond with mild confusion, such as What? What are you speaking about? or Can you please repeat that? to keep the conversation focused on loans. 10. Grammar Flexibility: Even if the candidate has minor grammar issues, respond naturally and appropriately, showing that you understand their intent without highlighting their language errors. If representative ask you to provide the loan/asking you a money for a loan. Please mention I'm not providing any loans. Kindly understand the last conversation and answer. Answer I'm not providing any loans/money. If the last one conversation regarding the can you give/borrow money/loan"""

@app.route('/')
def index():
    # Clear the session to start fresh
    session.clear()
    # Initialize a new session
    session['chat_history'] = []
    return render_template('index.html')

@app.route('/api', methods=['POST'])
def chat_api():
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
         # Initialize chat session if not already done
        if 'chat_history' not in session:
            session['chat_history'] = []

        # Start a chat session if necessary
        chat = model.start_chat()

        # Send the initial prompt to set context
        chat.send_message(initial_prompt)

        # Send user message to the chat model
        response = chat.send_message(user_message)
        bot_response = response.text

         # Append messages to the chat history in the session
        session['chat_history'].append({
            'user': user_message,
            'bot': bot_response
        })

        # Optionally generate speech for the response
        generate_speech(bot_response)

        return jsonify({"response": bot_response})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to process your request."}), 500

@app.route('/end_session', methods=['POST'])
def end_session():
    try:
        # Retrieve chat history from the session
        conversation_history = session.get('chat_history', [])
        if not conversation_history:
            return jsonify({"error": "No conversation history found"}), 400

        # Format the conversation history
        formatted_history = "\n".join([f"User: {msg['user']}\nBot: {msg['bot']}" for msg in conversation_history])

        # Create a summary prompt
        summary_prompt = f"""
        Based on the following conversation history, summarize the user's performance, highlighting strengths and areas for improvement:
        {formatted_history}
        """

        # Send the prompt to the model
        chat = model.start_chat()
        chat.send_message(initial_prompt)  # Reinitialize the context
        response = chat.send_message(summary_prompt)
        summary = response.text
        
        # Store the session data in a variable before clearing
        saved_session = dict(session)  # Save session data
        print("Saved Session Data:", saved_session)  # Debugging or logging


        # Store saved session temporarily in the session object
        session['saved_session'] = saved_session

        # Clear the main session but keep saved_session
        session.pop('chat_history', None)

        # Clear session after storing
        # session.clear()

        return jsonify({"summary": summary})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to process the summary request."}), 500
    

@app.route('/clear_session', methods=['POST'])
def clear_session():
    session.pop('chat_history', None)  # Remove chat_history key
    return jsonify({"message": "Session cleared"})


def generate_speech(text):
    try:
        tts = gTTS(text=text, lang='en')
        audio_file = "static/response.mp3"
        tts.save(audio_file)
        print(f"Audio saved to {audio_file}")
    except Exception as e:
        print(f"Failed to generate speech: {e}")

# @app.route('/summary')
# def summary_page():
    # Get session details
    # print("Session Data:", dict(session)) A
    # session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME']) 
    # print("Session ID:", session_id)
    # session_data = dict(session)  # Convert session data to a dictionary
    # return render_template('summary.html',session_id=session_id, session_data=session_data)

@app.route('/summary')
def summary_page():
    # Retrieve the saved session from the session object
    saved_session = session.get('saved_session', {})
    session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME'])  # Get session ID if needed

    print("Session ID:", session_id)
    print("Saved Session Data:", saved_session)

    return render_template('summary.html', session_id=session_id, session_data=saved_session)    

if __name__ == '__main__':
    app.run(debug=True)
