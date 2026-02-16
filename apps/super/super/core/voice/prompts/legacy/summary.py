context_update_summary="""
You are updating the conversation context after a reset. 
Generate a concise summary that preserves essential user information.

Your goals:
1. Identify and retain the user's name, if mentioned.
2. Retain any personal details the user shared about themselves 
   (e.g., preferences, profile data, goals, interests, requirements).
3. Keep track of what the user has asked for so far or what they are trying to accomplish.
4. Preserve any commitments the assistant made (e.g., "I will do X next").
5. Do NOT include filler text, greetings, or irrelevant dialogue.
6. Do NOT include assistant formatting or markdown—only a plain summary.
7. The summary should be compact but complete enough so the assistant 
   can continue the conversation naturally after a context reset.
"""