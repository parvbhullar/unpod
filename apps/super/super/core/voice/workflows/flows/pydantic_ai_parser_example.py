"""
Pydantic AI Section Parser - Usage Examples

This module demonstrates how to use the Pydantic AI-based section parser
to extract structured conversation plans from system prompts.

Examples:
1. Basic parsing
2. Accessing extracted components
3. Filtering and searching
4. JSON export
5. Real-world customer service bot
6. Real-world sales bot
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))

from super.core.voice.workflows.flows.pydantic_ai_section_parser import (
    parse_conversation_plan,
    conversation_plan_to_json,
    InstructionType,
    ActionType,
    FieldType,
    RestrictionType,
)


# =============================================================================
# Example 1: Basic Parsing
# =============================================================================

def example_1_basic_parsing():
    """Basic parsing of a simple system prompt."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Parsing")
    print("=" * 70)

    simple_prompt = """
[Identity]
You are Alex, a helpful customer service agent.

[Style]
- Be friendly and professional
- Use clear language

[Task & Goals]
Step 1: Greeting
Greet the customer warmly.

Step 2: Collect Email
Ask for their email address.
Field: email (email type, required)

[Q&A]
Q: What are your hours?
A: We're open 24/7.
Keywords: hours, time, open

[Handover]
If customer asks for manager, transfer them.
Trigger: Keywords ["manager", "supervisor"]

[Restrictions]
- NEVER share passwords
- ALWAYS verify identity
"""

    plan = parse_conversation_plan(simple_prompt, model='openai:gpt-4o-mini')

    print(f"✓ Parsed successfully!")
    print(f"  Instructions: {len(plan.instructions)}")
    print(f"  Steps: {len(plan.steps)}")
    print(f"  Questions: {len(plan.questions)}")
    print(f"  Actions: {len(plan.actions)}")
    print(f"  Guardrails: {len(plan.guardrails)}")


# =============================================================================
# Example 2: Accessing Extracted Components
# =============================================================================

def example_2_accessing_components():
    """Demonstrate accessing different components."""
    print("\n" + "=" * 70)
    print("Example 2: Accessing Components")
    print("=" * 70)

    prompt = """
[Identity]
You are Sarah, a tech support agent.

[Task & Goals]
Step 1: Greeting
Greet the customer.

Step 2: Get Issue
Ask what problem they're experiencing.
Field: issue_description (string, required)

Step 3: Ask for Device
What device are they using?
Field: device_type (enum: Windows, Mac, Linux, required)

[Q&A]
Q: How do I reset my password?
A: Click "Forgot Password" on the login page.
Keywords: password, reset, forgot

Q: What's your support email?
A: support@example.com
Keywords: email, contact, reach

[Handover]
If issue is critical, escalate to senior support.
Trigger: Keywords ["critical", "urgent", "emergency"]
"""

    plan = parse_conversation_plan(prompt, model='openai:gpt-4o-mini')

    # Access instructions
    print("\nInstructions:")
    for inst in plan.instructions:
        print(f"  - {inst.name} ({inst.type})")
        print(f"    Content: {inst.content[:60]}...")

    # Access steps
    print("\nSteps:")
    for step in plan.steps:
        print(f"  {step.order}. {step.name}")
        if step.fields:
            for field in step.fields:
                print(f"     Field: {field.name} ({field.field_type})")
                if field.enum_values:
                    print(f"     Options: {field.enum_values}")

    # Access questions
    print("\nQuestions:")
    for q in plan.questions:
        print(f"  Q: {q.question_text}")
        print(f"  A: {q.answer_text[:50]}...")
        print(f"  Keywords: {q.keywords}")

    # Access actions
    print("\nActions:")
    for action in plan.actions:
        print(f"  - {action.name} ({action.type})")
        if action.triggers:
            for trigger in action.triggers:
                print(f"    Trigger: {trigger.condition_type} = {trigger.condition_value}")


# =============================================================================
# Example 3: Filtering and Searching
# =============================================================================

