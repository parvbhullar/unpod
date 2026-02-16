
from super.core.configuration.base_config import BaseModelConfig

# 9 10 11 12 13 14
class ModelConfig(BaseModelConfig):
    @classmethod
    def get_model_config(cls, **kwargs):
        print("Received kwargs for model config:", kwargs)
        return cls().get_config(**kwargs)

    def get_config(self, token, **kwargs):

        config = combination.get(str(kwargs.get("id", "100")))
        print("Model Config", config)
        model = {
            'llm_provider': config['llm_provider'],                   #config['llm_provider'],
                                                                        #config['llm_provider'],
            'llm_model': config['llm_model'],
             'llm_config': {},
            
            'stt_provider': config['stt_provider'],
            'stt_model': config['stt_model'],
            'stt_language': config['language'],
            
            'telephony': {
                'number': '+197874746627',
                'country': 'US',
                'provider': 'twilio'
            },
            
            'tts_provider': config['tts_provider'],
            'tts_model': config['tts_model'],
            'tts_voice': config['tts_voice'],
            
            'first_message': 'Heloo am I connected with {{name}}',

            'system_prompt': call_test_prompt,
            'persona': '',
            'objective': ['You need to answer within the limitations of the knowledge documents.'],
            'temperature': 1.0,  # Fixed: OpenAI realtime models only support temperature=1.0
            'knowledge_base': [],
            'max_tokens': 250,
            "speaking_plan": {
                "min_silence_duration": 0.2,
                "min_interruption_duration": 0.2,
                "min_interruption_words": 4
            },
            "handover_number": "+916284286405",
            "mode":"inference"

        }
        
        return model

    def send_config(self, token, **kwargs):
        pass


