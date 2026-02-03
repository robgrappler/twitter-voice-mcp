import os
import google.generativeai as genai
from openai import OpenAI
from anthropic import Anthropic
from typing import List, Optional, Union
import json
try:
    from PIL import Image
except ImportError:
    Image = None

class AIHandler:
    def __init__(self):
        self.provider = "gemini" # Default
        self.model = "gemini-1.5-flash"
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.voice_profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "voice_profile.txt")
        
        # Initialize default from env if available
        if os.getenv("GEMINI_API_KEY"):
            self.configure("gemini", os.getenv("GEMINI_API_KEY"), "gemini-1.5-flash")
        elif os.getenv("OPENAI_API_KEY"):
            self.configure("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o-mini")
        elif os.getenv("ANTHROPIC_API_KEY"):
            self.configure("anthropic", os.getenv("ANTHROPIC_API_KEY"), "claude-3-haiku-20240307")

    def configure(self, provider: str, api_key: str, model: str = None):
        self.provider = provider.lower()
        self.api_key = api_key
        
        if self.provider == "gemini":
            self.model = model or "gemini-1.5-flash-001" # Try specific version
            genai.configure(api_key=self.api_key)
        elif self.provider == "openai":
            self.model = model or "gpt-4o-mini"
            self.client = OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            self.model = model or "claude-3-haiku-20240307"
            self.client = Anthropic(api_key=self.api_key)
            
    def analyze_style(self, tweets: List[str]) -> str:
        prompt = f"""
        Analyze the following tweets to understand the author's voice, style, and persona.
        Pay attention to:
        1. Tone (e.g., dominant, casual, professional, sarcastic)
        2. Formatting (e.g., capitalization, line breaks, emoji usage)
        3. Vocabulary (e.g., specific slang, jargon)
        4. Themes (e.g., wrestling, fitness, coding)
        
        Tweets:
        {json.dumps(tweets, indent=2)}
        
        Output a concise "Voice Profile" description that can be used to instruct an AI to generate new tweets in this exact style.
        """
        
        response = self._call_model(prompt)
        
        # Save profile
        os.makedirs(os.path.dirname(self.voice_profile_path), exist_ok=True)
        with open(self.voice_profile_path, "w") as f:
            f.write(response)
            
        return response

    def get_voice_profile(self) -> str:
        if os.path.exists(self.voice_profile_path):
            with open(self.voice_profile_path, "r") as f:
                return f.read()
        return "No voice profile found. Please run analyze_voice first."

    def generate_tweet(self, topic: str, count: int = 1) -> List[str]:
        voice_profile = self.get_voice_profile()

        system_instruction = f"""
        You are a ghostwriter for a specific persona. Here is their voice profile:
        <voice_profile>
        {voice_profile}
        </voice_profile>
        
        Constraints:
        - Strictly follow the voice profile (tone, emojis, formatting).
        - Do not include hashtags unless the voice profile explicitly uses them.
        - Under 280 characters.
        - Output ONLY the tweets, one per line (or separated by a clear delimiter like ---).
        - Do not number them.
        """

        prompt = f"""
        Task: Write {count} distinct tweets about the topic in the <topic> tags.
        
        <topic>
        {topic}
        </topic>
        """

        response = self._call_model(prompt, system_instruction=system_instruction)
        tweets = [t.strip() for t in response.split('\n') if t.strip() and not t.strip().startswith('---')]
        # Simple cleanup if the model creates numbered lists
        clean_tweets = []
        for t in tweets:
            if t[0].isdigit() and t[1] in ['.', ')']:
                t = t[2:].strip()
            clean_tweets.append(t)
            
        return clean_tweets[:count]

    def generate_retweet_comment(self, original_tweet_text: str) -> str:
        voice_profile = self.get_voice_profile()

        system_instruction = f"""
        You are a ghostwriter for a specific persona. Here is their voice profile:
        <voice_profile>
        {voice_profile}
        </voice_profile>
        
        Constraints:
        - Strictly follow the voice profile.
        - Add value, agreement, or a dominant take on the original tweet.
        - Under 280 characters.
        - Output ONLY the comment text.
        """

        prompt = f"""
        Task: Write a Quote Tweet comment for the tweet in the <original_tweet> tags.
        
        <original_tweet>
        {original_tweet_text}
        </original_tweet>
        """

        return self._call_model(prompt, system_instruction=system_instruction).strip()

    def generate_tweet_from_image(self, image_path: str, count: int = 1) -> List[str]:
        if not Image:
             return ["Error: Pillow library not installed. Please install it to use image features."]
             
        voice_profile = self.get_voice_profile()

        system_instruction = f"""
        You are a ghostwriter for a specific persona. Here is their voice profile:
        <voice_profile>
        {voice_profile}
        </voice_profile>
        
        Constraints:
        - Strictly follow the voice profile (tone, emojis, formatting).
        - Describe what you see in the image but through the lens of the persona.
        - Under 280 characters.
        - Output ONLY the tweets, one per line.
        """
        
        prompt = f"Task: Analyze the provided image and write {count} distinct tweets based on it."

        try:
            img = Image.open(image_path)
            response = self._call_model(prompt, images=[img], system_instruction=system_instruction)
            
            tweets = [t.strip() for t in response.split('\n') if t.strip() and not t.strip().startswith('---')]
            clean_tweets = []
            for t in tweets:
                if t[0].isdigit() and t[1] in ['.', ')']:
                    t = t[2:].strip()
                clean_tweets.append(t)
                
            return clean_tweets[:count]
        except Exception as e:
            return [f"Error analyzing image: {str(e)}"]

    def _call_model(self, prompt: str, images: list = None, system_instruction: str = None) -> str:
        try:
            if self.provider == "gemini":
                # Initialize model with system instruction if provided
                model = genai.GenerativeModel(self.model, system_instruction=system_instruction)
                if images:
                    response = model.generate_content([prompt, *images])
                else:
                    response = model.generate_content(prompt)
                return response.text
                
            elif self.provider == "openai":
                if images:
                    # TODO: Implement OpenAI Vision support if needed
                    return "Error: Image support only implemented for Gemini currently."

                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                return response.choices[0].message.content
                
            elif self.provider == "anthropic":
                if images:
                     # TODO: Implement Claude Vision support if needed
                    return "Error: Image support only implemented for Gemini currently."

                kwargs = {
                    "model": self.model,
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                }
                if system_instruction:
                    kwargs["system"] = system_instruction

                response = self.client.messages.create(**kwargs)
                return response.content[0].text
                
        except Exception as e:
            return f"Error generating content: {str(e)}"