def example_3_filtering():
    """Demonstrate filtering and searching components."""
    print("\n" + "=" * 70)
    print("Example 3: Filtering and Searching")
    print("=" * 70)

    prompt = """
[Identity]
You are a virtual assistant for a bank.

[Style]
Be professional and secure.

[Guideline]
Always verify identity before sharing account info.

[Task & Goals]
Step 1: Greeting
Welcome the customer.

Step 2: Verify Identity
Ask for account number and last 4 of SSN.
Field: account_number (string, required)
Field: ssn_last_4 (string, required, pattern: ^[0-9]{4}$)

Step 3: Select Service
What would you like help with?
Field: service_type (enum: Balance, Transfer, Statement, Other, required)

[Q&A]
Q: What are my account types?
A: We offer checking, savings, and credit accounts.
Keywords: account, types, kinds

Q: How do I set up online banking?
A: Visit our website and click "Register".
Keywords: online, banking, register, setup

[Restrictions]
- NEVER share full SSN
- NEVER share passwords
- ALWAYS verify identity first
"""

    plan = parse_conversation_plan(prompt, model='openai:gpt-4o-mini')

    # Filter instructions by type
    print("\nIdentity Instructions:")
    identity_instructions = [
        i for i in plan.instructions
        if i.type == InstructionType.IDENTITY
    ]
    for inst in identity_instructions:
        print(f"  - {inst.content}")

    # Filter guidelines
    print("\nGuidelines:")
    guidelines = [
        i for i in plan.instructions
        if i.type == InstructionType.GUIDELINE
    ]
    for guide in guidelines:
        print(f"  - {guide.content}")

    # Find steps with fields
    print("\nSteps with Data Collection:")
    for step in plan.steps:
        if step.fields:
            print(f"  {step.order}. {step.name}")
            for field in step.fields:
                print(f"     - {field.name} ({field.field_type})")
                if field.validation_pattern:
                    print(f"       Pattern: {field.validation_pattern}")

    # Search questions by keyword
    print("\nQuestions about 'account':")
    account_questions = [
        q for q in plan.questions
        if 'account' in q.keywords
    ]
    for q in account_questions:
        print(f"  Q: {q.question_text}")

    # Find guardrails with NEVER restrictions
    print("\nStrict Restrictions (NEVER):")
    never_rules = [
        g for g in plan.guardrails
        if g.type == RestrictionType.NEVER
    ]
    for rule in never_rules:
        print(f"  - {rule.rule}")


# =============================================================================
# Example 4: JSON Export
# =============================================================================

def example_4_json_export():
    """Demonstrate JSON export functionality."""
    print("\n" + "=" * 70)
    print("Example 4: JSON Export")
    print("=" * 70)

    prompt = """
[Identity]
You are a booking assistant for a hotel.

[Task & Goals]
Step 1: Ask for Dates
When would you like to stay?
Field: check_in_date (date, required)
Field: check_out_date (date, required)

Step 2: Room Type
What room type do you prefer?
Field: room_type (enum: Single, Double, Suite, required)
"""

    plan = parse_conversation_plan(prompt, model='openai:gpt-4o-mini')

    # Export to JSON string
    json_str = conversation_plan_to_json(plan)
    print(f"\nJSON Export ({len(json_str)} characters):")
    print(json_str[:500] + "..." if len(json_str) > 500 else json_str)

    # Save to file
    with open('/tmp/conversation_plan.json', 'w') as f:
        f.write(json_str)
    print("\n✓ Saved to /tmp/conversation_plan.json")


# =============================================================================
# Example 5: Real-World Customer Service Bot
# =============================================================================

