# LAMB User Manual
## Learning Assistant Manager and Builder

### User Roles in LAMB

LAMB has three types of users, each with different responsibilities and access levels:

#### 1. System Administrators
- Manage the LAMB installation and configuration
- Set up and maintain the server infrastructure
- Create and manage user accounts
- Configure LMS integrations
- Monitor system performance and security
- Manage API keys and external service connections

#### 2. Assistant Creators
- Create and manage Knowledge Bases
- Design and configure Learning Assistants
- Test and refine assistant responses
- Publish assistants as LTI activities
- Monitor assistant usage and effectiveness
- Update course materials and assistant configurations

#### 3. End Users (Students/Learners)
- Access assistants through LMS courses via LTI activities
- Or use credentials provided by administrators
- Interact with assistants through the chat interface
- Ask questions and receive guided responses
- Access course-specific information and support

### What is LAMB?
LAMB (Learning Assistant Manager and Builder) is an open-source software framework that helps educators create AI-powered learning assistants without needing programming knowledge. Think of it as a tool that lets teachers create their own specialized "ChatGPT-like" assistants that are specifically designed for their courses and integrated into their learning platforms.

### What Can LAMB Do?
- Create customized AI learning assistants that understand your course materials
- Integrate these assistants directly into your learning management system (like Moodle)
- Provide students with instant, accurate responses based on your approved course content
- Help answer student questions using verified course materials
- Maintain privacy and security of educational data

### Key Concepts

#### Learning Assistants
A Learning Assistant is like having a knowledgeable teaching assistant available 24/7 to help students with their questions. Unlike general AI chatbots, these assistants:
- Only use approved course materials as their source of knowledge
- Can reference specific parts of your lectures or materials
- Maintain academic integrity by providing proper citations
- Are integrated directly into your course platform

#### Knowledge Base
The Knowledge Base is like a specialized library for your Learning Assistant. It contains:
- Course materials (lecture transcripts, documents, presentations)
- Additional reference materials you approve
- Structured information that the assistant can easily access and cite

Think of it as giving your assistant all the approved materials it needs to help students effectively.

#### RAG (Retrieval-Augmented Generation)
RAG is the technology that helps your Learning Assistant provide accurate answers. Here's how it works:
1. When a student asks a question, the system searches through your Knowledge Base
2. It finds the most relevant information from your approved materials
3. It uses this information to generate an accurate, contextual response
4. It can provide citations and references to the original materials

This ensures that responses are based on your actual course content rather than general knowledge.

### Creating Your First Learning Assistant

#### Step 1: Prepare Your Materials
1. Gather your course materials (lectures, notes, presentations)
2. Organize them into clear topics or modules
3. Make sure they're in digital format (text, PDF, or video transcripts)

#### Step 2: Create Your Knowledge Base
1. Use LAMB's Content Library Manager to upload your materials
2. Add metadata (descriptions, tags) to help organize the content
3. Let LAMB process the materials into a searchable format

#### Step 3: Design Your Assistant
1. Define the assistant's role and purpose
2. Set up how it should interact with students
3. Test it with sample questions
4. Refine its responses based on test results

### Integration with Learning Management Systems

#### What is IMS LTI?
IMS LTI (Learning Tools Interoperability) is a standard that allows LAMB to connect securely with your learning management system. Think of it as a secure bridge between different educational tools.

#### Integrating with Moodle
LAMB can be added to your Moodle course as an external tool:
1. Your administrator sets up LAMB on your institution's systems
2. You receive connection details (like a special key and password)
3. Add the Learning Assistant to your course using Moodle's external tool feature
4. Students can then access the assistant directly within your course

### Privacy and Security
LAMB takes privacy seriously:
- All data stays within your institution's control
- Student interactions are private and secure
- You can set privacy policies for each assistant
- Complies with educational privacy requirements

### Best Practices

#### For Creating Effective Assistants
1. Start small with a specific topic or module
2. Test thoroughly before making it available to students
3. Gather student feedback and adjust as needed
4. Keep your knowledge base up to date

#### For Using in Your Course
1. Clearly explain to students how to use the assistant
2. Set expectations about what the assistant can and cannot do
3. Encourage students to verify important information
4. Monitor usage and adjust based on student needs

### Getting Help
- Consult your institution's LAMB administrator
- Check the LAMB documentation website
- Join the LAMB educator community
- Share experiences with other educators using LAMB

### The Chat Interface

LAMB's chat interface is based on Open WebUI, an open-source chat interface designed for AI interactions. This provides:
- A familiar chat-style interaction similar to popular messaging apps
- Clear distinction between user questions and assistant responses
- Easy access to chat history
- Support for markdown formatting in responses
- The ability to start new conversations or continue existing ones
- A clean, intuitive design that works well on both desktop and mobile devices

End users will primarily interact with LAMB through this chat interface, which they can access either through their LMS course (via LTI integration) or through direct login if they have been provided credentials.

### Common Questions

**Q: How much technical knowledge do I need?**
A: Very little. If you can use a learning management system, you can use LAMB.

**Q: Can students misuse the assistant?**
A: LAMB assistants only use approved course materials and provide citations, making it clear where information comes from.

**Q: How much time does it take to create an assistant?**
A: Initial setup might take a few hours, but once created, assistants can be reused and refined over time.

**Q: Can I customize how the assistant interacts with students?**
A: Yes, you can define the assistant's tone, response style, and how it uses course materials.

### Conclusion
LAMB provides an accessible way to create AI-powered learning support while maintaining educational standards and privacy. Start small, experiment, and gradually expand your use as you become more comfortable with the system.