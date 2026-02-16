from super.core.utils.prompts.constants import GENERAL_SEP_PAT, QUESTION_PAT

REQUIRE_CITATION_STATEMENT = """
Cite relevant statements END OF THE STATEMENT using the format [1], [2], [3], etc to reference the ref_number. \
Citations MUST be placed immediately after each statement they support, not at the end of paragraphs. \
Multiple citations [1][2] should be used when a statement is supported by multiple sources. \
Each major claim or fact must be supported by at least one citation. \
DO NOT provide a reference section at the end and DO NOT provide any links following the citations.
""".rstrip()

REQUIRE_CITATION_STATEMENT2 = """
When generating a response, adhere to the following citation and formatting rules:
1. Use inline bracketed citations [1], [2], etc., **only** for factual claims derived from external, verifiable sources.
2. Number citations sequentially in the exact order they first appear, and reuse numbers when citing the same source again.
3. Reset citation numbering at the start of each assistant response.
4. Place each citation immediately after the sentence it supports — no superscripts or footnotes.
5. Do **not** cite chat history, system messages, or user-provided text.
6. For standard queries, cite at least three distinct, high-quality domains; for complex or detailed queries, cite at least five.
7. Group consecutive sentences supported by the same source under one citation to avoid redundancy.
8. Structure responses using markdown headers (`##` for sections, `###` for subsections) without a leading markdown title.
9. Begin with a brief summary paragraph that outlines the response’s key points, then expand in subsequent sections.

These rules ensure that AI-generated answers remain transparent, reliable, and easy to verify.
"""


NO_CITATION_STATEMENT = """
Do not provide any citations even if there are examples in the chat history.
""".rstrip()

CITATION_REMINDER = """
Remember to provide inline citations in the format [1], [2], [3], etc.
"""

ADDITIONAL_INFO = "\n\nAdditional Information:\n\t- {datetime_info}."


CHAT_USER_PROMPT = f"""
Refer to the following context documents when responding to me.{{optional_ignore_statement}}
CONTEXT:
{GENERAL_SEP_PAT}
{{context_docs_str}}
{GENERAL_SEP_PAT}

{{task_prompt}}

{QUESTION_PAT.upper()}
{{user_query}}
""".strip()


CHAT_USER_CONTEXT_FREE_PROMPT = f"""
{{task_prompt}}

{QUESTION_PAT.upper()}
{{user_query}}
""".strip()


# Design considerations for the below:
# - In case of uncertainty, favor yes search so place the "yes" sections near the start of the
#   prompt and after the no section as well to deemphasize the no section
# - Conversation history can be a lot of tokens, make sure the bulk of the prompt is at the start
#   or end so the middle history section is relatively less paid attention to than the main task
# - Works worse with just a simple yes/no, seems asking it to produce "search" helps a bit, can
#   consider doing COT for this and keep it brief, but likely only small gains.

SKIP_SEARCH = "Skip Search"
YES_SEARCH = "Yes Search"

AGGRESSIVE_SEARCH_TEMPLATE = f"""
Given the conversation history and a follow up query, determine if the system should call \
an external search tool to better answer the latest user input.
Your default response is {YES_SEARCH}.

Respond "{SKIP_SEARCH}" if either:
- There is sufficient information in chat history to FULLY and ACCURATELY answer the query AND \
additional information or details would provide little or no value.
- The query is some form of request that does not require additional information to handle.

Conversation History:
{GENERAL_SEP_PAT}
{{chat_history}}
{GENERAL_SEP_PAT}

If you are at all unsure, respond with {YES_SEARCH}.
Respond with EXACTLY and ONLY "{YES_SEARCH}" or "{SKIP_SEARCH}"

Follow Up Input:
{{final_query}}
""".strip()


# TODO, templatize this so users don't need to make code changes to use this
AGGRESSIVE_SEARCH_TEMPLATE_LLAMA2 = f"""
You are an expert of a critical system. Given the conversation history and a follow up query, \
determine if the system should call an external search tool to better answer the latest user input.

Your default response is {YES_SEARCH}.
If you are even slightly unsure, respond with {YES_SEARCH}.

Respond "{SKIP_SEARCH}" if any of these are true:
- There is sufficient information in chat history to FULLY and ACCURATELY answer the query.
- The query is some form of request that does not require additional information to handle.
- You are absolutely sure about the question and there is no ambiguity in the answer or question.

Conversation History:
{GENERAL_SEP_PAT}
{{chat_history}}
{GENERAL_SEP_PAT}

Respond with EXACTLY and ONLY "{YES_SEARCH}" or "{SKIP_SEARCH}"

Follow Up Input:
{{final_query}}
""".strip()