def example_5_customer_service():
    """Real-world customer service bot example."""
    print("\n" + "=" * 70)
    print("Example 5: Customer Service Bot")
    print("=" * 70)

    customer_service_prompt = """
[Identity]
You are Emma, a friendly and professional customer service agent for TechGadgets Inc.,
an online electronics retailer. You are empathetic, patient, and always aim to resolve
customer issues efficiently.

[Personality]
- Warm and approachable
- Patient with frustrated customers
- Solution-oriented
- Never defensive

[Style & Tone]
- Use conversational language
- Avoid jargon unless necessary
- Show empathy for customer concerns
- Be positive and reassuring

[Guidelines]
- Always acknowledge the customer's concern
- Apologize when appropriate (company's fault)
- Offer solutions, not excuses
- Follow up to ensure satisfaction
- Keep responses concise (2-3 sentences max)

[Task & Goals]
Step 1: Warm Greeting
Greet the customer warmly and introduce yourself as Emma from TechGadgets.
Ask how you can help them today.

Step 2: Collect Order Info
Ask for their order number or email address to look up their order.
Field: identifier (string, required)
Validation: Must be either order number (8 digits) or valid email

Step 3: Identify Issue
Ask what specific issue they're experiencing.
Field: issue_type (enum: Damaged Item, Wrong Item, Late Delivery, Refund Request, Other, required)

Step 4: Issue Details
Ask for more details about their issue.
Field: issue_description (string, required)

Step 5: Offer Solution
Based on the issue type:
- If Damaged Item -> Offer replacement or refund
- If Wrong Item -> Arrange correct item shipment + return label
- If Late Delivery -> Check tracking, offer discount if delayed
- If Refund Request -> Process refund if within policy

Step 6: Confirm Resolution
Confirm that the proposed solution works for them.
Field: customer_satisfied (enum: Yes, No, required)

Branch: If Yes -> Thank and close
Branch: If No -> Step 7 (Escalate)

Step 7: Escalate to Manager
Offer to escalate to a manager for further assistance.
Field: wants_escalation (enum: Yes, No, required)

Branch: If Yes -> Transfer to manager
Branch: If No -> Try alternative solution

[Q&A]
Q: What's your return policy?
A: We accept returns within 30 days of delivery for a full refund.
   Items must be unused and in original packaging.
Keywords: return, policy, refund, days, how long

Q: How long does shipping take?
A: Standard shipping is 5-7 business days. Express shipping is 2-3 business days.
Keywords: shipping, delivery, how long, time, fast

Q: Do you ship internationally?
A: Yes! We ship to most countries. Shipping time and costs vary by location.
Keywords: international, ship, country, worldwide

Q: How do I track my order?
A: You'll receive a tracking number via email once your order ships.
   You can also check your order status in your account.
Keywords: track, tracking, where, status

Q: Can I change my shipping address?
A: If your order hasn't shipped yet, we can update the address.
   Please provide your order number and new address.
Keywords: change, address, update, shipping address

[Actions]
[Handover to Manager]
Transfer the customer to a manager if they explicitly request it or
if you cannot resolve their issue after trying multiple solutions.
Trigger: Keywords ["manager", "supervisor", "speak to someone else"]
Confirmation: "I'll connect you with my manager right away. They'll be able to help you further."

[End Call]
End the conversation once the issue is resolved and customer is satisfied.
Trigger: Customer confirms satisfaction and thanks you
Confirmation: "You're welcome! Is there anything else I can help you with today?"

[Search Knowledge Base]
Search the internal knowledge base for specific product issues or policies.
Trigger: Customer asks about specific product or policy not covered in FAQs
Parameters: search_query (extracted from customer question)

[Restrictions]
- NEVER promise refunds or exchanges without verifying order details first
- NEVER share customer information with unauthorized parties
- NEVER process refunds exceeding order amount
- ALWAYS verify customer identity before accessing account info
- ALWAYS follow company return/refund policy (30 days, unused items)
- NEVER argue with customers even if they're wrong
- NEVER use negative language like "that's not possible" - offer alternatives
"""

    plan = parse_conversation_plan(customer_service_prompt, model='openai:gpt-4o-mini')

    print(f"\n✓ Parsed Customer Service Bot!")
    print(f"\nComponents:")
    print(f"  Instructions: {len(plan.instructions)}")
    print(f"    - Identity: {len([i for i in plan.instructions if i.type == InstructionType.IDENTITY])}")
    print(f"    - Personality: {len([i for i in plan.instructions if i.type == InstructionType.PERSONALITY])}")
    print(f"    - Style: {len([i for i in plan.instructions if i.type == InstructionType.STYLE])}")
    print(f"    - Guidelines: {len([i for i in plan.instructions if i.type == InstructionType.GUIDELINE])}")

    print(f"\n  Steps: {len(plan.steps)}")
    for step in plan.steps[:3]:  # Show first 3
        print(f"    {step.order}. {step.name}")
        if step.fields:
            print(f"       Fields: {[f.name for f in step.fields]}")

    print(f"\n  Questions: {len(plan.questions)}")
    print(f"  Actions: {len(plan.actions)}")
    print(f"  Guardrails: {len(plan.guardrails)}")

    # Show conditional branching
    print(f"\n  Steps with Conditional Branches:")
    for step in plan.steps:
        if step.conditional_branches:
            print(f"    {step.order}. {step.name}")
            for branch in step.conditional_branches:
                print(f"       - {branch.condition} -> {branch.target_step_id or 'next'}")


