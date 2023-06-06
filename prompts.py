INITIAL_RESPONSE = "Welcome to Ecoute 👋"
def create_prompt(transcript):
        return f"""Customer says this.
        
{transcript}.

Please sell Box cloud content management to this customer in concise simple response. Use bullet points to hit as anchors"""