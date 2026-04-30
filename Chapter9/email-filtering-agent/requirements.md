# Implementing AI Agents in Practice

We are now approaching the end of our journey in building LLM-based agents. Throughout this and 8 chapters, we have covered both the theoretical foundations and practical aspects of designing and developing modern AI agents. Now it’s time to bring everything together.
In this final section, we will walk through an end-to-end example of building an AI agent: a personal email filtering agent. Step by step, we will implement this agent and explore the key design decisions, trade-offs, and challenges that arise in real-world scenarios.

## Email filtering agent – requirements
In Chapter 8, we briefly introduced a personal email filtering agent. Now, let’s apply the design principles from this chapter and walk through the key steps to define and build this agent.
Due to the scope of this book, we will focus on the most important aspects of this agent. However, in practice, production-ready agents would require more detailed design and additional considerations. At the end of this section, we will provide the full code implementation of this agent as well.

### Functional requirements:
We want to develop an agent that processes incoming user emails and performs the following actions:
•	Ignore — if an email is not important, the agent takes no action.
•	Escalate — if an email is urgent and requires immediate attention, the agent sends a mobile push notification to the user.
•	Summarize and log — if an email contains important updates or status information, the agent generates a summary and stores it for inclusion in a daily report.
•	Open dialog — if an email contains open questions or missing information, the agent initiates a follow-up interaction to gather the required details and then classifies the email into one of the categories above.
So, overall, this agent improves the efficiency of email management by automatically categorizing, prioritizing, and summarizing incoming messages, while initiating follow-up actions when needed. This reduces the user’s cognitive load, ensures urgent emails matters are addressed promptly, and minimizes the need for constant manual inbox monitoring.
In addition, the agent should support natural language interaction. Users should be able to ask questions about current or recent emails, as well as historical data within a defined retention window (for example, 6–12 months).
Since the goal is to reduce user effort, the agent should be accessible via a mobile application. This includes sending push notifications for urgent emails, allowing users to query their email activity, and presenting daily summaries.
However, mobile devices cannot efficiently host LLMs (except for very small models), and certain data must be stored and processed externally. Therefore, a server-side component is required to support model inference, data storage, and overall system functionality.
At this stage, we also need to define quality thresholds for the agent. To be useful, the agent should maintain a high level of accuracy in email classification, with no more than 3–5% misclassifications. Similarly, daily reports should capture the vast majority of important information, with no more than 3–5% of key details missed.
In addition, generated summaries must be factually grounded, containing only information derived from emails and avoiding hallucinations.
System requirements:
Since this agent is designed for a large number of individual users, it must support high scale and variable load. At the same time, operational costs must remain low to ensure the solution is affordable for a broad user base.
Users may receive dozens or even hundreds of emails per day, and these emails can vary in size and format, including long text and embedded content such as images. Therefore, the agent must efficiently process high volumes of data while maintaining acceptable latency and cost. This requires careful design of model usage and data processing pipelines to ensure scalability and performance in real-world conditions.

### Interaction mode:
At first glance, this agent may seem to be a background agent, as it processes incoming emails autonomously in background. However, it also needs to interact with users or other agents. For example, by initiating follow-up conversations, sending urgent notifications, presenting daily reports, and answering user questions.
Based on these requirements, this agent is best described as a hybrid one that supports both background processing and conversational interactions.
In this setup, the agent can be triggered by events such as:
•	Incoming emails.
•	User requests, such as asking for daily reports or querying past emails.
As a result, the agent produces outputs such as:
•	Urgent email notifications
•	Daily summaries and reports
•	Interactive responses to user queries

### Implementation approach:
Since this agent is relatively complex and requires both a mobile application, backend storage and processing capabilities, we will use a code-first approach. The mobile application will be implemented in TypeScript, while the backend service will be developed in Python to handle model inference, data storage, and orchestration.
Skills, tools and capabilities:
Based on the functional requirements, the agent needs the following skills, tools, and capabilities:
•	Monitor the user’s inbox and detect new incoming emails.
•	Read and process email content.
•	Send push notifications for urgent emails.
•	Classify emails into categories such as urgent, important, requires follow-up, or ignore.
•	Generate and present daily reports summarizing email activity.
•	Answer user questions about current and historical email reports.
Identifying these capabilities helps determine which external tools, APIs, and systems the agent must integrate with in order to operate effectively.

### Memory, state, and learning:
This agent operates in two main modes: background processing and conversational interaction, each with different memory requirements.
For background processing, the agent analyzes incoming emails, classifies them, and prepares summaries. This part requires only minimal short-term memory (STM), primarily to process the current email and temporarily store intermediate results before updating the daily report.
However, the agent also requires long-term memory (LTM) to persist information across sessions. Specifically, it needs to store:
•	Draft daily reports that accumulate summaries of important (but not urgent) emails throughout the day
•	Historical daily reports retained over a defined period (e.g., 6–12 months)
In addition, the agent supports conversational functionality, including email follow-ups and answering user questions about reports. These interactions will involve multi-turn conversations, requiring efficient short-term memory (STM) to maintain context and ensure coherent dialogue.
Designing memory for this agent therefore involves combining STM for real-time processing with structured LTM for persistence and retrieval across interactions.