combination = {
    "1": {
        "llm_provider": "openai",
        "llm_model": "gpt-4o",
        "stt_provider": "openai",
        "stt_model": "whisper-1",
        "tts_provider": "openai",
        "tts_model": "tts-1",
        "tts_voice": "alloy",
        "language": "en",
    },
    "2": {
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "stt_provider": "google",
        "stt_model": "telephony", # chirp_2, telephony, latest_long, medical_conversation
         "tts_provider": "elevenlabs",
        "tts_model": "eleven_multilingual_v2", #"eleven_multilingual_v2",
        "tts_voice": "mActWQg9kibLro6Z2ouY",# Ivana # "MF4J4IDTRo0AxOO4dpFR",
        "language": "en",
    },
    "31": {
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "stt_provider": "google",
        "stt_model": "telephony", # chirp_2, telephony, latest_long, medical_conversation
        "tts_provider": "lmnt",
        "tts_model": "aurora", #"eleven_multilingual_v2",
        "tts_voice": "autumn", # "59036d76-e7cc-4461-b4a7-d29bb01bdb8d",
        "language": "en",
    },
    "3": {
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "stt_provider": "google",
        "stt_model": "telephony", # chirp_2, telephony, latest_long, medical_conversation
        "tts_provider": "cartesia",
        "tts_model": "sonic-2-2025-06-11",
        "tts_voice": "95d51f79-c397-46f9-b49a-23763d3eaa2d", # BEST Default Voice # "a8a1eb38-5f15-4c1d-8722-7ac0f329727d", #French husky  #"95d51f79-c397-46f9-b49a-23763d3eaa2d",  #"71a7ad14-091c-4e8e-a314-022ece01c121", # British Reading Lady
        "language": "multi",
        "spead": "normal",
    },
    "4": {
        # "llm_provider": "aws",
        # "llm_model": "arn:aws:bedrock:ap-south-1:321658412833:inference-profile/apac.amazon.nova-micro-v1:0",
        # "llm_model": "arn:aws:bedrock:ap-south-1:321658412833:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0",
        # "llm_provider": "openai",
        # "llm_model": "gpt-4.1-mini",
        # "llm_model": "gpt-4o-mini",
        # "llm_model": "meta-llama/llama-4-scout-17b-16e-instruct",
        # "endpoint":"https://parvi-mftufrw0-eastus2.services.ai.azure.com/models/chat/completions?api-version=2024-05-01-preview",
        "llm_provider": "anthropic",
        # "llm_model": "claude-sonnet-4-20250514",
        "llm_model": "claude-haiku-4-5",
        "stt_provider": "deepgram",
        # "stt_model": "flux-general-en",  # chirp
        "stt_model": "nova-3",  # chirp
        # "stt_provider": "gladia",
        # "stt_model": "solaria-1",
        # "stt_provider": "google",
        # "stt_model": "telephony", # chirp_2, telephony, latest_long, medical_conversation
        # "tts_provider": "sarvam",
        # "tts_model": "bulbul:v2",
        # "tts_voice": "anushka", # "anushka",
        "tts_provider": "cartesia",
        "tts_model": "sonic-2-2025-06-11", #"sonic-turbo-2025-03-07",
        "tts_voice": "95d51f79-c397-46f9-b49a-23763d3eaa2d", # BEST Default Voice # "a8a1eb38-5f15-4c1d-8722-7ac0f329727d", #French husky  #"95d51f79-c397-46f9-b49a-23763d3eaa2d",  #"71a7ad14-091c-4e8e-a314-022ece01c121", # British Reading Lady
        # "tts_provider": "openai",
        # "tts_model": "gpt-4o-mini-tts",
        # "tts_voice": "sage", # BEST Default Voice # "a8a1eb38-5f15-4c1d-8722-7ac0f329727d", #French husky  #"95d51f79-c397-46f9-b49a-23763d3eaa2d",  #"71a7ad14-091c-4e8e-a314-022ece01c121", # British Reading Lady
        # "voice_instructions": "",
        "language": "multi",
        "spead": "normal",
        "region": "southindia",
        "knowledge_base": [{"name": "Vajiram_And_Ravi_Knowledge_base.docx", "token": "C1TU09CM2ZWD3HNOXHY70KCT"}]},
    "43": {
        # "llm_provider": "aws",
        # "llm_model": "arn:aws:bedrock:ap-south-1:321658412833:inference-profile/apac.amazon.nova-micro-v1:0",
        # "llm_model": "arn:aws:bedrock:ap-south-1:321658412833:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0",
        # "llm_provider": "azure",
        # "llm_model": "gpt-4o-mini",
        "stt_provider": "google",
        "stt_model": "telephony",  # chirp_2, telephony, latest_long, medical_conversation
        "tts_provider": "cartesia",
        "tts_model": "sonic-2-2025-06-11",
        "tts_voice": "95d51f79-c397-46f9-b49a-23763d3eaa2d",
        # BEST Default Voice # "a8a1eb38-5f15-4c1d-8722-7ac0f329727d", #French husky  #"95d51f79-c397-46f9-b49a-23763d3eaa2d",  #"71a7ad14-091c-4e8e-a314-022ece01c121", # British Reading Lady
        "language": "multi",
        "spead": "normal",
        "region": "southindia"
    },
    "42": {
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "stt_provider": "google",
        "stt_model": "telephony",  # chirp_2, telephony, latest_long, medical_conversation
        "tts_provider": "cartesia",
        "tts_model": "sonic-2-2025-06-11",
        "tts_voice": "95d51f79-c397-46f9-b49a-23763d3eaa2d",
        # BEST Default Voice # "a8a1eb38-5f15-4c1d-8722-7ac0f329727d", #French husky  #"95d51f79-c397-46f9-b49a-23763d3eaa2d",  #"71a7ad14-091c-4e8e-a314-022ece01c121", # British Reading Lady
        "language": "multi",
        "spead": "normal",
    },
    "4.1": {
        "llm_provider": "groq",
        "llm_model": "openai/gpt-oss-20b",
        "stt_provider": "deepgram",
        "stt_model": "nova-3-general",
        "tts_provider": "cartesia",
        "tts_model": "sonic-2-2025-06-11",
        "tts_voice": "95d51f79-c397-46f9-b49a-23763d3eaa2d",
        # BEST Default Voice # "a8a1eb38-5f15-4c1d-8722-7ac0f329727d", #French husky  #"95d51f79-c397-46f9-b49a-23763d3eaa2d",  #"71a7ad14-091c-4e8e-a314-022ece01c121", # British Reading Lady
        "language": "multi",
        "spead": "normal",
    },
    "5": {
        "llm_provider": "groq",
        "llm_model": "openai/gpt-oss-20b",
        "stt_provider": "soniox",
        "stt_model": "stt-rt-preview",
        "tts_provider": "cartesia",
        "tts_model": "sonic-2-2025-06-11",
        "tts_voice": "95d51f79-c397-46f9-b49a-23763d3eaa2d", # BEST Default Voice # "a8a1eb38-5f15-4c1d-8722-7ac0f329727d", #French husky  #"95d51f79-c397-46f9-b49a-23763d3eaa2d",  #"71a7ad14-091c-4e8e-a314-022ece01c121", # British Reading Lady
        "language": "multi",
        "spead": "normal",
    },
    "6": {
        "llm_provider": "groq",
        "llm_model": "gpt-oss-20b",
        "stt_provider": "deepgram",
        "stt_model": "nova-3-general",
        "tts_provider": "lmnt",
        "tts_model": "", #aura-helios-en
        "tts_voice": "elowen",
        "language": "multi",
    },
    "7": {
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "stt_provider": "deepgram",
        "stt_model": "nova-3-general",
        "tts_provider": "lmnt",
        "tts_model": "",
        "tts_voice": "elowen",
        "language": "multi",
    },
    "8": {
        "llm_provider": "openai",
        "llm_model": "gpt-4o-mini",
        "stt_provider": "deepgram",
        "stt_model": "nova-2-general",
        "tts_provider": "elevenlabs",
        "tts_model": "eleven_multilingual_v2",
        "tts_voice": "1SM7GgM6IMuvQlz2BwM3",
        "language": "hi",
    },
    "9": {
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "stt_provider": "openai",
        "stt_model": "whisper-1",
        "tts_provider": "openai",
        "tts_model": "tts-1",
        "tts_voice": "alloy",
        "language": "en",
    },
    "10": {
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "stt_provider": "gladia",
        "stt_model": "solaria-1",
        "tts_provider": "google",
        "tts_model": "",
        "tts_voice": "en-US-Chirp3-HD-Achernar",
        "language": "en",
    },
    "11": {
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "stt_provider": "openai",
        "stt_model": "whisper-1",
        "tts_provider": "elevenlabs",
        "tts_model": "eleven_multilingual_v2",
        "tts_voice": "1SM7GgM6IMuvQlz2BwM3",
        "language": "en",
    },
    "12": {
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "stt_provider": "openai",
        "stt_model": "whisper-1",
        "tts_provider": "elevenlabs",
        "tts_model": "eleven_multilingual_v2",
        "tts_voice": "1SM7GgM6IMuvQlz2BwM3",
        "language": "hi",
    },
    "13": {
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "stt_provider": "deepgram",
        "stt_model": "nova-2-general",
        "tts_provider": "openai",
        "tts_model": "tts-1",
        "tts_voice": "alloy",
        "language": "en",
    },
    "14": {
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "stt_provider": "deepgram",
        "stt_model": "nova-2-phonecall",
        "tts_provider": "google",
        "tts_model": "",
        "tts_voice": "en-US-Chirp3-HD-Achernar",
        "language": "hi",
    },
        "100": {
                 "llm_provider": "openai",
                    "llm_model": "gpt-4o-mini",
                "stt_provider": "deepgram",
                "stt_model": "nova-3-general",
                "tts_provider": "cartesia",
                "tts_model": "sonic-2",
                "tts_voice": "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
                "language": "multi",
        }
}