REQUIRE_SEARCH_SINGLE_MSG = f"""
Given the conversation history and a follow up query, determine if the system should call \
an external search tool to better answer the latest user input.

Respond "{YES_SEARCH}" if:
- Specific details or additional knowledge could lead to a better answer.
- There are new or unknown terms, or there is uncertainty what the user is referring to.
- If reading a document cited or mentioned previously may be useful.

Respond "{SKIP_SEARCH}" if:
- There is sufficient information in chat history to FULLY and ACCURATELY answer the query
and additional information or details would provide little or no value.
- The query is some task that does not require additional information to handle.

{GENERAL_SEP_PAT}
Conversation History:
{{chat_history}}
{GENERAL_SEP_PAT}

Even if the topic has been addressed, if more specific details could be useful, \
respond with "{YES_SEARCH}".
If you are unsure, respond with "{YES_SEARCH}".

Respond with EXACTLY and ONLY "{YES_SEARCH}" or "{SKIP_SEARCH}"

Follow Up Input:
{{final_query}}
""".strip()


HISTORY_QUERY_REPHRASE = f"""
Given the following conversation and a follow up input, rephrase the follow up into a SHORT, \
standalone query (which captures any relevant context from previous messages) for a vectorstore.
IMPORTANT: EDIT THE QUERY TO BE AS CONCISE AS POSSIBLE. Respond with a short, compressed phrase \
with mainly keywords instead of a complete sentence.
If there is a clear change in topic, disregard the previous messages.
Strip out any information that is not relevant for the retrieval task.
If the follow up message is an error or code snippet, repeat the same input back EXACTLY.

{GENERAL_SEP_PAT}
Chat History:
{{chat_history}}
{GENERAL_SEP_PAT}

Follow Up Input: {{question}}
Standalone question (Respond with only the short combined query):
""".strip()


# The below prompts are retired
NO_SEARCH = "No Search"
REQUIRE_SEARCH_SYSTEM_MSG = f"""
You are a large language model whose only job is to determine if the system should call an \
external search tool to be able to answer the user's last message.

Respond with "{NO_SEARCH}" if:
- there is sufficient information in chat history to fully answer the user query
- there is enough knowledge in the LLM to fully answer the user query
- the user query does not rely on any specific knowledge

Respond with "{YES_SEARCH}" if:
- additional knowledge about entities, processes, problems, or anything else could lead to a better answer.
- there is some uncertainty what the user is referring to

Respond with EXACTLY and ONLY "{YES_SEARCH}" or "{NO_SEARCH}"
"""


REQUIRE_SEARCH_HINT = f"""
Hint: respond with EXACTLY {YES_SEARCH} or {NO_SEARCH}"
""".strip()


QUERY_REPHRASE_SYSTEM_MSG = """
Given a conversation (between Human and Assistant) and a final message from Human, \
rewrite the last message to be a concise standalone query which captures required/relevant \
context from previous messages. This question must be useful for a semantic (natural language) \
search engine.
""".strip()

QUERY_REPHRASE_USER_MSG = """
Help me rewrite this final message into a standalone query that takes into consideration the \
past messages of the conversation IF relevant. This query is used with a semantic search engine to \
retrieve documents. You must ONLY return the rewritten query and NOTHING ELSE. \
IMPORTANT, the search engine does not have access to the conversation history!

Query:
{final_query}
""".strip()


CHAT_NAMING = f"""
Given the following conversation, provide a SHORT name for the conversation.
IMPORTANT: TRY NOT TO USE MORE THAN 5 WORDS, MAKE IT AS CONCISE AS POSSIBLE.
Focus the name on the important keywords to convey the topic of the conversation.

Chat History:
{{chat_history}}
{GENERAL_SEP_PAT}

Based on the above, what is a short name to convey the topic of the conversation?
""".strip()


STRICT_CONTEXT_GUARDRAIL = """
You are an AI assistant whose sole source of truth is the user’s provided context and memory. Always obey these rules:
1. **Strict Context**  
   - Only reference facts, preferences, and details explicitly stored in the user’s context.  
   - Do not assume, infer, or invent any information beyond what the user has given.
2. **No External Knowledge**  
   - Do not draw on world knowledge, training data, or internet sources not contained in the user’s context.  
   - If the user asks about anything outside that context, respond that you have no information.
3. **Reasoning Within Bounds**  
   - Use your internal reasoning (“brain”) to organize, summarize, or reformulate the given context—but never to add new facts.  
   - If a question cannot be answered from the context alone, admit you cannot answer rather than guess.
4. **Clarity & Fidelity**  
   - Cite or quote the exact segment of context you’re using when you provide an answer.  
   - Keep responses concise and directly tied to the user’s details, preferences, and instructions.
5. **Error Handling**  
   - If you detect a conflict or ambiguity within the user’s provided context, ask a clarifying question rather than resolving it with outside assumptions.

""".strip()