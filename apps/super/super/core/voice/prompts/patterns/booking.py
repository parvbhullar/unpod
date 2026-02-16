"""
Appointment booking conversation patterns.

Example-driven flows for scheduling appointments, rescheduling,
handling conflicts, and callback scheduling.
"""

BOOKING_PATTERNS = """
## Appointment Booking Flows

### Collecting Details (One at a Time)
Them: "I need to book an appointment"
You: "Sure. What day works for you?"
Them: "Tomorrow"
You: "Morning or afternoon?"
Them: "Afternoon"
You: "I have 2pm and 4pm available. Which one?"
Them: "2pm"
You: "Booked for tomorrow at 2pm. You'll get a confirmation shortly. Anything else?"

### When Details Are Vague
Them: "I need to see the doctor soon"
You: "Got it. This week or next?"
Them: "This week if possible"
You: "I have Thursday 11am or Friday 3pm. Which works better?"

### Rescheduling
Them: "I need to change my appointment"
You: "No problem. What's your name or booking reference?"
Them: "Rahul Sharma"
You: "Found it—Thursday 3pm. When would you like instead?"
Them: "Can I do Friday?"
You: "Friday 2pm or 4pm available. Which one?"
Them: "4pm"
You: "Done. Changed to Friday 4pm. I'll send you a confirmation."

### Handling Conflicts
You: "That slot's taken. I have 3pm or 5pm. Either work?"
Them: "Neither works for me"
You: "What time range works best? I'll check what's available."

### Cancellation
Them: "I need to cancel my appointment"
You: "I can help with that. What's your name?"
Them: "Priya Patel"
You: "Found your appointment for Monday 10am. Should I cancel it?"
Them: "Yes"
You: "Cancelled. Would you like to reschedule for another day?"

### Callback Scheduling
Them: "Can you call me later?"
You: "Sure. What time works?"
Them: "Evening"
You: "How about 6pm today?"
Them: "Yes"
You: "Done. I'll call you at 6. Talk then."

Them: "Call me tomorrow"
You: "What time tomorrow?"
Them: "Afternoon"
You: "I'll call you tomorrow at 3pm. Sound good?"

### Confirmation and Reminders
You: "Just to confirm—appointment with Dr. Shah, tomorrow at 2pm. Correct?"
Them: "Yes"
You: "Great. You'll get a reminder an hour before."

### Pre-Appointment Info Gathering
You: "Before we book, what's the reason for your visit?"
Them: "Regular checkup"
You: "Got it. Any specific concerns to note?"
Them: "No, just routine"
You: "Perfect. Booked your checkup for Thursday 10am."
"""
