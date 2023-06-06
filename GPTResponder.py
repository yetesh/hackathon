import openai
from keys import OPENAI_API_KEY
from prompts import create_prompt, INITIAL_RESPONSE
import time

openai.api_key = OPENAI_API_KEY

def generate_response_from_transcript(transcript):
    try:
        content = create_prompt(transcript)
        messages = [{"role": "system", "content": content}]
        
        print(f'Sending this to Chat GPT: {messages}')
        response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=messages,
                temperature = 0.0
        )
        print(response)
    except Exception as e:
        print(e)
        return ''
    full_response = response.choices[0].message.content
    try:
        # return full_response.split('[')[1].split(']')[0]
        return full_response
    except Exception as e:
        print(e)
        return ''
    
class GPTResponder:
    def __init__(self):
        self.response = INITIAL_RESPONSE
        self.response_interval = 2

    def respond_to_transcriber(self, transcriber, freeze_state):
        while True:
            if transcriber.transcript_changed_event.is_set() and not freeze_state[0]:
                start_time = time.time()

                transcriber.transcript_changed_event.clear() 
                transcript_string = transcriber.get_transcript()
                response = generate_response_from_transcript(transcript_string)
                
                end_time = time.time()  # Measure end time
                execution_time = end_time - start_time  # Calculate the time it took to execute the function
                
                if response != '':
                    self.response = response

                remaining_time = self.response_interval - execution_time
                if remaining_time > 0:
                    time.sleep(remaining_time)
            else:
                time.sleep(0.3)

    def update_response_interval(self, interval):
        self.response_interval = interval