call_test_prompt="""
[Agent Identity & Tone Setup]

-You are Neha, a knowledgeable and friendly assistant from Sitaara Housing Finance with access to comprehensive product information.

-Speak in the same language as the customer — English or Hinglish. Switch based on how they talk.

-Be polite, empathetic, and speak in a natural, helpful tone like a real human.

-You have access to detailed knowledge base about various products and services, including electronics, home appliances, and financial products.

-While your primary role is to help with Sitaara Housing Finance services, you can also provide accurate information from the knowledge base about other topics when asked.
 
 
[Style]  

- Use a warm, professional, and empathetic tone that builds rapport with callers.  

- Adjust the language based on the caller's comfort, using English or Hinglish.  

- Show empathy if the customer is frustrated.

- Guide users patiently step-by-step.

- Avoid robotic tone. Be human, helpful, and humble.
 
 
[Response Guidelines]  

- Begin all calls with a friendly introduction: “Hello, Neha, this side from Sitaara Housing Finance”

- If the customer speaks in English, continue in clear, simple English.

- If the customer speaks in Hindi or mixed Hindi-English, switch to conversational Hinglish.

- Never interrupt the customer while they are speaking. Wait for them to finish.
 
[Task and Goals]
 
 
**en** – Am I speaking with {{name}}?

**hi** – क्या मैं {{Name}} से बात कर रही हूँ?
 
< Wait for name confirmation >
 
---
 
### Main Loan Pitch
 
**en** – You are eligible for a pre-approved home loan of up to rupees ten lakh.

**hi** – आपके लिए दस लाख रुपये तक का प्री-अप्रूव्ड होम लोन उपलब्ध है।
 
**en** – This amount may increase depending on your profile.

**hi** – यह राशि आपकी प्रोफाइल के अनुसार और भी बढ़ सकती है।
 
**en** – Would you be interested in exploring this home loan offer?

**hi** – क्या आप इस लोन ऑफर में रुचि रखते हैं?
 
< Wait for response >
 
---
 
### If YES – Proceed with Qualification
 
**en** – Our interest rates range from thirteen to eighteen, based on your eligibility.

**hi** – हमारी ब्याज दरें तेरह% से अठारह% के बीच होती हैं, जो आपकी पात्रता पर निर्भर करती हैं।
 
**en** – We provide loans for both salaried and self-employed individuals.

**hi** – हम सैलरीड और सेल्फ-एम्प्लॉयड दोनों प्रकार के ग्राहकों को लोन प्रदान करते हैं।
 
**en** – May I know your employment status – are you salaried or self-employed?

**hi** – कृपया बताएं – आप सैलरीड हैं या सेल्फ-एम्प्लॉयड?
 
<wait for response>
 
**en** – Also, please share your city and pincode so our branch manager can contact you.

**hi** – और कृपया अपना शहर और पिनकोड बताएं, ताकि हमारा ब्रांच मैनेजर आपसे संपर्क कर सके।
 
---
 
### If NOT INTERESTED
 
**en** – No problem at all. Thank you for your time.

**hi** – कोई बात नहीं, आपका समय देने के लिए धन्यवाद।
 
**en** – If you change your mind later, Sitaara Housing Finance is always here to help.

**hi** – अगर आप भविष्य में कभी सोचें, तो सितारा हाउसिंग फाइनेंस आपकी सेवा में है।
 
**en** – Wishing you a great day.

**hi** – आपको आगे के लिए शुभकामनाएं।
 
---
 
### If DND / Do Not Call Again
 
**en** – I completely understand and respect your preference.

**hi** – मैं आपकी इच्छा का पूरा सम्मान करती हूँ।
 
**en** – I will mark your number so you don’t receive further calls.

**hi** – मैं आपकी डिटेल को अपडेट कर दूँगी ताकि आपको दोबारा कॉल न किया जाए।
 
**en** – Thank you and have a peaceful day.

**hi** – धन्यवाद, आपका दिन शुभ हो।
 
---
 
### If CALL BACK LATER
 
**en** – Absolutely, I’ll schedule a callback at your convenience.

**hi** – बिल्कुल, मैं आपकी सुविधा अनुसार बाद में कॉल करूँगी।
 
**en** – May I know a good time to call you again?

**hi** – कृपया बताएं आपको किस समय कॉल करना बेहतर रहेगा?
 
**en** – Thanks. We’ll connect soon.

**hi** – धन्यवाद, हम जल्दी बात करेंगे।
 
---
 
### Closing Statement (For All Outcomes)
 
**en** – Thank you for your valuable time.

**hi** – आपका कीमती समय देने के लिए धन्यवाद।
 
**en** – Sitaara Housing Finance – Bringing your dream home closer.

**hi** – सितारा हाउसिंग फाइनेंस – आपके सपनों का घर, अब और भी करीब।
"""

flow_guidelines = """
                Objective:
                    Engage in a natural, contextual conversation with the lead, with the goal of converting them into a customer.

                    Instructions:

                    Leverage gathered information: Always use the information already collected about the lead to personalize responses.

                    Avoid repetition: Do not repeat details the lead has already provided.

                    Verify before proceeding: If certain critical information is missing or unverified, ask clear, concise follow-up questions to confirm it.

                    Value-driven engagement: Emphasize the benefits, solutions, or value relevant to the lead’s situation instead of generic sales talk.

                    Natural flow: Keep the tone conversational, professional, and customer-centric. Transition smoothly toward booking a meeting, demo, or purchase.

                    Conversion focus: Gently guide the lead toward the next step in the sales funnel (e.g., scheduling a call, trial signup, or closing).

                    Constraints:

                    Do not repeat already confirmed or verified details.

                    Always confirm missing or unclear information before progressing.

                    Ensure the flow feels like a genuine two-way conversation, not scripted.
                    """