### Reasoning and control mechanisms:
In this step, we define how the agent makes decisions and controls its behavior. The agent must support the following decision-making tasks:
•	Classify emails (urgent, important, requires follow-up, or ignore).
•	Answer user questions about daily activity and reports.
•	Initiate and manage follow-ups when additional information is required.
The first two tasks are relatively constrained. Email classification operates on a single input and produces a single label, while answering user questions typically results in a single response.
In contrast, managing follow-ups is more complex and requires explicit control mechanisms to avoid excessive or unnecessary communication. Without proper constraints, the agent may generate too many follow-up messages or create loops. To address this, the agent should enforce rules such as:
•	Single reply per email — do not send multiple follow-ups without receiving a response.
•	Limit the number of follow-ups — for example, no more than 3–5 attempts.
•	Stop when sufficient information is obtained — avoid continuing the conversation unnecessarily.
These control mechanisms ensure that the agent behaves predictably, avoids over-communication, and maintains a good user experience.

### Safety and control boundaries:
Since the agent supports two natural language interfaces, it is essential to implement robust safety mechanisms to ensure appropriate and secure behavior. We will cover safety and responsible AI in more detail in Chapter 10; here, we highlight the most important risks.
In particular, follow-up interactions must be carefully controlled to prevent the exposure of sensitive information. The agent should only engage in focused, task-specific communication and must enforce strict limits on what information can be shared with external users or other agents.
This is especially important because such interfaces can be exploited by malicious actors attempting to extract personal or confidential data. Therefore, the agent must include safeguards such as input validation, response filtering, and clear permission boundaries to protect user data and maintain secure interactions.
Evaluation and success metrics:
We will explore agent evaluation in more detail in Chapter 10. At this stage, it is important to recognize that the overall quality of the agent depends on the quality of the individual tasks it performs. These include:
•	Email classification
•	Email summarization
•	Follow-up question answering
•	User question answering
Each of these tasks must meet a high-quality bar as we mentioned in functional requirements above. For example, incorrect email classification may result in urgent or important messages being missed. Similarly, poor summarization can lead to incomplete or inaccurate daily reports.
Therefore, evaluating and optimizing each component is essential to ensure the reliability and usefulness of the agent as a whole.
Deployment and operations:
Since the agent consists of both a client-side mobile application and a server-side backend, an appropriate deployment and release strategy is required.
The mobile application can be distributed through platforms such as the Apple App Store or Google Play. The backend service, which handles model inference, data processing, and storage, should be deployed in the cloud using providers such as Microsoft Azure, Amazon Web Services, or Google Cloud.
This setup enables scalable, reliable operation while supporting continuous updates and maintenance of both the client and server components.

## Email filtering agent – design
As we can see, this agent is relatively sophisticated. Taking into account the requirements outlined above, we can now derive its high-level architecture, as shown in the diagram below:

Figure . High-level architecture diagram of the personal email filtering agent.
In this diagram, incoming emails are first processed by the personal email agent and then classified into one of several categories. Based on the classification result, the agent takes the appropriate action: ignoring non-relevant emails, summarizing important ones for inclusion in daily reports, escalating urgent messages via push notifications, or initiating a dialog when follow-up is required.
Since the agent consists of both a backend service (server) and a mobile application (client), its functionality is distributed across these components. The backend is responsible for tasks such as email processing, classification, summarization, and data storage, while the mobile application handles user interaction, notifications, and presentation of results.
The following diagram illustrates the high-level client–server architecture of the system:

Figure 2. Client–server architecture of the personal email filtering agent
In this diagram, incoming emails are received from the email server and processed by the backend service. The backend performs classification, summarization, and decision-making, and then sends urgent notifications and daily reports to the mobile application.
The mobile application serves as the primary interface for the user, allowing them to receive notifications, view reports, and submit queries. User requests are sent back to the backend service for processing.
In addition, the backend service can initiate follow-up communications with external users when additional information is required. This architecture separates processing and interaction responsibilities, enabling scalable and efficient operation.
So, we now have a clear picture of the agent’s design and can move on to the implementation phase.

## Email filtering agent – implementation
Now, let’s move to the implementation of the email filtering agent. Since most of the core functionality resides in the backend service, we will focus primarily on that component. The mobile application serves mainly as the user interface, providing access to urgent notifications, daily reports, and conversational interactions.
The agent backend service can be decomposed into the following core components:
•	Email classifier — responsible for emails classification. The input includes the email content and user-defined preferences (e.g., what is considered urgent, important, or ignorable). The output is the assigned category. This component can be implemented using an LLM with prompt engineering and optionally optimized using smaller models with fine-tuning.
•	Email summarizer — responsible for generating a daily summary of important (but not urgent) emails. Since emails arrive continuously, the summary must be built incrementally. We will implement this component with an LLM and prompting.
•	Follow-up service — responsible for initiating follow-up communications when additional information is needed. Inputs include the original email, prior follow-ups, and constraints on what information can be shared. The output is a follow-up message. This component will be implemented with LLMs, prompts, and short-term memory to maintain context.
•	User question responder — responsible for answering user queries about emails and reports. It takes user questions and historical reports as input and produces context-aware responses. This component supports multi-turn conversations and will be implemented using RAG, LLMs, and short-term memory.
•	Short-term memory (STM) — supports multi-turn interactions for both follow-ups and user queries. A hybrid strategy can be used, such as keeping the most recent interactions in full, summarizing older ones, and truncating long histories to control context size.
•	Email report storage — responsible for storing daily reports and enabling retrieval for future queries.
These components form the foundation of the agent. The system can be further enhanced with additional capabilities, such as:
•	Human-in-the-loop (HITL) mechanisms for handling critical or ambiguous situations.
•	Learning from feedback to improve the agent overtime. Here we can use approaches like memory-augmented learning (MAL).
•	MCP and A2A interfaces to expose the agent’s capabilities to other agents and systems.
At this point, you have everything needed to start implementing such an agent. We strongly encourage you to build your own version from scratch. You can use tools such as Claude Code or GitHub Copilot to speed up development. You have all requirements in place. You can then deploy it locally or in the cloud and test it with a simulated mobile application.