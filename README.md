# LAMB - Learning Assistants Manager and Builder

<div align="center">
  <img src="static/img/lamb_logo.png" alt="LAMB Logo" width="300">
  
  **Create AI assistants for education integrated in your Learning Management System**
  
  [![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](LICENSE)
  [![GitHub](https://img.shields.io/badge/GitHub-Lamb--Project-black)](https://github.com/Lamb-Project/lamb)
</div>

## 📋 Project Description

**LAMB** (Learning Assistants Manager and Builder) is an open-source web platform that enables educators to design, test, and publish AI-based learning assistants into your Learning Management System (LMS like Moodle) without writing any code. It functions as a visual "teaching chatbot builder" that seamlessly combines large language models (GPT-4, Mistral, local models) with your own educational materials.

Developed by Marc Alier and Juanan Pereira, professors and researchers at the Universitat Politècnica de Catalunya (UPC) and Universidad del País Vasco (UPV/EHU), LAMB addresses the critical need for educational AI tools that maintain student privacy while providing powerful, context-aware learning support.

## 🎯 Key Features

### 🎓 **Specialized Subject Tutors**
Design assistants that stay strictly within your chosen subject area, ensuring responses are always educationally appropriate and contextually relevant.

### 📚 **Intelligent Knowledge Ingestion**
Upload educational materials (PDF, Word, Markdown) and LAMB automatically processes them with:
- Flexible data model that preserves context and relationships
- Semantic embeddings optimized for educational search
- Custom metadata support for each document
- Adaptive processing for different content structures
- RAG (Retrieval Augmented Generation) integration

### 🔒 **Privacy-First Architecture**
- The students will access the Learning Assitants as Learning Activities within the LMS Course
- No user information is shared with AI model providers
- Can run on open source and open weights models running on your compute
- Secure, self-hosted solution

### 🔌 **LTI Integration**
Seamlessly integrate with Moodle and other Learning Management Systems through LTI (Learning Tools Interoperability) standard - publish your assistant as an external tool with just a few clicks.

### 🤖 **Multi-Model Support**
- Works with OpenAI API compatible models
- Ollama inetgration
- One-click model switching
- Model-agnostic architecture

### 🔍 **Advanced Testing & Debugging**
- Debug mode showing complete prompts
- Citation tracking with source references


### 🌍 **Multilingual Interface**
Built-in support for Catalan, Spanish, English, and Basque, with easy extensibility for additional languages.  

### 💾 **Portability & Versioning**
- Export/import assistants in JSON format


## 👥 Target Audience

LAMB is designed for:

- **📖 Teachers and Trainers**: Create virtual assistants focused on specific curricula without technical expertise
- **🏫 Educational Institutions**: Integrate AI into existing LMS platforms while maintaining data sovereignty
- **💡 Innovation Teams**: Experiment with different LLMs through a unified management interface
- **🔬 Researchers**: Study AI in education with complete control over the learning environment

## 🏗️ Architecture Overview

LAMB features a modular, extensible architecture:

- **Backend**: FastAPI-based server handling assistant management, LTI integration, and model orchestration
- **Frontend**: Modern Svelte 5 application providing intuitive UI for assistant creation and management
- **Knowledge Base Server**: Dedicated service for document ingestion and vector search
- **Integration Layer**: Bridges with Open WebUI for model management  https://github.com/open-webui/open-webui

## 🚀 Installation

### Recommended: Docker Installation

For the easiest setup experience, we recommend using Docker Compose to run all LAMB services:

📘 **[Docker Installation Guide](docker.md)** - One-command deployment with all services configured

### Alternative: Manual Installation

For development or custom deployments:

📘 **[Complete Installation Guide](installationguide.md)** - Step-by-step manual setup for all components

### Quick Overview

LAMB requires four main services:
1. **Open WebUI Server** (port 8080) - Model management interface
2. **LAMB Knowledge Base Server** (port 9090) - Document processing and vector search
3. **LAMB Backend Server** (port 9099) - Core API and business logic
4. **Frontend Application** (port 5173) - Web interface

## 📖 Documentation

Comprehensive documentation is available in the `/Documentation` directory:

- [Backend Architecture](Documentation/backend-briefing.md)
- [Frontend Development Guide](Documentation/frontend-dev.md)
- [Knowledge Base Integration](Documentation/kb-server-integration.md)
- [Multi-Organization Setup](Documentation/multi_org.md)
- [API Documentation](Documentation/openapi/api.json)

## 🗂️ Project Structure

```
lamb/
├── backend/               # FastAPI backend server
│   ├── lamb/             # Core LAMB functionality
│   ├── creator_interface/# Assistant creation interface
│   └── utils/            # Utility functions
├── frontend/             # Svelte 5 frontend
│   └── svelte-app/      # Main web application
├── lamb-kb-server/       # Knowledge base server
├── Documentation/        # Project documentation
└── docker-compose.yaml   # Container orchestration
```

## 🤝 Contributing

We welcome contributions! LAMB is an open-source project that thrives on community involvement. Areas where you can help:

- 📝 Documentation improvements
- 🌍 Translations to new languages
- 🔌 New LMS integrations
- 🤖 Additional model support
- 🐛 Bug fixes and testing

Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📜 License

LAMB is licensed under the GNU General Public License v3.0 (GPL v3). 

Copyright (c) 2024-2025 Marc Alier (UPC) @granludo & Juanan Pereira (UPV/EHU) @juananpe

See [LICENSE](LICENSE) for full details.

## 🙏 Acknowledgments

- Universidad del País Vasco (UPV/EHU)
- Universitat Politècnica de Catalunya (UPC)
- 
- Open WebUI project for advanced chatbot web interface 
- All contributors and early adopters in the educational community

## 📧 Contact

- **Project Leads**: Marc Alier, Juanan Pereira
- **GitHub**: [https://github.com/Lamb-Project/lamb](https://github.com/Lamb-Project/lamb)
- **Issues**: [GitHub Issues](https://github.com/Lamb-Project/lamb/issues)

---

**LAMB** - Empowering educators to create intelligent, privacy-respecting AI assistants for enhanced learning experiences.