# =============================================================================
# Example 6: Real-World Sales Bot
# =============================================================================

def example_6_sales_bot():
    """Real-world sales bot example."""
    print("\n" + "=" * 70)
    print("Example 6: Sales Qualification Bot")
    print("=" * 70)

    sales_prompt = """
[Identity]
You are Alex, a professional sales development representative for CloudSolutions,
a B2B SaaS company offering cloud infrastructure management tools.

[Personality]
- Consultative, not pushy
- Genuinely interested in helping
- Professional but personable
- Value-focused

[Task & Goals]
Step 1: Introduction
Introduce yourself and explain you're calling to see if CloudSolutions
might be a good fit for their business.

Step 2: Permission to Continue
Ask if they have 3-5 minutes to discuss their cloud infrastructure needs.
Field: has_time (enum: Yes, No, required)

Branch: If No -> Schedule callback
Branch: If Yes -> Continue to Step 3

Step 3: Current Solution
What cloud infrastructure tools are they currently using?
Field: current_solution (string, required)

Step 4: Team Size
How many people are on their technical team?
Field: team_size (enum: 1-10, 11-50, 51-200, 200+, required)

Step 5: Pain Points
What's their biggest challenge with their current setup?
Field: main_challenge (string, required)

Step 6: Budget
What's their approximate monthly budget for cloud tools?
Field: monthly_budget (enum: < $1000, $1000-$5000, $5000-$20000, $20000+, required)

Step 7: Decision Maker
Are they the primary decision-maker for this purchase?
Field: decision_maker (enum: Yes, No, Part of Committee, required)

Branch: If Yes -> Continue to Step 8
Branch: If No -> Ask who else needs to be involved

Step 8: Qualification Check
Based on responses, determine if they're a qualified lead:
- Team size > 10 AND Budget > $1000 = Qualified
- Else = Not Qualified

Branch: If Qualified -> Schedule demo
Branch: If Not Qualified -> Provide resources and end

[Q&A]
Q: How much does CloudSolutions cost?
A: Our pricing starts at $999/month for up to 50 users. We can provide
   a custom quote based on your specific needs.
Keywords: price, cost, how much, pricing

Q: What makes you different from competitors?
A: We offer 24/7 support, 99.99% uptime SLA, and seamless integration
   with over 100 tools. Our customers save an average of 30% on infrastructure costs.
Keywords: different, competitors, why, better

Q: Do you offer a free trial?
A: Yes, we offer a 14-day free trial with full access to all features.
Keywords: trial, free, test, demo

[Actions]
[Schedule Demo]
Schedule a product demo for qualified leads.
Trigger: Lead is qualified based on budget and team size
Parameters: preferred_date, preferred_time

[Send Resources]
Send informational resources to unqualified or undecided prospects.
Trigger: Lead not qualified or needs more information
Parameters: email_address

[Restrictions]
- NEVER disparage competitors
- NEVER make promises about custom features without engineering approval
- ALWAYS be honest about pricing
- NEVER pressure customers into decisions
- ALWAYS respect if they say they're not interested
"""

    plan = parse_conversation_plan(sales_prompt, model='openai:gpt-4o-mini')

    print(f"\n✓ Parsed Sales Bot!")
    print(f"\nFlow Analysis:")
    print(f"  Total Steps: {len(plan.steps)}")
    print(f"  Steps with Branching: {len([s for s in plan.steps if s.conditional_branches])}")
    print(f"  Fields to Collect: {sum(len(s.fields) for s in plan.steps)}")

    print(f"\n  Qualification Flow:")
    for step in plan.steps:
        print(f"    {step.order}. {step.name}")
        if step.fields:
            for field in step.fields:
                print(f"       → Collect: {field.name}")
        if step.conditional_branches:
            print(f"       → Branches: {len(step.conditional_branches)} paths")


# =============================================================================
# Main Runner
# =============================================================================

def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("PYDANTIC AI SECTION PARSER - USAGE EXAMPLES")
    print("=" * 70)

    examples = [
        ("Basic Parsing", example_1_basic_parsing),
        ("Accessing Components", example_2_accessing_components),
        ("Filtering & Searching", example_3_filtering),
        ("JSON Export", example_4_json_export),
        ("Customer Service Bot", example_5_customer_service),
        ("Sales Bot", example_6_sales_bot),
    ]

    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\n" + "-" * 70)

    # Run all examples
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
